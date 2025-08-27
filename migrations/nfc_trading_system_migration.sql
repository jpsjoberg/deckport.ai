-- NFC Trading System Migration
-- Adds NTAG 424 DNA support, trading, activation codes, and security features

-- Create enhanced NFC cards table
CREATE TABLE IF NOT EXISTS enhanced_nfc_cards (
    id SERIAL PRIMARY KEY,
    
    -- Card Identity
    ntag_uid VARCHAR(32) UNIQUE NOT NULL,
    product_sku VARCHAR(64) NOT NULL,
    serial_number VARCHAR(50),
    batch_id INTEGER,
    
    -- Security (NTAG 424 DNA)
    security_level VARCHAR(20) DEFAULT 'NTAG424_DNA' CHECK (security_level IN ('NTAG424_DNA', 'NTAG213', 'MOCK')),
    issuer_key_ref VARCHAR(128),
    auth_counter INTEGER DEFAULT 0,
    tap_counter INTEGER DEFAULT 0,
    
    -- Ownership
    status VARCHAR(20) DEFAULT 'provisioned' CHECK (status IN ('provisioned', 'sold', 'activated', 'traded', 'revoked', 'damaged')),
    owner_player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    reserved_for_player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    
    -- Public Access
    public_url VARCHAR(500),
    is_public BOOLEAN DEFAULT true,
    
    -- Timestamps
    provisioned_at TIMESTAMP WITH TIME ZONE,
    sold_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Card activation codes
CREATE TABLE IF NOT EXISTS card_activation_codes (
    id SERIAL PRIMARY KEY,
    nfc_card_id INTEGER REFERENCES enhanced_nfc_cards(id) ON DELETE CASCADE NOT NULL,
    
    -- Code Details
    activation_code VARCHAR(8) NOT NULL CHECK (LENGTH(activation_code) = 8),
    code_hash VARCHAR(255) NOT NULL,
    
    -- Delivery
    delivery_method VARCHAR(20) DEFAULT 'email' CHECK (delivery_method IN ('email', 'sms', 'physical')),
    sent_to VARCHAR(255),
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage
    used_at TIMESTAMP WITH TIME ZONE,
    used_by_player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    
    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Card trading system
CREATE TABLE IF NOT EXISTS card_trades (
    id SERIAL PRIMARY KEY,
    
    -- Trade Parties
    seller_player_id INTEGER REFERENCES players(id) ON DELETE CASCADE NOT NULL,
    buyer_player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    nfc_card_id INTEGER REFERENCES enhanced_nfc_cards(id) ON DELETE CASCADE NOT NULL,
    
    -- Trade Details
    trade_code VARCHAR(12) UNIQUE NOT NULL,
    asking_price DECIMAL(10,2) DEFAULT 0 CHECK (asking_price >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status and Timing
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'completed', 'cancelled', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Completion
    completed_at TIMESTAMP WITH TIME ZONE,
    payment_reference VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Public card pages
CREATE TABLE IF NOT EXISTS card_public_pages (
    id SERIAL PRIMARY KEY,
    nfc_card_id INTEGER REFERENCES enhanced_nfc_cards(id) ON DELETE CASCADE NOT NULL,
    
    -- Public Access
    public_slug VARCHAR(64) UNIQUE NOT NULL,
    is_public BOOLEAN DEFAULT true,
    
    -- Statistics
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Display Settings
    show_owner BOOLEAN DEFAULT true,
    show_stats BOOLEAN DEFAULT true,
    show_history BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Card upgrade history
CREATE TABLE IF NOT EXISTS card_upgrades (
    id SERIAL PRIMARY KEY,
    nfc_card_id INTEGER REFERENCES enhanced_nfc_cards(id) ON DELETE CASCADE NOT NULL,
    
    -- Upgrade Details
    upgrade_type VARCHAR(30) NOT NULL,
    
    -- Before/After States
    old_level INTEGER,
    new_level INTEGER,
    old_stats JSONB,
    new_stats JSONB,
    
    -- Upgrade Context
    upgrade_cost JSONB,
    trigger_event VARCHAR(50),
    match_id INTEGER,
    
    upgraded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security logging
CREATE TABLE IF NOT EXISTS nfc_security_logs (
    id SERIAL PRIMARY KEY,
    nfc_card_id INTEGER REFERENCES enhanced_nfc_cards(id) ON DELETE CASCADE NOT NULL,
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    
    -- Context
    console_id INTEGER,
    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    
    -- Technical Data
    auth_challenge VARCHAR(255),
    auth_response VARCHAR(255),
    error_details JSONB,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Card production batches
CREATE TABLE IF NOT EXISTS card_batches (
    id SERIAL PRIMARY KEY,
    
    -- Batch Identity
    batch_code VARCHAR(20) UNIQUE NOT NULL,
    product_sku VARCHAR(64) NOT NULL,
    
    -- Production Details
    production_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_cards INTEGER NOT NULL,
    cards_programmed INTEGER DEFAULT 0,
    cards_sold INTEGER DEFAULT 0,
    cards_activated INTEGER DEFAULT 0,
    
    -- Quality Control
    quality_checked BOOLEAN DEFAULT false,
    quality_notes TEXT,
    
    -- Admin
    created_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key for batch_id in enhanced_nfc_cards
ALTER TABLE enhanced_nfc_cards ADD CONSTRAINT fk_enhanced_nfc_cards_batch 
    FOREIGN KEY (batch_id) REFERENCES card_batches(id) ON DELETE SET NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enhanced_nfc_cards_uid ON enhanced_nfc_cards(ntag_uid);
CREATE INDEX IF NOT EXISTS idx_enhanced_nfc_cards_status ON enhanced_nfc_cards(status);
CREATE INDEX IF NOT EXISTS idx_enhanced_nfc_cards_owner ON enhanced_nfc_cards(owner_player_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_nfc_cards_batch ON enhanced_nfc_cards(batch_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_nfc_cards_security ON enhanced_nfc_cards(security_level);

CREATE INDEX IF NOT EXISTS idx_card_activation_codes_card ON card_activation_codes(nfc_card_id);
CREATE INDEX IF NOT EXISTS idx_card_activation_codes_hash ON card_activation_codes(code_hash);

CREATE INDEX IF NOT EXISTS idx_card_trades_seller ON card_trades(seller_player_id);
CREATE INDEX IF NOT EXISTS idx_card_trades_buyer ON card_trades(buyer_player_id);
CREATE INDEX IF NOT EXISTS idx_card_trades_status ON card_trades(status);
CREATE INDEX IF NOT EXISTS idx_card_trades_expires ON card_trades(expires_at);

CREATE INDEX IF NOT EXISTS idx_card_public_pages_card ON card_public_pages(nfc_card_id);
CREATE INDEX IF NOT EXISTS idx_card_public_pages_slug ON card_public_pages(public_slug);
CREATE INDEX IF NOT EXISTS idx_card_public_pages_views ON card_public_pages(view_count);

CREATE INDEX IF NOT EXISTS idx_card_upgrades_card ON card_upgrades(nfc_card_id);
CREATE INDEX IF NOT EXISTS idx_card_upgrades_type ON card_upgrades(upgrade_type);
CREATE INDEX IF NOT EXISTS idx_card_upgrades_date ON card_upgrades(upgraded_at);

CREATE INDEX IF NOT EXISTS idx_nfc_security_logs_card ON nfc_security_logs(nfc_card_id);
CREATE INDEX IF NOT EXISTS idx_nfc_security_logs_event ON nfc_security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_nfc_security_logs_timestamp ON nfc_security_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_nfc_security_logs_severity ON nfc_security_logs(severity);

CREATE INDEX IF NOT EXISTS idx_card_batches_product ON card_batches(product_sku);
CREATE INDEX IF NOT EXISTS idx_card_batches_date ON card_batches(production_date);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_enhanced_nfc_cards_updated_at BEFORE UPDATE ON enhanced_nfc_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_card_trades_updated_at BEFORE UPDATE ON card_trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_card_public_pages_updated_at BEFORE UPDATE ON card_public_pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_card_batches_updated_at BEFORE UPDATE ON card_batches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO card_batches (batch_code, product_sku, production_date, total_cards, created_by_admin_id) VALUES
('BATCH-TEST-001', 'RADIANT-001', CURRENT_TIMESTAMP, 10, 1),
('BATCH-TEST-002', 'AZURE-014', CURRENT_TIMESTAMP, 10, 1),
('BATCH-TEST-003', 'VERDANT-007', CURRENT_TIMESTAMP, 10, 1)
ON CONFLICT (batch_code) DO NOTHING;

-- Insert sample enhanced NFC cards
INSERT INTO enhanced_nfc_cards (ntag_uid, product_sku, serial_number, batch_id, security_level, status) VALUES
('04523AB2C1800001', 'RADIANT-001', 'BATCH-TEST-001-001', 1, 'MOCK', 'provisioned'),
('04A37FC2D1900002', 'AZURE-014', 'BATCH-TEST-002-001', 2, 'MOCK', 'provisioned'),
('04B18ED3F2A10003', 'VERDANT-007', 'BATCH-TEST-003-001', 3, 'MOCK', 'provisioned')
ON CONFLICT (ntag_uid) DO NOTHING;

-- Insert sample activation codes
INSERT INTO card_activation_codes (nfc_card_id, activation_code, code_hash, expires_at) VALUES
(1, '12345678', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', CURRENT_TIMESTAMP + INTERVAL '1 year'),
(2, '87654321', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', CURRENT_TIMESTAMP + INTERVAL '1 year'),
(3, '11223344', 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9', CURRENT_TIMESTAMP + INTERVAL '1 year')
ON CONFLICT DO NOTHING;

COMMIT;
