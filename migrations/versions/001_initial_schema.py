"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('size', sa.String(length=20), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('condition', sa.String(length=20), nullable=True),
        sa.Column('availability', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_products_source_external_id', 'products', ['source', 'external_id'])
    op.create_index('idx_products_brand', 'products', ['brand'])
    op.create_index('idx_products_source', 'products', ['source'])
    op.create_index('idx_products_created_at', 'products', ['created_at'])
    op.create_index('idx_products_price', 'products', ['price'])
    
    # Create scraper_data table
    op.create_table('scraper_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scraper_data
    op.create_index('idx_scraper_data_source', 'scraper_data', ['source'])
    op.create_index('idx_scraper_data_status', 'scraper_data', ['status'])
    op.create_index('idx_scraper_data_created_at', 'scraper_data', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('scraper_data')
    op.drop_table('products')
