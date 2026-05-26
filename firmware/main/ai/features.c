#include "features.h"
#include <math.h>

/* Normalize window to [0,1] then quantize to INT8 */
void features_normalize_window(const float *window, size_t len,
                                int8_t *out, float scale, int32_t zero_point)
{
    float min_val = window[0], max_val = window[0];
    for (size_t i = 1; i < len; i++) {
        if (window[i] < min_val) min_val = window[i];
        if (window[i] > max_val) max_val = window[i];
    }
    float range = max_val - min_val;
    if (range < 1e-6f) range = 1e-6f;

    for (size_t i = 0; i < len; i++) {
        float norm  = (window[i] - min_val) / range;
        int32_t q   = (int32_t)roundf(norm / scale) + zero_point;
        if (q > 127)  q = 127;
        if (q < -128) q = -128;
        out[i] = (int8_t)q;
    }
}

/* General quantization: float → INT8 using model scale/zero_point */
void features_quantize(const float *input, size_t len,
                       int8_t *out, float scale, int32_t zero_point)
{
    for (size_t i = 0; i < len; i++) {
        int32_t q = (int32_t)roundf(input[i] / scale) + zero_point;
        if (q > 127)  q = 127;
        if (q < -128) q = -128;
        out[i] = (int8_t)q;
    }
}
