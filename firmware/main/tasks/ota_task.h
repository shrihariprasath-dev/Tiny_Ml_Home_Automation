#pragma once

#define OTA_VERSION_URL  CONFIG_OTA_VERSION_URL
#define OTA_POLL_PERIOD_S  3600   /* check every hour */

void ota_task(void *pvParams);
