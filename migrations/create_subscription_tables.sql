-- Subscription System Database Migration
-- Creates tables for subscription management, billing, and revenue tracking

-- Subscription status enum
DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM (
        'active', 'trialing', 'past_due', 'canceled', 
        'unpaid', 'incomplete', 'incomplete_expired', 'paused'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Subscription plan enum
DO $$ BEGIN
    CREATE TYPE subscription_plan AS ENUM (
        'basic', 'premium', 'pro', 'enterprise'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Billing interval enum
DO $$ BEGIN
    CREATE TYPE billing_interval AS ENUM (
        'monthly', 'quarterly', 'yearly'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Payment status enum
DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM (
        'pending', 'paid', 'failed', 'refunded', 'partially_refunded'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Main subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    
    -- Player and external references
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(100) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(100) NOT NULL,
    
    -- Subscription details
    plan subscription_plan NOT NULL,
    status subscription_status NOT NULL,
    billing_interval billing_interval NOT NULL,
    
    -- Pricing
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    
    -- Billing periods
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    
    -- Trial information
    trial_start TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    
    -- Cancellation
    canceled_at TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE NOT NULL,
    cancellation_reason TEXT,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Subscription invoices table
CREATE TABLE IF NOT EXISTS subscription_invoices (
    id SERIAL PRIMARY KEY,
    
    -- References
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    stripe_invoice_id VARCHAR(100) UNIQUE NOT NULL,
    stripe_payment_intent_id VARCHAR(100),
    
    -- Invoice details
    invoice_number VARCHAR(50) NOT NULL,
    
    -- Billing period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    
    -- Amounts
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0.00 NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00 NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) DEFAULT 0.00 NOT NULL,
    amount_due DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    
    -- Payment status and timing
    payment_status payment_status DEFAULT 'pending' NOT NULL,
    due_date TIMESTAMPTZ NOT NULL,
    paid_at TIMESTAMPTZ,
    
    -- Attempt tracking
    payment_attempts INTEGER DEFAULT 0 NOT NULL,
    next_payment_attempt TIMESTAMPTZ,
    
    -- Metadata
    invoice_pdf_url VARCHAR(500),
    hosted_invoice_url VARCHAR(500),
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Subscription usage tracking table
CREATE TABLE IF NOT EXISTS subscription_usage (
    id SERIAL PRIMARY KEY,
    
    -- References
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    
    -- Usage details
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0 NOT NULL,
    usage_date TIMESTAMPTZ NOT NULL,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Subscription discounts table
CREATE TABLE IF NOT EXISTS subscription_discounts (
    id SERIAL PRIMARY KEY,
    
    -- References
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    
    -- Discount details
    discount_code VARCHAR(50) NOT NULL,
    discount_type VARCHAR(20) NOT NULL, -- 'percent' or 'fixed_amount'
    discount_value DECIMAL(10,2) NOT NULL,
    
    -- Validity
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ,
    
    -- Usage limits
    max_uses INTEGER, -- NULL = unlimited
    times_used INTEGER DEFAULT 0 NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_subscriptions_player ON subscriptions(player_id);
CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS ix_subscriptions_plan ON subscriptions(plan);
CREATE INDEX IF NOT EXISTS ix_subscriptions_current_period ON subscriptions(current_period_start, current_period_end);

CREATE INDEX IF NOT EXISTS ix_subscription_invoices_subscription ON subscription_invoices(subscription_id);
CREATE INDEX IF NOT EXISTS ix_subscription_invoices_status ON subscription_invoices(payment_status);
CREATE INDEX IF NOT EXISTS ix_subscription_invoices_period ON subscription_invoices(period_start, period_end);
CREATE INDEX IF NOT EXISTS ix_subscription_invoices_due_date ON subscription_invoices(due_date);

CREATE INDEX IF NOT EXISTS ix_subscription_usage_subscription ON subscription_usage(subscription_id);
CREATE INDEX IF NOT EXISTS ix_subscription_usage_feature ON subscription_usage(feature_name);
CREATE INDEX IF NOT EXISTS ix_subscription_usage_date ON subscription_usage(usage_date);

CREATE INDEX IF NOT EXISTS ix_subscription_discounts_subscription ON subscription_discounts(subscription_id);
CREATE INDEX IF NOT EXISTS ix_subscription_discounts_code ON subscription_discounts(discount_code);
CREATE INDEX IF NOT EXISTS ix_subscription_discounts_active ON subscription_discounts(is_active);

-- Update trigger for subscriptions
CREATE OR REPLACE FUNCTION update_subscription_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();

-- Update trigger for subscription_invoices
CREATE TRIGGER update_subscription_invoices_updated_at
    BEFORE UPDATE ON subscription_invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();

-- Comments for documentation
COMMENT ON TABLE subscriptions IS 'Player subscriptions for premium features and recurring billing';
COMMENT ON TABLE subscription_invoices IS 'Subscription billing invoices and payment tracking';
COMMENT ON TABLE subscription_usage IS 'Track subscription feature usage for analytics and billing';
COMMENT ON TABLE subscription_discounts IS 'Discounts and coupons applied to subscriptions';

COMMENT ON COLUMN subscriptions.stripe_subscription_id IS 'Stripe subscription ID for external reference';
COMMENT ON COLUMN subscriptions.cancel_at_period_end IS 'Whether to cancel at the end of current billing period';
COMMENT ON COLUMN subscription_invoices.payment_attempts IS 'Number of payment attempts made for this invoice';
COMMENT ON COLUMN subscription_usage.feature_name IS 'Name of the feature being tracked (e.g., premium_cards, tournaments)';
COMMENT ON COLUMN subscription_discounts.discount_type IS 'Type of discount: percent or fixed_amount';
