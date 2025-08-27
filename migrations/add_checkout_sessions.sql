-- Shop Checkout Sessions Migration
-- Adds secure session storage for checkout process

-- Shop Checkout Sessions
CREATE TABLE IF NOT EXISTS shop_checkout_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    session_data JSONB NOT NULL,
    session_hash VARCHAR(128) NOT NULL,
    
    -- Customer info
    customer_id INTEGER REFERENCES players(id),
    customer_ip VARCHAR(45),
    
    -- Status
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_shop_checkout_sessions_session_id ON shop_checkout_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_shop_checkout_sessions_customer_id ON shop_checkout_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_shop_checkout_sessions_expires_at ON shop_checkout_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_shop_checkout_sessions_is_used ON shop_checkout_sessions(is_used);

-- Cleanup expired sessions (can be run periodically)
-- DELETE FROM shop_checkout_sessions WHERE expires_at < CURRENT_TIMESTAMP AND is_used = FALSE;
