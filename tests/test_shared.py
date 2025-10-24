import pytest
from decimal import Decimal

from shared.schemas.product import Product, ProductCreate, ProductUpdate
from shared.schemas.scraper_data import ScraperData, ScraperDataCreate
from shared.events.product_events import ProductCreated, ProductUpdated, ProductDeleted
from shared.events.scraper_events import ScraperDataReceived, ScraperDataProcessed
from shared.utils.retry import with_retry


class TestProductSchemas:
    """Test product schemas."""
    
    def test_product_create(self):
        """Test ProductCreate schema."""
        data = {
            "name": "Test Product",
            "brand": "Test Brand",
            "price": Decimal("100.00"),
            "currency": "USD",
            "description": "Test description",
            "image_url": "https://example.com/image.jpg",
            "source_url": "https://example.com/product",
            "source": "test",
            "external_id": "test-123",
            "size": "10",
            "color": "Black",
            "condition": "new",
            "availability": True,
        }
        
        product = ProductCreate(**data)
        assert product.name == "Test Product"
        assert product.brand == "Test Brand"
        assert product.price == Decimal("100.00")
        assert product.currency == "USD"
        assert product.source == "test"
        assert product.external_id == "test-123"
    
    def test_product_update(self):
        """Test ProductUpdate schema."""
        data = {
            "name": "Updated Product",
            "price": Decimal("150.00"),
            "availability": False,
        }
        
        product = ProductUpdate(**data)
        assert product.name == "Updated Product"
        assert product.price == Decimal("150.00")
        assert product.availability is False
        assert product.brand is None  # Not provided


class TestScraperDataSchemas:
    """Test scraper data schemas."""
    
    def test_scraper_data_create(self):
        """Test ScraperDataCreate schema."""
        data = {
            "source": "test",
            "external_id": "test-123",
            "raw_data": {"name": "Test Product", "price": "$100"},
            "status": "pending",
        }
        
        scraper_data = ScraperDataCreate(**data)
        assert scraper_data.source == "test"
        assert scraper_data.external_id == "test-123"
        assert scraper_data.raw_data == {"name": "Test Product", "price": "$100"}
        assert scraper_data.status == "pending"
        assert scraper_data.error_message is None


class TestProductEvents:
    """Test product events."""
    
    def test_product_created(self):
        """Test ProductCreated event."""
        event = ProductCreated(
            product_id="123e4567-e89b-12d3-a456-426614174000",
            name="Test Product",
            brand="Test Brand",
            source="test",
            external_id="test-123"
        )
        
        assert event.event_type == "product.created"
        assert event.name == "Test Product"
        assert event.brand == "Test Brand"
        assert event.source == "test"
        assert event.external_id == "test-123"
    
    def test_product_updated(self):
        """Test ProductUpdated event."""
        event = ProductUpdated(
            product_id="123e4567-e89b-12d3-a456-426614174000",
            changes={"name": "Updated Product", "price": 150.00}
        )
        
        assert event.event_type == "product.updated"
        assert event.changes == {"name": "Updated Product", "price": 150.00}
    
    def test_product_deleted(self):
        """Test ProductDeleted event."""
        event = ProductDeleted(
            product_id="123e4567-e89b-12d3-a456-426614174000",
            name="Test Product",
            brand="Test Brand",
            source="test"
        )
        
        assert event.event_type == "product.deleted"
        assert event.name == "Test Product"
        assert event.brand == "Test Brand"
        assert event.source == "test"


class TestScraperEvents:
    """Test scraper events."""
    
    def test_scraper_data_received(self):
        """Test ScraperDataReceived event."""
        event = ScraperDataReceived(
            scraper_data_id="123e4567-e89b-12d3-a456-426614174000",
            source="test",
            external_id="test-123",
            data_size=1024
        )
        
        assert event.event_type == "scraper.data.received"
        assert event.source == "test"
        assert event.external_id == "test-123"
        assert event.data_size == 1024
    
    def test_scraper_data_processed(self):
        """Test ScraperDataProcessed event."""
        event = ScraperDataProcessed(
            scraper_data_id="123e4567-e89b-12d3-a456-426614174000",
            source="test",
            external_id="test-123",
            status="completed",
            products_created=1,
            products_updated=0
        )
        
        assert event.event_type == "scraper.data.processed"
        assert event.source == "test"
        assert event.external_id == "test-123"
        assert event.status == "completed"
        assert event.products_created == 1
        assert event.products_updated == 0


class TestRetryDecorator:
    """Test retry decorator."""
    
    def test_sync_function_retry(self):
        """Test retry decorator with sync function."""
        call_count = 0
        
        @with_retry(max_attempts=3, wait_multiplier=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3
    
    def test_sync_function_no_retry_needed(self):
        """Test retry decorator with sync function that succeeds immediately."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        def succeeding_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeeding_function()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_function_retry(self):
        """Test retry decorator with async function."""
        call_count = 0
        
        @with_retry(max_attempts=3, wait_multiplier=0.01)
        async def failing_async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"
        
        result = await failing_async_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_function_no_retry_needed(self):
        """Test retry decorator with async function that succeeds immediately."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        async def succeeding_async_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await succeeding_async_function()
        assert result == "success"
        assert call_count == 1
