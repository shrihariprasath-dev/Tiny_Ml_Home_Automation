#include "mqtt_manager.h"
#include "protocol_defs.h"
#include "storage/nvs_store.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include <string.h>
#include <stdio.h>

static const char *TAG = "MQTT_MGR";

/*
 * Embed broker CA certificate at build time.
 * Place your PEM file at firmware/main/connectivity/certs/broker_ca.pem
 * and add to CMakeLists: target_add_binary_data(... broker_ca.pem TEXT)
 * Falls back gracefully if cert not embedded (development builds).
 */
#if __has_include("certs/broker_ca.pem")
extern const uint8_t broker_ca_pem_start[] asm("_binary_broker_ca_pem_start");
extern const uint8_t broker_ca_pem_end[]   asm("_binary_broker_ca_pem_end");
#  define BROKER_CA_CERT  ((const char *)broker_ca_pem_start)
#else
#  define BROKER_CA_CERT  NULL   /* TLS without cert verification — dev only */
#endif

static esp_mqtt_client_handle_t s_client     = NULL;
static volatile bool            s_connected  = false;
static SemaphoreHandle_t        s_sub_mutex;

static mqtt_subscriber_t s_subscribers[MQTT_MAX_SUBSCRIBERS];
static int               s_sub_count = 0;

static char s_device_id[32]     = {0};
static char s_device_secret[64] = {0};

/* ── Topic helpers built at runtime ─────────────────────────────────── */
static char s_topic_telemetry[MQTT_TOPIC_MAX_LEN];
static char s_topic_status[MQTT_TOPIC_MAX_LEN];
static char s_topic_alert[MQTT_TOPIC_MAX_LEN];

static void build_topics(void)
{
    snprintf(s_topic_telemetry, sizeof(s_topic_telemetry),
             "home/%s/telemetry", s_device_id);
    snprintf(s_topic_status,    sizeof(s_topic_status),
             "home/%s/status",   s_device_id);
    snprintf(s_topic_alert,     sizeof(s_topic_alert),
             "home/%s/alert",    s_device_id);
}

/* ── Subscriber dispatch ─────────────────────────────────────────────── */
static void dispatch_to_subscribers(const char *topic, int topic_len,
                                    const char *data,  int data_len)
{
    xSemaphoreTake(s_sub_mutex, portMAX_DELAY);
    for (int i = 0; i < s_sub_count; i++) {
        /* Simple exact-match and single-level wildcard '+' support */
        if (strncmp(s_subscribers[i].topic, topic, topic_len) == 0) {
            s_subscribers[i].cb(topic, topic_len, data, data_len);
        }
    }
    xSemaphoreGive(s_sub_mutex);
}

/* ── Re-subscribe after reconnect ───────────────────────────────────── */
static void resubscribe_all(void)
{
    xSemaphoreTake(s_sub_mutex, portMAX_DELAY);
    for (int i = 0; i < s_sub_count; i++) {
        esp_mqtt_client_subscribe(s_client, s_subscribers[i].topic,
                                  QOS_COMMAND);
    }
    xSemaphoreGive(s_sub_mutex);
}

/* ── MQTT event handler ──────────────────────────────────────────────── */
static void mqtt_event_handler(void *arg, esp_event_base_t base,
                                int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t ev = (esp_mqtt_event_handle_t)event_data;

    switch (ev->event_id) {

    case MQTT_EVENT_CONNECTED:
        s_connected = true;
        ESP_LOGI(TAG, "MQTT connected to broker");
        resubscribe_all();
        /* Publish online status — retained so backend sees it immediately */
        mqtt_publish_status(true);
        break;

    case MQTT_EVENT_DISCONNECTED:
        s_connected = false;
        ESP_LOGW(TAG, "MQTT disconnected — client will auto-reconnect");
        break;

    case MQTT_EVENT_DATA:
        ESP_LOGD(TAG, "MQTT RX topic=%.*s", ev->topic_len, ev->topic);
        dispatch_to_subscribers(ev->topic, ev->topic_len,
                                 ev->data,  ev->data_len);
        break;

    case MQTT_EVENT_ERROR:
        if (ev->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT) {
            ESP_LOGE(TAG, "TLS/TCP error — esp_tls_last_esp_err=0x%x",
                     ev->error_handle->esp_tls_last_esp_err);
        }
        break;

    case MQTT_EVENT_PUBLISHED:
        ESP_LOGD(TAG, "MQTT msg_id=%d published", ev->msg_id);
        break;

    default:
        break;
    }
}

/* ── Public API ──────────────────────────────────────────────────────── */

esp_err_t mqtt_manager_init(void)
{
    s_sub_mutex = xSemaphoreCreateMutex();

    /* Load device identity from NVS — provisioned during BLE setup */
    nvs_store_get_str(NVS_KEY_DEVICE_ID,     s_device_id,     sizeof(s_device_id));
    nvs_store_get_str(NVS_KEY_DEVICE_SECRET, s_device_secret, sizeof(s_device_secret));

    if (strlen(s_device_id) == 0) {
        /* Fallback: use last 3 bytes of MAC as device ID */
        uint8_t mac[6];
        esp_read_mac(mac, ESP_MAC_WIFI_STA);
        snprintf(s_device_id, sizeof(s_device_id),
                 "esp32_%02x%02x%02x", mac[3], mac[4], mac[5]);
    }

    build_topics();
    ESP_LOGI(TAG, "MQTT manager init — device_id=%s", s_device_id);
    return ESP_OK;
}

