-- Shop System Database Migration
-- Creates tables for e-commerce functionality: products, orders, inventory, etc.

-- Shop Categories
CREATE TABLE IF NOT EXISTS shop_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES shop_categories(id),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shop Products
CREATE TABLE IF NOT EXISTS shop_products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    
    -- Pricing
    price DECIMAL(10,2) NOT NULL,
    compare_at_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Product Details
    product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('single_card', 'bundle', 'booster_pack', 'starter_deck', 'accessory', 'digital')),
    category_id INTEGER REFERENCES shop_categories(id),
    
    -- Inventory
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 5,
    track_inventory BOOLEAN DEFAULT TRUE,
    allow_backorder BOOLEAN DEFAULT FALSE,
    
    -- Physical Properties
    weight DECIMAL(8,3),
    length DECIMAL(8,2),
    width DECIMAL(8,2),
    height DECIMAL(8,2),
    
    -- Digital Properties
    card_skus JSONB,
    digital_assets JSONB,
    
    -- Media
    image_url VARCHAR(500),
    gallery_images JSONB,
    video_url VARCHAR(500),
    
    -- SEO & Marketing
    meta_title VARCHAR(200),
    meta_description VARCHAR(500),
    tags JSONB,
    is_featured BOOLEAN DEFAULT FALSE,
    is_bestseller BOOLEAN DEFAULT FALSE,
    
    -- Status & Visibility
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'inactive', 'discontinued')),
    is_active BOOLEAN DEFAULT TRUE,
    is_visible BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

-- Shop Orders
CREATE TABLE IF NOT EXISTS shop_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer Information
    customer_id INTEGER REFERENCES players(id),
    customer_email VARCHAR(255),
    customer_name VARCHAR(200),
    customer_phone VARCHAR(50),
    
    -- Pricing
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    shipping_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status
    order_status VARCHAR(20) DEFAULT 'pending' CHECK (order_status IN ('pending', 'processing', 'shipped', 'delivered', 'completed', 'cancelled', 'refunded')),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded', 'partially_refunded')),
    shipping_status VARCHAR(20) DEFAULT 'not_shipped' CHECK (shipping_status IN ('not_shipped', 'preparing', 'shipped', 'in_transit', 'out_for_delivery', 'delivered', 'failed_delivery', 'returned')),
    
    -- Addresses
    billing_address JSONB,
    shipping_address JSONB,
    
    -- Shipping
    shipping_method VARCHAR(100),
    tracking_number VARCHAR(100),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    
    -- Payment
    payment_method VARCHAR(50),
    payment_reference VARCHAR(200),
    paid_at TIMESTAMP,
    
    -- Metadata
    notes TEXT,
    admin_notes TEXT,
    source VARCHAR(50) DEFAULT 'web',
    
    -- Flags
    is_priority BOOLEAN DEFAULT FALSE,
    is_gift BOOLEAN DEFAULT FALSE,
    requires_shipping BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shop Order Items
CREATE TABLE IF NOT EXISTS shop_order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES shop_orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES shop_products(id),
    
    -- Product snapshot at time of order
    product_sku VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_image_url VARCHAR(500),
    
    -- Pricing
    unit_price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    
    -- Fulfillment
    is_fulfilled BOOLEAN DEFAULT FALSE,
    fulfilled_at TIMESTAMP,
    fulfillment_notes TEXT,
    
    -- Digital delivery
    digital_assets_delivered JSONB,
    delivery_method VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shop Order Status History
CREATE TABLE IF NOT EXISTS shop_order_status_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES shop_orders(id) ON DELETE CASCADE,
    
    -- Status change
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    status_type VARCHAR(20),
    
    -- Details
    reason VARCHAR(200),
    notes TEXT,
    changed_by VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shop Inventory Logs
CREATE TABLE IF NOT EXISTS shop_inventory_logs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES shop_products(id) ON DELETE CASCADE,
    
    -- Change details
    change_type VARCHAR(50) NOT NULL,
    quantity_before INTEGER NOT NULL,
    quantity_change INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    
    -- Reference
    reference_type VARCHAR(50),
    reference_id INTEGER,
    
    -- Details
    reason VARCHAR(200),
    notes TEXT,
    changed_by VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shop Discounts
