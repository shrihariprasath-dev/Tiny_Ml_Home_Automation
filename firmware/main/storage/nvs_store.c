#include "nvs_store.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG      = "NVS_STORE";
static const char *NVS_NS   = "smarthome";

esp_err_t nvs_store_init(void)
{
    ESP_LOGI(TAG, "NVS namespace: %s", NVS_NS);
    return ESP_OK;
}

esp_err_t nvs_store_set_str(const char *key, const char *value)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err != ESP_OK) return err;
    err = nvs_set_str(h, key, value);
    if (err == ESP_OK) nvs_commit(h);
    nvs_close(h);
    return err;
}

esp_err_t nvs_store_get_str(const char *key, char *buf, size_t len)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READONLY, &h);
    if (err != ESP_OK) return err;
    err = nvs_get_str(h, key, buf, &len);
    nvs_close(h);
    return err;
}

esp_err_t nvs_store_set_u32(const char *key, uint32_t value)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err != ESP_OK) return err;
    err = nvs_set_u32(h, key, value);
    if (err == ESP_OK) nvs_commit(h);
    nvs_close(h);
    return err;
}

esp_err_t nvs_store_get_u32(const char *key, uint32_t *out)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READONLY, &h);
    if (err != ESP_OK) return err;
    err = nvs_get_u32(h, key, out);
    nvs_close(h);
    return err;
}

esp_err_t nvs_store_load_rules(automation_rule_t *rules, int max)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return ESP_FAIL;
    size_t len = sizeof(automation_rule_t) * max;
    esp_err_t err = nvs_get_blob(h, "rules", rules, &len);
    nvs_close(h);
    if (err != ESP_OK) {
        memset(rules, 0, sizeof(automation_rule_t) * max);
    }
    return err;
}

esp_err_t nvs_store_save_rules(const automation_rule_t *rules, int count)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READWRITE, &h) != ESP_OK) return ESP_FAIL;
    esp_err_t err = nvs_set_blob(h, "rules", rules,
                                  sizeof(automation_rule_t) * count);
    if (err == ESP_OK) nvs_commit(h);
    nvs_close(h);
    return err;
}

esp_err_t nvs_store_load_schedules(schedule_entry_t *sched, int max)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return ESP_FAIL;
    size_t len = sizeof(schedule_entry_t) * max;
    esp_err_t err = nvs_get_blob(h, "schedules", sched, &len);
    nvs_close(h);
    if (err != ESP_OK) {
        memset(sched, 0, sizeof(schedule_entry_t) * max);
    }
    return err;
}

esp_err_t nvs_store_save_schedules(const schedule_entry_t *sched, int count)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READWRITE, &h) != ESP_OK) return ESP_FAIL;
    esp_err_t err = nvs_set_blob(h, "schedules", sched,
                                  sizeof(schedule_entry_t) * count);
    if (err == ESP_OK) nvs_commit(h);
    nvs_close(h);
    return err;
}
