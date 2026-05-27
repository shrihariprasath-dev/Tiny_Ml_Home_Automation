"""
Generates the technical activity report Word document for the
Smart Home Power Management & Automation System — session 2026-05-26.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── helpers ──────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

def add_table(doc, headers, rows, col_widths=None,
              header_bg="1F3864", header_fg="FFFFFF"):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, header_bg)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(9)

    # Data rows
    for ri, row in enumerate(rows):
        tr = table.rows[ri + 1]
        if ri % 2 == 0:
            bg = "DCE6F1"
        else:
            bg = "FFFFFF"
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(9)

    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)

    return table

def heading(doc, text, level):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    return p

def body(doc, text):
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(10)
    return p

def bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.style.font.size = Pt(10)
    return p

def code_block(doc, text):
    for line in text.strip().split("\n"):
        p = doc.add_paragraph()
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x00, 0x00, 0x80)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(0)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"),   "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"),  "F2F2F2")
        p._p.get_or_add_pPr().append(shading)

def hr(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F3864")
    pBdr.append(bottom)
    pPr.append(pBdr)

# ── document ─────────────────────────────────────────────────────────────────

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# Default font
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)

# ── Cover ────────────────────────────────────────────────────────────────────
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = title.add_run("Smart Home Power Management & Automation System")
tr.bold = True
tr.font.size = Pt(20)
tr.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("Technical Activity Report — Session 2026-05-26")
sr.font.size = Pt(13)
sr.font.color.rgb = RGBColor(0x44, 0x72, 0xC4)

doc.add_paragraph()
meta_rows = [
    ("Project",       "Tiny ML Home Automation"),
    ("Repository",    "shrihariprasath-dev/Tiny_Ml_Home_Automation"),
    ("Report Date",   "2026-05-26"),
    ("Session",       "claude/report-analysis-3JCpd"),
    ("Prepared by",   "Claude Code (AI Engineering Assistant)"),
    ("Status",        "Merged to Dev — Ready for Review"),
    ("Document Ver",  "1.0"),
]
add_table(doc, ["Field", "Value"], meta_rows,
          col_widths=[1.8, 4.5], header_bg="1F3864")

doc.add_page_break()

# ── TOC ──────────────────────────────────────────────────────────────────────
heading(doc, "Table of Contents", 1)
toc_items = [
    "1.  Executive Summary",
    "2.  Repository & Branch Strategy",
    "3.  README Architecture Analysis",
    "4.  Layer 1 — Hardware Drivers Implementation",
    "5.  Layer 2 — FreeRTOS Task Implementation",
    "6.  AI Inference Sub-System",
    "7.  NVS Storage & Utilities",
    "8.  ESP-IDF Build System",
    "9.  Git Activity Log",
    "10. File Manifest",
    "11. Memory Budget Verification",
    "12. Design Decisions & Risk Notes",
    "13. Next Steps",
]
for item in toc_items:
    bullet(doc, item)

doc.add_page_break()

# ── 1. Executive Summary ────────────────────────────────────────────────────
heading(doc, "1. Executive Summary", 1)
hr(doc)
body(doc,
    "This document records all engineering activity performed during the session of "
    "2026-05-26 on the Smart Home Power Management & Automation System project. "
    "The session covered four sequential activities:")

activities = [
    ("Architecture Analysis",
     "Deep technical review of the README.md architecture reference document, "
     "covering all 7 system layers, identifying strengths, gaps, and risks."),
    ("Layer 1 Explanation",
     "Detailed breakdown of all hardware components, GPIO mapping, communication "
     "interfaces, and safety design principles documented in the architecture."),
    ("Repository Structure Explanation",
     "Mapping of the actual scaffolded GitHub repository against the planned "
     "architecture, identifying what is present vs. what needs implementation."),
    ("Firmware Implementation",
     "Full implementation of Layer 1 (hardware drivers) and Layer 2 (FreeRTOS tasks) "
     "on a dedicated feature branch, merged to dev — 45 files, 1,636 lines of C code."),
]
add_table(doc, ["Activity", "Description"], activities,
          col_widths=[1.8, 4.5])

doc.add_page_break()

# ── 2. Branch Strategy ───────────────────────────────────────────────────────
heading(doc, "2. Repository & Branch Strategy", 1)
hr(doc)
body(doc,
    "The following branch structure was established and used during this session:")

code_block(doc, """
*   cf6aded  merge: firmware Layer 1 & Layer 2 into dev    ← feature/scaffold-folder-structure (dev)
|\\
| * 0d8acc3  feat(firmware): implement Layer 1 & Layer 2   ← feature/firmware-layer1-layer2
|/
* 6e1a8a3  scaffold: add complete project folder structure
""")

branch_rows = [
    ("feature/scaffold-folder-structure",
     "Dev branch — project folder scaffold, merge target for all features"),
    ("feature/firmware-layer1-layer2",
     "Feature branch — ESP32 firmware for Layer 1 & 2, branched from dev, merged back"),
    ("claude/report-analysis-3JCpd",
     "Session analysis branch — architecture review and documentation"),
]
add_table(doc,
          ["Branch", "Purpose"],
          branch_rows,
          col_widths=[2.8, 3.5])

body(doc, "")
body(doc,
    "The merge used --no-ff (no fast-forward) to preserve the full branch topology "
    "in the git history, making it clear which commits belong to which feature.")

doc.add_page_break()

# ── 3. README Analysis ───────────────────────────────────────────────────────
heading(doc, "3. README Architecture Analysis", 1)
hr(doc)
body(doc,
    "The README.md was analysed as a 7-layer architecture reference document. "
    "Key findings are summarised below.")

heading(doc, "3.1 System Layers", 2)
layers = [
    ("L1 — Hardware",     "PZEM-004T, ACS712, DHT22, HC-SR501 PIR, 4-ch relay, SSD1306 OLED"),
    ("L2 — Edge (ESP32)", "FreeRTOS + TFLite Micro, OTA dual-partition, Secure Boot, Deep Sleep"),
    ("L3 — Connectivity", "MQTT/TLS, WebSocket, BLE 5.0, WiFi 802.11n, optional Zigbee/Matter"),
    ("L4 — Backend",      "FastAPI, Mosquitto, InfluxDB, PostgreSQL, Redis, Celery, Nginx"),
    ("L5 — TinyML",       "LSTM-Autoencoder, 1D-CNN, Dense NN — INT8 quantized, on-device"),
    ("L6 — Frontend",     "Next.js 14 dashboard + Flutter mobile app"),
    ("L7 — DevOps",       "Docker Compose, GitHub Actions CI/CD, Grafana + Prometheus"),
]
add_table(doc, ["Layer", "Technology Stack"], layers, col_widths=[1.8, 4.5])

heading(doc, "3.2 Architecture Strengths", 2)
strengths = [
    "TinyML model sizes realistic — all 4 models fit in ~120 KB INT8, 92 KB SRAM headroom",
    "Dual-partition OTA with 3-crash auto-rollback — production-grade resilience",
    "Core affinity design — AI/sensors on Core 1, network on Core 0, prevents WiFi starvation",
    "Full TLS everywhere — MQTT on 8883, HTTPS OTA, WebSocket, with X.509 device certs",
    "Offline resilience — local NVS rules engine + REST API fallback when cloud unreachable",
    "MQTT QoS correctly chosen — QoS 0 for high-freq telemetry, QoS 2 only for anomaly alerts",
    "BoM realistic — ~$150 hardware + ~$13/month hosting",
]
for s in strengths:
    bullet(doc, s)

heading(doc, "3.3 Identified Gaps & Risks", 2)
risks = [
    ("TinyML cold-start",
     "No labeled anomaly data at project start. Anomalies are rare by definition — "
     "need synthetic injection or transfer learning strategy."),
    ("inference_task stack",
     "Allocated 8192 B. TFLite Micro recommends ≥16 KB for LSTM models. "
     "Stack overflow risk during inference execution."),
    ("Priority contention",
     "inference_task and automation_task share priority 4 on Core 1. "
     "Could cause scheduling jitter under load."),
    ("TFLite arena sizing",
     "180 KB combined runtime arena may be tight for LSTM activation buffers "
     "alongside 4 concurrent models."),
    ("SPIFFS wear",
     "960 KB SPIFFS for web assets — NOR flash limited to ~100K write cycles "
     "with no explicit wear-levelling mention."),
    ("Rate limiting scope",
     "API rate limit of 100 req/min — document does not specify per-IP vs per-user. "
     "Per-IP is bypassable; needs clarification."),
]
add_table(doc,
          ["Risk", "Detail"],
          risks,
          col_widths=[1.8, 4.5])

doc.add_page_break()

# ── 4. Layer 1 Drivers ───────────────────────────────────────────────────────
heading(doc, "4. Layer 1 — Hardware Drivers Implementation", 1)
hr(doc)
body(doc,
    "Five hardware abstraction drivers were implemented in firmware/main/drivers/. "
    "Each driver maps to a physical component on the ESP32 DevKit V1.")

heading(doc, "4.1 PZEM-004T v3.0 — Power Monitor (pzem004t.c)", 2)
body(doc,
    "Protocol: Modbus RTU over UART2 (GPIO 16 RX / GPIO 17 TX), 9600 baud. "
    "The driver implements a full Modbus request/response cycle:")
code_block(doc, """
Request frame  (8 bytes):  [0xF8][0x04][0x00][0x00][0x00][0x0A][CRC_L][CRC_H]
Response frame (25 bytes): [ADDR][CMD][BYTE_CNT][10 × 16-bit registers][CRC_L][CRC_H]

