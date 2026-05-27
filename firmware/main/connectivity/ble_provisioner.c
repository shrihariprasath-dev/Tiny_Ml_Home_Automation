#include "ble_provisioner.h"
#include "protocol_defs.h"
#include "wifi_manager.h"
#include "storage/nvs_store.h"
#include "esp_log.h"
#include "esp_bt.h"
#include "esp_gap_ble_api.h"
#include "esp_gatts_api.h"
#include "esp_gatt_common_api.h"
#include "esp_bt_main.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>
#include <stdio.h>

static const char *TAG = "BLE_PROV";

#define GATTS_APP_ID        0
#define GATTS_NUM_HANDLES   8    /* service + 3 chars + 3 descriptors */
#define PROFILE_IDX         0

/* Attribute table indices */
enum {
    IDX_SVC,
    IDX_SSID_CHAR,   IDX_SSID_VAL,
    IDX_PASS_CHAR,   IDX_PASS_VAL,
    IDX_STAT_CHAR,   IDX_STAT_VAL,  IDX_STAT_CFG,
    IDX_MAX,
};

static uint16_t s_handle_table[IDX_MAX];
static uint16_t s_conn_id      = 0xFFFF;
static uint16_t s_gatts_if     = ESP_GATT_IF_NONE;
static bool     s_active       = false;

static char     s_ssid[WIFI_SSID_MAX_LEN] = {0};
static char     s_pass[WIFI_PASS_MAX_LEN] = {0};
static bool     s_ssid_set = false;
static bool     s_pass_set = false;

static uint8_t s_status_val = BLE_PROV_STATUS_IDLE;

/* ── Service UUID ──────────────────────────────────────────────────────── */
static uint8_t svc_uuid128[]  = { BLE_PROV_SERVICE_UUID };
static uint8_t ssid_uuid128[] = { BLE_PROV_SSID_CHAR_UUID };
static uint8_t pass_uuid128[] = { BLE_PROV_PASS_CHAR_UUID };
static uint8_t stat_uuid128[] = { BLE_PROV_STAT_CHAR_UUID };

static esp_bt_uuid_t svc_uuid  = { .len = ESP_UUID_LEN_128,
                                    .uuid.uuid128 = { BLE_PROV_SERVICE_UUID } };

/* ── Advertising payload ───────────────────────────────────────────────── */
static uint8_t s_adv_data_raw[31];
static uint8_t s_adv_data_len = 0;

static esp_ble_adv_params_t s_adv_params = {
    .adv_int_min       = BLE_ADV_INTERVAL_MS,
    .adv_int_max       = BLE_ADV_INTERVAL_MS,
    .adv_type          = ADV_TYPE_IND,
    .own_addr_type     = BLE_ADDR_TYPE_PUBLIC,
    .channel_map       = ADV_CHNL_ALL,
    .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};

/* ── GATT attribute table ──────────────────────────────────────────────── */
static const uint16_t primary_svc_uuid  = ESP_GATT_UUID_PRI_SERVICE;
static const uint16_t char_decl_uuid    = ESP_GATT_UUID_CHAR_DECLARE;
static const uint16_t cccd_uuid         = ESP_GATT_UUID_CHAR_CLIENT_CONFIG;

static const uint8_t char_prop_write    = ESP_GATT_CHAR_PROP_BIT_WRITE_NR;
static const uint8_t char_prop_rn       = ESP_GATT_CHAR_PROP_BIT_READ
                                        | ESP_GATT_CHAR_PROP_BIT_NOTIFY;
static const uint8_t cccd_val[2]        = {0x00, 0x00};

