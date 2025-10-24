from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from apps.api.common.db import get_db, Base
from apps.api.common.decorators import handle_errors
from apps.api.catalog.models import Product as ProductModel
from shared.schemas.product import Product, ProductCreate, ProductUpdate
from shared.utils.logging import get_logger
from shared.utils.metrics import PRODUCT_OPERATIONS

logger = get_logger(__name__)

router = APIRouter(prefix="/catalog")


@router.get("/products", response_model=List[Product])
@handle_errors("retrieve products")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get products with filtering and pagination."""
    query = select(ProductModel)
    
    # Apply filters
    filters = []
    if source:
        filters.append(ProductModel.source == source)
    if brand:
        filters.append(ProductModel.brand == brand)
    if search:
        search_filter = or_(
            ProductModel.name.ilike(f"%{search}%"),
            ProductModel.description.ilike(f"%{search}%"),
            ProductModel.brand.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(ProductModel.created_at.desc())
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    PRODUCT_OPERATIONS.labels(operation="list", source="api").inc()
    
    return [Product.model_validate(product) for product in products]


@router.get("/products/{product_id}", response_model=Product)
@handle_errors("retrieve product")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific product by ID."""
    query = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    PRODUCT_OPERATIONS.labels(operation="get", source="api").inc()
    
    return Product.model_validate(product)


@router.post("/products", response_model=Product)
@handle_errors("create product")
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new product."""
    # Check if product already exists
    existing_query = select(ProductModel).where(
        and_(
            ProductModel.source == product_data.source,
            ProductModel.external_id == product_data.external_id
        )
    )
    result = await db.execute(existing_query)
    existing_product = result.scalar_one_or_none()
    
    if existing_product:
        raise HTTPException(
            status_code=409, 
            detail="Product with this source and external_id already exists"
        )
    
    # Create new product
    product = ProductModel(**product_data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    PRODUCT_OPERATIONS.labels(operation="create", source="api").inc()
    
    logger.info("Product created", product_id=str(product.id), source=product.source)
    
    return Product.model_validate(product)


@router.put("/products/{product_id}", response_model=Product)
@handle_errors("update product")
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    query = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    PRODUCT_OPERATIONS.labels(operation="update", source="api").inc()
    
    logger.info("Product updated", product_id=str(product.id))
    
    return Product.model_validate(product)


@router.delete("/products/{product_id}")
@handle_errors("delete product")
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a product."""
    query = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()
    
    PRODUCT_OPERATIONS.labels(operation="delete", source="api").inc()
    
    logger.info("Product deleted", product_id=str(product_id))
    
    return {"message": "Product deleted successfully"}


@router.get("/products/stats/sources")
@handle_errors("retrieve statistics")
async def get_source_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics by source."""
    from sqlalchemy import func
    
    query = select(
        ProductModel.source,
        func.count(ProductModel.id).label("count"),
        func.avg(ProductModel.price).label("avg_price")
    ).group_by(ProductModel.source)
    
    result = await db.execute(query)
    stats = result.all()
    
    return [
        {
            "source": stat.source,
            "count": stat.count,
            "avg_price": float(stat.avg_price) if stat.avg_price else 0
        }
        for stat in stats
    ]
