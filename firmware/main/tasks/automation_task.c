#include "automation_task.h"
#include "tasks/sensor_task.h"
#include "tasks/inference_task.h"
#include "drivers/relay.h"
#include "storage/nvs_store.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "AUTOMATION";

/* Rules and schedules loaded from NVS at startup */
static automation_rule_t s_rules[MAX_RULES];
static schedule_entry_t  s_schedules[MAX_SCHEDULES];

static void evaluate_rules(const sensor_reading_t *r)
{
    uint32_t now_s = (uint32_t)(esp_timer_get_time() / 1000000);

    for (int i = 0; i < MAX_RULES; i++) {
        automation_rule_t *rule = &s_rules[i];
        if (!rule->enabled) continue;
        if ((now_s - rule->last_fired_s) < rule->cooldown_s) continue;

        bool triggered = false;
        switch (rule->trigger) {
        case TRIGGER_POWER_ABOVE:
            triggered = r->pzem.power_w > rule->threshold; break;
        case TRIGGER_POWER_BELOW:
            triggered = r->pzem.power_w < rule->threshold; break;
        case TRIGGER_TEMP_ABOVE:
            triggered = r->dht.temperature > rule->threshold; break;
        case TRIGGER_TEMP_BELOW:
            triggered = r->dht.temperature < rule->threshold; break;
        case TRIGGER_MOTION:
            triggered = r->motion; break;
        case TRIGGER_NO_MOTION:
            triggered = !r->motion; break;
        case TRIGGER_OCCUPANCY:
            triggered = g_inference_result.occupancy_prob > rule->threshold; break;
        default: break;
        }

        if (triggered) {
            relay_set(rule->relay_index, rule->relay_action);
            rule->last_fired_s = now_s;
            ESP_LOGI(TAG, "Rule %d fired → relay %d %s",
                     i, rule->relay_index, rule->relay_action ? "ON" : "OFF");
        }
    }
}

void automation_task(void *pvParams)
{
    /* Load persisted rules from NVS */
    nvs_store_load_rules(s_rules, MAX_RULES);
    nvs_store_load_schedules(s_schedules, MAX_SCHEDULES);

    /* Default example rule: turn off fan if power < 10 W (idle) */
    s_rules[0].enabled      = true;
    s_rules[0].trigger      = TRIGGER_POWER_BELOW;
    s_rules[0].threshold    = 10.0f;
    s_rules[0].relay_index  = 1;   /* fan */
    s_rules[0].relay_action = false;
    s_rules[0].cooldown_s   = 60;

    ESP_LOGI(TAG, "Automation task started — 2 Hz evaluation");

    TickType_t last = xTaskGetTickCount();
    sensor_reading_t r;

    for (;;) {
        if (xQueuePeek(g_sensor_queue, &r, pdMS_TO_TICKS(100)) == pdTRUE) {
            evaluate_rules(&r);
        }
        vTaskDelayUntil(&last, pdMS_TO_TICKS(500));
    }
}
