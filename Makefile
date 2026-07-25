# Theme Stock Research Agent - common development commands
#
# Prerequisites: GNU Make, Python, and Node.js/npm.
# The application source and dependency manifests are added as each feature is built.

PYTHON ?= python
NPM ?= npm
BACKEND_DIR := backend
FRONTEND_DIR := frontend

.DEFAULT_GOAL := help
.PHONY: help install backend-install frontend-install backend-dev frontend-dev dev test backend-test frontend-test lint format clean

help: ## Show available commands
	@echo "Usage: make <target>"
	@echo.
	@echo "Targets:"
	@findstr /R /C:"^[a-zA-Z0-9_-]*:.*##" $(MAKEFILE_LIST)

install: backend-install frontend-install ## Install backend and frontend dependencies

backend-install: ## Install Python dependencies from backend/requirements.txt
	@if exist "$(BACKEND_DIR)\\requirements.txt" (cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt) else (echo backend/requirements.txt is not available yet. & exit /b 1)

frontend-install: ## Install Node.js dependencies from frontend/package.json
	@if exist "$(FRONTEND_DIR)\\package-lock.json" (cd $(FRONTEND_DIR) && $(NPM) ci) else if exist "$(FRONTEND_DIR)\\package.json" (cd $(FRONTEND_DIR) && $(NPM) install) else (echo frontend/package.json is not available yet. & exit /b 1)

backend-dev: ## Run the FastAPI development server (http://127.0.0.1:8000)
	@if exist "$(BACKEND_DIR)\\app\\main.py" ($(PYTHON) -m uvicorn app.main:app --reload --app-dir $(BACKEND_DIR)) else (echo backend/app/main.py is not available yet. & exit /b 1)

frontend-dev: ## Run the Vite development server
	@if exist "$(FRONTEND_DIR)\\package.json" (cd $(FRONTEND_DIR) && $(NPM) run dev) else (echo frontend/package.json is not available yet. & exit /b 1)

dev: ## Show commands for running backend and frontend in separate terminals
	@echo Open two terminals and run:
	@echo   make backend-dev
	@echo   make frontend-dev

test: backend-test frontend-test ## Run all available tests

backend-test: ## Run backend tests with pytest
	@if exist "$(BACKEND_DIR)\\tests" (cd $(BACKEND_DIR) && $(PYTHON) -m pytest) else (echo backend/tests is not available yet. & exit /b 1)

frontend-test: ## Run frontend tests when a test script is configured
	@if exist "$(FRONTEND_DIR)\\package.json" (cd $(FRONTEND_DIR) && $(NPM) run test) else (echo frontend/package.json is not available yet. & exit /b 1)

lint: ## Run configured frontend lint checks
	@if exist "$(FRONTEND_DIR)\\package.json" (cd $(FRONTEND_DIR) && $(NPM) run lint) else (echo frontend/package.json is not available yet. & exit /b 1)

format: ## Run configured frontend formatting checks
	@if exist "$(FRONTEND_DIR)\\package.json" (cd $(FRONTEND_DIR) && $(NPM) run format) else (echo frontend/package.json is not available yet. & exit /b 1)

clean: ## Remove generated Python test and cache files
	@if exist "$(BACKEND_DIR)\\.pytest_cache" rmdir /S /Q "$(BACKEND_DIR)\\.pytest_cache"
	@if exist "$(BACKEND_DIR)\\.coverage" del /Q "$(BACKEND_DIR)\\.coverage"
	@for /d /r $(BACKEND_DIR) %i in (__pycache__) do @if exist "%i" rmdir /S /Q "%i"