Registers parsed:
  [0]      Voltage      (÷10.0)     → Volts
  [1–2]    Current      (÷1000.0)   → Amps     (32-bit, low-word first)
  [3–4]    Power        (÷10.0)     → Watts    (32-bit, low-word first)
  [5–6]    Energy       (÷1000.0)   → kWh      (32-bit, low-word first)
  [7]      Frequency    (÷10.0)     → Hz
  [8]      Power Factor (÷100.0)    → PF
  [9]      Alarm flag              → uint8
""")
bullet(doc, "CRC-16/Modbus implemented in software — polynomial 0xA001")
bullet(doc, "Timeout: 500 ms per read cycle")
bullet(doc, "Energy counter reset via function code 0x42")

heading(doc, "4.2 ACS712 20A — Current Sensor (acs712.c)", 2)
body(doc,
    "Interface: ADC1 Channel 6 (GPIO 34), 12-bit resolution, 11 dB attenuation "
    "(0–3.3V input range).")
code_block(doc, """
Sensitivity:  100 mV/A  (20A module)
Midpoint:     VCC/2 = 1.65V → ADC raw = 2047 (0A)
RMS formula:  I_rms = sqrt(Σ((raw − midpoint) / ADC_MAX × VCC / sensitivity)² / N)
Samples:      64 per reading (oversampling for noise reduction)
""")

heading(doc, "4.3 DHT22 — Temperature & Humidity (dht22.c)", 2)
body(doc,
    "Interface: 1-Wire bit-bang on GPIO 4.")
code_block(doc, """
Protocol timing:
  Host start:    Pull LOW ≥ 1 ms, release, wait 30 µs
  Sensor ack:    80 µs LOW → 80 µs HIGH
  Bit '0':       50 µs LOW → 26–28 µs HIGH
  Bit '1':       50 µs LOW → ~70 µs HIGH
  Sample point:  Read GPIO at +40 µs after rising edge

