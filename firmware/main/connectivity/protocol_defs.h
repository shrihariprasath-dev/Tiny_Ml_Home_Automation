#pragma once

/* ── MQTT Topic Definitions ──────────────────────────────────────────────── */

#define MQTT_TOPIC_TELEMETRY(id)     "home/" id "/telemetry"
#define MQTT_TOPIC_CMD_RELAY(id)     "home/" id "/cmd/relay"
#define MQTT_TOPIC_CMD_CONFIG(id)    "home/" id "/cmd/config"
#define MQTT_TOPIC_CMD_OTA(id)       "home/" id "/cmd/ota_trigger"
#define MQTT_TOPIC_STATUS(id)        "home/" id "/status"
#define MQTT_TOPIC_ALERT(id)         "home/" id "/alert"
#define MQTT_TOPIC_BROADCAST         "home/gateway/broadcast"
#define MQTT_TOPIC_DISCOVERY         "home/gateway/discovery"
#define MQTT_TOPIC_PREDICTIONS       "home/analytics/predictions"
#define MQTT_TOPIC_INSIGHTS          "home/analytics/insights"

/* ── MQTT QoS Levels ─────────────────────────────────────────────────────── */
/*
 * QoS 0 — telemetry   : high-frequency, occasional loss acceptable
 * QoS 1 — commands    : at-least-once delivery for relay control
 * QoS 1 — status/LWT  : retained online/offline state
 * QoS 2 — alerts      : exactly-once, critical anomaly events
 */
#define QOS_TELEMETRY   0
#define QOS_COMMAND     1
#define QOS_STATUS      1
#define QOS_ALERT       2

/* ── WiFi ────────────────────────────────────────────────────────────────── */
#define WIFI_MAX_RETRIES        5
#define WIFI_BACKOFF_BASE_MS    1000   /* doubled each retry */
#define WIFI_SSID_MAX_LEN       32
#define WIFI_PASS_MAX_LEN       64
#define NVS_KEY_WIFI_SSID       "wifi_ssid"
#define NVS_KEY_WIFI_PASS       "wifi_pass"
#define NVS_KEY_DEVICE_ID       "device_id"
#define NVS_KEY_DEVICE_SECRET   "device_secret"

/* ── BLE Provisioning ────────────────────────────────────────────────────── */
/* Custom 128-bit UUIDs for WiFi provisioning GATT service */
#define BLE_PROV_SERVICE_UUID   0xAB, 0xCD, 0x00, 0x01, 0xEF, 0x12, \
                                0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, \
                                0xF0, 0x12, 0x34, 0x56
#define BLE_PROV_SSID_CHAR_UUID 0xAB, 0xCD, 0x00, 0x02, 0xEF, 0x12, \
                                0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, \
                                0xF0, 0x12, 0x34, 0x56
#define BLE_PROV_PASS_CHAR_UUID 0xAB, 0xCD, 0x00, 0x03, 0xEF, 0x12, \
                                0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, \
                                0xF0, 0x12, 0x34, 0x56
#define BLE_PROV_STAT_CHAR_UUID 0xAB, 0xCD, 0x00, 0x04, 0xEF, 0x12, \
                                0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, \
                                0xF0, 0x12, 0x34, 0x56
#define BLE_DEVICE_NAME_PREFIX  "SmartHome-"
#define BLE_ADV_INTERVAL_MS     160    /* 100 ms in units of 0.625 ms */

/* ── WebSocket ───────────────────────────────────────────────────────────── */
#define WS_RECONNECT_TIMEOUT_MS  5000
#define WS_SEND_TIMEOUT_MS       2000
#define WS_BUFFER_SIZE           1024

/* ── HTTP REST (offline) ─────────────────────────────────────────────────── */
#define REST_SERVER_PORT         80
#define REST_MAX_URI_HANDLERS    8

/* ── Protocol status codes used across connectivity modules ─────────────── */
typedef enum {
    CONN_OK              = 0,
    CONN_ERR_WIFI        = 1,
    CONN_ERR_MQTT        = 2,
    CONN_ERR_BLE         = 3,
    CONN_ERR_WS          = 4,
    CONN_ERR_TIMEOUT     = 5,
    CONN_ERR_NOT_READY   = 6,
} conn_err_t;
