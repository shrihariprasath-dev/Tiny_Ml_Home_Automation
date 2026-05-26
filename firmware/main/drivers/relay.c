#include "relay.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "RELAY";

static const int RELAY_PINS[RELAY_COUNT] = {
    RELAY_1_GPIO, RELAY_2_GPIO, RELAY_3_GPIO, RELAY_4_GPIO
};

static bool relay_states[RELAY_COUNT] = {false};

esp_err_t relay_init(void)
{
    gpio_config_t io = {
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
        .pin_bit_mask = ((1ULL << RELAY_1_GPIO) | (1ULL << RELAY_2_GPIO) |
                         (1ULL << RELAY_3_GPIO) | (1ULL << RELAY_4_GPIO)),
    };
    ESP_ERROR_CHECK(gpio_config(&io));

    /* All relays off at startup */
    for (int i = 0; i < RELAY_COUNT; i++) {
        gpio_set_level(RELAY_PINS[i], RELAY_OFF);
        relay_states[i] = false;
    }
    ESP_LOGI(TAG, "Relay module initialised — all off");
    return ESP_OK;
}

esp_err_t relay_set(uint8_t idx, bool on)
{
    if (idx >= RELAY_COUNT) return ESP_ERR_INVALID_ARG;
    relay_states[idx] = on;
    gpio_set_level(RELAY_PINS[idx], on ? RELAY_ON : RELAY_OFF);
    ESP_LOGI(TAG, "Relay %d -> %s", idx + 1, on ? "ON" : "OFF");
    return ESP_OK;
}

bool relay_get(uint8_t idx)
{
    if (idx >= RELAY_COUNT) return false;
    return relay_states[idx];
}

esp_err_t relay_set_all(bool states[RELAY_COUNT])
{
    for (int i = 0; i < RELAY_COUNT; i++) relay_set(i, states[i]);
    return ESP_OK;
}

void relay_get_all(bool states[RELAY_COUNT])
{
    for (int i = 0; i < RELAY_COUNT; i++) states[i] = relay_states[i];
}
