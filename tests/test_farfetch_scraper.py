"""Тесты для скрапера Farfetch."""

import pytest
from unittest.mock import patch, AsyncMock

from pytest_cases import case, parametrize

from services.scraper_core import save_products, load_products
from services.scrapers.farfetch.domain import FarfetchProduct
from services.scrapers.farfetch.scraper import FarfetchScraper
from services.scraper_core.utils import extract_json_ld_from_html, validate_product_data


@case(tags=["basic"])
def case_scraper_init():
    """Кейс: Инициализация скрапера."""
    return {
        "description": "Тест инициализации скрапера",
        "expected_session": True,
        "expected_user_agent": True,
    }


@case(tags=["parsing"])
def case_extract_json_ld():
    """Кейс: Извлечение JSON-LD данных."""
    return {
        "description": "Тест извлечения JSON-LD данных",
        "html": """
        <html>
            <script type="application/ld+json">
            {
                "@type": "ProductGroup",
                "name": "Nike Air Force 1",
                "brand": {"name": "Nike"}
            }
            </script>
        </html>
        """,
        "expected_type": "ProductGroup",
        "expected_name": "Nike Air Force 1",
    }


@case(tags=["validation"])
def case_validate_product():
    """Кейс: Валидация данных товара."""
    return {
        "description": "Тест валидации данных товара",
        "json_data": {
            "@type": "ProductGroup",
            "name": "Nike Air Force 1",
            "brand": {"name": "Nike"},
            "description": "Test description",
        },
        "expected_valid": True,
    }


@case(tags=["scraping"])
def case_scrape_product():
    """Кейс: Скрапинг товара."""
    return {
        "description": "Тест скрапинга товара",
        "url": "https://www.farfetch.com/shopping/men/nike-item-123.aspx",
        "json_ld": {
            "@type": "ProductGroup",
            "name": "Nike Air Force 1 x Supreme",
            "brand": {"name": "Nike"},
            "color": "белый",
            "description": "Test description",
            "productGroupID": "15252505",
            "image": [{"contentUrl": "test.jpg", "description": "Test"}],
            "hasVariant": [
                {
                    "sku": "test-123",
                    "name": "Test | 6",
                    "size": "6",
                    "image": "test.jpg",
                    "offers": {
                        "url": "test.com",
                        "availability": "InStock",
                        "priceSpecification": [{"price": 190}],
                    },
                }
            ],
            "url": "https://www.farfetch.com/shopping/men/nike-item-123.aspx",
        },
        "expected_name": "Nike Air Force 1 x Supreme",
        "expected_brand": "Nike",
    }


@case(tags=["file_manager"])
def case_file_operations():
    """Кейс: Операции с файлом."""
    return {"description": "Тест операций с файлом", "expected_save": True, "expected_load": True}


class TestFarfetchScraper:
    """Тесты для класса FarfetchScraper."""

    @parametrize("case_data", [case_scraper_init()])
    def test_scraper_initialization(self, case_data, scraper_config):
        """Тест инициализации скрапера."""
        scraper = FarfetchScraper(config=scraper_config)

        assert scraper.config == scraper_config
        assert scraper.http_client is None
        assert scraper.html_parser is not None
        assert scraper.json_parser is not None

    @parametrize("case_data", [case_extract_json_ld()])
    def test_extract_json_ld(self, case_data, scraper):
        """Тест извлечения JSON-LD данных."""
        result = extract_json_ld_from_html(case_data["html"])

        assert result is not None
        assert result["@type"] == case_data["expected_type"]
        assert result["name"] == case_data["expected_name"]

    @parametrize("case_data", [case_validate_product()])
    def test_validate_product_data(self, case_data, scraper):
        """Тест валидации данных товара."""
        if case_data["expected_valid"]:
            validate_product_data(case_data["json_data"])
        else:
            with pytest.raises(Exception):
                validate_product_data(case_data["json_data"])

    @pytest.mark.asyncio
    @parametrize("case_data", [case_scrape_product()])
    async def test_scrape_product(self, case_data, scraper):
        """Тест скрапинга товара."""
        with patch.object(scraper, 'http_client', new_callable=AsyncMock) as mock_client:
            mock_client.get.return_value = "<html>Test content</html>"
            with patch(
                "services.scrapers.farfetch.scraper.extract_json_ld_from_html"
            ) as mock_extract:
                mock_extract.return_value = case_data["json_ld"]

                result = await scraper.scrape_product(case_data["url"])

                assert result is not None
                assert result.name == case_data["expected_name"]
                assert result.brand == case_data["expected_brand"]


class TestFileOperations:
    """Тесты для операций с файлами."""

    @parametrize("case_data", [case_file_operations()])
    def test_file_operations(self, case_data, temp_file, sample_product):
        """Тест операций с файлом."""
        save_products([sample_product], str(temp_file))

        assert temp_file.exists()

        loaded_products = load_products(str(temp_file), FarfetchProduct)
        assert len(loaded_products) == 1
        assert loaded_products[0].name == sample_product.name


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    @parametrize("case_data", [case_scrape_product()])
    async def test_full_scraping_flow(self, case_data, scraper):
        """Тест полного процесса скрапинга."""
        with patch.object(scraper, 'http_client', new_callable=AsyncMock) as mock_client:
            mock_client.get.return_value = "<html>Test content</html>"

            with patch(
                "services.scrapers.farfetch.scraper.extract_json_ld_from_html",
                return_value=case_data["json_ld"],
            ):
                result = await scraper.scrape_product(case_data["url"])

                assert result is not None
                assert result.name == case_data["expected_name"]
                assert result.brand == case_data["expected_brand"]
                assert len(result.variants) == 1
                assert len(result.images) == 1