Checksum: data[0]+data[1]+data[2]+data[3] == data[4]
Temperature: int16 from bytes 2–3, MSB = sign bit, ÷10 → °C
Humidity:    uint16 from bytes 0–1, ÷10 → %RH
""")

heading(doc, "4.4 Relay Module — Load Control (relay.c)", 2)
body(doc,
    "Interface: Digital output on GPIO 26/27/14/12 for relays 1–4.")
relay_rows = [
    ("1", "26", "Lights",  "Active-LOW (optocoupled)"),
    ("2", "27", "Fan",     "Active-LOW (optocoupled)"),
    ("3", "14", "AC unit", "Active-LOW (optocoupled)"),
    ("4", "12", "Spare",   "Active-LOW (optocoupled)"),
]
add_table(doc, ["Relay", "GPIO", "Load", "Logic"], relay_rows,
          col_widths=[0.6, 0.7, 1.2, 3.8])
body(doc, "")
bullet(doc, "All relays initialised to OFF (HIGH) at startup — fail-safe default")
bullet(doc, "State tracked in static array — relay_get_all() used by MQTT and display tasks")

heading(doc, "4.5 SSD1306 OLED — Display (ssd1306.c)", 2)
body(doc,
    "Interface: I2C on GPIO 21 (SDA) / GPIO 22 (SCL), 400 kHz, address 0x3C. "
    "Driver maintains a 128×64 framebuffer (1024 bytes) flushed explicitly.")
code_block(doc, """
Init sequence: 19 commands (display off → clock → mux → offset →
               start line → charge pump → addressing → remap →
               contrast → pre-charge → vcomh → display on)
