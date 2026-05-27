#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_wifi.h"

#include "tasks/sensor_task.h"
#include "tasks/mqtt_task.h"
#include "tasks/inference_task.h"
#include "tasks/web_server_task.h"
#include "tasks/automation_task.h"
#include "tasks/ota_task.h"
#include "tasks/display_task.h"
#include "storage/nvs_store.h"
#include "utils/logger.h"
#include "utils/watchdog.h"
#include "connectivity/connectivity_manager.h"

static const char *TAG = "APP_MAIN";

void app_main(void)
{
    /* Initialize NVS — required by WiFi driver */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    ESP_ERROR_CHECK(esp_event_loop_create_default());

    logger_init();
    nvs_store_init();
    watchdog_init();

    ESP_LOGI(TAG, "Starting Smart Home firmware v%s", CONFIG_APP_PROJECT_VER);

    /*
     * Layer 3 — bring up WiFi (+ BLE provisioning if needed),
     * MQTT/TLS, and WebSocket before launching application tasks.
     * This blocks until the network stack is ready.
     */
    ESP_ERROR_CHECK(connectivity_manager_init());

    /*
     * Core affinity:
     *   Core 1 — sensor_task, inference_task, automation_task  (time-critical)
     *   Core 0 — mqtt_task, web_server_task, ota_task, display_task (network/IO)
     */
    xTaskCreatePinnedToCore(sensor_task,      "sensor",     4096, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(inference_task,   "inference",  8192, NULL, 4, NULL, 1);
    xTaskCreatePinnedToCore(automation_task,  "automation", 4096, NULL, 4, NULL, 1);
    xTaskCreatePinnedToCore(mqtt_task,        "mqtt",       6144, NULL, 6, NULL, 0);
    xTaskCreatePinnedToCore(web_server_task,  "web_server", 4096, NULL, 3, NULL, 0);
    xTaskCreatePinnedToCore(ota_task,         "ota",        4096, NULL, 2, NULL, 0);
    xTaskCreatePinnedToCore(display_task,     "display",    2048, NULL, 1, NULL, 0);
}
