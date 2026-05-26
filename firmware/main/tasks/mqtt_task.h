#pragma once
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "tasks/sensor_task.h"

#define MQTT_BROKER_URI     CONFIG_MQTT_BROKER_URI
#define MQTT_DEVICE_ID      CONFIG_MQTT_DEVICE_ID
#define MQTT_DEVICE_SECRET  CONFIG_MQTT_DEVICE_SECRET

#define TOPIC_TELEMETRY     "home/" MQTT_DEVICE_ID "/telemetry"
#define TOPIC_CMD_RELAY     "home/" MQTT_DEVICE_ID "/cmd/relay"
#define TOPIC_CMD_CONFIG    "home/" MQTT_DEVICE_ID "/cmd/config"
#define TOPIC_CMD_OTA       "home/" MQTT_DEVICE_ID "/cmd/ota_trigger"
#define TOPIC_STATUS        "home/" MQTT_DEVICE_ID "/status"
#define TOPIC_ALERT         "home/" MQTT_DEVICE_ID "/alert"

void mqtt_task(void *pvParams);
void mqtt_publish_alert(const char *alert_json);