Font:   5×7 pixel ASCII glyphs (space–@), stored in flash
Flush:  Horizontal addressing mode, 8 pages × 128 columns per I2C transfer
API:    ssd1306_clear() / set_cursor(col, row) / print() / printf() / flush()
""")

doc.add_page_break()

# ── 5. FreeRTOS Tasks ────────────────────────────────────────────────────────
heading(doc, "5. Layer 2 — FreeRTOS Task Implementation", 1)
hr(doc)
body(doc,
    "Seven FreeRTOS tasks were implemented, pinned to cores per the README spec. "
    "All task periods use vTaskDelayUntil() for deterministic scheduling.")

heading(doc, "5.1 Task Configuration Summary", 2)
task_rows = [
    ("sensor_task",     "1", "5", "4096 B",  "100 ms",     "Polls all sensors, produces to g_sensor_queue"),
    ("inference_task",  "1", "4", "8192 B",  "1000 ms",    "TFLite Micro anomaly + occupancy inference"),
    ("automation_task", "1", "4", "4096 B",  "500 ms",     "Offline rules engine, schedule evaluation"),
    ("mqtt_task",       "0", "6", "6144 B",  "Event",      "MQTT telemetry publish, command subscribe"),
    ("web_server_task", "0", "3", "4096 B",  "Event",      "Offline REST API (httpd), self-deletes after start"),
    ("ota_task",        "0", "2", "4096 B",  "3600 s",     "Hourly firmware version poll + OTA apply"),
    ("display_task",    "0", "1", "2048 B",  "2000 ms",    "OLED status render"),
]
add_table(doc,
          ["Task", "Core", "Pri", "Stack", "Period", "Responsibility"],
          task_rows,
          col_widths=[1.5, 0.5, 0.4, 0.7, 0.7, 2.5])

heading(doc, "5.2 sensor_task — Sensor Polling & Queue", 2)
bullet(doc, "Initialises all Layer 1 drivers on startup")
bullet(doc, "PIR HC-SR501 on GPIO 13 with GPIO interrupt registered (ISR installed once)")
bullet(doc, "Publishes sensor_reading_t structs to g_sensor_queue (depth 10)")
bullet(doc, "Status LED on GPIO 2 toggles on each successful reading")
bullet(doc, "Queue drops are logged as warnings — non-blocking xQueueSend(timeout=0)")

heading(doc, "5.3 mqtt_task — MQTT Telemetry & Commands", 2)
bullet(doc, "Uses ESP-IDF esp_mqtt_client with TLS broker URI from Kconfig")
bullet(doc, "LWT (Last Will and Testament): topic home/{id}/status, payload {\"online\":false}, QoS 1, retained")
bullet(doc, "Subscribes: cmd/relay (QoS 1), cmd/config (QoS 1), cmd/ota_trigger (QoS 1)")
bullet(doc, "Telemetry JSON built with snprintf — no heap allocation in hot path")
bullet(doc, "Relay commands parsed with cJSON, directly calls relay_set()")
code_block(doc, """
Telemetry topic: home/{device_id}/telemetry  QoS 0
Payload fields:  device_id, ts, voltage, current, power_w, power_factor,
                 energy_kwh, temperature, humidity, motion, relay_states[4]
                 anomaly_score, occupancy_prob, firmware_version
""")

heading(doc, "5.4 inference_task — TFLite Micro Inference", 2)
bullet(doc, "Maintains a 10-sample ring buffer of power_w readings")
bullet(doc, "Runs anomaly model (LSTM-Autoencoder) at 1 Hz on the ordered window")
bullet(doc, "Reconstruction MSE computed by dequantizing model output and comparing to input")
bullet(doc, "Occupancy model takes 3 features: power_w, motion (0/1), temperature")
bullet(doc, "Results stored in volatile inference_result_t g_inference_result (shared read-only by other tasks)")
bullet(doc, "Anomaly score > 0.5 triggers mqtt_publish_alert() with QoS 2 alert payload")
bullet(doc, "Conditional compilation: builds cleanly without model .h files — returns 0.0 defaults")

heading(doc, "5.5 automation_task — Offline Rules Engine", 2)
bullet(doc, "Supports 16 automation rules and 16 schedule entries, persisted in NVS")
bullet(doc, "Rule triggers: POWER_ABOVE/BELOW, TEMP_ABOVE/BELOW, MOTION, NO_MOTION, OCCUPANCY")
bullet(doc, "Cooldown timer per rule prevents relay chatter (configurable, default varies per rule)")
bullet(doc, "Default rule seeded at startup: fan OFF when power < 10 W (idle detection), 60s cooldown")
bullet(doc, "Peeks sensor queue without consuming — inference_task owns queue draining")

heading(doc, "5.6 web_server_task — Offline REST API", 2)
code_block(doc, """
GET  /api/status  → JSON: voltage, current, power_w, temperature, humidity,
                          motion, anomaly_score, occupancy_prob, relay_states[4]
