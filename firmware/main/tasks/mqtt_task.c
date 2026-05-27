#include "mqtt_task.h"
#include "mqtt_client.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "freertos/event_groups.h"
#include "drivers/relay.h"
#include "tasks/sensor_task.h"
#include "cJSON.h"
#include <string.h>
#include <stdio.h>

static const char *TAG = "MQTT_TASK";

#define WIFI_CONNECTED_BIT  BIT0
static EventGroupHandle_t s_wifi_eg;
static esp_mqtt_client_handle_t s_client;

static const char *LWT_PAYLOAD = "{\"online\":false}";

static void on_mqtt_event(void *arg, esp_event_base_t base,
                          int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t ev = event_data;

    switch (ev->event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT connected");
        esp_mqtt_client_subscribe(s_client, TOPIC_CMD_RELAY,  1);
        esp_mqtt_client_subscribe(s_client, TOPIC_CMD_CONFIG, 1);
        esp_mqtt_client_subscribe(s_client, TOPIC_CMD_OTA,    1);
        /* Publish online status */
        esp_mqtt_client_publish(s_client, TOPIC_STATUS,
                                "{\"online\":true}", 0, 1, 1);
        break;

    case MQTT_EVENT_DATA: {
        char topic[128] = {0};
        char payload[256] = {0};
        snprintf(topic, sizeof(topic), "%.*s", ev->topic_len, ev->topic);
        snprintf(payload, sizeof(payload), "%.*s", ev->data_len, ev->data);

        if (strcmp(topic, TOPIC_CMD_RELAY) == 0) {
            /* {"relay": 0, "state": true} */
            cJSON *root = cJSON_Parse(payload);
            if (root) {
                int idx   = cJSON_GetObjectItem(root, "relay")->valueint;
                bool on   = cJSON_IsTrue(cJSON_GetObjectItem(root, "state"));
                relay_set((uint8_t)idx, on);
                cJSON_Delete(root);
            }
        }
        break;
    }

    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected — will reconnect");
        break;

    default:
        break;
    }
}

void mqtt_publish_alert(const char *alert_json)
{
    if (s_client) {
        esp_mqtt_client_publish(s_client, TOPIC_ALERT, alert_json, 0, 2, 0);
    }
}

void mqtt_task(void *pvParams)
{
    /* Wait for WiFi — handled externally by WiFi provisioning code */
    vTaskDelay(pdMS_TO_TICKS(3000));

    esp_mqtt_client_config_t cfg = {
        .broker.address.uri       = MQTT_BROKER_URI,
        .credentials.username     = MQTT_DEVICE_ID,
        .credentials.authentication.password = MQTT_DEVICE_SECRET,
        .session.last_will.topic  = TOPIC_STATUS,
        .session.last_will.msg    = LWT_PAYLOAD,
        .session.last_will.qos    = 1,
        .session.last_will.retain = 1,
    };
    s_client = esp_mqtt_client_init(&cfg);
    esp_mqtt_client_register_event(s_client, ESP_EVENT_ANY_ID,
                                   on_mqtt_event, NULL);
    esp_mqtt_client_start(s_client);

    ESP_LOGI(TAG, "MQTT client started → %s", MQTT_BROKER_URI);

    sensor_reading_t reading;
    char json_buf[512];

    for (;;) {
        if (xQueueReceive(g_sensor_queue, &reading,
                          pdMS_TO_TICKS(200)) != pdTRUE) {
            continue;
        }

        bool relay_states[RELAY_COUNT];
        relay_get_all(relay_states);

        snprintf(json_buf, sizeof(json_buf),
            "{"
            "\"device_id\":\"%s\","
            "\"ts\":%lld,"
            "\"voltage\":%.1f,"
            "\"current\":%.3f,"
            "\"power_w\":%.1f,"
            "\"power_factor\":%.2f,"
            "\"energy_kwh\":%.3f,"
            "\"temperature\":%.1f,"
            "\"humidity\":%.1f,"
            "\"motion\":%s,"
            "\"relay_states\":[%s,%s,%s,%s]"
            "}",
            MQTT_DEVICE_ID,
            reading.timestamp_ms / 1000,
            reading.pzem.voltage,
            reading.pzem.current,
            reading.pzem.power_w,
            reading.pzem.power_factor,
            reading.pzem.energy_kwh,
            reading.dht.temperature,
            reading.dht.humidity,
            reading.motion ? "true" : "false",
            relay_states[0] ? "true" : "false",
            relay_states[1] ? "true" : "false",
            relay_states[2] ? "true" : "false",
            relay_states[3] ? "true" : "false"
        );

        esp_mqtt_client_publish(s_client, TOPIC_TELEMETRY, json_buf, 0, 0, 0);
    }
}
