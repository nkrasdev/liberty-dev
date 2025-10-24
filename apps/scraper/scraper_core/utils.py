"""Общие утилиты для всех скраперов."""

import json
import re
from typing import Any, Dict
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .exceptions import JSONLDNotFoundError, ProductValidationError, URLValidationError
from .logger import get_logger

logger = get_logger(__name__)


def is_valid_url(url: str) -> bool:
    """Проверка валидности URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_url(url: str) -> None:
    """Валидация URL."""
    if not is_valid_url(url):
        raise URLValidationError(f"Невалидный URL: {url}", url)


def clean_text(text: str) -> str:
    """Очистка текста."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"<[^>]+>", "", text)

    return text


def validate_price(price: Any) -> bool:
    """Валидация цены."""
    if not isinstance(price, (int, float)):
        return False
    return 0 <= price <= 10000


def validate_product_data(data: Dict[str, Any]) -> None:
    """Валидация данных товара."""
    required_fields = ["name", "brand", "description"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        raise ProductValidationError(f"Отсутствуют обязательные поля: {missing_fields}")


def extract_json_ld_from_html(html: str) -> Dict[str, Any]:
    """Извлечение JSON-LD из HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        script_tags = soup.find_all("script", type="application/ld+json")

        for script in script_tags:
            if script.string:
                try:
                    json_data = json.loads(script.string)
                    if json_data.get("@type") == "ProductGroup":
                        logger.debug("JSON-LD данные найдены")
                        return json_data
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Ошибка парсинга JSON-LD: {e}")
                    continue

        raise JSONLDNotFoundError("JSON-LD данные не найдены в HTML")

    except JSONLDNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при извлечении JSON-LD: {e}")
        raise JSONLDNotFoundError(f"Ошибка при извлечении JSON-LD: {e}")
