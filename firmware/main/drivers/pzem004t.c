#include "pzem004t.h"
#include "driver/uart.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "PZEM004T";

/* PZEM-004T v3 Modbus RTU frame constants */
#define PZEM_SLAVE_ADDR  0xF8
#define PZEM_CMD_RIR     0x04   /* Read Input Registers */
#define PZEM_REG_START   0x0000
#define PZEM_REG_COUNT   10
#define PZEM_FRAME_LEN   8
#define PZEM_RESP_LEN    25     /* 3 header + 20 data + 2 CRC */
#define PZEM_TIMEOUT_MS  500

static uint16_t crc16(const uint8_t *buf, uint16_t len)
{
    uint16_t crc = 0xFFFF;
    for (uint16_t i = 0; i < len; i++) {
        crc ^= buf[i];
        for (uint8_t j = 0; j < 8; j++) {
            crc = (crc & 0x0001) ? ((crc >> 1) ^ 0xA001) : (crc >> 1);
        }
    }
    return crc;
}

esp_err_t pzem004t_init(void)
{
    uart_config_t cfg = {
        .baud_rate  = PZEM_BAUD_RATE,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
    };
    ESP_ERROR_CHECK(uart_param_config(PZEM_UART_PORT, &cfg));
    ESP_ERROR_CHECK(uart_set_pin(PZEM_UART_PORT, PZEM_TX_PIN, PZEM_RX_PIN,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(PZEM_UART_PORT, 256, 0, 0, NULL, 0));
    ESP_LOGI(TAG, "UART2 initialised on RX=%d TX=%d", PZEM_RX_PIN, PZEM_TX_PIN);
    return ESP_OK;
}

esp_err_t pzem004t_read(pzem_data_t *out)
{
    uint8_t req[PZEM_FRAME_LEN];
    req[0] = PZEM_SLAVE_ADDR;
    req[1] = PZEM_CMD_RIR;
    req[2] = (PZEM_REG_START >> 8) & 0xFF;
    req[3] =  PZEM_REG_START       & 0xFF;
    req[4] = (PZEM_REG_COUNT >> 8) & 0xFF;
    req[5] =  PZEM_REG_COUNT       & 0xFF;
    uint16_t crc = crc16(req, 6);
    req[6] = crc & 0xFF;
    req[7] = (crc >> 8) & 0xFF;

    uart_flush(PZEM_UART_PORT);
    uart_write_bytes(PZEM_UART_PORT, (const char *)req, PZEM_FRAME_LEN);

    uint8_t resp[PZEM_RESP_LEN];
    int len = uart_read_bytes(PZEM_UART_PORT, resp, PZEM_RESP_LEN,
                              pdMS_TO_TICKS(PZEM_TIMEOUT_MS));
    if (len != PZEM_RESP_LEN) {
        ESP_LOGW(TAG, "Short response: %d bytes", len);
        return ESP_ERR_TIMEOUT;
    }

    uint16_t resp_crc  = (uint16_t)resp[len - 1] << 8 | resp[len - 2];
    uint16_t calc_crc  = crc16(resp, len - 2);
    if (resp_crc != calc_crc) {
        ESP_LOGW(TAG, "CRC mismatch");
        return ESP_ERR_INVALID_CRC;
    }

    /* Parse Modbus registers — each register is 2 bytes big-endian */
    uint8_t *d = &resp[3];
    out->voltage      = ((uint16_t)d[0]  << 8 | d[1])  / 10.0f;
    out->current      = ((uint32_t)d[4]  << 24 | (uint32_t)d[5] << 16 |
                         (uint16_t)d[2]  << 8  | d[3])  / 1000.0f;
    out->power_w      = ((uint32_t)d[8]  << 24 | (uint32_t)d[9] << 16 |
                         (uint16_t)d[6]  << 8  | d[7])  / 10.0f;
    out->energy_kwh   = ((uint32_t)d[12] << 24 | (uint32_t)d[13] << 16 |
                         (uint16_t)d[10] << 8  | d[11]) / 1000.0f;
    out->frequency    = ((uint16_t)d[14] << 8 | d[15]) / 10.0f;
    out->power_factor = ((uint16_t)d[16] << 8 | d[17]) / 100.0f;
    out->alarm        = (uint8_t)((uint16_t)d[18] << 8 | d[19]);

    return ESP_OK;
}

esp_err_t pzem004t_reset_energy(void)
{
    uint8_t req[] = { PZEM_SLAVE_ADDR, 0x42 };
    uint16_t crc = crc16(req, 2);
    uint8_t frame[4] = { req[0], req[1], crc & 0xFF, (crc >> 8) & 0xFF };
    uart_write_bytes(PZEM_UART_PORT, (const char *)frame, sizeof(frame));
    return ESP_OK;
}
