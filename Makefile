# Finacle App Makefile

.PHONY: help install install-dev setup test lint format clean docker-build docker-up docker-down migrate shell

# Variables
PYTHON := python
PIP := pip
MANAGE := $(PYTHON) manage.py
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.prod.yml

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

setup: install-dev ## Setup development environment
	@echo "Creating necessary directories..."
	@mkdir -p logs media staticfiles
	@echo "Running migrations..."
	$(MANAGE) migrate
	@echo "Creating superuser (skip if exists)..."
	@echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | $(MANAGE) shell
	@echo "Setup complete!"

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term

lint: ## Run linting
	flake8 .
	mypy .

format: ## Format code
	black .
	isort .

format-check: ## Check code formatting
	black --check .
	isort --check-only .

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage

migrate: ## Run database migrations
	$(MANAGE) makemigrations
	$(MANAGE) migrate

shell: ## Open Django shell
	$(MANAGE) shell

runserver: ## Run development server
	$(MANAGE) runserver

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

# Docker commands
docker-build: ## Build Docker image
	docker build -t finacle-app .

docker-up: ## Start development environment with Docker
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop development environment
	$(DOCKER_COMPOSE) down

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-shell: ## Open shell in Docker container
	$(DOCKER_COMPOSE) exec web $(MANAGE) shell

docker-test: ## Run tests in Docker
	$(DOCKER_COMPOSE) exec web pytest

# Production Docker commands
docker-prod-build: ## Build production Docker image
	$(DOCKER_COMPOSE_PROD) build

docker-prod-up: ## Start production environment
	$(DOCKER_COMPOSE_PROD) up -d

docker-prod-down: ## Stop production environment
	$(DOCKER_COMPOSE_PROD) down

# Database commands
db-reset: ## Reset database (WARNING: destroys all data)
	rm -f db.sqlite3
	$(MANAGE) migrate

db-backup: ## Backup database
	$(MANAGE) dumpdata --natural-foreign --natural-primary > backup.json

db-restore: ## Restore database from backup
	$(MANAGE) loaddata backup.json

# Utility commands
check: ## Run Django system checks
	$(MANAGE) check

requirements: ## Update requirements.txt from current environment
	$(PIP) freeze > requirements.txt

security: ## Run security checks
	safety check
	bandit -r . -x tests/

ci: format-check lint test ## Run all CI checks locally



