import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

import tempfile
from pathlib import Path
from apps.api.main import app
from apps.api.common.db import get_db, Base
from shared.utils.logging import setup_logging

# Setup logging for tests
setup_logging(log_level="INFO", log_format="json")

# Test database URL
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aggregator_test")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Nike Air Jordan 1",
        "brand": "Nike",
        "price": 150.00,
        "currency": "USD",
        "description": "Classic basketball shoe",
        "image_url": "https://example.com/image.jpg",
        "source_url": "https://example.com/product",
        "source": "test",
        "external_id": "test-123",
        "size": "10",
        "color": "Black/White",
        "condition": "new",
        "availability": True,
    }


@pytest.fixture
def sample_scraper_data():
    """Sample scraper data for testing."""
    return {
        "source": "test",
        "external_id": "test-123",
        "raw_data": {
            "name": "Test Product",
            "price": "$100",
            "brand": "Test Brand"
        },
        "status": "pending",
        "error_message": None,
    }


@pytest.fixture
def scraper_config():
    """Фикстура конфигурации скрапера."""
    return FarfetchConfig(
        base_url="https://test.farfetch.com", timeout=5, max_retries=2, retry_delay=0.1
    )


@pytest.fixture
def scraper(scraper_config):
    """Фикстура скрапера."""

    return FarfetchScraper(config=scraper_config)


@pytest.fixture
def sample_json_ld():
    """Фикстура с примером JSON-LD данных."""
    return {
        "@type": "ProductGroup",
        "name": "Nike Air Force 1 x Supreme",
        "brand": {"name": "Nike"},
        "color": "белый",
        "description": "Nike кроссовки Air Force 1 из коллаборации с Supreme",
        "productGroupID": "15252505",
        "image": [
            {
                "contentUrl": "https://example.com/image1.jpg",
                "description": "Nike Air Force 1 Supreme",
            }
        ],
        "hasVariant": [
            {
                "sku": "15252505-27",
                "name": "Nike Air Force 1 x Supreme | 6",
                "size": "6",
                "image": "https://example.com/image1.jpg",
                "offers": {
                    "url": "https://test.com/item",
                    "availability": "InStock",
                    "priceSpecification": [{"price": 190}],
                },
            }
        ],
        "url": "https://test.farfetch.com/item",
    }


@pytest.fixture
def sample_html():
    """Фикстура с примером HTML."""
    return """
    <html>
        <head>
            <title>Test Product</title>
        </head>
        <body>
            <script type="application/ld+json">
            {
                "@type": "ProductGroup",
                "name": "Test Product",
                "brand": {"name": "Nike"}
            }
            </script>
            <h2>Состав</h2>
            <div>Подошва: Резина 100%</div>
            <h2>Рекомендации по уходу</h2>
            <div>Только сухая чистка</div>
        </body>
    </html>
    """


@pytest.fixture
def sample_product():
    """Фикстура с примером товара."""
    return FarfetchProduct(
        name="Nike Air Force 1 x Supreme",
        brand="Nike",
        color="белый",
        description="Test description",
        product_group_id="15252505",
        images=[
            BaseImage(content_url="https://example.com/image1.jpg", description="Test image")
        ],
        variants=[
            ProductVariant(
                sku="15252505-27",
                name="Nike Air Force 1 x Supreme | 6",
                size="6",
                image="https://example.com/image1.jpg",
                offers=BaseOffer(
                    url="https://test.com/item",
                    availability="InStock",
                    price_specification=[{"price": 190}],
                ),
            )
        ],
        url="https://test.farfetch.com/item",
    )


@pytest.fixture
def sample_products(sample_product):
    """Фикстура с несколькими товарами."""
    product2 = sample_product.model_copy()
    product2.name = "Nike Dunk Low"
    product2.product_group_id = "15252506"

    return [sample_product, product2]


@pytest.fixture
def temp_file():
    """Фикстура временного файла."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_urls():
    """Фикстура с тестовыми URL."""
    return [
        "https://www.farfetch.com/shopping/men/nike-air-force-1-supreme-item-15252505.aspx",
        "https://www.farfetch.com/shopping/women/nike-dunk-low-item-15252506.aspx",
    ]


@pytest.fixture
def invalid_urls():
    """Фикстура с невалидными URL."""
    return ["not-a-url", "https://google.com", "https://farfetch.com/not-a-product"]


@pytest.fixture
def sample_scraped_data(sample_products):
    """Фикстура с данными скрапинга."""
    return {
        "products": [product.model_dump() for product in sample_products],
        "scraped_at": "2024-01-01T00:00:00",
        "total_products": len(sample_products),
    }