static const esp_gatts_attr_db_t s_gatt_db[IDX_MAX] = {
    /* Primary service */
    [IDX_SVC] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_16, (uint8_t *)&primary_svc_uuid,
          ESP_GATT_PERM_READ,
          sizeof(svc_uuid128), sizeof(svc_uuid128), svc_uuid128 }
    },
    /* SSID characteristic declaration */
    [IDX_SSID_CHAR] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_16, (uint8_t *)&char_decl_uuid,
          ESP_GATT_PERM_READ,
          sizeof(char_prop_write), sizeof(char_prop_write),
          (uint8_t *)&char_prop_write }
    },
    /* SSID characteristic value */
    [IDX_SSID_VAL] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_128, ssid_uuid128,
          ESP_GATT_PERM_WRITE,
          WIFI_SSID_MAX_LEN, 0, NULL }
    },
    /* Password characteristic declaration */
    [IDX_PASS_CHAR] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_16, (uint8_t *)&char_decl_uuid,
          ESP_GATT_PERM_READ,
          sizeof(char_prop_write), sizeof(char_prop_write),
          (uint8_t *)&char_prop_write }
    },
    /* Password characteristic value */
    [IDX_PASS_VAL] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_128, pass_uuid128,
          ESP_GATT_PERM_WRITE,
          WIFI_PASS_MAX_LEN, 0, NULL }
    },
    /* Status characteristic declaration */
    [IDX_STAT_CHAR] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_16, (uint8_t *)&char_decl_uuid,
          ESP_GATT_PERM_READ,
          sizeof(char_prop_rn), sizeof(char_prop_rn),
          (uint8_t *)&char_prop_rn }
    },
    /* Status characteristic value */
    [IDX_STAT_VAL] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_128, stat_uuid128,
          ESP_GATT_PERM_READ,
          sizeof(s_status_val), sizeof(s_status_val), &s_status_val }
    },
    /* Status CCCD (notify enable) */
    [IDX_STAT_CFG] = {
        { ESP_GATT_AUTO_RSP },
        { ESP_UUID_LEN_16, (uint8_t *)&cccd_uuid,
          ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
          sizeof(cccd_val), sizeof(cccd_val), (uint8_t *)cccd_val }
    },
};

/* ── GAP callback ──────────────────────────────────────────────────────── */
static void gap_cb(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t *param)
{
    switch (event) {
    case ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT:
        esp_ble_gap_start_advertising(&s_adv_params);
        break;
    case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
        if (param->adv_start_cmpl.status == ESP_BT_STATUS_SUCCESS) {
            ESP_LOGI(TAG, "BLE advertising started");
        }
        break;
    case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
        ESP_LOGI(TAG, "BLE advertising stopped");
        break;
    default:
        break;
    }
}

/* ── GATT server callback ──────────────────────────────────────────────── */
static void gatts_cb(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if,
                     esp_ble_gatts_cb_param_t *param)
{
    switch (event) {
    case ESP_GATTS_REG_EVT:
        s_gatts_if = gatts_if;
        esp_ble_gatts_create_attr_tab(s_gatt_db, gatts_if,
                                      IDX_MAX, GATTS_APP_ID);
        break;

    case ESP_GATTS_CREAT_ATTR_TAB_EVT:
        if (param->add_attr_tab.status == ESP_GATT_OK
            && param->add_attr_tab.num_handle == IDX_MAX) {
            memcpy(s_handle_table, param->add_attr_tab.handles,
                   sizeof(s_handle_table));
            esp_ble_gatts_start_service(s_handle_table[IDX_SVC]);
        }
        break;

    case ESP_GATTS_CONNECT_EVT:
        s_conn_id = param->connect.conn_id;
        ESP_LOGI(TAG, "BLE client connected, conn_id=%d", s_conn_id);
        /* Update connection parameters for faster data transfer */
        esp_ble_conn_update_params_t conn_params = {
            .min_int = 0x10, .max_int = 0x20,
            .latency = 0,    .timeout = 400,
        };
        memcpy(conn_params.bda, param->connect.remote_bda, sizeof(esp_bd_addr_t));
        esp_ble_gap_update_conn_params(&conn_params);
        break;

    case ESP_GATTS_DISCONNECT_EVT:
        s_conn_id = 0xFFFF;
        ESP_LOGI(TAG, "BLE client disconnected — restarting advertising");
        esp_ble_gap_start_advertising(&s_adv_params);
        break;

    case ESP_GATTS_WRITE_EVT: {
        uint16_t handle = param->write.handle;
        uint16_t len    = param->write.len;
        uint8_t *val    = param->write.value;

        if (handle == s_handle_table[IDX_SSID_VAL]) {
            uint16_t copy = len < WIFI_SSID_MAX_LEN - 1 ? len : WIFI_SSID_MAX_LEN - 1;
            memcpy(s_ssid, val, copy);
            s_ssid[copy] = '\0';
            s_ssid_set = true;
            ESP_LOGI(TAG, "SSID received: %s", s_ssid);

        } else if (handle == s_handle_table[IDX_PASS_VAL]) {
            uint16_t copy = len < WIFI_PASS_MAX_LEN - 1 ? len : WIFI_PASS_MAX_LEN - 1;
            memcpy(s_pass, val, copy);
            s_pass[copy] = '\0';
            s_pass_set = true;
            ESP_LOGI(TAG, "Password received (length=%d)", copy);
        }

        /* Once both credentials received, save and trigger WiFi connect */
        if (s_ssid_set && s_pass_set) {
            nvs_store_set_str(NVS_KEY_WIFI_SSID, s_ssid);
            nvs_store_set_str(NVS_KEY_WIFI_PASS, s_pass);
            s_ssid_set = s_pass_set = false;

            ble_provisioner_set_status(BLE_PROV_STATUS_CONNECTING);
            wifi_manager_on_credentials_updated();
        }
        break;
    }

    default:
        break;
    }
}

