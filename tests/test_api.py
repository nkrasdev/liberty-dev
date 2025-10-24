import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.catalog.models import Product


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api"


class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestProductEndpoints:
    """Test product API endpoints."""
    
    async def test_create_product(self, client: AsyncClient, sample_product_data):
        """Test creating a product."""
        response = await client.post("/api/v1/catalog/products", json=sample_product_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == sample_product_data["name"]
        assert data["brand"] == sample_product_data["brand"]
        assert data["price"] == sample_product_data["price"]
        assert data["source"] == sample_product_data["source"]
        assert data["external_id"] == sample_product_data["external_id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_get_products(self, client: AsyncClient, db_session: AsyncSession, sample_product_data):
        """Test getting products."""
        # Create a product first
        product = Product(**sample_product_data)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Get products
        response = await client.get("/api/v1/catalog/products")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_product_data["name"]
    
    async def test_get_product_by_id(self, client: AsyncClient, db_session: AsyncSession, sample_product_data):
        """Test getting a product by ID."""
        # Create a product first
        product = Product(**sample_product_data)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Get product by ID
        response = await client.get(f"/api/v1/catalog/products/{product.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(product.id)
        assert data["name"] == sample_product_data["name"]
    
    async def test_get_product_not_found(self, client: AsyncClient):
        """Test getting a non-existent product."""
        response = await client.get("/api/v1/catalog/products/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    async def test_update_product(self, client: AsyncClient, db_session: AsyncSession, sample_product_data):
        """Test updating a product."""
        # Create a product first
        product = Product(**sample_product_data)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Update product
        update_data = {"name": "Updated Product Name", "price": 200.00}
        response = await client.put(f"/api/v1/catalog/products/{product.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["price"] == 200.00
    
    async def test_delete_product(self, client: AsyncClient, db_session: AsyncSession, sample_product_data):
        """Test deleting a product."""
        # Create a product first
        product = Product(**sample_product_data)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Delete product
        response = await client.delete(f"/api/v1/catalog/products/{product.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Product deleted successfully"
    
    async def test_get_products_with_filters(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting products with filters."""
        # Create test products
        products = [
            Product(
                name="Product 1",
                brand="Brand A",
                price=100.00,
                currency="USD",
                source_url="https://example.com/1",
                source="test1",
                external_id="test-1"
            ),
            Product(
                name="Product 2", 
                brand="Brand B",
                price=200.00,
                currency="USD",
                source_url="https://example.com/2",
                source="test2",
                external_id="test-2"
            ),
        ]
        
        for product in products:
            db_session.add(product)
        await db_session.commit()
        
        # Test filtering by source
        response = await client.get("/api/v1/catalog/products?source=test1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source"] == "test1"
        
        # Test filtering by brand
        response = await client.get("/api/v1/catalog/products?brand=Brand A")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["brand"] == "Brand A"
        
        # Test search
        response = await client.get("/api/v1/catalog/products?search=Product 1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Product 1" in data[0]["name"]
    
    async def test_get_source_stats(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting source statistics."""
        # Create test products
        products = [
            Product(
                name="Product 1",
                brand="Brand A",
                price=100.00,
                currency="USD",
                source_url="https://example.com/1",
                source="test1",
                external_id="test-1"
            ),
            Product(
                name="Product 2",
                brand="Brand A", 
                price=200.00,
                currency="USD",
                source_url="https://example.com/2",
                source="test1",
                external_id="test-2"
            ),
        ]
        
        for product in products:
            db_session.add(product)
        await db_session.commit()
        
        # Get stats
        response = await client.get("/api/v1/catalog/products/stats/sources")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["source"] == "test1"
        assert data[0]["count"] == 2
        assert data[0]["avg_price"] == 150.0
