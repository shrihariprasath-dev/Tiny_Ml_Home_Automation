#pragma once
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "drivers/pzem004t.h"
#include "drivers/acs712.h"
#include "drivers/dht22.h"

#define SENSOR_QUEUE_LEN    10
#define PIR_GPIO_PIN        13
#define STATUS_LED_GPIO     2

typedef struct {
    pzem_data_t pzem;
    float       acs_current_a;
    dht22_data_t dht;
    bool        motion;
    int64_t     timestamp_ms;
} sensor_reading_t;

extern QueueHandle_t g_sensor_queue;

void sensor_task(void *pvParams);
