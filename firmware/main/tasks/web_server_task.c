#include "web_server_task.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "tasks/sensor_task.h"
#include "tasks/inference_task.h"
#include "drivers/relay.h"
#include "cJSON.h"
#include <string.h>

static const char *TAG = "WEB_SERVER";

/* GET /api/status — returns latest telemetry + relay states */
static esp_err_t handle_status(httpd_req_t *req)
{
    sensor_reading_t r = {0};
    xQueuePeek(g_sensor_queue, &r, pdMS_TO_TICKS(50));

    bool relays[RELAY_COUNT];
    relay_get_all(relays);

    char resp[512];
    snprintf(resp, sizeof(resp),
        "{\"voltage\":%.1f,\"current\":%.3f,\"power_w\":%.1f,"
        "\"temperature\":%.1f,\"humidity\":%.1f,\"motion\":%s,"
        "\"anomaly_score\":%.3f,\"occupancy_prob\":%.3f,"
        "\"relay_states\":[%s,%s,%s,%s]}",
        r.pzem.voltage, r.pzem.current, r.pzem.power_w,
        r.dht.temperature, r.dht.humidity,
        r.motion ? "true" : "false",
        g_inference_result.anomaly_score,
        g_inference_result.occupancy_prob,
        relays[0]?"true":"false", relays[1]?"true":"false",
        relays[2]?"true":"false", relays[3]?"true":"false");

    httpd_resp_set_type(req, "application/json");
    return httpd_resp_sendstr(req, resp);
}

/* POST /api/relay  body: {"relay":0,"state":true} */
static esp_err_t handle_relay(httpd_req_t *req)
{
    char body[128];
    int  len = httpd_req_recv(req, body, sizeof(body) - 1);
    if (len <= 0) return httpd_resp_send_500(req);
    body[len] = '\0';

    cJSON *root = cJSON_Parse(body);
    if (!root) return httpd_resp_send_500(req);

    int  idx = cJSON_GetObjectItem(root, "relay")->valueint;
    bool on  = cJSON_IsTrue(cJSON_GetObjectItem(root, "state"));
    cJSON_Delete(root);

    relay_set((uint8_t)idx, on);
    httpd_resp_set_type(req, "application/json");
    return httpd_resp_sendstr(req, "{\"ok\":true}");
}

void web_server_task(void *pvParams)
{
    httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
    cfg.server_port = 80;

    httpd_handle_t server = NULL;
    if (httpd_start(&server, &cfg) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start HTTP server");
        vTaskDelete(NULL);
    }

    httpd_uri_t status_uri = {
        .uri     = "/api/status",
        .method  = HTTP_GET,
        .handler = handle_status,
    };
    httpd_uri_t relay_uri = {
        .uri     = "/api/relay",
        .method  = HTTP_POST,
        .handler = handle_relay,
    };

    httpd_register_uri_handler(server, &status_uri);
    httpd_register_uri_handler(server, &relay_uri);

    ESP_LOGI(TAG, "Offline REST API listening on :80");
    vTaskDelete(NULL);   /* httpd runs its own tasks internally */
}
