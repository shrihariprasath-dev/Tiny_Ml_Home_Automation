#include "display_task.h"
#include "drivers/ssd1306.h"
#include "tasks/sensor_task.h"
#include "tasks/inference_task.h"
#include "drivers/relay.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "DISPLAY_TASK";

void display_task(void *pvParams)
{
    ssd1306_init();
    ESP_LOGI(TAG, "Display task started — 0.5 Hz refresh");

    TickType_t last = xTaskGetTickCount();
    sensor_reading_t r = {0};

    for (;;) {
        xQueuePeek(g_sensor_queue, &r, pdMS_TO_TICKS(100));

        bool relays[RELAY_COUNT];
        relay_get_all(relays);

        ssd1306_clear();

        ssd1306_set_cursor(0, 0);
        ssd1306_printf("%.0fV %.1fA %.0fW", r.pzem.voltage,
                        r.pzem.current, r.pzem.power_w);

        ssd1306_set_cursor(0, 1);
        ssd1306_printf("T:%.1fC H:%.0f%%", r.dht.temperature, r.dht.humidity);

        ssd1306_set_cursor(0, 2);
        ssd1306_printf("Mot:%s Occ:%.0f%%",
                        r.motion ? "Y" : "N",
                        g_inference_result.occupancy_prob * 100.0f);

        ssd1306_set_cursor(0, 3);
        ssd1306_printf("R:[%c%c%c%c] Anom:%.2f",
                        relays[0]?'1':'-', relays[1]?'1':'-',
                        relays[2]?'1':'-', relays[3]?'1':'-',
                        g_inference_result.anomaly_score);

        ssd1306_flush();

        vTaskDelayUntil(&last, pdMS_TO_TICKS(2000));
    }
}
