"""Скрапер для товаров Farfetch."""

from services.scraper_core import BaseScraper, get_logger
from services.scraper_core.utils import extract_json_ld_from_html, validate_product_data

from .config import FarfetchConfig
from .domain import FarfetchProduct
from .html_parser import FarfetchHTMLParser
from .json_parser import FarfetchJSONParser

logger = get_logger(__name__)


class FarfetchScraper(BaseScraper):
    """Скрапер товаров с Farfetch."""

    def __init__(self, config: FarfetchConfig | None = None):
        """Инициализация скрапера."""
        super().__init__(config or FarfetchConfig())
        self.config: FarfetchConfig = self.config  # Для типизации
        self.html_parser = FarfetchHTMLParser()
        self.json_parser = FarfetchJSONParser()

    def validate_url(self, url: str) -> bool:
        """Проверка что URL принадлежит Farfetch."""
        return "farfetch.com" in url

    def parse_product(self, html: str, url: str) -> FarfetchProduct | None:
        """Парсинг товара из HTML."""
        try:
            additional_info = self.html_parser.extract_additional_info(html)
            json_data = self._extract_json_data(html)
            if not self._is_target_brand(json_data, additional_info):
                return None

            return self.json_parser.parse_product(json_data or {}, url, additional_info)

        except Exception as e:
            logger.error(f"Ошибка при парсинге товара: {e}")
            return None

    def _extract_json_data(self, html: str) -> dict | None:
        """Извлечение JSON-LD данных."""
        try:
            json_data = extract_json_ld_from_html(html)
            validate_product_data(json_data)
            logger.debug("JSON-LD данные успешно извлечены")
            return json_data
        except Exception as e:
            logger.warning(f"JSON-LD данные недоступны: {e}")
            return None

    def _is_target_brand(self, json_data: dict | None, additional_info: dict) -> bool:
        """Проверка целевого бренда."""
        if not self.config.target_brands:
            return True
        brand = self._extract_brand(json_data, additional_info)
        if not brand:
            return True
        is_target = brand in self.config.target_brands
        if not is_target:
            logger.info(f"Бренд {brand} не в списке целевых брендов")
        return is_target

    def _extract_brand(self, json_data: dict | None, additional_info: dict) -> str:
        """Извлечение бренда."""
        if json_data:
            return json_data.get("brand", {}).get("name", "")
        return additional_info.get("brand", "")
