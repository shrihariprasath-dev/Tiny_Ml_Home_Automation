#pragma once

#define INFERENCE_WINDOW_SIZE   10      /* samples fed into anomaly model */
#define ANOMALY_THRESHOLD       0.5f   /* reconstruction error threshold */
#define OCCUPANCY_THRESHOLD     0.6f   /* probability threshold */

typedef struct {
    float anomaly_score;
    float occupancy_prob;
} inference_result_t;

extern volatile inference_result_t g_inference_result;

void inference_task(void *pvParams);
