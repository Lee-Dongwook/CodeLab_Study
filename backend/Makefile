.DEFAULT_GOAL := help

VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP := $(PYTHON) -m pip
APP_MODULE := app.main:app

.PHONY: help install run test check clean

help: ## 사용할 수 있는 명령을 표시합니다.
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## 백엔드 실행에 필요한 패키지를 설치합니다.
	test -x $(PYTHON) || python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run: ## 개발 서버를 실행합니다. 주소: http://127.0.0.1:8000
	PYTHONPATH=. $(PYTHON) -m uvicorn $(APP_MODULE) --reload

test: ## 백엔드 단위·통합 테스트를 실행합니다.
	PYTHONPATH=. $(PYTHON) -m unittest discover -s tests -v

check: ## 테스트와 Python 문법 검사를 실행합니다.
	PYTHONPATH=. $(PYTHON) -m unittest discover -s tests -v
	PYTHONPATH=. $(PYTHON) -m compileall -q app

clean: ## Python 캐시 파일을 삭제합니다.
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
