# Smart Home System — Developer Makefile
# Usage: make <target>

COMPOSE       = docker compose -f infra/docker-compose.yml
COMPOSE_PROD  = docker compose -f infra/docker-compose.prod.yml
BACKEND_DIR   = backend
FRONTEND_DIR  = frontend
ML_DIR        = ml

.PHONY: help up down logs ps build \
        backend-test frontend-test \
        ml-clean ml-features ml-train ml-convert \
        fw-build fw-flash fw-monitor \
        fmt lint

## ── Help ─────────────────────────────────────────────────────────────────────
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

## ── Docker Compose ───────────────────────────────────────────────────────────
up: ## Start all services (dev)
	cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

logs: ## Tail logs (all services)
	$(COMPOSE) logs -f

ps: ## Show running containers
	$(COMPOSE) ps

build: ## Rebuild all Docker images
	$(COMPOSE) build --no-cache

restart-api: ## Restart only the API container
	$(COMPOSE) restart api

## ── Backend ──────────────────────────────────────────────────────────────────
backend-test: ## Run pytest
	cd $(BACKEND_DIR) && pytest tests/ -v --tb=short

backend-shell: ## Open shell in running API container
	$(COMPOSE) exec api bash

migrate: ## Run Alembic migrations
	$(COMPOSE) exec api alembic upgrade head

## ── Frontend ─────────────────────────────────────────────────────────────────
frontend-install: ## Install npm dependencies
	cd $(FRONTEND_DIR) && npm ci

frontend-dev: ## Run Next.js dev server (local, no Docker)
	cd $(FRONTEND_DIR) && npm run dev

frontend-test: ## Run Jest tests
	cd $(FRONTEND_DIR) && npm test

frontend-build: ## Build Next.js for production
	cd $(FRONTEND_DIR) && npm run build

## ── ML Pipeline ──────────────────────────────────────────────────────────────
ml-clean: ## Remove generated feature arrays and models
	rm -f $(ML_DIR)/data/features/*.npy $(ML_DIR)/data/clean.csv
	rm -f $(ML_DIR)/models/*.tflite $(ML_DIR)/models/*.keras $(ML_DIR)/models/*.json

ml-features: ## Run data cleaning + feature engineering
	cd $(ML_DIR) && python src/data_cleaning.py && python src/feature_engineering.py

ml-train: ## Train all four models
	cd $(ML_DIR) && \
	  python src/train_anomaly.py && \
	  python src/train_occupancy.py && \
	  python src/train_forecast.py && \
	  python src/train_appliance.py

ml-evaluate: ## Evaluate trained models
	cd $(ML_DIR) && python src/model_evaluate.py

ml-convert: ## Convert Keras → TFLite INT8
	cd $(ML_DIR) && python src/convert_tflite.py

ml-headers: ## Generate C headers for firmware
	cd $(ML_DIR) && python src/generate_header.py

ml-all: ml-features ml-train ml-evaluate ml-convert ml-headers ## Full ML pipeline

## ── ESP32 Firmware ───────────────────────────────────────────────────────────
fw-build: ## Build ESP32 firmware with ESP-IDF
	cd firmware && idf.py build

fw-flash: ## Flash firmware to connected ESP32
	cd firmware && idf.py flash

fw-monitor: ## Open serial monitor
	cd firmware && idf.py monitor

fw-flash-monitor: ## Flash + open monitor in one step
	cd firmware && idf.py flash monitor

## ── Code Quality ─────────────────────────────────────────────────────────────
lint: ## Run all linters
	cd $(FRONTEND_DIR) && npm run lint
	cd $(BACKEND_DIR)  && python -m flake8 app/ --max-line-length=100 || true

fmt: ## Format Python code with black
	cd $(BACKEND_DIR) && python -m black app/ || true
