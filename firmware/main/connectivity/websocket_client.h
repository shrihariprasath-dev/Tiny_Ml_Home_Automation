#pragma once
#include "esp_err.h"
#include "protocol_defs.h"
#include <stdbool.h>

/*
 * WebSocket Client — Server → Client real-time channel.
 *
 * Direction per README:  Server → ESP32 (push commands, dashboard sync).
 * The ESP32 connects to the backend WebSocket endpoint and:
 *   - Receives real-time commands (relay, config updates)
 *   - Sends lightweight telemetry frames for low-latency dashboard updates
 *
 * This is a secondary channel — MQTT remains the primary telemetry path.
 * The WebSocket client is optional; it degrades gracefully if the backend
 * endpoint is unavailable.
 */

typedef void (*ws_msg_cb_t)(const char *data, int len);

esp_err_t ws_client_init(const char *uri, ws_msg_cb_t on_message);
esp_err_t ws_client_start(void);
esp_err_t ws_client_stop(void);
bool      ws_client_is_connected(void);
conn_err_t ws_client_send(const char *payload, int len);
