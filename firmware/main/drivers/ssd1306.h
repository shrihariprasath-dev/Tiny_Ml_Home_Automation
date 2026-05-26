#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#define SSD1306_I2C_PORT    I2C_NUM_0
#define SSD1306_SDA_PIN     21
#define SSD1306_SCL_PIN     22
#define SSD1306_I2C_ADDR    0x3C
#define SSD1306_WIDTH       128
#define SSD1306_HEIGHT      64

esp_err_t ssd1306_init(void);
void      ssd1306_clear(void);
void      ssd1306_set_cursor(uint8_t col, uint8_t row);
void      ssd1306_print(const char *str);
void      ssd1306_printf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
void      ssd1306_flush(void);             /* Push framebuffer to display */
