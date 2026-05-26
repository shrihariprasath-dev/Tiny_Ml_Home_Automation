#include "logger.h"
#include "esp_log.h"

void logger_init(void)
{
    esp_log_level_set("*",          ESP_LOG_INFO);
    esp_log_level_set("SENSOR_TASK",ESP_LOG_DEBUG);
    esp_log_level_set("INFERENCE",  ESP_LOG_DEBUG);
    esp_log_level_set("MQTT_TASK",  ESP_LOG_INFO);
    esp_log_level_set("AUTOMATION", ESP_LOG_INFO);
    esp_log_level_set("OTA_TASK",   ESP_LOG_INFO);
    esp_log_level_set("PZEM004T",   ESP_LOG_WARN);
    esp_log_level_set("ACS712",     ESP_LOG_WARN);
    esp_log_level_set("DHT22",      ESP_LOG_WARN);
}
