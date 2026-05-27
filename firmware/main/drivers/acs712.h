#pragma once
#include <stdint.h>
#include "esp_err.h"

#define ACS712_ADC_CHANNEL  ADC1_CHANNEL_6   /* GPIO 34 */
#define ACS712_SENSITIVITY  0.100f           /* 100 mV/A for 20A module */
#define ACS712_VCC          3.3f
#define ACS712_ADC_MAX      4095             /* 12-bit ADC */
#define ACS712_SAMPLES      64               /* oversampling for noise reduction */

esp_err_t acs712_init(void);
float     acs712_read_current_a(void);      /* Returns RMS current in Amps */
