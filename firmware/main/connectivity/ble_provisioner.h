#pragma once
#include "esp_err.h"
#include <stdbool.h>

/*
 * BLE 5.0 WiFi Credential Provisioner
 *
 * Exposes a custom GATT service with three characteristics:
 *   SSID_CHAR  (Write Without Response) — receive WiFi SSID
 *   PASS_CHAR  (Write Without Response) — receive WiFi password
 *   STATUS_CHAR (Read | Notify)         — provisioning result
 *
 * Mobile app writes SSID then PASSWORD; firmware saves to NVS and
 * signals wifi_manager to reconnect.  BLE is stopped after success.
 *
 * STATUS values:
 *   0x00 = idle / waiting
 *   0x01 = credentials received, connecting
 *   0x02 = connected OK — provisioning complete
 *   0x03 = connection failed — retry
 */

typedef enum {
    BLE_PROV_STATUS_IDLE        = 0x00,
    BLE_PROV_STATUS_CONNECTING  = 0x01,
    BLE_PROV_STATUS_SUCCESS     = 0x02,
    BLE_PROV_STATUS_FAILED      = 0x03,
} ble_prov_status_t;

esp_err_t ble_provisioner_init(void);
esp_err_t ble_provisioner_start(void);
esp_err_t ble_provisioner_stop(void);
bool      ble_provisioner_is_active(void);
void      ble_provisioner_set_status(ble_prov_status_t status);
