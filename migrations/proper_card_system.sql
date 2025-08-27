-- Proper 3-Tier Card System Migration
-- Tier 1: Templates (LLM designs) → Tier 2: Products (final cards) → Tier 3: NFC Cards (physical)

-- ===== TIER 1: CARD_TEMPLATES (Design Layer) =====
-- Raw card designs created by LLM - NOT final products
CREATE TABLE IF NOT EXISTS card_templates (
    id SERIAL PRIMARY KEY,
    card_set_id INTEGER REFERENCES card_sets(id) ON DELETE CASCADE,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    flavor_text TEXT,
    
    -- Card Properties
    rarity VARCHAR(20) NOT NULL CHECK (rarity IN ('common', 'rare', 'epic', 'legendary')),
    category VARCHAR(30) NOT NULL CHECK (category IN ('creature', 'structure', 'action_fast', 'action_slow', 'equipment', 'enchantment', 'special', 'artifact', 'ritual', 'trap', 'summon', 'terrain', 'objective')),
    color_code VARCHAR(20),
    
    -- LLM Generation Data
    base_stats JSONB, -- Raw stats from LLM
    attachment_rules JSONB,
    duration JSONB,
    token_spec JSONB,
    reveal_trigger JSONB,
    
    -- Image Generation
    art_prompt TEXT, -- Prompt for image generation
    art_style VARCHAR(50) DEFAULT 'painterly',
    negative_prompt TEXT,
    
    -- Template Status
    is_design_complete BOOLEAN DEFAULT FALSE, -- LLM design finished
    is_balanced BOOLEAN DEFAULT FALSE, -- Passed balance review
    is_ready_for_production BOOLEAN DEFAULT FALSE, -- Ready to generate final card
    
    -- AI Balance Data
    balance_weight INTEGER DEFAULT 50, -- 1-100 power level
    generation_context TEXT, -- Context used for LLM generation
    last_balance_check TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===== TIER 2: CARD_PRODUCTS (Production/Catalog Layer) =====
-- Final cards with generated graphics - THIS IS THE CARD CATALOG
CREATE TABLE IF NOT EXISTS card_products (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES card_templates(id) ON DELETE RESTRICT,
    card_set_id INTEGER REFERENCES card_sets(id) ON DELETE CASCADE,
    
    -- Product Identity
    product_sku VARCHAR(64) UNIQUE NOT NULL, -- "RADIANT-001", "CRIMSON-042"
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    flavor_text TEXT,
    display_label VARCHAR(40),
    
    -- Final Card Properties (may differ from template after balancing)
    rarity VARCHAR(20) NOT NULL,
    category VARCHAR(30) NOT NULL,
    color_code VARCHAR(20),
    
    -- Final Game Mechanics
    base_stats JSONB NOT NULL, -- Final balanced stats
    attachment_rules JSONB,
    duration JSONB,
    token_spec JSONB,
    reveal_trigger JSONB,
    
    -- Generated Assets
    image_url VARCHAR(500), -- Final card image
    thumbnail_url VARCHAR(500), -- Small preview image
    art_metadata JSONB, -- Generation metadata (seed, model, etc.)
    
    -- Production Status
    is_published BOOLEAN DEFAULT FALSE, -- Available for play
    is_printable BOOLEAN DEFAULT FALSE, -- Ready for physical production
    print_quality_approved BOOLEAN DEFAULT FALSE,
    
    -- Catalog Info
    release_date DATE,
    retirement_date DATE, -- When card rotates out
    print_run_size INTEGER, -- How many physical cards to produce
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===== TIER 3: NFC_CARDS (Physical Layer) =====
-- Individual physical cards that can be played, upgraded, traded
-- (Keep existing structure but link to card_products)
ALTER TABLE nfc_cards 
ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES card_products(id) ON DELETE RESTRICT;

-- Update existing nfc_cards to use product_id instead of template_id
-- (We'll handle this migration separately)

-- ===== INDEXES FOR PERFORMANCE =====
CREATE INDEX IF NOT EXISTS idx_card_templates_set_ready ON card_templates(card_set_id, is_ready_for_production);
CREATE INDEX IF NOT EXISTS idx_card_templates_balanced ON card_templates(is_balanced, balance_weight);
CREATE INDEX IF NOT EXISTS idx_card_products_published ON card_products(is_published, release_date);
CREATE INDEX IF NOT EXISTS idx_card_products_sku ON card_products(product_sku);
CREATE INDEX IF NOT EXISTS idx_card_products_category ON card_products(category, rarity);
CREATE INDEX IF NOT EXISTS idx_nfc_cards_product ON nfc_cards(product_id);

-- ===== WORKFLOW VIEWS =====
-- View for cards ready for image generation
CREATE OR REPLACE VIEW cards_ready_for_generation AS
SELECT 
    t.*,
    cs.name as set_name,
    cs.code as set_code
FROM card_templates t
JOIN card_sets cs ON t.card_set_id = cs.id
WHERE t.is_design_complete = TRUE 
  AND t.is_balanced = TRUE 
  AND t.is_ready_for_production = TRUE
  AND NOT EXISTS (
      SELECT 1 FROM card_products p WHERE p.template_id = t.id
  );

-- View for published cards (the actual game catalog)
CREATE OR REPLACE VIEW card_catalog AS
SELECT 
    p.*,
    cs.name as set_name,
    cs.code as set_code,
    t.art_prompt,
    t.generation_context
FROM card_products p
JOIN card_sets cs ON p.card_set_id = cs.id
LEFT JOIN card_templates t ON p.template_id = t.id
WHERE p.is_published = TRUE;

-- View for playable cards (NFC cards with their product info)
CREATE OR REPLACE VIEW playable_cards AS
SELECT 
    nfc.*,
    p.product_sku,
    p.name,
    p.description,
    p.base_stats,
    p.image_url,
    p.rarity,
    p.category,
    p.color_code
FROM nfc_cards nfc
JOIN card_products p ON nfc.product_id = p.id
WHERE nfc.status = 'activated' 
  AND p.is_published = TRUE;
