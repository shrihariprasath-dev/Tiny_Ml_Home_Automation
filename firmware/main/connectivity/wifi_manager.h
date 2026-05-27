#pragma once
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include <stdbool.h>

/* EventGroup bits — other tasks block on these */
#define WIFI_CONNECTED_BIT   BIT0
#define WIFI_FAIL_BIT        BIT1
#define WIFI_PROV_NEEDED_BIT BIT2   /* set when no credentials found or max retries hit */

extern EventGroupHandle_t g_wifi_event_group;

typedef enum {
    WIFI_STATE_UNINIT,
    WIFI_STATE_PROVISIONING,   /* waiting for BLE credential push */
    WIFI_STATE_CONNECTING,
    WIFI_STATE_CONNECTED,
    WIFI_STATE_DISCONNECTED,
} wifi_state_t;

esp_err_t   wifi_manager_init(void);
esp_err_t   wifi_manager_start(void);
wifi_state_t wifi_manager_get_state(void);
bool        wifi_manager_is_connected(void);

/* Called by ble_provisioner once new credentials are saved to NVS */
void        wifi_manager_on_credentials_updated(void);

/* Blocking wait — returns true if connected, false on timeout */
bool        wifi_manager_wait_connected(uint32_t timeout_ms);
