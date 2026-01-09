.PHONY: help install dev test lint format clean init-db init-db-sample run docker-up docker-down

help:
	@echo "Issue Tracker API - Make Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies"
	@echo "  make init-db          Initialize database tables"
	@echo "  make init-db-sample   Initialize database with sample data"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run development server (with reload)"
	@echo "  make run              Run production server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             Run test suite"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with autopep8"
	@echo "  make clean            Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start Docker containers"
	@echo "  make docker-down      Stop Docker containers"
	@echo "  make docker-logs      View Docker logs"

install:
	pip install -r requirements.txt

dev:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

init-db:
	python init_db.py

init-db-sample:
	python init_db.py --sample

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ --cov=app --cov-report=html

lint:
	pylint app/ --disable=all --enable=E,F --exit-zero
	mypy app/ --ignore-missing-imports || true

format:
	autopep8 -r app/ --in-place --aggressive --aggressive

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-rebuild:
	docker-compose up -d --build