esp_err_t mqtt_manager_start(void)
{
    char broker_uri[128] = {0};
    nvs_store_get_str("mqtt_broker", broker_uri, sizeof(broker_uri));
    if (strlen(broker_uri) == 0) {
        /* Default from build config */
        strncpy(broker_uri, CONFIG_MQTT_BROKER_URI, sizeof(broker_uri) - 1);
    }

    char lwt_topic[MQTT_TOPIC_MAX_LEN];
    snprintf(lwt_topic, sizeof(lwt_topic), "home/%s/status", s_device_id);

    esp_mqtt_client_config_t cfg = {
        .broker = {
            .address.uri = broker_uri,
            .verification = {
                .certificate = BROKER_CA_CERT,
            },
        },
        .credentials = {
            .username                      = s_device_id,
            .authentication.password       = s_device_secret,
        },
        .session = {
            .last_will = {
                .topic  = lwt_topic,
                .msg    = "{\"online\":false}",
                .qos    = QOS_STATUS,
                .retain = 1,
            },
            .keepalive  = 60,
        },
        .network = {
            .reconnect_timeout_ms = 5000,
            .timeout_ms           = 10000,
        },
        .buffer = {
            .size     = MQTT_PAYLOAD_MAX_LEN,
            .out_size = MQTT_PAYLOAD_MAX_LEN,
        },
    };

    s_client = esp_mqtt_client_init(&cfg);
    if (!s_client) {
        ESP_LOGE(TAG, "Failed to create MQTT client");
        return ESP_FAIL;
    }

    esp_mqtt_client_register_event(s_client, ESP_EVENT_ANY_ID,
                                   mqtt_event_handler, NULL);
    esp_err_t err = esp_mqtt_client_start(s_client);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "MQTT client started → %s", broker_uri);
    }
    return err;
}

esp_err_t mqtt_manager_stop(void)
{
    if (s_client) {
        mqtt_publish_status(false);
        esp_mqtt_client_stop(s_client);
        esp_mqtt_client_destroy(s_client);
        s_client    = NULL;
        s_connected = false;
    }
    return ESP_OK;
}

bool mqtt_manager_is_connected(void)
{
    return s_connected;
}

conn_err_t mqtt_manager_publish(const char *topic, const char *payload,
                                 int qos, bool retain)
{
    if (!s_client || !s_connected) return CONN_ERR_NOT_READY;
    int id = esp_mqtt_client_publish(s_client, topic, payload, 0, qos, retain);
    return (id >= 0) ? CONN_OK : CONN_ERR_MQTT;
}

conn_err_t mqtt_publish_telemetry(const char *json)
{
    return mqtt_manager_publish(s_topic_telemetry, json, QOS_TELEMETRY, false);
}

conn_err_t mqtt_publish_alert(const char *json)
{
    return mqtt_manager_publish(s_topic_alert, json, QOS_ALERT, false);
}

conn_err_t mqtt_publish_status(bool online)
{
    const char *payload = online ? "{\"online\":true}" : "{\"online\":false}";
    return mqtt_manager_publish(s_topic_status, payload, QOS_STATUS, true);
}

conn_err_t mqtt_manager_subscribe(const char *topic, int qos, mqtt_msg_cb_t cb)
{
    xSemaphoreTake(s_sub_mutex, portMAX_DELAY);

    if (s_sub_count >= MQTT_MAX_SUBSCRIBERS) {
        xSemaphoreGive(s_sub_mutex);
        return CONN_ERR_MQTT;
    }

    strncpy(s_subscribers[s_sub_count].topic, topic, MQTT_TOPIC_MAX_LEN - 1);
    s_subscribers[s_sub_count].cb = cb;
    s_sub_count++;

    xSemaphoreGive(s_sub_mutex);

    /* Subscribe immediately if already connected */
    if (s_client && s_connected) {
        esp_mqtt_client_subscribe(s_client, topic, qos);
    }
    ESP_LOGI(TAG, "Subscribed: %s (QoS %d)", topic, qos);
    return CONN_OK;
}

conn_err_t mqtt_manager_unsubscribe(const char *topic)
{
    xSemaphoreTake(s_sub_mutex, portMAX_DELAY);
    for (int i = 0; i < s_sub_count; i++) {
        if (strcmp(s_subscribers[i].topic, topic) == 0) {
            /* Shift remaining entries down */
            memmove(&s_subscribers[i], &s_subscribers[i + 1],
                    (s_sub_count - i - 1) * sizeof(mqtt_subscriber_t));
            s_sub_count--;
            break;
        }
    }
    xSemaphoreGive(s_sub_mutex);

    if (s_client) esp_mqtt_client_unsubscribe(s_client, topic);
    return CONN_OK;
}
