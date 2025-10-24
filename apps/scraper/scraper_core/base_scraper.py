"""Базовый скрапер для всех сайтов."""

from abc import ABC, abstractmethod
from typing import List

from .async_http_client import AsyncHTTPClient
from .config import BaseScraperConfig
from .exceptions import ParsingError, URLValidationError
from .logger import get_logger
from .models import BaseProduct

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Базовый класс для всех скраперов."""

    def __init__(self, config: BaseScraperConfig):
        """Инициализация скрапера."""
        self.config = config
        self.http_client: AsyncHTTPClient | None = None
        logger.info(f"Скрапер {self.__class__.__name__} инициализирован")

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """Проверка что URL принадлежит этому сайту."""
        pass

    @abstractmethod
    def parse_product(self, html: str, url: str) -> BaseProduct | None:
        """Парсинг товара из HTML."""
        pass

    async def scrape_product(self, url: str) -> BaseProduct | None:
        """Скрапинг одного товара."""
        if not self.validate_url(url):
            raise URLValidationError(f"URL не подходит для {self.__class__.__name__}: {url}", url)

        logger.info(f"Скрапинг товара: {url}")

        if not self.http_client:
            raise RuntimeError(
                "HTTP клиент не инициализирован. Используйте scrape_products() или инициализируйте клиент вручную."
            )

        html = await self.http_client.get(url)
        if not html:
            return None

        try:
            product = self.parse_product(html, url)
            if product:
                logger.info(f"Успешно извлечен товар: {product.name}")
            else:
                logger.warning(f"Не удалось извлечь товар: {url}")
            return product
        except Exception as e:
            logger.error(f"Ошибка парсинга товара {url}: {e}")
            raise ParsingError(f"Ошибка парсинга товара: {e}", url)

    async def scrape_products(self, urls: List[str]) -> List[BaseProduct]:
        """Скрапинг нескольких товаров."""
        if not urls:
            logger.warning("Список URL пуст")
            return []

        products = []
        logger.info(f"Начинаем скрапинг {len(urls)} товаров")

        async with AsyncHTTPClient(self.config) as http_client:
            self.http_client = http_client

            for i, url in enumerate(urls, 1):
                logger.info(f"Скрапинг товара {i}/{len(urls)}: {url}")

                try:
                    product = await self.scrape_product(url)
                    if product:
                        products.append(product)
                        logger.info(f"Товар {i} успешно извлечен: {product.name}")
                    else:
                        logger.warning(f"Не удалось извлечь товар {i}: {url}")
                except Exception as e:
                    logger.error(f"Ошибка при скрапинге товара {i} ({url}): {e}")

                if i < len(urls):
                    import asyncio

                    await asyncio.sleep(2)

        logger.info(f"Скрапинг завершен. Извлечено товаров: {len(products)}/{len(urls)}")
        return products

    async def close(self):
        """Закрытие ресурсов."""
        if self.http_client:
            await self.http_client.close()
            logger.debug("HTTP клиент закрыт")
