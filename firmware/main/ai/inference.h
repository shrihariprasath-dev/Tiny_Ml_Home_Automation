#pragma once
#include <stdint.h>
#include <stddef.h>

#define TFLITE_ARENA_SIZE   (180 * 1024)   /* 180 KB combined arena */

void  inference_init(void);
float inference_run_anomaly(const float *power_window, size_t len);
float inference_run_occupancy(float power_w, bool motion, float temperature);
