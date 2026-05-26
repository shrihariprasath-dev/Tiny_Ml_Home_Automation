#pragma once
#include <stdint.h>
#include "esp_err.h"

#define PZEM_UART_PORT   UART_NUM_2
#define PZEM_RX_PIN      16
#define PZEM_TX_PIN      17
#define PZEM_BAUD_RATE   9600

typedef struct {
    float voltage;      /* Volts */
    float current;      /* Amps */
    float power_w;      /* Watts */
    float energy_kwh;   /* kWh */
    float frequency;    /* Hz */
    float power_factor;
    uint8_t alarm;
} pzem_data_t;

esp_err_t pzem004t_init(void);
esp_err_t pzem004t_read(pzem_data_t *out);
esp_err_t pzem004t_reset_energy(void);