/* ── Public API ────────────────────────────────────────────────────────── */

esp_err_t ble_provisioner_init(void)
{
    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BLE));
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());

    ESP_ERROR_CHECK(esp_ble_gap_register_callback(gap_cb));
    ESP_ERROR_CHECK(esp_ble_gatts_register_callback(gatts_cb));
    ESP_ERROR_CHECK(esp_ble_gatts_app_register(GATTS_APP_ID));
    ESP_ERROR_CHECK(esp_ble_gatt_set_local_mtu(500));

    ESP_LOGI(TAG, "BLE provisioner initialised");
    return ESP_OK;
}

esp_err_t ble_provisioner_start(void)
{
    /* Build advertising data: Flags + Complete Local Name */
    char dev_name[32];
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_BT);
    snprintf(dev_name, sizeof(dev_name), "%s%02X%02X",
             BLE_DEVICE_NAME_PREFIX, mac[4], mac[5]);
    esp_ble_gap_set_device_name(dev_name);

    /* AD structure: [len][type][data] */
    s_adv_data_len = 0;
    uint8_t name_len = strlen(dev_name);

    s_adv_data_raw[s_adv_data_len++] = 2;
    s_adv_data_raw[s_adv_data_len++] = 0x01;  /* Flags type */
    s_adv_data_raw[s_adv_data_len++] = 0x06;  /* LE General Discoverable, BR/EDR not supported */

    s_adv_data_raw[s_adv_data_len++] = name_len + 1;
    s_adv_data_raw[s_adv_data_len++] = 0x09;  /* Complete Local Name type */
    memcpy(&s_adv_data_raw[s_adv_data_len], dev_name, name_len);
    s_adv_data_len += name_len;

    esp_ble_gap_config_adv_data_raw(s_adv_data_raw, s_adv_data_len);
    s_active = true;

    ESP_LOGI(TAG, "BLE provisioning started — device name: %s", dev_name);
    return ESP_OK;
}

esp_err_t ble_provisioner_stop(void)
{
    esp_ble_gap_stop_advertising();
    s_active = false;
    ESP_LOGI(TAG, "BLE provisioner stopped");
    return ESP_OK;
}

bool ble_provisioner_is_active(void)
{
    return s_active;
}

void ble_provisioner_set_status(ble_prov_status_t status)
{
    s_status_val = (uint8_t)status;

    /* Notify connected client if notifications are enabled */
    if (s_conn_id != 0xFFFF && s_gatts_if != ESP_GATT_IF_NONE) {
        esp_ble_gatts_send_indicate(s_gatts_if, s_conn_id,
                                    s_handle_table[IDX_STAT_VAL],
                                    sizeof(s_status_val), &s_status_val, false);
    }
    ESP_LOGI(TAG, "Provisioning status -> 0x%02X", status);
}
