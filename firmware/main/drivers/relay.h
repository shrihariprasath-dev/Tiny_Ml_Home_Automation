#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#define RELAY_COUNT     4

#define RELAY_1_GPIO    26   /* Lights */
#define RELAY_2_GPIO    27   /* Fan */
#define RELAY_3_GPIO    14   /* AC */
#define RELAY_4_GPIO    12   /* Spare */

/* Relays are active-LOW (optocoupled modules) */
#define RELAY_ON        0
#define RELAY_OFF       1

esp_err_t relay_init(void);
esp_err_t relay_set(uint8_t relay_index, bool on);
bool      relay_get(uint8_t relay_index);
esp_err_t relay_set_all(bool states[RELAY_COUNT]);
void      relay_get_all(bool states[RELAY_COUNT]);
