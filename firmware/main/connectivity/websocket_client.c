#include "websocket_client.h"
#include "esp_websocket_client.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = "WS_CLIENT";

static esp_websocket_client_handle_t s_client   = NULL;
static volatile bool                 s_connected = false;
static ws_msg_cb_t                   s_msg_cb    = NULL;

/* ── Event handler ───────────────────────────────────────────────────── */
static void ws_event_handler(void *arg, esp_event_base_t base,
                              int32_t event_id, void *event_data)
{
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;

    switch (event_id) {

    case WEBSOCKET_EVENT_CONNECTED:
        s_connected = true;
        ESP_LOGI(TAG, "WebSocket connected");
        break;

    case WEBSOCKET_EVENT_DISCONNECTED:
        s_connected = false;
        ESP_LOGW(TAG, "WebSocket disconnected — will reconnect");
        break;

    case WEBSOCKET_EVENT_DATA:
        if (data->op_code == 0x08) {
            /* Close frame */
            ESP_LOGI(TAG, "WebSocket close frame received");
            break;
        }
        if (data->data_len > 0 && s_msg_cb) {
            s_msg_cb(data->data_ptr, data->data_len);
        }
        break;

    case WEBSOCKET_EVENT_ERROR:
        ESP_LOGE(TAG, "WebSocket error — transport error");
        s_connected = false;
        break;

    default:
        break;
    }
}

/* ── Public API ──────────────────────────────────────────────────────── */

esp_err_t ws_client_init(const char *uri, ws_msg_cb_t on_message)
{
    s_msg_cb = on_message;

    esp_websocket_client_config_t cfg = {
        .uri                = uri,
        .reconnect_timeout_ms = WS_RECONNECT_TIMEOUT_MS,
        .network_timeout_ms   = WS_SEND_TIMEOUT_MS,
        .buffer_size          = WS_BUFFER_SIZE,
        .task_stack           = 4096,
        .task_prio            = 5,
    };

    s_client = esp_websocket_client_init(&cfg);
    if (!s_client) {
        ESP_LOGE(TAG, "Failed to init WebSocket client");
        return ESP_FAIL;
    }

    esp_websocket_register_events(s_client, WEBSOCKET_EVENT_ANY,
                                   ws_event_handler, NULL);
    ESP_LOGI(TAG, "WebSocket client initialised → %s", uri);
    return ESP_OK;
}

esp_err_t ws_client_start(void)
{
    if (!s_client) return ESP_ERR_INVALID_STATE;
    return esp_websocket_client_start(s_client);
}

esp_err_t ws_client_stop(void)
{
    if (s_client) {
        esp_websocket_client_stop(s_client);
        esp_websocket_client_destroy(s_client);
        s_client    = NULL;
        s_connected = false;
    }
    return ESP_OK;
}

bool ws_client_is_connected(void)
{
    return s_connected && esp_websocket_client_is_connected(s_client);
}

conn_err_t ws_client_send(const char *payload, int len)
{
    if (!ws_client_is_connected()) return CONN_ERR_NOT_READY;

    int sent = esp_websocket_client_send_text(s_client, payload, len,
                                               pdMS_TO_TICKS(WS_SEND_TIMEOUT_MS));
    if (sent < 0) {
        ESP_LOGW(TAG, "WebSocket send failed");
        return CONN_ERR_WS;
    }
    return CONN_OK;
}
