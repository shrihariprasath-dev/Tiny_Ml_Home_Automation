#pragma once
#include "esp_err.h"
#include "mqtt_client.h"
#include "protocol_defs.h"
#include <stdint.h>
#include <stdbool.h>

/*
 * MQTT Manager — Layer 3 connection lifecycle owner.
 *
 * Handles:
 *   - TLS 1.2 with embedded CA certificate
 *   - X.509 device certificate (mutual TLS, optional)
 *   - Last Will and Testament (LWT) for offline detection
 *   - Auto-reconnect on disconnect
 *   - QoS-aware publish with per-topic defaults from protocol_defs.h
 *   - Subscribe registry — tasks register callbacks by topic pattern
 *
 * Tasks (Layer 2) call mqtt_manager_publish() / mqtt_manager_subscribe()
 * rather than holding their own esp_mqtt_client_handle_t.
 */

#define MQTT_MAX_SUBSCRIBERS    16
#define MQTT_TOPIC_MAX_LEN      128
#define MQTT_PAYLOAD_MAX_LEN    512

typedef void (*mqtt_msg_cb_t)(const char *topic, int topic_len,
                               const char *data,  int data_len);

typedef struct {
    char         topic[MQTT_TOPIC_MAX_LEN];
    mqtt_msg_cb_t cb;
} mqtt_subscriber_t;

/* ── Lifecycle ───────────────────────────────────────────────────────── */
esp_err_t mqtt_manager_init(void);
esp_err_t mqtt_manager_start(void);
esp_err_t mqtt_manager_stop(void);
bool      mqtt_manager_is_connected(void);

/* ── Publish ─────────────────────────────────────────────────────────── */
/*  qos = -1  →  use per-topic default from protocol_defs.h             */
conn_err_t mqtt_manager_publish(const char *topic, const char *payload,
                                 int qos, bool retain);

/* Shorthand wrappers that enforce the QoS contract */
conn_err_t mqtt_publish_telemetry(const char *json);
conn_err_t mqtt_publish_alert(const char *json);
conn_err_t mqtt_publish_status(bool online);

/* ── Subscribe ───────────────────────────────────────────────────────── */
conn_err_t mqtt_manager_subscribe(const char *topic, int qos,
                                   mqtt_msg_cb_t cb);
conn_err_t mqtt_manager_unsubscribe(const char *topic);
