#include "ota_task.h"
#include "esp_https_ota.h"
#include "esp_log.h"
#include "esp_http_client.h"
#include "esp_ota_ops.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "cJSON.h"
#include <string.h>

static const char *TAG = "OTA_TASK";

/* TLS CA certificate for OTA server — embed at build time */
extern const uint8_t ota_ca_cert_pem_start[] asm("_binary_ota_ca_cert_pem_start");
extern const uint8_t ota_ca_cert_pem_end[]   asm("_binary_ota_ca_cert_pem_end");

static char s_version_buf[256];

static esp_err_t fetch_latest_version(char *version_out, char *url_out,
                                       size_t buf_len)
{
    esp_http_client_config_t cfg = {
        .url            = OTA_VERSION_URL,
        .cert_pem       = (const char *)ota_ca_cert_pem_start,
        .timeout_ms     = 10000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    if (!client) return ESP_FAIL;

    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK) {
        int len = esp_http_client_read_response(client, s_version_buf,
                                                sizeof(s_version_buf) - 1);
        s_version_buf[len] = '\0';
        cJSON *root = cJSON_Parse(s_version_buf);
        if (root) {
            strncpy(version_out,
                    cJSON_GetObjectItem(root, "version")->valuestring, buf_len);
            strncpy(url_out,
                    cJSON_GetObjectItem(root, "url")->valuestring, buf_len);
            cJSON_Delete(root);
        }
    }
    esp_http_client_cleanup(client);
    return err;
}

void ota_task(void *pvParams)
{
    const esp_app_desc_t *running = esp_app_get_description();
    ESP_LOGI(TAG, "Running firmware: %s", running->version);

    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(OTA_POLL_PERIOD_S * 1000));

        char latest_ver[32] = {0};
        char firmware_url[256] = {0};

        if (fetch_latest_version(latest_ver, firmware_url,
                                  sizeof(latest_ver)) != ESP_OK) {
            ESP_LOGW(TAG, "Version check failed");
            continue;
        }

        if (strcmp(latest_ver, running->version) == 0) {
            ESP_LOGI(TAG, "Firmware up to date (%s)", running->version);
            continue;
        }

        ESP_LOGI(TAG, "Update available: %s → %s", running->version, latest_ver);

        esp_https_ota_config_t ota_cfg = {
            .http_config = &(esp_http_client_config_t){
                .url      = firmware_url,
                .cert_pem = (const char *)ota_ca_cert_pem_start,
            },
        };

        esp_err_t ret = esp_https_ota(&ota_cfg);
        if (ret == ESP_OK) {
            ESP_LOGI(TAG, "OTA complete — rebooting");
            esp_restart();
        } else {
            ESP_LOGE(TAG, "OTA failed: %s", esp_err_to_name(ret));
        }
    }
}
