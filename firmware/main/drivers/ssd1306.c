#include "ssd1306.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

static const char *TAG = "SSD1306";

#define SSD1306_CMD   0x00
#define SSD1306_DATA  0x40
#define I2C_TIMEOUT_MS 100

/* Minimal 5x7 ASCII font (space to ~) — 96 characters */
static const uint8_t FONT5x7[][5] = {
    {0x00,0x00,0x00,0x00,0x00}, /* space */
    {0x00,0x00,0x5F,0x00,0x00}, /* ! */
    {0x00,0x07,0x00,0x07,0x00}, /* " */
    {0x14,0x7F,0x14,0x7F,0x14}, /* # */
    {0x24,0x2A,0x7F,0x2A,0x12}, /* $ */
    {0x23,0x13,0x08,0x64,0x62}, /* % */
    {0x36,0x49,0x55,0x22,0x50}, /* & */
    {0x00,0x05,0x03,0x00,0x00}, /* ' */
    {0x00,0x1C,0x22,0x41,0x00}, /* ( */
    {0x00,0x41,0x22,0x1C,0x00}, /* ) */
    {0x08,0x2A,0x1C,0x2A,0x08}, /* * */
    {0x08,0x08,0x3E,0x08,0x08}, /* + */
    {0x00,0x50,0x30,0x00,0x00}, /* , */
    {0x08,0x08,0x08,0x08,0x08}, /* - */
    {0x00,0x60,0x60,0x00,0x00}, /* . */
    {0x20,0x10,0x08,0x04,0x02}, /* / */
    {0x3E,0x51,0x49,0x45,0x3E}, /* 0 */
    {0x00,0x42,0x7F,0x40,0x00}, /* 1 */
    {0x42,0x61,0x51,0x49,0x46}, /* 2 */
    {0x21,0x41,0x45,0x4B,0x31}, /* 3 */
    {0x18,0x14,0x12,0x7F,0x10}, /* 4 */
    {0x27,0x45,0x45,0x45,0x39}, /* 5 */
    {0x3C,0x4A,0x49,0x49,0x30}, /* 6 */
    {0x01,0x71,0x09,0x05,0x03}, /* 7 */
    {0x36,0x49,0x49,0x49,0x36}, /* 8 */
    {0x06,0x49,0x49,0x29,0x1E}, /* 9 */
    {0x00,0x36,0x36,0x00,0x00}, /* : */
    {0x00,0x56,0x36,0x00,0x00}, /* ; */
    {0x00,0x08,0x14,0x22,0x41}, /* < */
    {0x14,0x14,0x14,0x14,0x14}, /* = */
    {0x41,0x22,0x14,0x08,0x00}, /* > */
    {0x02,0x01,0x51,0x09,0x06}, /* ? */
    {0x32,0x49,0x79,0x41,0x3E}, /* @ */
};

static uint8_t framebuf[SSD1306_WIDTH * SSD1306_HEIGHT / 8];
static uint8_t cursor_col = 0;
static uint8_t cursor_row = 0;

static esp_err_t ssd1306_cmd(uint8_t cmd)
{
    uint8_t buf[2] = {SSD1306_CMD, cmd};
    return i2c_master_write_to_device(SSD1306_I2C_PORT, SSD1306_I2C_ADDR,
                                      buf, 2, pdMS_TO_TICKS(I2C_TIMEOUT_MS));
}

esp_err_t ssd1306_init(void)
{
    i2c_config_t conf = {
        .mode             = I2C_MODE_MASTER,
        .sda_io_num       = SSD1306_SDA_PIN,
        .scl_io_num       = SSD1306_SCL_PIN,
        .sda_pullup_en    = GPIO_PULLUP_ENABLE,
        .scl_pullup_en    = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 400000,
    };
    ESP_ERROR_CHECK(i2c_param_config(SSD1306_I2C_PORT, &conf));
    ESP_ERROR_CHECK(i2c_driver_install(SSD1306_I2C_PORT, I2C_MODE_MASTER, 0, 0, 0));

    static const uint8_t init_cmds[] = {
        0xAE,             /* display off */
        0xD5, 0x80,       /* clock divide */
        0xA8, 0x3F,       /* mux ratio */
        0xD3, 0x00,       /* display offset */
        0x40,             /* start line 0 */
        0x8D, 0x14,       /* charge pump on */
        0x20, 0x00,       /* horizontal addressing */
        0xA1,             /* segment remap */
        0xC8,             /* com scan direction */
        0xDA, 0x12,       /* com pins */
        0x81, 0xCF,       /* contrast */
        0xD9, 0xF1,       /* pre-charge */
        0xDB, 0x40,       /* vcomh */
        0xA4,             /* entire display on */
        0xA6,             /* normal display */
        0xAF,             /* display on */
    };
    for (size_t i = 0; i < sizeof(init_cmds); i++) ssd1306_cmd(init_cmds[i]);

    ssd1306_clear();
    ssd1306_flush();
    ESP_LOGI(TAG, "SSD1306 128x64 OLED ready on I2C addr 0x%02X", SSD1306_I2C_ADDR);
    return ESP_OK;
}

void ssd1306_clear(void)
{
    memset(framebuf, 0, sizeof(framebuf));
    cursor_col = 0;
    cursor_row = 0;
}

void ssd1306_set_cursor(uint8_t col, uint8_t row)
{
    cursor_col = col;
    cursor_row = row;
}

static void ssd1306_draw_char(char c)
{
    if (c < 0x20 || c > 0x60) c = 0x20;
    const uint8_t *glyph = FONT5x7[c - 0x20];
    for (int col = 0; col < 5; col++) {
        int x = cursor_col * 6 + col;
        if (x >= SSD1306_WIDTH) break;
        framebuf[x + cursor_row * SSD1306_WIDTH] = glyph[col];
    }
    cursor_col++;
}

void ssd1306_print(const char *str)
{
    while (*str) ssd1306_draw_char(*str++);
}

void ssd1306_printf(const char *fmt, ...)
{
    char buf[64];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    ssd1306_print(buf);
}

void ssd1306_flush(void)
{
    ssd1306_cmd(0x21); ssd1306_cmd(0); ssd1306_cmd(127);
    ssd1306_cmd(0x22); ssd1306_cmd(0); ssd1306_cmd(7);

    uint8_t buf[SSD1306_WIDTH + 1];
    buf[0] = SSD1306_DATA;
    for (int page = 0; page < 8; page++) {
        memcpy(&buf[1], &framebuf[page * SSD1306_WIDTH], SSD1306_WIDTH);
        i2c_master_write_to_device(SSD1306_I2C_PORT, SSD1306_I2C_ADDR,
                                   buf, sizeof(buf), pdMS_TO_TICKS(I2C_TIMEOUT_MS));
    }
}
