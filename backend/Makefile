# Makefile for Supply Chain Tracking System Backend

.PHONY: help install dev test lint format check migrations migrate shell clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv install

dev: ## Start development server
	uv run python src/manage.py runserver

test: ## Run tests
	uv run python src/manage.py test

lint: ## Run linting checks
	uv run ruff check src/

format: ## Format code
	uv run ruff format src/

check: lint test ## Run linting and tests

fix: ## Auto-fix linting issues and format code
	uv run ruff check src/ --fix
	uv run ruff format src/

migrations: ## Create new migrations
	uv run python src/manage.py makemigrations

migrate: ## Apply migrations
	uv run python src/manage.py migrate

shell: ## Open Django shell
	uv run python src/manage.py shell

collectstatic: ## Collect static files
	uv run python src/manage.py collectstatic --noinput

seed-products: ## Seed database with sample products
	uv run python src/manage.py seed_products

seed-products-clear: ## Clear and seed products
	uv run python src/manage.py seed_products --clear

seed-batches: ## Seed database with sample batches
	uv run python src/manage.py seed_batches

seed-batches-clear: ## Clear and seed batches
	uv run python src/manage.py seed_batches --clear

seed-packs: ## Seed database with sample packs
	uv run python src/manage.py seed_packs

seed-packs-clear: ## Clear and seed packs
	uv run python src/manage.py seed_packs --clear

seed-shipments: ## Seed database with sample shipments
	uv run python src/manage.py seed_shipments

seed-shipments-clear: ## Clear and seed shipments
	uv run python src/manage.py seed_shipments --clear

seed-all: ## Seed all data (products, batches, packs, and shipments)
	uv run python src/manage.py seed_products
	uv run python src/manage.py seed_batches
	uv run python src/manage.py seed_packs
	uv run python src/manage.py seed_shipments

reset: ## Reset app data (delete all data)
	uv run python src/reset_app.py

test-email: ## Test email configuration (requires --to argument)
	@if [ -z "$(to)" ]; then echo "Usage: make test-email to=your@email.com"; exit 1; fi
	uv run python src/manage.py test_email --to $(to)

clean: ## Clean up cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Examples:
# make install
# make dev
# make lint
# make format
# make test-email to=admin@example.com
