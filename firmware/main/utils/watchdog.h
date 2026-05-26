#pragma once
#include "esp_err.h"

#define WATCHDOG_TIMEOUT_S  30

esp_err_t watchdog_init(void);
void      watchdog_feed(void);
