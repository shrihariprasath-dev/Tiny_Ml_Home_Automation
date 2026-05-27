#include "wifi_manager.h"
#include "protocol_defs.h"
#include "storage/nvs_store.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = "WIFI_MGR";

EventGroupHandle_t g_wifi_event_group;

static volatile wifi_state_t s_state      = WIFI_STATE_UNINIT;
static volatile int          s_retry_cnt  = 0;

/* ── Event handlers ────────────────────────────────────────────────────── */

static void on_wifi_event(void *arg, esp_event_base_t base,
                          int32_t id, void *data)
{
    if (id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        s_state = WIFI_STATE_CONNECTING;

    } else if (id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(g_wifi_event_group, WIFI_CONNECTED_BIT);
        s_state = WIFI_STATE_DISCONNECTED;

        if (s_retry_cnt < WIFI_MAX_RETRIES) {
            /* Exponential back-off: 1s, 2s, 4s, 8s, 16s */
            uint32_t delay_ms = WIFI_BACKOFF_BASE_MS << s_retry_cnt;
            ESP_LOGW(TAG, "Disconnected — retry %d/%d in %lu ms",
                     s_retry_cnt + 1, WIFI_MAX_RETRIES, (unsigned long)delay_ms);
            vTaskDelay(pdMS_TO_TICKS(delay_ms));
            esp_wifi_connect();
            s_retry_cnt++;
        } else {
            ESP_LOGE(TAG, "Max retries reached — provisioning required");
            xEventGroupSetBits(g_wifi_event_group,
                               WIFI_FAIL_BIT | WIFI_PROV_NEEDED_BIT);
            s_state = WIFI_STATE_PROVISIONING;
        }

    } else if (id == WIFI_EVENT_STA_CONNECTED) {
        ESP_LOGI(TAG, "Associated to AP — waiting for IP");
    }
}

static void on_ip_event(void *arg, esp_event_base_t base,
                        int32_t id, void *data)
{
    if (id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *ev = (ip_event_got_ip_t *)data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&ev->ip_info.ip));
        s_retry_cnt = 0;
        s_state     = WIFI_STATE_CONNECTED;
        xEventGroupClearBits(g_wifi_event_group, WIFI_FAIL_BIT);
        xEventGroupSetBits(g_wifi_event_group,   WIFI_CONNECTED_BIT);
    }
}

/* ── Public API ────────────────────────────────────────────────────────── */

esp_err_t wifi_manager_init(void)
{
    g_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, on_wifi_event, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, on_ip_event, NULL, NULL));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));

    s_state = WIFI_STATE_DISCONNECTED;
    ESP_LOGI(TAG, "WiFi manager initialised");
    return ESP_OK;
}

esp_err_t wifi_manager_start(void)
{
    char ssid[WIFI_SSID_MAX_LEN] = {0};
    char pass[WIFI_PASS_MAX_LEN] = {0};

    esp_err_t ssid_err = nvs_store_get_str(NVS_KEY_WIFI_SSID, ssid, sizeof(ssid));
    esp_err_t pass_err = nvs_store_get_str(NVS_KEY_WIFI_PASS, pass, sizeof(pass));

    if (ssid_err != ESP_OK || strlen(ssid) == 0) {
        ESP_LOGW(TAG, "No WiFi credentials in NVS — triggering BLE provisioning");
        s_state = WIFI_STATE_PROVISIONING;
        xEventGroupSetBits(g_wifi_event_group, WIFI_PROV_NEEDED_BIT);
        return ESP_ERR_NOT_FOUND;
    }

    wifi_config_t wifi_cfg = {0};
    strncpy((char *)wifi_cfg.sta.ssid,     ssid, sizeof(wifi_cfg.sta.ssid));
    strncpy((char *)wifi_cfg.sta.password, pass, sizeof(wifi_cfg.sta.password));

    /* Require PMF capable — WPA3 / WPA2 compatible */
    wifi_cfg.sta.pmf_cfg.capable  = true;
    wifi_cfg.sta.pmf_cfg.required = false;
    wifi_cfg.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Connecting to SSID: %s", ssid);
    return ESP_OK;
}

void wifi_manager_on_credentials_updated(void)
{
    ESP_LOGI(TAG, "New credentials received — restarting WiFi connection");
    s_retry_cnt = 0;
    xEventGroupClearBits(g_wifi_event_group,
                         WIFI_FAIL_BIT | WIFI_PROV_NEEDED_BIT);
    esp_wifi_disconnect();
    wifi_manager_start();
}

wifi_state_t wifi_manager_get_state(void)
{
    return s_state;
}

bool wifi_manager_is_connected(void)
{
    return (s_state == WIFI_STATE_CONNECTED);
}

bool wifi_manager_wait_connected(uint32_t timeout_ms)
{
    EventBits_t bits = xEventGroupWaitBits(
        g_wifi_event_group,
        WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
        pdFALSE, pdFALSE,
        pdMS_TO_TICKS(timeout_ms));

    return (bits & WIFI_CONNECTED_BIT) != 0;
}
