# Smart Home Power Management & Automation System
## Complete Architecture & Tech Stack Reference

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram (Text)](#architecture-diagram-text)
3. [Layer 1 — Hardware & Sensors](#layer-1--hardware--sensors)
4. [Layer 2 — Edge Intelligence (ESP32)](#layer-2--edge-intelligence-esp32)
5. [Layer 3 — Connectivity Protocols](#layer-3--connectivity-protocols)
6. [Layer 4 — Backend Stack](#layer-4--backend-stack)
7. [Layer 5 — TinyML / AI Pipeline](#layer-5--tinyml--ai-pipeline)
8. [Layer 6 — Frontend & Mobile](#layer-6--frontend--mobile)
9. [Layer 7 — DevOps & Infrastructure](#layer-7--devops--infrastructure)
10. [Security Architecture](#security-architecture)
11. [MQTT Topic Design](#mqtt-topic-design)
12. [Database Schema Overview](#database-schema-overview)
13. [REST API Endpoints](#rest-api-endpoints)
14. [ESP32 Memory Budget](#esp32-memory-budget)
15. [Folder Structure](#folder-structure)
16. [Development Roadmap](#development-roadmap)
17. [Bill of Materials](#bill-of-materials)

---

## System Overview

An end-to-end AI-powered smart home system built on ESP32 microcontrollers. The system monitors real-time energy consumption, runs TinyML models at the edge for anomaly detection and occupancy prediction, automates loads, and provides a cloud dashboard and mobile app for remote control.

### Core Capabilities

| Capability | Implementation |
|---|---|
| Real-time energy monitoring | PZEM-004T + ACS712 → ESP32 → InfluxDB |
| Edge AI inference | TensorFlow Lite Micro on ESP32 |
| Offline/offline resilience | Local NVS rules engine, offline REST API |
| Remote control | FastAPI + MQTT → Next.js + Flutter |
| OTA firmware updates | ESP-IDF dual-partition OTA with rollback |
| Anomaly detection | LSTM-Autoencoder, inference on device |
| Appliance classification | CNN on power signature, on-device |

---

## Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — HARDWARE / SENSORS                                       │
│  PZEM-004T │ ACS712 │ DHT22 │ HC-SR501 PIR │ Relay │ OLED          │
│  [Optional] Solar CT │ BMS/LiPo │ Zigbee dongle │ Matter switch    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ UART / I2C / GPIO
┌────────────────────────────▼────────────────────────────────────────┐
│  LAYER 2 — EDGE INTELLIGENCE (ESP32 DevKit V1)                      │
│  FreeRTOS Tasks │ TFLite Micro │ Local Automation │ NVS Storage      │
│  WiFi Provisioning │ OTA │ Secure Boot │ Deep Sleep                 │
│  Framework: ESP-IDF v5.x (primary) · Arduino/PlatformIO (alt)       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ WiFi / BLE
┌────────────────────────────▼────────────────────────────────────────┐
│  LAYER 3 — CONNECTIVITY PROTOCOLS                                   │
│  MQTT/TLS · REST API · WebSocket · BLE 5.0 · WiFi 802.11n          │
│  [Optional] Zigbee · Matter protocol                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │ TCP/IP
┌────────────────────────────▼────────────────────────────────────────┐
│  LAYER 4 — BACKEND (Dockerized)                                     │
│  FastAPI · Mosquitto MQTT broker · InfluxDB · PostgreSQL            │
│  Redis · Celery (alerts) · Nginx + SSL · Prometheus                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
┌─────────▼──────┐  ┌────────▼────────┐  ┌──────▼──────────────────┐
│  LAYER 5       │  │  LAYER 6        │  │  LAYER 7                │
│  TinyML        │  │  Frontend       │  │  DevOps                 │
│  AI Pipeline   │  │  & Mobile       │  │  & Infra                │
│  TF · TFLite   │  │  Next.js        │  │  Docker Compose         │
│  scikit-learn  │  │  Flutter        │  │  GitHub Actions         │
│  INT8 quant.   │  │  Recharts       │  │  Grafana · Prometheus   │
└────────────────┘  └─────────────────┘  └─────────────────────────┘
```

---

## Layer 1 — Hardware & Sensors

### Component Selection

| Component | Model | Interface | Role |
|---|---|---|---|
| Microcontroller | ESP32 DevKit V1 | — | Main controller |
| Power monitor | PZEM-004T v3.0 | UART (TTL) | Voltage, current, PF, kWh |
| Current sensor | ACS712 (20A) | ADC | Per-circuit current |
| Temp/humidity | DHT22 | 1-Wire GPIO | AC automation input |
| Motion sensor | HC-SR501 PIR | GPIO interrupt | Occupancy detection |
| Relay module | 4-ch optocoupled | GPIO | Load control |
| Display | SSD1306 0.96" OLED | I2C | Local status readout |
| Smart switch | Any Matter/Zigbee | — | Optional integration |
| Solar monitor | SCT-013 CT clamp | ADC | Optional solar input |
| Battery management | TP4056 + 18650 | I2C | Optional backup power |

### GPIO Mapping

| GPIO | Function | Type |
|---|---|---|
| GPIO 16/17 | PZEM-004T UART2 RX/TX | UART |
| GPIO 4 | DHT22 data | Digital |
| GPIO 34 | ACS712 analog output | ADC1 |
| GPIO 13 | PIR signal | Digital interrupt |
| GPIO 26 | Relay 1 (lights) | Digital output |
| GPIO 27 | Relay 2 (fan) | Digital output |
| GPIO 14 | Relay 3 (AC) | Digital output |
| GPIO 12 | Relay 4 (spare) | Digital output |
| GPIO 21/22 | OLED SDA/SCL | I2C |
| GPIO 2 | Status LED | Digital output |

### Safety Design Principles

- Optocoupler isolation between ESP32 GPIO and relay coil circuits
- 10A fuse on each relay output line
- MOV (Metal Oxide Varistor) surge protection on mains input
- PZEM-004T connected via non-invasive split-core CT or series shunt
- 5V regulated power rail for ESP32, separate from relay 12V supply
- Flyback diode on each relay coil to suppress back-EMF

---

## Layer 2 — Edge Intelligence (ESP32)

### Firmware Architecture

```
firmware/
├── main/
│   ├── app_main.c              # Entry point, task launcher
│   ├── tasks/
│   │   ├── sensor_task.c       # 10 Hz sensor polling
│   │   ├── mqtt_task.c         # Publish telemetry, receive commands
│   │   ├── inference_task.c    # TFLite Micro inference loop (1 Hz)
│   │   ├── web_server_task.c   # Local REST API (offline fallback)
│   │   ├── automation_task.c   # Rules engine + schedule execution
│   │   ├── ota_task.c          # OTA update polling and apply
│   │   └── display_task.c      # OLED status rendering
│   ├── drivers/
│   │   ├── pzem004t.c          # PZEM UART driver
│   │   ├── acs712.c            # ADC current driver
│   │   ├── dht22.c             # Temperature sensor driver
│   │   ├── relay.c             # Relay abstraction layer
│   │   └── ssd1306.c           # OLED I2C driver
│   ├── ai/
│   │   ├── model_anomaly.h     # Anomaly model C array
│   │   ├── model_occupancy.h   # Occupancy model C array
│   │   ├── inference.c         # TFLite Micro wrapper
│   │   └── features.c          # Feature extraction
│   ├── storage/
│   │   └── nvs_store.c         # Config + offline log via NVS
│   └── utils/
│       ├── logger.c            # Structured logging
│       └── watchdog.c          # Task watchdog + recovery
├── CMakeLists.txt
├── sdkconfig.defaults
└── partitions.csv              # Dual OTA partition table
```

### FreeRTOS Task Configuration

| Task | Core | Priority | Stack | Period |
|---|---|---|---|---|
| `sensor_task` | 1 | 5 | 4096 B | 100 ms |
| `inference_task` | 1 | 4 | 8192 B | 1000 ms |
| `mqtt_task` | 0 | 6 | 6144 B | Event-driven |
| `web_server_task` | 0 | 3 | 4096 B | Event-driven |
| `automation_task` | 1 | 4 | 4096 B | 500 ms |
| `ota_task` | 0 | 2 | 4096 B | 3600 s |
| `display_task` | 0 | 1 | 2048 B | 2000 ms |

### OTA Partition Table

```
# partitions.csv
# Name,   Type, SubType,  Offset,   Size,  Flags
nvs,      data, nvs,      0x9000,   0x5000,
otadata,  data, ota,      0xe000,   0x2000,
app0,     app,  ota_0,    0x10000,  0x180000,
app1,     app,  ota_1,    0x190000, 0x180000,
spiffs,   data, spiffs,   0x310000, 0xF0000,
```

### Key Design Decisions

- **ESP-IDF over Arduino** — direct FreeRTOS control, partition management, secure boot, and flash encryption APIs
- **Dual partition OTA** — if a new firmware crashes on boot 3× consecutively, ESP-IDF automatically rolls back to the previous partition
- **Core affinity** — AI inference and sensor reading pinned to Core 1; network stack on Core 0, preventing interference
- **Deep sleep** — sensor-only nodes (no relay) can sleep between readings, drawing ~20 µA vs ~240 mA active

---

## Layer 3 — Connectivity Protocols

### Protocol Roles

| Protocol | Direction | Use Case |
|---|---|---|
| MQTT over TLS 1.2 | Bidirectional | Primary telemetry and command channel |
| WebSocket | Server → Client | Real-time dashboard updates |
| HTTP REST (ESP32) | Local | Offline device control, provisioning API |
| BLE 5.0 | Local | Initial WiFi credential provisioning |
| WiFi 802.11n 2.4 GHz | Infrastructure | Primary network transport |
| Zigbee (optional) | Local mesh | Third-party device integration |
| Matter (optional) | Local/cloud | Apple Home / Google Home interop |

### MQTT Quality of Service

| Message Type | QoS Level | Reason |
|---|---|---|
| Telemetry (sensor data) | QoS 0 | High frequency, loss acceptable |
| Commands (relay on/off) | QoS 1 | Must be delivered at least once |
| Alerts (anomaly detected) | QoS 2 | Exactly once, critical |
| Status (device online/offline) | QoS 1 | LWT (Last Will and Testament) |

---

## Layer 4 — Backend Stack

### Service Architecture

| Service | Technology | Version | Port |
|---|---|---|---|
| API server | Python FastAPI | 0.111+ | 8000 |
| MQTT broker | Eclipse Mosquitto | 2.0 | 1883 / 8883 (TLS) |
| Time-series database | InfluxDB | 2.7 | 8086 |
| Relational database | PostgreSQL | 16 | 5432 |
| In-memory cache | Redis | 7.x | 6379 |
| Background worker | Celery | 5.x | — |
| AI inference service | FastAPI (separate) | — | 8001 |
| Reverse proxy | Nginx | 1.25 | 80 / 443 |
| Metrics collection | Prometheus | 2.x | 9090 |
| Metrics dashboard | Grafana | 10.x | 3000 |

### Docker Compose Service Map

```yaml
services:
  api:          FastAPI application
  mosquitto:    MQTT broker with TLS
  influxdb:     Time-series storage
  postgres:     Relational storage
  redis:        Cache and pub/sub
  celery:       Background alert processing
  ai_service:   AI forecast and retrain API
  nginx:        TLS termination and routing
  prometheus:   Metrics scraper
  grafana:      Observability dashboards
```

### Authentication Flow

```
Client → POST /auth/login (username + password)
       ← { access_token (15 min), refresh_token (7 days) }

Client → GET /api/devices  Authorization: Bearer <access_token>
       ← device list

Client → POST /auth/refresh  { refresh_token }
       ← { new access_token }

ESP32  → MQTT CONNECT  username: device_id, password: device_secret
       ← CONNACK (Mosquitto ACL validates device_id)
```

---

## Layer 5 — TinyML / AI Pipeline

### Models Overview

| Model | Algorithm | Input Features | Output | Size (INT8) |
|---|---|---|---|---|
| Anomaly detection | LSTM-Autoencoder | 10-step power sequence | Reconstruction error score | ~40 KB |
| Occupancy prediction | Dense NN (3 layers) | PIR + power + time-of-day | Probability (0–1) | ~15 KB |
| Energy forecasting | LSTM (2 layers) | 24-hour historical kWh | Next-hour kWh prediction | ~55 KB |
| Appliance classification | 1D-CNN | 50-sample power waveform | Class label (1 of N) | ~30 KB |

### Training Pipeline

```
Raw sensor CSV
      │
      ▼
data_cleaning.py        # Remove outliers, fill gaps, normalize
      │
      ▼
feature_engineering.py  # Rolling stats, time features, lag features
      │
      ▼
model_train.py          # TensorFlow/Keras training with early stopping
      │
      ▼
model_evaluate.py       # Confusion matrix, MAE, F1, ROC-AUC
      │
      ▼
convert_tflite.py       # TFLiteConverter + INT8 post-training quantize
      │
      ▼
generate_header.py      # xxd → model_anomaly.h C array for ESP32
```

### TFLite Conversion (key settings)

```python
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
converter.representative_dataset = representative_data_gen
tflite_model = converter.convert()
```

### Edge Inference Flow

```
Sensor buffer (10 samples) → feature_extract() → normalize to INT8
    → tflite_micro_invoke() → dequantize output
    → threshold check → trigger alert or automation action
```

---

## Layer 6 — Frontend & Mobile

### Web Dashboard (Next.js)

| Component | Technology | Purpose |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSR + client components |
| Styling | Tailwind CSS 3.x | Utility-first responsive design |
| Charts | Recharts | Energy time-series, prediction plots |
| Real-time | WebSocket (native) | Live sensor updates without polling |
| State | Zustand | Lightweight global state |
| Auth | NextAuth.js | JWT session management |
| Forms | React Hook Form + Zod | Schedule editor, device config |

### Dashboard Views

| View | Key Features |
|---|---|
| Overview | Live kWh gauge, cost estimate, anomaly status |
| Energy Analytics | Hourly/daily/monthly bar charts, per-room breakdown |
| Device Control | Relay toggles, dimmer sliders, schedule editor |
| AI Predictions | Forecast chart, occupancy heatmap, anomaly log |
| Alerts | Notification inbox, severity filter, acknowledge |
| Settings | Device management, thresholds, user profile |

### Mobile App (Flutter)

| Feature | Implementation |
|---|---|
| Architecture | Clean Architecture + BLoC state management |
| Real-time data | `mqtt_client` package, persistent connection |
| Push notifications | Firebase Cloud Messaging (FCM) |
| Offline caching | Hive local database |
| Charts | fl_chart package |
| QR onboarding | `qr_code_scanner` package |
| Voice commands | speech_to_text + local intent parsing |

---

## Layer 7 — DevOps & Infrastructure

### CI/CD Pipeline (GitHub Actions)

```
Push to main branch
      │
      ├── firmware_build.yml
      │     └── Build ESP32 firmware .bin
      │         Run unit tests (Unity framework)
      │         Upload artifact to S3/GitHub releases
      │
      ├── backend_deploy.yml
      │     └── Run pytest
      │         Build Docker images
      │         Push to container registry
      │         Deploy via Docker Compose (SSH)
      │
      └── frontend_deploy.yml
            └── Run jest tests
                Build Next.js static export
                Deploy to Vercel or Nginx
```

### OTA Deployment Flow

```
New firmware .bin built by CI
      │
      ▼
Uploaded to /ota/firmware endpoint (FastAPI)
      │
      ▼
ESP32 ota_task polls /ota/version every hour
      │  (compares running version with latest)
      ▼
If update available: esp_https_ota() downloads and writes to inactive partition
      │
      ▼
Reboot → ESP-IDF validates new firmware → marks partition as valid
      │  (if 3 crashes: auto-rollback to previous partition)
      ▼
Device reports new version via MQTT
```

### Infrastructure Requirements (Self-hosted VPS)

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Storage | 40 GB SSD | 100 GB SSD |
| Estimated cost | ~$12/month | ~$24/month |

---

## Security Architecture

### Threat Model & Mitigations

| Threat | Mitigation |
|---|---|
| MQTT eavesdropping | TLS 1.2 on port 8883, client certificates |
| Unauthorized device | X.509 device certificates, Mosquitto ACL |
| API abuse | JWT expiry (15 min), rate limiting (100 req/min) |
| Firmware tampering | ESP32 secure boot V2 + flash encryption |
| OTA man-in-the-middle | HTTPS OTA with certificate pinning |
| Brute force login | Bcrypt password hashing, account lockout |
| Database exposure | Containers on private Docker network, no public ports |
| Replay attacks | MQTT message timestamps + server-side dedup |

### Security Layers

```
ESP32 Hardware:    Secure Boot V2 + Flash Encryption (eFuse)
Transport:         TLS 1.2 everywhere (MQTT, HTTP, WebSocket)
Authentication:    JWT (users) + X.509 certificates (devices)
Authorization:     Role-based (admin / user / viewer) + device ACL
Network:           All backend services on private Docker network
                   Only Nginx exposed on ports 80/443
Storage:           Passwords bcrypt-hashed, secrets in env vars
                   InfluxDB tokens, no hardcoded credentials
```

---

## MQTT Topic Design

```
home/
├── {device_id}/
│   ├── telemetry          # Sensor data JSON, published by ESP32 (QoS 0)
│   ├── cmd                # Commands to ESP32 (QoS 1)
│   │   ├── relay          # {"relay": 1, "state": true}
│   │   ├── config         # {"threshold_watts": 2000}
│   │   └── ota_trigger    # {"version": "1.2.0", "url": "..."}
│   ├── status             # LWT: {"online": false} (QoS 1, retained)
│   └── alert              # Anomaly / threshold alerts (QoS 2)
│
├── gateway/
│   ├── broadcast          # System-wide announcements
│   └── discovery          # New device announcements
│
└── analytics/
    ├── predictions        # AI forecast results
    └── insights           # Daily/weekly summaries
```

### Telemetry Payload Schema

```json
{
  "device_id": "esp32_room_01",
  "ts": 1718000000,
  "voltage": 231.4,
  "current": 4.21,
  "power_w": 972.3,
  "power_factor": 0.98,
  "energy_kwh": 1.24,
  "temperature": 26.5,
  "humidity": 58.2,
  "motion": true,
  "relay_states": [true, false, true, false],
  "anomaly_score": 0.12,
  "occupancy_prob": 0.87,
  "firmware_version": "1.2.0"
}
```

---

## Database Schema Overview

### PostgreSQL (Relational)

```sql
users           (id, email, password_hash, role, created_at)
devices         (id, device_id, name, room, owner_id, secret_hash)
rooms           (id, name, floor, owner_id)
schedules       (id, device_id, cron_expr, action, enabled)
automation_rules(id, device_id, trigger_type, condition, action)
alerts          (id, device_id, type, severity, message, acknowledged_at)
ota_releases    (id, version, firmware_url, checksum, released_at)
```

### InfluxDB (Time-Series)

```
Measurement: energy_telemetry
Tags:        device_id, room, floor
Fields:      voltage, current, power_w, power_factor, energy_kwh,
             temperature, humidity, anomaly_score, occupancy_prob
Timestamp:   Unix nanoseconds

Retention:   Raw data → 30 days
             Hourly downsampled → 1 year
             Daily downsampled → indefinite
```

---

## REST API Endpoints

### Devices

```
GET    /api/devices                    List all devices
POST   /api/devices                    Register new device
GET    /api/devices/{id}               Device details
PUT    /api/devices/{id}/relay         Control relay
DELETE /api/devices/{id}               Remove device
```

### Energy

```
GET    /api/energy/realtime            Latest telemetry (all devices)
GET    /api/energy/history?from=&to=   Historical data
GET    /api/energy/summary?period=     Daily/monthly totals
GET    /api/energy/rooms               Per-room breakdown
```

### AI / Predictions

```
GET    /api/ai/forecast?device_id=     Next-hour energy forecast
GET    /api/ai/anomalies?limit=        Recent anomaly events
GET    /api/ai/occupancy               Current occupancy predictions
POST   /api/ai/retrain                 Trigger model retraining job
```

### Alerts & Automation

```
GET    /api/alerts?acknowledged=false  Unacknowledged alerts
PUT    /api/alerts/{id}/acknowledge    Mark alert as read
GET    /api/schedules                  List schedules
POST   /api/schedules                  Create schedule
PUT    /api/schedules/{id}             Update schedule
DELETE /api/schedules/{id}             Delete schedule
```

---

## ESP32 Memory Budget

| Region | Allocation | Notes |
|---|---|---|
| TFLite Micro arena | 180 KB | All 4 model arenas combined |
| FreeRTOS task stacks | 80 KB | 7 tasks × avg ~11 KB |
| WiFi + TCP/IP stack | 60 KB | lwIP + WiFi driver |
| MQTT client buffers | 20 KB | In/out buffers |
| Application heap | 80 KB | Sensor buffers, JSON, misc |
| **Total used** | **~420 KB** | of 512 KB SRAM |
| **Headroom** | **~92 KB** | ~18% free |

**Flash usage** (4 MB total):

| Region | Size |
|---|---|
| Bootloader | 28 KB |
| Partition table | 8 KB |
| NVS | 20 KB |
| OTA data | 8 KB |
| App partition (×2) | 1536 KB each |
| SPIFFS (web assets) | 960 KB |

---

## Folder Structure

### Complete Repository Layout

```
smart-home-system/
│
├── firmware/                          # ESP32 firmware (ESP-IDF)
│   ├── main/
│   │   ├── app_main.c
│   │   ├── tasks/
│   │   ├── drivers/
│   │   ├── ai/
│   │   ├── storage/
│   │   └── utils/
│   ├── components/                    # Reusable ESP-IDF components
│   ├── partitions.csv
│   ├── sdkconfig.defaults
│   └── CMakeLists.txt
│
├── ml/                                # TinyML training pipeline
│   ├── data/                          # Raw + processed datasets
│   ├── notebooks/                     # Exploration notebooks
│   ├── src/
│   │   ├── data_cleaning.py
│   │   ├── feature_engineering.py
│   │   ├── train_anomaly.py
│   │   ├── train_occupancy.py
│   │   ├── train_forecast.py
│   │   ├── train_appliance.py
│   │   ├── convert_tflite.py
│   │   └── generate_header.py
│   ├── models/                        # Saved .h5 and .tflite files
│   └── requirements.txt
│
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── devices.py
│   │   │   ├── energy.py
│   │   │   ├── ai.py
│   │   │   ├── alerts.py
│   │   │   └── auth.py
│   │   ├── models/                    # SQLAlchemy models
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── services/
│   │   │   ├── mqtt_bridge.py
│   │   │   ├── influx_client.py
│   │   │   ├── alert_engine.py
│   │   │   └── ai_service.py
│   │   └── core/
│   │       ├── config.py
│   │       ├── security.py
│   │       └── database.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                          # Next.js web dashboard
│   ├── app/
│   │   ├── (auth)/
│   │   ├── dashboard/
│   │   ├── devices/
│   │   ├── analytics/
│   │   └── settings/
│   ├── components/
│   │   ├── charts/
│   │   ├── controls/
│   │   └── ui/
│   ├── lib/
│   │   ├── api.ts
│   │   └── websocket.ts
│   └── package.json
│
├── mobile/                            # Flutter mobile app
│   ├── lib/
│   │   ├── features/
│   │   ├── core/
│   │   └── main.dart
│   └── pubspec.yaml
│
├── infra/                             # Infrastructure config
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   ├── mosquitto/
│   │   └── mosquitto.conf
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
└── .github/
    └── workflows/
        ├── firmware_build.yml
        ├── backend_deploy.yml
        └── frontend_deploy.yml
```

---

## Development Roadmap

### Phase 1 — Hardware & Firmware Foundation (Weeks 1–3)

- [ ] Assemble hardware, wire sensors to ESP32
- [ ] Write PZEM-004T and ACS712 drivers
- [ ] Implement FreeRTOS task skeleton
- [ ] Basic MQTT telemetry publishing
- [ ] NVS config storage
- [ ] WiFi provisioning via BLE

### Phase 2 — Backend & Basic Dashboard (Weeks 4–6)

- [ ] Docker Compose setup (Mosquitto, InfluxDB, PostgreSQL, Redis)
- [ ] FastAPI: device auth, telemetry ingest, relay control endpoints
- [ ] MQTT bridge service (backend subscribes to device topics)
- [ ] Next.js dashboard: live gauges, relay toggles
- [ ] JWT authentication flow

### Phase 3 — TinyML Integration (Weeks 7–9)

- [ ] Collect 2–4 weeks of sensor data
- [ ] Train anomaly detection model (LSTM-Autoencoder)
- [ ] Train occupancy prediction model
- [ ] Convert to TFLite INT8, generate C headers
- [ ] Integrate TFLite Micro into firmware inference task
- [ ] Expose anomaly alerts via MQTT and dashboard

### Phase 4 — Automation & Mobile App (Weeks 10–12)

- [ ] Rules engine on ESP32 (offline automation)
- [ ] Schedule editor in dashboard
- [ ] OTA update pipeline (CI builds .bin, backend serves it)
- [ ] Flutter app: live data, relay control, push notifications
- [ ] QR code device onboarding

### Phase 5 — Production Hardening (Ongoing)

- [ ] Enable ESP32 secure boot and flash encryption
- [ ] Full CI/CD pipeline with test gates
- [ ] Prometheus + Grafana observability
- [ ] Model retraining pipeline (weekly automated retrain)
- [ ] Multi-device support and room grouping
- [ ] Optional: Zigbee / Matter integration

---

## Bill of Materials

| Component | Qty | Unit Cost (USD) | Subtotal |
|---|---|---|---|
| ESP32 DevKit V1 | 4 | $5.00 | $20.00 |
| PZEM-004T v3.0 | 2 | $12.00 | $24.00 |
| ACS712 20A module | 4 | $2.00 | $8.00 |
| DHT22 sensor | 4 | $2.50 | $10.00 |
| HC-SR501 PIR | 4 | $1.50 | $6.00 |
| 4-ch relay module (optocoupled) | 4 | $3.50 | $14.00 |
| SSD1306 OLED 0.96" | 4 | $2.50 | $10.00 |
| Power supply (5V 3A) | 4 | $4.00 | $16.00 |
| PCB / protoboard | 4 | $3.00 | $12.00 |
| Wires, fuses, connectors | — | — | $10.00 |
| Enclosure (DIN rail box) | 4 | $5.00 | $20.00 |
| **Hardware Total** | | | **~$150** |
| VPS (backend hosting) | 1 | $12/month | $12/month |
| Domain + SSL | 1 | $12/year | ~$1/month |
| **Recurring Total** | | | **~$13/month** |

---

*Architecture version 1.0 — Generated for AI Smart Home Power Management System*
*Stack finalized: ESP-IDF · FastAPI · InfluxDB · PostgreSQL · Redis · Next.js · Flutter · TensorFlow Lite Micro*
