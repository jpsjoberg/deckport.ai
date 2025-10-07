"""
Database migration: Add console location tracking, version management, and product categories

This migration adds:
1. Console location tracking with coordinates and address
2. Console version management and update tracking  
3. Product category system for shop items
4. Console activity and health monitoring
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid
from datetime import datetime, timezone

# Migration ID
revision = 'add_console_enhancements'
down_revision = None  # Set to your latest migration ID
branch_labels = None
depends_on = None

def upgrade():
    """Add new features to existing tables"""
    
    # 1. Add location tracking to consoles table
    print("Adding console location tracking...")
    op.add_column('consoles', sa.Column('location_name', sa.String(255), nullable=True))
    op.add_column('consoles', sa.Column('location_address', sa.Text, nullable=True))
    op.add_column('consoles', sa.Column('location_latitude', sa.Numeric(precision=10, scale=8), nullable=True))
    op.add_column('consoles', sa.Column('location_longitude', sa.Numeric(precision=11, scale=8), nullable=True))
    op.add_column('consoles', sa.Column('location_updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consoles', sa.Column('location_source', sa.String(50), nullable=True))  # 'manual', 'gps', 'ip'
    
    # 2. Add version management to consoles table
    print("Adding console version management...")
    op.add_column('consoles', sa.Column('software_version', sa.String(50), nullable=True))
    op.add_column('consoles', sa.Column('hardware_version', sa.String(50), nullable=True))
    op.add_column('consoles', sa.Column('firmware_version', sa.String(50), nullable=True))
    op.add_column('consoles', sa.Column('last_update_check', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consoles', sa.Column('update_available', sa.Boolean, default=False, nullable=False))
    op.add_column('consoles', sa.Column('auto_update_enabled', sa.Boolean, default=True, nullable=False))
    
    # 3. Add health and activity monitoring
    print("Adding console health monitoring...")
    op.add_column('consoles', sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consoles', sa.Column('health_status', sa.String(20), default='unknown', nullable=False))  # 'healthy', 'warning', 'critical', 'unknown'
    op.add_column('consoles', sa.Column('uptime_seconds', sa.BigInteger, default=0, nullable=False))
    op.add_column('consoles', sa.Column('cpu_usage_percent', sa.Float, nullable=True))
    op.add_column('consoles', sa.Column('memory_usage_percent', sa.Float, nullable=True))
    op.add_column('consoles', sa.Column('disk_usage_percent', sa.Float, nullable=True))
    op.add_column('consoles', sa.Column('temperature_celsius', sa.Float, nullable=True))
    op.add_column('consoles', sa.Column('network_latency_ms', sa.Float, nullable=True))
    
    # 4. Create product categories table
    print("Creating product categories table...")
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('parent_id', sa.Integer, sa.ForeignKey('product_categories.id', ondelete='CASCADE'), nullable=True),
        sa.Column('sort_order', sa.Integer, default=0, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('banner_url', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Index('ix_product_categories_slug', 'slug'),
        sa.Index('ix_product_categories_parent', 'parent_id'),
        sa.Index('ix_product_categories_active', 'is_active'),
    )
    
    # 5. Create console location history table for tracking location changes
    print("Creating console location history table...")
    op.create_table(
        'console_location_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('console_id', sa.Integer, sa.ForeignKey('consoles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('location_address', sa.Text, nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),  # 'manual', 'gps', 'ip'
        sa.Column('accuracy_meters', sa.Float, nullable=True),
        sa.Column('changed_by_admin_id', sa.Integer, sa.ForeignKey('admins.id'), nullable=True),
        sa.Column('change_reason', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Index('ix_console_location_history_console', 'console_id'),
        sa.Index('ix_console_location_history_created', 'created_at'),
    )
    
    # 6. Create console version history table
    print("Creating console version history table...")
    op.create_table(
        'console_version_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('console_id', sa.Integer, sa.ForeignKey('consoles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_type', sa.String(20), nullable=False),  # 'software', 'hardware', 'firmware'
        sa.Column('old_version', sa.String(50), nullable=True),
        sa.Column('new_version', sa.String(50), nullable=False),
        sa.Column('update_method', sa.String(20), nullable=False),  # 'automatic', 'manual', 'forced'
        sa.Column('update_status', sa.String(20), nullable=False),  # 'pending', 'in_progress', 'completed', 'failed'
        sa.Column('update_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('update_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('initiated_by_admin_id', sa.Integer, sa.ForeignKey('admins.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Index('ix_console_version_history_console', 'console_id'),
        sa.Index('ix_console_version_history_status', 'update_status'),
        sa.Index('ix_console_version_history_created', 'created_at'),
    )
    
    # 7. Update shop_products table to reference categories
    print("Adding category relationship to shop products...")
    # Check if category_id column exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('shop_products')]
    
    if 'category_id' not in columns:
        op.add_column('shop_products', sa.Column('category_id', sa.Integer, sa.ForeignKey('product_categories.id', ondelete='SET NULL'), nullable=True))
    
    # Add index for category lookups
    op.create_index('ix_shop_products_category', 'shop_products', ['category_id'])
    
    # 8. Insert default product categories
    print("Creating default product categories...")
    connection = op.get_bind()
    
    # Main categories
    categories = [
        {'name': 'Card Packs', 'slug': 'card-packs', 'description': 'Booster packs and card bundles', 'sort_order': 1},
        {'name': 'Individual Cards', 'slug': 'individual-cards', 'description': 'Single cards for purchase', 'sort_order': 2},
        {'name': 'Physical Cards', 'slug': 'physical-cards', 'description': 'NFC-enabled physical cards', 'sort_order': 3},
        {'name': 'Accessories', 'slug': 'accessories', 'description': 'Gaming accessories and merchandise', 'sort_order': 4},
        {'name': 'Digital Content', 'slug': 'digital-content', 'description': 'Digital assets and content', 'sort_order': 5},
    ]
    
    for cat in categories:
        connection.execute(
            text("""
                INSERT INTO product_categories (name, slug, description, sort_order, is_active, created_at, updated_at)
                VALUES (:name, :slug, :description, :sort_order, true, NOW(), NOW())
            """),
            cat
        )
    
    # 9. Add indexes for performance
    print("Adding performance indexes...")
    op.create_index('ix_consoles_location', 'consoles', ['location_latitude', 'location_longitude'])
    op.create_index('ix_consoles_health', 'consoles', ['health_status'])
    op.create_index('ix_consoles_version', 'consoles', ['software_version'])
    op.create_index('ix_consoles_heartbeat', 'consoles', ['last_heartbeat'])
    
    print("Migration completed successfully!")

def downgrade():
    """Remove the added features"""
    
    print("Rolling back console enhancements...")
    
    # Remove indexes
    op.drop_index('ix_consoles_heartbeat')
    op.drop_index('ix_consoles_version')
    op.drop_index('ix_consoles_health')
    op.drop_index('ix_consoles_location')
    op.drop_index('ix_shop_products_category')
    
    # Remove new tables
    op.drop_table('console_version_history')
    op.drop_table('console_location_history')
    op.drop_table('product_categories')
    
    # Remove columns from consoles table
    console_columns = [
        'location_name', 'location_address', 'location_latitude', 'location_longitude',
        'location_updated_at', 'location_source', 'software_version', 'hardware_version',
        'firmware_version', 'last_update_check', 'update_available', 'auto_update_enabled',
        'last_heartbeat', 'health_status', 'uptime_seconds', 'cpu_usage_percent',
        'memory_usage_percent', 'disk_usage_percent', 'temperature_celsius', 'network_latency_ms'
    ]
    
    for column in console_columns:
        op.drop_column('consoles', column)
    
    # Remove category_id from shop_products if it exists
    try:
        op.drop_column('shop_products', 'category_id')
    except:
        pass  # Column might not exist
    
    print("Rollback completed!")
