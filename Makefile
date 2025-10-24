.PHONY: up down migrate test lint build clean logs shell-api shell-saver

# Docker Compose
up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# Database
migrate:
	docker-compose exec api uv run alembic upgrade head

migrate-create:
	docker-compose exec api uv run alembic revision --autogenerate -m "$(msg)"

# Development
test:
	docker-compose exec api uv run pytest tests/ -v

lint:
	docker-compose exec api uv run ruff check .
	docker-compose exec api uv run ruff format --check .

format:
	docker-compose exec api uv run ruff format .
	docker-compose exec api uv run ruff check --fix .

# Build
build:
	docker-compose build

# Shell access
shell-api:
	docker-compose exec api bash

shell-saver:
	docker-compose exec saver bash

# Cleanup
clean:
	docker-compose down -v
	docker system prune -f

# Health checks
health:
	@echo "Checking services..."
	@curl -s http://localhost:8000/health || echo "API not ready"
	@curl -s http://localhost:15672 || echo "RabbitMQ Management not ready"
	@curl -s http://localhost:9001 || echo "MinIO Console not ready"
