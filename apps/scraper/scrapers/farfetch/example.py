import asyncio

from services.scraper_core import get_logger, save_products
from services.scrapers.farfetch.config import FarfetchConfig
from services.scrapers.farfetch.scraper import FarfetchScraper

logger = get_logger(__name__)


async def main():
    """Простой пример скрапинга."""

    test_urls = [
        "https://www.farfetch.com/shopping/men/nike-air-force-1-supreme-item-15252505.aspx",
        "https://www.farfetch.com/shopping/women/nike-air-force-1-low-mini-box-logo-black-supreme-item-15252506.aspx",
        "https://www.farfetch.com/shopping/women/nike-dunk-low-retro-item-16403569.aspx",
    ]

    config = FarfetchConfig(
        target_brands=["Nike", "Adidas", "Supreme"],
        use_mobile_ua=True,
        visit_intermediate_pages=False,
        randomize_delays=True,
        timeout=60,
        max_retries=3,
        retry_delay=2.0,
        min_delay=1.0,
        max_delay=3.0,
        proxy_list=[
            "http://af1BPm:TwRpF9@168.80.203.44:8000",
            "socks5://af1BPm:TwRpF9@168.80.203.44:8000",
            "socks4://af1BPm:TwRpF9@168.80.203.44:8000",
        ],
    )

    scraper = FarfetchScraper(config)

    try:
        logger.info("🚀 Начинаем скрапинг товаров...")

        products = await scraper.scrape_products(test_urls)

        for i, product in enumerate(products, 1):
            logger.info(f"Товар {i}: {product.name}")
            logger.info(f"Бренд: {product.brand}")
            logger.info(f"Цвет: {product.color}")
            logger.info(f"Вариантов: {len(product.variants)}")

            min_price, max_price = product.price_range
            if min_price and max_price:
                logger.info(f"   Цены: ${min_price:.0f} - ${max_price:.0f}")

        save_products(products, "scraped_products.json")

        logger.info("🎉 Скрапинг завершен!")
        logger.info(f"📊 Всего товаров: {len(products)}")

    except KeyboardInterrupt:
        logger.info("⚠️ Скрапинг прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при скрапинге: {e}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