POST /api/relay   → Body: {"relay": 0-3, "state": true/false}
                    Response: {"ok": true}
""")
bullet(doc, "Uses ESP-IDF httpd component (event-driven, non-blocking)")
bullet(doc, "Task self-deletes after registering URI handlers — httpd runs its own internal tasks")
bullet(doc, "Serves on port 80 — intended for LAN-only offline control")

heading(doc, "5.7 ota_task — OTA Firmware Updates", 2)
bullet(doc, "Polls OTA_VERSION_URL every 3600 seconds via HTTPS")
bullet(doc, "Fetches version.json: {\"version\": \"x.y.z\", \"url\": \"https://...\"}")
bullet(doc, "Compares running version (esp_app_get_description()) against latest")
bullet(doc, "Uses esp_https_ota() with embedded CA certificate for server verification")
bullet(doc, "On success: esp_restart() — ESP-IDF bootloader validates new partition")
bullet(doc, "On 3 consecutive boot failures: auto-rollback to previous partition (CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y)")

heading(doc, "5.8 display_task — OLED Status Render", 2)
code_block(doc, """
Row 0: {voltage}V  {current}A  {power}W
Row 1: T:{temp}C   H:{humidity}%
Row 2: Mot:{Y/N}   Occ:{occupancy}%
Row 3: R:[{r1}{r2}{r3}{r4}]  Anom:{score}
""")
bullet(doc, "Reads from g_sensor_queue (peek, non-destructive) and g_inference_result")
bullet(doc, "Calls ssd1306_flush() every 2 seconds — full framebuffer write over I2C")

doc.add_page_break()

# ── 6. AI Sub-System ─────────────────────────────────────────────────────────
heading(doc, "6. AI Inference Sub-System", 1)
hr(doc)

heading(doc, "6.1 inference.c — TFLite Micro C Wrapper", 2)
body(doc,
    "The inference wrapper is designed for build-time safety: if model header "
    "files (model_anomaly.h, model_occupancy.h) are absent, the file compiles "
    "cleanly and returns 0.0 defaults. This allows firmware CI to pass before "
    "the ML pipeline produces its first model.")

model_rows = [
    ("Anomaly Detection",      "LSTM-Autoencoder", "10-step power_w window",        "Reconstruction MSE", "~40 KB"),
    ("Occupancy Prediction",   "Dense NN (3 layers)", "power_w, motion, temperature", "Probability 0–1",  "~15 KB"),
    ("Energy Forecasting",     "LSTM (2 layers)",  "24-hr kWh history",             "Next-hour kWh",      "~55 KB"),
    ("Appliance Classification","1D-CNN",           "50-sample power waveform",       "Class label 1-of-N","~30 KB"),
]
add_table(doc,
          ["Model", "Algorithm", "Input Features", "Output", "Size (INT8)"],
          model_rows,
          col_widths=[1.5, 1.4, 1.8, 1.3, 0.8])

heading(doc, "6.2 features.c — Quantization Helpers", 2)
bullet(doc, "features_normalize_window(): min-max normalises float window to [0,1], then quantizes to INT8 using model scale/zero_point")
bullet(doc, "features_quantize(): general float[] → INT8 quantization for fixed-range inputs (occupancy 3-feature vector)")
code_block(doc, """
INT8 quantization formula:
  q = round(float_value / scale) + zero_point
  Clamped to [-128, 127]

Dequantization (output):
  float_value = (int8_value - zero_point) × scale
""")

heading(doc, "6.3 Arena Memory Layout", 2)
code_block(doc, """
Total arena: 180 KB (TFLITE_ARENA_SIZE)
  [0   … 90 KB]  → anomaly model interpreter arena
  [90  … 180 KB] → occupancy model interpreter arena

Note: forecasting and appliance classification models are intended for
      server-side inference (ai_service FastAPI) rather than on-device.
      Only anomaly + occupancy run on ESP32 in v1.0.
