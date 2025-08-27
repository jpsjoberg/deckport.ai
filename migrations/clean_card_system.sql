-- Clean Card System Migration
-- Consolidates the card system into a logical structure

-- 1. First, let's enhance card_templates to be the master table
ALTER TABLE card_templates 
ADD COLUMN IF NOT EXISTS image_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS base_stats JSONB,
ADD COLUMN IF NOT EXISTS attachment_rules JSONB,
ADD COLUMN IF NOT EXISTS duration JSONB,
ADD COLUMN IF NOT EXISTS token_spec JSONB,
ADD COLUMN IF NOT EXISTS reveal_trigger JSONB,
ADD COLUMN IF NOT EXISTS display_label VARCHAR(40),
ADD COLUMN IF NOT EXISTS product_sku VARCHAR(64) UNIQUE,
ADD COLUMN IF NOT EXISTS is_ready_for_production BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS balance_weight INTEGER DEFAULT 50,
ADD COLUMN IF NOT EXISTS generation_prompt TEXT,
ADD COLUMN IF NOT EXISTS last_balance_check TIMESTAMP WITH TIME ZONE;

-- 2. Create a proper card set for testing
INSERT INTO card_sets (name, code, description, is_active) 
VALUES ('Core Set Alpha', 'CORE-A', 'Initial core set for testing and development', true)
ON CONFLICT (code) DO NOTHING;

-- 3. Create a test set for our current test cards
INSERT INTO card_sets (name, code, description, is_active) 
VALUES ('Test Set', 'TEST', 'Development and testing cards', true)
ON CONFLICT (code) DO NOTHING;

-- 4. Migrate existing card_catalog data to card_templates
-- (We'll do this step by step to preserve data)

-- First, let's see what we have in card_catalog that's not in card_templates
-- This query will help us understand the migration needed
