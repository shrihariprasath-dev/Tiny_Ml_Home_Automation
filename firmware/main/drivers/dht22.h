#pragma once
#include <stdint.h>
#include "esp_err.h"

#define DHT22_GPIO_PIN  4

typedef struct {
    float temperature;  /* Celsius */
    float humidity;     /* Percent RH */
} dht22_data_t;

esp_err_t dht22_init(void);
esp_err_t dht22_read(dht22_data_t *out);
