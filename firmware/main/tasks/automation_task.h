#pragma once
#include <stdint.h>
#include <stdbool.h>

#define MAX_RULES       16
#define MAX_SCHEDULES   16

typedef enum {
    TRIGGER_POWER_ABOVE,
    TRIGGER_POWER_BELOW,
    TRIGGER_TEMP_ABOVE,
    TRIGGER_TEMP_BELOW,
    TRIGGER_MOTION,
    TRIGGER_NO_MOTION,
    TRIGGER_OCCUPANCY,
} trigger_type_t;

typedef struct {
    bool          enabled;
    trigger_type_t trigger;
    float         threshold;
    uint8_t       relay_index;
    bool          relay_action;    /* true = ON, false = OFF */
    uint32_t      cooldown_s;
    uint32_t      last_fired_s;
} automation_rule_t;

typedef struct {
    bool     enabled;
    uint8_t  hour;
    uint8_t  minute;
    uint8_t  relay_index;
    bool     relay_action;
    uint8_t  days_mask;            /* bitmask: bit0=Mon … bit6=Sun */
} schedule_entry_t;

void automation_task(void *pvParams);
