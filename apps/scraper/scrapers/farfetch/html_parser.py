from typing import Dict, List

from bs4 import BeautifulSoup

from services.scraper_core.logger import get_logger

logger = get_logger(__name__)


class FarfetchHTMLParser:
    """Парсер дополнительной информации из HTML."""

    def extract_additional_info(self, html: str) -> Dict[str, str | list[str]]:
        """Извлечение дополнительной информации из HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            return {
                "title": self._extract_title(soup),
                "brand": self._extract_brand(soup),
                "images": self._extract_images(soup),
                "sizes": self._extract_sizes(soup),
                "description": self._extract_description(soup),
            }
        except Exception as e:
            logger.warning(f"Ошибка при парсинге HTML: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечение названия товара."""
        selectors = [
            'h1[data-testid="product-name"]',
            'h1[data-testid="product-title"]',
            "h1.product-name",
            'h1[class*="product"]',
            "h1",
            ".product-title",
            '[data-testid*="title"]',
        ]
        return self._extract_text_by_selectors(soup, selectors)

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Извлечение бренда товара."""
        selectors = [
            '[data-testid="brand"]',
            ".brand",
            '[class*="brand"]',
            '[data-testid*="brand"]',
            ".product-brand",
            'h2[class*="brand"]',
        ]
        return self._extract_text_by_selectors(soup, selectors)

    def _extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Извлечение текста по селекторам."""
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        return ""

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Извлечение изображений товара."""
        images = []
        selectors = [
            ".product-image img",
            '[data-testid*="image"] img',
            ".gallery img",
            ".product-gallery img",
            '[class*="gallery"] img',
            'img[src*="farfetch"]',
        ]
        for selector in selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get("src") or img.get("data-src") or img.get("data-lazy")
                if src and src not in images:
                    images.append(src)
        return images[:10]

    def _extract_sizes(self, soup: BeautifulSoup) -> List[str]:
        """Извлечение размеров."""
        sizes = []
        selectors = [
            '[data-testid*="size"]',
            ".size-selector button",
            ".size-option",
            '[class*="size"] button',
            ".product-sizes button",
        ]
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                size_text = element.get_text(strip=True)
                if size_text and size_text not in sizes:
                    sizes.append(size_text)
        return sizes

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлечение описания товара."""
        selectors = [
            '[data-testid="description"]',
            ".product-description",
            '[class*="description"]',
            '[data-testid*="description"]',
            ".product-details",
            ".product-info",
        ]
        return self._extract_text_by_selectors(soup, selectors)
