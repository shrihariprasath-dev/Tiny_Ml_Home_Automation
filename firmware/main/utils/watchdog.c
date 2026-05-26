#include "watchdog.h"
#include "esp_task_wdt.h"
#include "esp_log.h"

static const char *TAG = "WATCHDOG";

esp_err_t watchdog_init(void)
{
    esp_task_wdt_config_t cfg = {
        .timeout_ms     = WATCHDOG_TIMEOUT_S * 1000,
        .idle_core_mask = 0,
        .trigger_panic  = true,
    };
    esp_err_t err = esp_task_wdt_init(&cfg);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Task watchdog armed — %ds timeout", WATCHDOG_TIMEOUT_S);
    }
    return err;
}

void watchdog_feed(void)
{
    esp_task_wdt_reset();
}
