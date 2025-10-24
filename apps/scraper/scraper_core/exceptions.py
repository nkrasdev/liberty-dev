"""Специфичные исключения для скраперов."""

from typing import Optional


class ScraperError(Exception):
    """Базовое исключение для всех ошибок скраперов."""

    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.url = url


class ValidationError(ScraperError):
    """Ошибка валидации данных."""

    pass


class URLValidationError(ValidationError):
    """Ошибка валидации URL."""

    pass


class ProductValidationError(ValidationError):
    """Ошибка валидации данных товара."""

    pass


class HTTPError(ScraperError):
    """Ошибка HTTP запроса."""

    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message, url)
        self.status_code = status_code


class TimeoutError(ScraperError):
    """Ошибка таймаута."""

    pass


class ParsingError(ScraperError):
    """Ошибка парсинга данных."""

    pass


class JSONLDNotFoundError(ParsingError):
    """JSON-LD данные не найдены."""

    pass


class StorageError(ScraperError):
    """Ошибка сохранения/загрузки данных."""

    pass


class ConfigurationError(ScraperError):
    """Ошибка конфигурации."""

    pass
