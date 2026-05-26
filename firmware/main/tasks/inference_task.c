#include "inference_task.h"
#include "tasks/sensor_task.h"
#include "ai/inference.h"
#include "tasks/mqtt_task.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = "INFERENCE_TASK";

volatile inference_result_t g_inference_result = {0};

/* Ring buffer of the last INFERENCE_WINDOW_SIZE power readings */
static float s_power_window[INFERENCE_WINDOW_SIZE];
static int   s_window_idx = 0;
static int   s_window_full = 0;

void inference_task(void *pvParams)
{
    inference_init();
    ESP_LOGI(TAG, "TFLite Micro inference ready — 1 Hz");

    TickType_t last = xTaskGetTickCount();

    for (;;) {
        /* Drain the sensor queue to fill the window — process up to 10 readings */
        sensor_reading_t r;
        while (xQueuePeek(g_sensor_queue, &r, 0) == pdTRUE) {
            xQueueReceive(g_sensor_queue, &r, 0);
            s_power_window[s_window_idx] = r.pzem.power_w;
            s_window_idx = (s_window_idx + 1) % INFERENCE_WINDOW_SIZE;
            if (s_window_idx == 0) s_window_full = 1;
        }

        if (s_window_full) {
            /* Re-order window so it is chronological starting from s_window_idx */
            float ordered[INFERENCE_WINDOW_SIZE];
            for (int i = 0; i < INFERENCE_WINDOW_SIZE; i++) {
                ordered[i] = s_power_window[(s_window_idx + i) % INFERENCE_WINDOW_SIZE];
            }

            float anomaly = inference_run_anomaly(ordered, INFERENCE_WINDOW_SIZE);
            float occupancy = inference_run_occupancy(
                r.pzem.power_w, r.motion, r.dht.temperature);

            g_inference_result.anomaly_score  = anomaly;
            g_inference_result.occupancy_prob = occupancy;

            ESP_LOGD(TAG, "anomaly=%.3f occupancy=%.3f", anomaly, occupancy);

            if (anomaly > ANOMALY_THRESHOLD) {
                char alert[128];
                snprintf(alert, sizeof(alert),
                    "{\"type\":\"anomaly\",\"score\":%.3f,\"severity\":\"high\"}",
                    anomaly);
                mqtt_publish_alert(alert);
                ESP_LOGW(TAG, "Anomaly detected! score=%.3f", anomaly);
            }
        }

        vTaskDelayUntil(&last, pdMS_TO_TICKS(1000));
    }
}
