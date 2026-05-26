#include "sensor_task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "SENSOR_TASK";

QueueHandle_t g_sensor_queue;

static void pir_isr_handler(void *arg)
{
    /* Handled via gpio_get_level in the task loop to avoid ISR-safe queue issues */
}

void sensor_task(void *pvParams)
{
    g_sensor_queue = xQueueCreate(SENSOR_QUEUE_LEN, sizeof(sensor_reading_t));

    pzem004t_init();
    acs712_init();
    dht22_init();

    /* PIR GPIO — interrupt on rising edge */
    gpio_config_t pir_cfg = {
        .pin_bit_mask = (1ULL << PIR_GPIO_PIN),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLDOWN_ENABLE,
        .intr_type    = GPIO_INTR_POSEDGE,
    };
    gpio_config(&pir_cfg);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(PIR_GPIO_PIN, pir_isr_handler, NULL);

    /* Status LED */
    gpio_set_direction(STATUS_LED_GPIO, GPIO_MODE_OUTPUT);

    ESP_LOGI(TAG, "Sensor task started — 10 Hz polling");

    TickType_t last = xTaskGetTickCount();

    for (;;) {
        sensor_reading_t reading = {0};
        reading.timestamp_ms = esp_timer_get_time() / 1000;

        if (pzem004t_read(&reading.pzem) != ESP_OK) {
            ESP_LOGW(TAG, "PZEM read failed");
        }

        reading.acs_current_a = acs712_read_current_a();

        if (dht22_read(&reading.dht) != ESP_OK) {
            ESP_LOGW(TAG, "DHT22 read failed");
        }

        reading.motion = (bool)gpio_get_level(PIR_GPIO_PIN);

        /* Blink LED on each reading */
        gpio_set_level(STATUS_LED_GPIO, 1);

        if (xQueueSend(g_sensor_queue, &reading, 0) != pdTRUE) {
            ESP_LOGW(TAG, "Sensor queue full — dropping reading");
        }

        gpio_set_level(STATUS_LED_GPIO, 0);

        /* 10 Hz = 100 ms period */
        vTaskDelayUntil(&last, pdMS_TO_TICKS(100));
    }
}
