"""Общий функционал для всех скраперов."""

from .async_http_client import AsyncHTTPClient
from .base_scraper import BaseScraper
from .config import BaseScraperConfig
from .exceptions import (
    ConfigurationError,
    HTTPError,
    JSONLDNotFoundError,
    ParsingError,
    ProductValidationError,
    ScraperError,
    StorageError,
    TimeoutError,
    URLValidationError,
    ValidationError,
)
from .logger import get_logger
from .models import BaseImage, BaseOffer, BaseProduct, BaseVariant
from .storage import load_products, save_products
from .utils import (
    clean_text,
    extract_json_ld_from_html,
    is_valid_url,
    validate_price,
    validate_product_data,
    validate_url,
)

__all__ = [
    # Основные классы
    "BaseScraper",
    "AsyncHTTPClient",
    # Исключения
    "ScraperError",
    "ValidationError",
    "URLValidationError",
    "ProductValidationError",
    "HTTPError",
    "TimeoutError",
    "ParsingError",
    "JSONLDNotFoundError",
    "StorageError",
    "ConfigurationError",
    # Конфигурация
    "BaseScraperConfig",
    # Модели
    "BaseProduct",
    "BaseImage",
    "BaseOffer",
    "BaseVariant",
    # Утилиты
    "get_logger",
    "save_products",
    "load_products",
    "is_valid_url",
    "validate_url",
    "clean_text",
    "validate_price",
    "validate_product_data",
    "extract_json_ld_from_html",
]
