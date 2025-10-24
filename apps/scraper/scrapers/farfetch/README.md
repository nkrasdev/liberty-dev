# Farfetch Scraper

Скрапер для извлечения данных о товарах с сайта Farfetch.

## Структура

```
farfetch/
├── __init__.py
├── config.py          # Конфигурация скрапера
├── domain.py          # Модели данных
├── html_parser.py     # Парсер HTML
├── json_parser.py     # Парсер JSON-LD
├── scraper.py         # Основной скрапер
└── example.py         # Пример использования
```

## Использование

```python
from apps.scraper.scrapers.farfetch import FarfetchScraper, FarfetchConfig

# Создание конфигурации
config = FarfetchConfig(
    target_brands=["Nike", "Adidas", "Supreme"],
    use_mobile_ua=True,
    timeout=60
)

# Создание скрапера
scraper = FarfetchScraper(config)

# Скрапинг товаров
urls = ["https://www.farfetch.com/shopping/men/nike-item-123.aspx"]
products = await scraper.scrape_products(urls)
```

## Особенности

- Поддержка JSON-LD и HTML парсинга
- Фильтрация по целевым брендам
- Реалистичная имитация человеческого поведения
- Обработка различных вариантов товаров
- Извлечение изображений и размеров

## Конфигурация

- `target_brands` - список целевых брендов
- `use_mobile_ua` - использование мобильного User-Agent
- `timeout` - таймаут запросов
- `max_retries` - количество повторных попыток