.PHONY: up down test migrate seed lint build logs clean

# ─── Docker Compose Commands ─────────────────────────────────────────

up:  ## Start all services
	docker compose up -d

up-dev:  ## Start all services with dev overrides (hot reload)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:  ## Stop all services
	docker compose down

build:  ## Build all Docker images
	docker compose build

logs:  ## Tail logs for all services
	docker compose logs -f

clean:  ## Stop services and remove volumes
	docker compose down -v

# ─── Backend Commands ────────────────────────────────────────────────

test:  ## Run backend tests
	docker compose run --rm backend pytest tests/ -v

test-health:  ## Run health check tests only
	docker compose run --rm backend pytest tests/test_health.py -v

test-db:  ## Run database connection tests only
	docker compose run --rm backend pytest tests/test_db_connection.py -v

migrate:  ## Run database migrations
	docker compose run --rm backend alembic upgrade head

migrate-down:  ## Rollback last migration
	docker compose run --rm backend alembic downgrade -1

seed:  ## Seed database with sample data
	docker compose run --rm backend python -m app.db.seed

lint:  ## Run linting (ruff)
	docker compose run --rm backend ruff check app/ tests/

lint-fix:  ## Fix linting issues
	docker compose run --rm backend ruff check --fix app/ tests/

typecheck:  ## Run type checking (mypy)
	docker compose run --rm backend mypy app/

format:  ## Format code (ruff)
	docker compose run --rm backend ruff format app/ tests/

# ─── Helpers ─────────────────────────────────────────────────────────

shell:  ## Open a shell in the backend container
	docker compose run --rm backend bash

db-shell:  ## Open psql shell
	docker compose exec db psql -U wearable -d wearable

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