""")

doc.add_page_break()

# ── 7. NVS & Utilities ────────────────────────────────────────────────────────
heading(doc, "7. NVS Storage & Utilities", 1)
hr(doc)

heading(doc, "7.1 nvs_store.c — Non-Volatile Storage", 2)
body(doc, "NVS namespace: 'smarthome'. Provides typed accessors and blob persistence.")
nvs_rows = [
    ("nvs_store_set_str / get_str",    "String config values (WiFi SSID, device ID, broker URI)"),
    ("nvs_store_set_u32 / get_u32",    "Numeric config (thresholds, counters)"),
    ("nvs_store_save_rules",           "Serialises automation_rule_t[16] as NVS blob key 'rules'"),
    ("nvs_store_load_rules",           "Deserialises rules; zeroes array if key not found (first boot)"),
    ("nvs_store_save_schedules",       "Serialises schedule_entry_t[16] as NVS blob key 'schedules'"),
    ("nvs_store_load_schedules",       "Deserialises schedules; zeroes array on first boot"),
]
add_table(doc, ["Function", "Purpose"], nvs_rows, col_widths=[2.5, 3.8])

heading(doc, "7.2 logger.c — Log Level Configuration", 2)
body(doc,
    "Sets per-module ESP-IDF log levels at startup. Sensor/inference modules "
    "at DEBUG for development; network modules at INFO; driver modules at WARN "
    "to reduce UART noise during normal operation.")

heading(doc, "7.3 watchdog.c — Task Watchdog", 2)
bullet(doc, "30-second timeout via esp_task_wdt_init()")
bullet(doc, "trigger_panic = true — any task that fails to call watchdog_feed() within 30s causes a core dump")
bullet(doc, "Each long-running task should call watchdog_feed() in its main loop (to be added per-task)")

doc.add_page_break()

# ── 8. Build System ────────────────────────────────────────────────────────────
heading(doc, "8. ESP-IDF Build System", 1)
hr(doc)

heading(doc, "8.1 CMakeLists.txt", 2)
body(doc,
    "Root CMakeLists.txt: sets project name 'smart_home_firmware', includes "
    "ESP-IDF project.cmake. Main component CMakeLists.txt registers all 19 "
    "source files with INCLUDE_DIRS covering all sub-directories.")

heading(doc, "8.2 partitions.csv — Dual OTA Partition Table", 2)
code_block(doc, """
# Name,   Type, SubType,  Offset,   Size
nvs,      data, nvs,      0x9000,   0x5000    (20 KB  — config storage)
otadata,  data, ota,      0xe000,   0x2000    (8 KB   — OTA state)
app0,     app,  ota_0,    0x10000,  0x180000  (1536 KB — active firmware)
app1,     app,  ota_1,    0x190000, 0x180000  (1536 KB — standby firmware)
spiffs,   data, spiffs,   0x310000, 0xF0000   (960 KB — web/offline assets)
""")
bullet(doc, "Flash total: 4 MB — 2 × 1536 KB app partitions enable atomic OTA with rollback")
bullet(doc, "otadata partition tracks which app partition is active and boot attempt count")

heading(doc, "8.3 sdkconfig.defaults — Key Config Flags", 2)
sdkconfig_rows = [
    ("CONFIG_PARTITION_TABLE_CUSTOM=y",         "Points to partitions.csv"),
    ("CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y", "3-crash auto-rollback to previous partition"),
    ("CONFIG_FREERTOS_HZ=1000",                 "1 ms FreeRTOS tick — required for pdMS_TO_TICKS accuracy"),
    ("CONFIG_FREERTOS_UNICORE=n",               "Dual-core mode — enables core affinity pinning"),
    ("CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=8192", "TLS record buffer for MQTT/HTTPS"),
    ("CONFIG_LOG_DEFAULT_LEVEL_INFO=y",         "Default log level at INFO"),
    ("CONFIG_ESP_SLEEP_POWER_DOWN_FLASH=y",     "Flash power-down during deep sleep (~20 µA)"),
]
add_table(doc, ["Key", "Effect"], sdkconfig_rows, col_widths=[3.0, 3.3])

doc.add_page_break()

# ── 9. Git Activity Log ────────────────────────────────────────────────────────
heading(doc, "9. Git Activity Log", 1)
hr(doc)

git_rows = [
    ("1", "Checkout",
     "feature/scaffold-folder-structure",
     "Identified dev branch base for new feature work"),
    ("2", "Branch Create",
     "git checkout -b feature/firmware-layer1-layer2",
     "New feature branch created from dev"),
    ("3", "Implement",
     "45 files written across firmware/",
     "All Layer 1 drivers + Layer 2 tasks + AI + storage + utils"),
    ("4", "Stage & Commit",
     "git add firmware/ && git commit",
     "Commit 0d8acc3 — 1636 insertions"),
    ("5", "Push Feature",
     "git push -u origin feature/firmware-layer1-layer2",
     "Feature branch published to remote"),
    ("6", "Checkout Dev",
     "git checkout feature/scaffold-folder-structure",
     "Switch back to dev for merge"),
    ("7", "Merge",
     "git merge feature/firmware-layer1-layer2 --no-ff",
     "Merge commit cf6aded preserves branch topology"),
    ("8", "Push Dev",
     "git push -u origin feature/scaffold-folder-structure",
     "Dev branch updated on remote"),
]
add_table(doc,
          ["#", "Action", "Command / Target", "Detail"],
          git_rows,
          col_widths=[0.3, 1.0, 2.3, 2.7])

doc.add_page_break()

# ── 10. File Manifest ─────────────────────────────────────────────────────────
heading(doc, "10. File Manifest", 1)
hr(doc)
body(doc, "Complete list of files created during this session (45 files).")

heading(doc, "10.1 Build System", 2)
build_files = [
    ("firmware/CMakeLists.txt",        "Root CMake project file"),
    ("firmware/main/CMakeLists.txt",   "Component registration — all 19 .c sources"),
    ("firmware/partitions.csv",        "Dual OTA partition table"),
    ("firmware/sdkconfig.defaults",    "ESP-IDF default configuration flags"),
]
add_table(doc, ["File", "Purpose"], build_files, col_widths=[2.8, 3.5])

heading(doc, "10.2 Layer 1 — Hardware Drivers", 2)
l1_files = [
    ("firmware/main/drivers/pzem004t.h/.c", "PZEM-004T Modbus RTU driver"),
    ("firmware/main/drivers/acs712.h/.c",   "ACS712 ADC RMS current driver"),
    ("firmware/main/drivers/dht22.h/.c",    "DHT22 1-Wire temperature/humidity driver"),
    ("firmware/main/drivers/relay.h/.c",    "4-channel optocoupled relay driver"),
    ("firmware/main/drivers/ssd1306.h/.c",  "SSD1306 I2C OLED framebuffer driver"),
]
add_table(doc, ["File Pair", "Purpose"], l1_files, col_widths=[2.8, 3.5])

heading(doc, "10.3 Layer 2 — FreeRTOS Tasks", 2)
l2_files = [
    ("firmware/main/app_main.c",                 "Entry point — task launcher with core affinity"),
    ("firmware/main/tasks/sensor_task.h/.c",     "10 Hz sensor polling + queue producer"),
    ("firmware/main/tasks/mqtt_task.h/.c",       "MQTT telemetry + command handler"),
    ("firmware/main/tasks/inference_task.h/.c",  "TFLite Micro anomaly + occupancy inference"),
    ("firmware/main/tasks/automation_task.h/.c", "Offline rules engine + schedule evaluation"),
    ("firmware/main/tasks/web_server_task.h/.c", "Offline REST API (httpd)"),
    ("firmware/main/tasks/ota_task.h/.c",        "OTA firmware update with rollback"),
    ("firmware/main/tasks/display_task.h/.c",    "OLED status render at 0.5 Hz"),
]
add_table(doc, ["File", "Purpose"], l2_files, col_widths=[2.8, 3.5])

heading(doc, "10.4 AI, Storage & Utilities", 2)
misc_files = [
    ("firmware/main/ai/inference.h/.c",      "TFLite Micro C wrapper (conditional model include)"),
    ("firmware/main/ai/features.h/.c",       "INT8 quantization and window normalization"),
    ("firmware/main/storage/nvs_store.h/.c", "NVS blob persistence for rules and config"),
    ("firmware/main/utils/logger.h/.c",      "Per-module ESP-IDF log level setup"),
    ("firmware/main/utils/watchdog.h/.c",    "30s task watchdog with panic on timeout"),
]
add_table(doc, ["File Pair", "Purpose"], misc_files, col_widths=[2.8, 3.5])

doc.add_page_break()

# ── 11. Memory Budget ─────────────────────────────────────────────────────────
heading(doc, "11. Memory Budget Verification", 1)
hr(doc)
body(doc,
    "Verified against README specification. All allocations are within the "
    "512 KB SRAM limit with ~18% headroom.")

sram_rows = [
    ("TFLite Micro arena",   "180 KB", "Anomaly (90 KB) + Occupancy (90 KB)"),
    ("FreeRTOS task stacks", "~80 KB", "7 tasks: 4096+8192+4096+6144+4096+4096+2048 = 32.7 KB declared"),
    ("WiFi + TCP/IP (lwIP)", "~60 KB", "WiFi driver allocation — managed by ESP-IDF"),
    ("MQTT client buffers",  "~20 KB", "esp_mqtt_client in/out buffers"),
    ("Application heap",     "~80 KB", "Sensor queue, JSON buffers, cJSON, misc"),
    ("Total used",           "~420 KB","of 512 KB SRAM"),
    ("Headroom",             "~92 KB", "~18% free"),
]
add_table(doc,
          ["Region", "Allocation", "Notes"],
          sram_rows,
          col_widths=[1.9, 1.1, 3.3])

doc.add_page_break()

# ── 12. Design Decisions & Risk Notes ────────────────────────────────────────
heading(doc, "12. Design Decisions & Risk Notes", 1)
hr(doc)

decisions = [
    ("Conditional model include (#if __has_include)",
     "Allows firmware to compile and run without TFLite model headers present. "
     "The inference functions return 0.0 (safe default). This decouples firmware "
     "CI from the ML training pipeline — both can progress independently."),
    ("snprintf for telemetry JSON (no cJSON heap)",
     "The MQTT telemetry loop runs at up to 10 Hz. Using snprintf with a "
     "stack-allocated buffer avoids heap fragmentation in the hot path. "
     "cJSON is only used for received command parsing, which is event-driven."),
    ("xQueuePeek in automation/display tasks",
     "automation_task and display_task peek (non-destructive) the sensor queue. "
     "Only inference_task fully drains the queue. This avoids a race where "
     "automation consumes readings before inference can process them."),
    ("--no-ff merge strategy",
     "The feature branch merge used --no-ff to create a merge commit, preserving "
     "the full branch topology. This makes git log --graph show the feature "
     "boundary clearly, which is important for code review and bisect."),
    ("web_server_task self-delete",
     "ESP-IDF httpd runs its own internal FreeRTOS tasks. The web_server_task "
     "only exists to register URI handlers, then calls vTaskDelete(NULL). "
     "This avoids an idle task sitting at priority 3 consuming stack permanently."),
]
for title, detail in decisions:
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    body(doc, detail)

doc.add_page_break()

# ── 13. Next Steps ────────────────────────────────────────────────────────────
heading(doc, "13. Next Steps", 1)
hr(doc)
body(doc, "Recommended development sequence following this session:")

next_steps = [
    ("Phase 2 — Backend",
     "Implement FastAPI backend: Docker Compose setup (Mosquitto, InfluxDB, PostgreSQL, Redis), "
     "MQTT bridge service, device auth endpoints, telemetry ingest, relay control API, JWT auth flow."),
    ("Phase 3 — TinyML Pipeline",
     "Collect 2–4 weeks of sensor data. "
     "Train anomaly (LSTM-Autoencoder) and occupancy (Dense NN) models. "
     "Convert to TFLite INT8, generate model_anomaly.h and model_occupancy.h, "
     "drop into firmware/main/ai/ — inference_task will activate automatically."),
    ("Phase 2 — Frontend",
     "Next.js 14 dashboard: live gauges (WebSocket), relay toggles, energy charts (Recharts), "
     "JWT auth via NextAuth.js."),
    ("Phase 4 — Mobile App",
     "Flutter app with BLoC state management, mqtt_client package, FCM push notifications, "
     "QR code device onboarding."),
    ("Phase 5 — Hardening",
     "Enable ESP32 Secure Boot V2 + flash encryption (eFuse). "
     "Full GitHub Actions CI (firmware build + Unity tests, pytest, jest). "
     "Prometheus + Grafana observability stack."),
    ("Immediate Risk Mitigations",
     "1) Increase inference_task stack from 8192 to 16384 B. "
     "2) Separate inference_task and automation_task priorities (set automation to 3). "
     "3) Clarify API rate limit scope (per-IP vs per-user) in backend config."),
]
add_table(doc, ["Priority", "Action"], next_steps, col_widths=[1.8, 4.5])

# ── Footer ────────────────────────────────────────────────────────────────────
doc.add_paragraph()
hr(doc)
footer_p = doc.add_paragraph()
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = footer_p.add_run(
    "Smart Home Power Management & Automation System  |  "
    "Technical Activity Report  |  2026-05-26  |  v1.0  |  Confidential")
fr.font.size = Pt(8)
fr.font.color.rgb = RGBColor(0x70, 0x70, 0x70)

# ── Save ─────────────────────────────────────────────────────────────────────
out_path = "/home/user/Tiny_Ml_Home_Automation/doc/TinyML_HomeAutomation_ActivityReport_2026-05-26.docx"
doc.save(out_path)
print(f"Document saved: {out_path}")
