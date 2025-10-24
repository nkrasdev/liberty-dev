"""Простые утилиты для сохранения и загрузки данных."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, TypeVar

from .exceptions import StorageError
from .logger import get_logger
from .models import BaseProduct

T = TypeVar("T", bound=BaseProduct)

logger = get_logger(__name__)


def save_products(products: List[T], file_path: str) -> None:
    """Сохранение товаров в JSON файл."""
    file_path = Path(file_path)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "products": [product.model_dump() for product in products],
            "scraped_at": datetime.now().isoformat(),
            "total_products": len(products),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Сохранено {len(products)} товаров в {file_path}")
    except Exception as e:
        error_msg = f"Ошибка сохранения файла {file_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, str(file_path))


def load_products(file_path: str, product_class: type = BaseProduct) -> List[T]:
    """Загрузка товаров из JSON файла."""
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"Файл {file_path} не существует")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        products = [product_class(**item) for item in data.get("products", [])]
        logger.info(f"Загружено {len(products)} товаров из {file_path}")
        return products

    except json.JSONDecodeError as e:
        error_msg = f"Ошибка парсинга JSON файла {file_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, str(file_path))
    except KeyError as e:
        error_msg = f"Отсутствует ключ в файле {file_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, str(file_path))
    except Exception as e:
        error_msg = f"Ошибка загрузки файла {file_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, str(file_path))