CREATE TABLE IF NOT EXISTS shop_discounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Discount details
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount', 'free_shipping')),
    discount_value DECIMAL(10,2) NOT NULL,
    minimum_order_amount DECIMAL(10,2),
    maximum_discount_amount DECIMAL(10,2),
    
    -- Usage limits
    usage_limit INTEGER,
    usage_limit_per_customer INTEGER,
    usage_count INTEGER DEFAULT 0,
    
    -- Validity
    starts_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Restrictions
    applicable_products JSONB,
    applicable_categories JSONB,
    customer_eligibility VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shop Customer Addresses
CREATE TABLE IF NOT EXISTS shop_customer_addresses (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    
    -- Address details
    type VARCHAR(20) NOT NULL CHECK (type IN ('billing', 'shipping')),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company VARCHAR(200),
    address_line_1 VARCHAR(200) NOT NULL,
    address_line_2 VARCHAR(200),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(2) NOT NULL,
    phone VARCHAR(50),
    
    -- Flags
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_shop_products_sku ON shop_products(sku);
CREATE INDEX IF NOT EXISTS idx_shop_products_status ON shop_products(status);
CREATE INDEX IF NOT EXISTS idx_shop_products_category ON shop_products(category_id);
CREATE INDEX IF NOT EXISTS idx_shop_products_featured ON shop_products(is_featured);
CREATE INDEX IF NOT EXISTS idx_shop_products_stock ON shop_products(stock_quantity);

CREATE INDEX IF NOT EXISTS idx_shop_orders_number ON shop_orders(order_number);
CREATE INDEX IF NOT EXISTS idx_shop_orders_customer ON shop_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_shop_orders_status ON shop_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_shop_orders_payment_status ON shop_orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_shop_orders_created ON shop_orders(created_at);

CREATE INDEX IF NOT EXISTS idx_shop_order_items_order ON shop_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_shop_order_items_product ON shop_order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_shop_inventory_logs_product ON shop_inventory_logs(product_id);
CREATE INDEX IF NOT EXISTS idx_shop_inventory_logs_created ON shop_inventory_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_shop_discounts_code ON shop_discounts(code);
CREATE INDEX IF NOT EXISTS idx_shop_discounts_active ON shop_discounts(is_active);

-- Insert default categories
INSERT INTO shop_categories (name, slug, description, sort_order) VALUES
('Trading Cards', 'trading-cards', 'Individual trading cards and singles', 1),
('Booster Packs', 'booster-packs', 'Random card booster packs', 2),
('Starter Decks', 'starter-decks', 'Pre-built starter decks for new players', 3),
('Bundles', 'bundles', 'Card bundles and special collections', 4),
('Accessories', 'accessories', 'Card sleeves, playmats, and other accessories', 5),
('Digital', 'digital', 'Digital content and downloads', 6)
ON CONFLICT (slug) DO NOTHING;

-- Insert sample products
INSERT INTO shop_products (sku, name, slug, description, price, product_type, category_id, stock_quantity, is_active, status, published_at) VALUES
('BUNDLE-STARTER', 'Starter Bundle', 'starter-bundle', 'Perfect starter bundle for new players. Includes 20 cards, basic rules, and a playmat.', 49.00, 'bundle', 4, 100, TRUE, 'active', CURRENT_TIMESTAMP),
('BUNDLE-RADIANT', 'Radiant Bundle', 'radiant-bundle', 'Premium collection of radiant cards with exclusive artwork.', 39.00, 'bundle', 4, 50, TRUE, 'active', CURRENT_TIMESTAMP),
('PACK-BASIC', 'Basic Booster Pack', 'basic-booster-pack', 'Standard booster pack with 15 random cards.', 4.99, 'booster_pack', 2, 500, TRUE, 'active', CURRENT_TIMESTAMP),
('DECK-FIRE', 'Fire Starter Deck', 'fire-starter-deck', 'Pre-built fire-themed starter deck ready to play.', 24.99, 'starter_deck', 3, 75, TRUE, 'active', CURRENT_TIMESTAMP)
ON CONFLICT (sku) DO NOTHING;

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_shop_categories_updated_at BEFORE UPDATE ON shop_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shop_products_updated_at BEFORE UPDATE ON shop_products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shop_orders_updated_at BEFORE UPDATE ON shop_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shop_order_items_updated_at BEFORE UPDATE ON shop_order_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shop_discounts_updated_at BEFORE UPDATE ON shop_discounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shop_customer_addresses_updated_at BEFORE UPDATE ON shop_customer_addresses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();





