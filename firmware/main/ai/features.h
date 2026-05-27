#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

void features_normalize_window(const float *window, size_t len,
                                int8_t *out, float scale, int32_t zero_point);
void features_quantize(const float *input, size_t len,
                       int8_t *out, float scale, int32_t zero_point);
