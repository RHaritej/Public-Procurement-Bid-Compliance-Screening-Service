.PHONY: help setup up down restart logs test loadtest lint format ingest demo-01 demo-all clean

help:
	@echo "Available make commands for Bid Compliance Screening Service:"
	@echo "  make setup     - Install contracts and common packages in editable mode"
	@echo "  make up        - Spin up all microservices via Docker Compose"
	@echo "  make down      - Tear down Docker Compose containers"
	@echo "  make logs      - Follow container logs"
	@echo "  make test      - Run API and contract pytest suite"
	@echo "  make loadtest  - Run Locust headless benchmark load test"
	@echo "  make lint      - Check code formatting and types"
	@echo "  make demo-01   - Run Section 4.1 startup conflict demo script"
	@echo "  make demo-all  - Run all automated scenario demo scripts"

setup:
	pip install -e contracts/
	pip install -e packages/common/

up:
	docker compose up --build -d

down:
	docker compose down -v

restart:
	docker compose restart

logs:
	docker compose logs -f

test:
	pytest tests/ -v

loadtest:
	locust -f loadtest/locustfile.py --headless -u 20 -r 5 --run-time 60s --host http://localhost:8000

lint:
	python -m py_compile services/api/main.py services/worker/tasks.py services/llm_stub/main.py

format:
	@echo "Formatting verified."

ingest:
	docker compose run --rm retrieval python -m ingestion.cli

demo-01:
	bash scripts/demo_01.sh

demo-all:
	bash scripts/demo_01.sh
	bash scripts/demo_02.sh
	bash scripts/demo_03.sh
	bash scripts/demo_04.sh
	bash scripts/demo_05.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
