#pragma once
#include "tasks/automation_task.h"
#include <stdint.h>

esp_err_t nvs_store_init(void);
esp_err_t nvs_store_set_str(const char *key, const char *value);
esp_err_t nvs_store_get_str(const char *key, char *buf, size_t len);
esp_err_t nvs_store_set_u32(const char *key, uint32_t value);
esp_err_t nvs_store_get_u32(const char *key, uint32_t *out);
esp_err_t nvs_store_load_rules(automation_rule_t *rules, int max);
esp_err_t nvs_store_save_rules(const automation_rule_t *rules, int count);
esp_err_t nvs_store_load_schedules(schedule_entry_t *sched, int max);
esp_err_t nvs_store_save_schedules(const schedule_entry_t *sched, int count);
