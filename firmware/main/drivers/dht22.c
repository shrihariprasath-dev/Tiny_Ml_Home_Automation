#include "dht22.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "rom/ets_sys.h"

static const char *TAG = "DHT22";

#define DHT_BIT_COUNT   40
#define DHT_TIMEOUT_US  1000

esp_err_t dht22_init(void)
{
    gpio_set_direction(DHT22_GPIO_PIN, GPIO_MODE_INPUT_OUTPUT_OD);
    gpio_set_pull_mode(DHT22_GPIO_PIN, GPIO_PULLUP_ONLY);
    gpio_set_level(DHT22_GPIO_PIN, 1);
    ESP_LOGI(TAG, "DHT22 on GPIO%d", DHT22_GPIO_PIN);
    return ESP_OK;
}

static esp_err_t dht22_await_level(int level, uint32_t timeout_us)
{
    uint32_t elapsed = 0;
    while (gpio_get_level(DHT22_GPIO_PIN) != level) {
        if (elapsed++ >= timeout_us) return ESP_ERR_TIMEOUT;
        ets_delay_us(1);
    }
    return ESP_OK;
}

esp_err_t dht22_read(dht22_data_t *out)
{
    uint8_t data[5] = {0};

    /* Host start signal: pull low >= 1 ms, then release */
    gpio_set_direction(DHT22_GPIO_PIN, GPIO_MODE_OUTPUT_OD);
    gpio_set_level(DHT22_GPIO_PIN, 0);
    vTaskDelay(pdMS_TO_TICKS(2));
    gpio_set_level(DHT22_GPIO_PIN, 1);
    ets_delay_us(30);
    gpio_set_direction(DHT22_GPIO_PIN, GPIO_MODE_INPUT);

    /* Sensor response: 80 µs low, 80 µs high */
    if (dht22_await_level(0, DHT_TIMEOUT_US) != ESP_OK) return ESP_ERR_TIMEOUT;
    if (dht22_await_level(1, DHT_TIMEOUT_US) != ESP_OK) return ESP_ERR_TIMEOUT;
    if (dht22_await_level(0, DHT_TIMEOUT_US) != ESP_OK) return ESP_ERR_TIMEOUT;

    /* Read 40 bits: 50 µs low then high pulse (26–28 µs = 0, ~70 µs = 1) */
    for (int i = 0; i < DHT_BIT_COUNT; i++) {
        if (dht22_await_level(1, DHT_TIMEOUT_US) != ESP_OK) return ESP_ERR_TIMEOUT;
        ets_delay_us(40);
        data[i / 8] <<= 1;
        if (gpio_get_level(DHT22_GPIO_PIN)) data[i / 8] |= 1;
        if (dht22_await_level(0, DHT_TIMEOUT_US) != ESP_OK) return ESP_ERR_TIMEOUT;
    }

    uint8_t checksum = data[0] + data[1] + data[2] + data[3];
    if (checksum != data[4]) {
        ESP_LOGW(TAG, "Checksum error");
        return ESP_ERR_INVALID_CRC;
    }

    out->humidity    = ((data[0] << 8) | data[1]) / 10.0f;
    int16_t raw_temp = ((data[2] & 0x7F) << 8) | data[3];
    out->temperature = raw_temp / 10.0f * ((data[2] & 0x80) ? -1.0f : 1.0f);

    return ESP_OK;
}
