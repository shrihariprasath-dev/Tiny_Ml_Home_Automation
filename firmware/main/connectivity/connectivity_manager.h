#pragma once
#include "esp_err.h"
#include "protocol_defs.h"

/*
 * Connectivity Manager — single entry point for Layer 3 startup.
 *
 * Boot sequence:
 *   1. wifi_manager_init()  — register event handlers, load credentials
 *   2. If credentials found → wifi_manager_start() → wait for IP
 *      If no credentials   → ble_provisioner_init() + ble_provisioner_start()
 *                            → block until wifi_manager_on_credentials_updated()
 *                            → stop BLE, proceed to step 3
 *   3. mqtt_manager_init()  — load device identity, build topics
 *   4. mqtt_manager_start() — connect to broker over TLS 1.2
 *   5. ws_client_init()     — optional WebSocket to backend
 *   6. ws_client_start()
 *
 * Called once from app_main before launching application tasks.
 */
esp_err_t connectivity_manager_init(void);

/* Individual getters for task-level status checks */
bool connectivity_wifi_ready(void);
bool connectivity_mqtt_ready(void);
bool connectivity_ws_ready(void);
