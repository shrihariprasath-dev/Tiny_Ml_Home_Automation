#include "acs712.h"
#include "driver/adc.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "ACS712";

esp_err_t acs712_init(void)
{
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ACS712_ADC_CHANNEL, ADC_ATTEN_DB_11);
    ESP_LOGI(TAG, "ADC1 channel 6 (GPIO34) initialised");
    return ESP_OK;
}

float acs712_read_current_a(void)
{
    /* Midpoint of ADC range corresponds to 0 A (VCC/2) */
    float midpoint = ACS712_ADC_MAX / 2.0f;
    float sum_sq = 0.0f;

    for (int i = 0; i < ACS712_SAMPLES; i++) {
        float raw = (float)adc1_get_raw(ACS712_ADC_CHANNEL);
        float delta = raw - midpoint;
        float volts = (delta / ACS712_ADC_MAX) * ACS712_VCC;
        float current = volts / ACS712_SENSITIVITY;
        sum_sq += current * current;
    }

    /* RMS current */
    return sqrtf(sum_sq / ACS712_SAMPLES);
}
