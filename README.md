# Aggregator Platform (modular monolith)

Стартовая платформа агрегатора: FastAPI API, Saver/Consumers (FastStream+RabbitMQ), PostgreSQL, Redis, MinIO.  
Код скраперов будет добавлен позже в `apps/scrapers/*`.

## Быстрый старт
```bash
cp env.example .env
make up
make migrate
curl -s http://localhost:8000/health
```

## Установка зависимостей

Проект использует `uv` для управления зависимостями:

```bash
# Установка uv (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установка зависимостей
uv sync --dev

# Запуск приложения
uv run python -m apps.api.main
```

## Архитектура

- **API**: FastAPI приложение с каталогом товаров
- **Saver**: FastStream consumers для обработки данных из RabbitMQ
- **Shared**: Общие схемы, события и утилиты
- **Infra**: Docker Compose, Grafana дашборды
- **CI**: GitHub Actions для lint, tests, docker-build

## Сервисы

- PostgreSQL (база данных)
- RabbitMQ (очереди сообщений)
- Redis (кэш)
- MinIO (S3-совместимое хранилище)
- API (FastAPI)
- Saver (FastStream consumers)

## Команды

```bash
make up          # Запуск всех сервисов
make down         # Остановка сервисов
make migrate      # Применение миграций
make test         # Запуск тестов
make lint         # Линтинг кода
make format       # Форматирование кода
make build        # Сборка Docker образов

# Локальная разработка с uv
uv run python -m apps.api.main     # Запуск API
uv run python -m apps.saver.main    # Запуск Saver
uv run pytest tests/ -v            # Запуск тестов
uv run ruff check .                # Линтинг
uv run ruff format .               # Форматирование
```