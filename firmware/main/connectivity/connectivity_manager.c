#include "connectivity_manager.h"
#include "wifi_manager.h"
#include "ble_provisioner.h"
#include "mqtt_manager.h"
#include "websocket_client.h"
#include "protocol_defs.h"
#include "storage/nvs_store.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include <string.h>

static const char *TAG = "CONN_MGR";

#define WIFI_CONNECT_TIMEOUT_MS   30000
#define BLE_PROV_TIMEOUT_MS       300000   /* 5 min to receive credentials */

/* ── BLE provisioning wait ───────────────────────────────────────────── */
static void wait_for_ble_provisioning(void)
{
    ESP_LOGI(TAG, "Entering BLE provisioning mode");
    ble_provisioner_init();
    ble_provisioner_start();

    /* Poll until WiFi credentials arrive and WiFi connects */
    uint32_t elapsed = 0;
    while (!wifi_manager_is_connected() && elapsed < BLE_PROV_TIMEOUT_MS) {
        vTaskDelay(pdMS_TO_TICKS(500));
        elapsed += 500;
    }

    if (wifi_manager_is_connected()) {
        ble_provisioner_set_status(BLE_PROV_STATUS_SUCCESS);
        vTaskDelay(pdMS_TO_TICKS(500));   /* let notify reach the app */
        ble_provisioner_stop();
        ESP_LOGI(TAG, "BLE provisioning complete — WiFi connected");
    } else {
        ESP_LOGE(TAG, "BLE provisioning timed out after %lu ms",
                 (unsigned long)BLE_PROV_TIMEOUT_MS);
        ble_provisioner_set_status(BLE_PROV_STATUS_FAILED);
        /* Restart to try again — operator must retry provisioning */
        esp_restart();
    }
}

/* ── Public API ──────────────────────────────────────────────────────── */

esp_err_t connectivity_manager_init(void)
{
    ESP_LOGI(TAG, "Initialising Layer 3 connectivity stack");

    /* ── Step 1: WiFi ── */
    ESP_ERROR_CHECK(wifi_manager_init());

    esp_err_t wifi_start = wifi_manager_start();

    if (wifi_start == ESP_ERR_NOT_FOUND) {
        /* No credentials — enter BLE provisioning */
        wait_for_ble_provisioning();
    } else {
        /* Credentials found — wait for connection */
        ESP_LOGI(TAG, "Waiting for WiFi (timeout=%d ms)", WIFI_CONNECT_TIMEOUT_MS);
        bool connected = wifi_manager_wait_connected(WIFI_CONNECT_TIMEOUT_MS);

        if (!connected) {
            ESP_LOGW(TAG, "WiFi connect timed out — entering BLE provisioning");
            wait_for_ble_provisioning();
        }
    }

    ESP_LOGI(TAG, "WiFi connected");

    /* ── Step 2: MQTT over TLS 1.2 ── */
    ESP_ERROR_CHECK(mqtt_manager_init());
    ESP_ERROR_CHECK(mqtt_manager_start());

    /* ── Step 3: WebSocket (optional — non-fatal if backend not ready) ── */
    char ws_uri[128] = {0};
    nvs_store_get_str("ws_uri", ws_uri, sizeof(ws_uri));

    if (strlen(ws_uri) > 0) {
        if (ws_client_init(ws_uri, NULL) == ESP_OK) {
            ws_client_start();
            ESP_LOGI(TAG, "WebSocket client started → %s", ws_uri);
        }
    } else {
        ESP_LOGD(TAG, "No ws_uri in NVS — WebSocket client skipped");
    }

    ESP_LOGI(TAG, "Layer 3 connectivity stack ready");
    return ESP_OK;
}

bool connectivity_wifi_ready(void)  { return wifi_manager_is_connected(); }
bool connectivity_mqtt_ready(void)  { return mqtt_manager_is_connected(); }
bool connectivity_ws_ready(void)    { return ws_client_is_connected();    }
