-- Enhanced Card Schema Migration
-- Adds video, frame, and asset management capabilities to existing card system
-- Includes all missing card types and action types

-- First, let's add the missing card categories to the enum
-- Note: PostgreSQL requires dropping and recreating enums to add values

-- Backup existing data
CREATE TABLE card_catalog_backup AS SELECT * FROM card_catalog;

-- Drop existing enum constraint
ALTER TABLE card_catalog DROP CONSTRAINT IF EXISTS card_catalog_category_check;

-- Drop the old enum type
DROP TYPE IF EXISTS card_category CASCADE;

-- Create enhanced card category enum with all types
CREATE TYPE card_category AS ENUM (
    'CREATURE',         -- Living beings and monsters
    'STRUCTURE',        -- Buildings and installations  
    'ACTION_FAST',      -- Instant speed actions
    'ACTION_SLOW',      -- Sorcery speed actions
    'SPECIAL',          -- Unique special cards
    'EQUIPMENT',        -- Weapons and gear
    'ENCHANTMENT',      -- Ongoing magical effects
    'ARTIFACT',         -- Magical items and constructs
    'RITUAL',           -- Powerful ceremonial magic
    'TRAP',             -- Hidden reactive cards
    'SUMMON',           -- Summoning spells
    'TERRAIN',          -- Environmental modifications
    'OBJECTIVE',        -- Win condition cards
    'HERO',             -- Player avatar cards
    'LEGENDARY_CREATURE', -- Unique legendary beings
    'LEGENDARY_ARTIFACT', -- Unique legendary items
    'TOKEN',            -- Generated temporary cards
    'CONSUMABLE',       -- Single-use items
    'VEHICLE',          -- Rideable constructs
    'PLANESWALKER'      -- Powerful ally cards
);

-- Add new columns to card_catalog for enhanced functionality
ALTER TABLE card_catalog 
ADD COLUMN IF NOT EXISTS frame_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS video_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS static_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS has_animation BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS frame_data JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS asset_quality_levels TEXT[] DEFAULT ARRAY['low', 'medium', 'high'],
ADD COLUMN IF NOT EXISTS generation_prompt TEXT,
ADD COLUMN IF NOT EXISTS video_prompt TEXT,
ADD COLUMN IF NOT EXISTS frame_style VARCHAR(50) DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS mana_colors TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS action_speed VARCHAR(20),
ADD COLUMN IF NOT EXISTS card_set_id VARCHAR(50) DEFAULT 'open_portal';

-- Re-add the category constraint with new enum
ALTER TABLE card_catalog 
ADD CONSTRAINT card_catalog_category_check 
CHECK (category::text = ANY(ARRAY[
    'CREATURE', 'STRUCTURE', 'ACTION_FAST', 'ACTION_SLOW', 'SPECIAL', 
    'EQUIPMENT', 'ENCHANTMENT', 'ARTIFACT', 'RITUAL', 'TRAP', 'SUMMON', 
    'TERRAIN', 'OBJECTIVE', 'HERO', 'LEGENDARY_CREATURE', 'LEGENDARY_ARTIFACT',
    'TOKEN', 'CONSUMABLE', 'VEHICLE', 'PLANESWALKER'
]));

-- Create card_assets table for multi-asset tracking
CREATE TABLE IF NOT EXISTS card_assets (
    id SERIAL PRIMARY KEY,
    card_catalog_id INTEGER NOT NULL REFERENCES card_catalog(id) ON DELETE CASCADE,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('static', 'video', 'frame', 'composite', 'thumbnail')),
    quality_level VARCHAR(20) NOT NULL CHECK (quality_level IN ('low', 'medium', 'high', 'print')),
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500),
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    duration_seconds DECIMAL(5,2), -- For video assets
    format VARCHAR(20), -- PNG, JPG, MP4, WEBM, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(card_catalog_id, asset_type, quality_level)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_card_assets_card_id ON card_assets(card_catalog_id);
CREATE INDEX IF NOT EXISTS idx_card_assets_type ON card_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_card_assets_quality ON card_assets(quality_level);
CREATE INDEX IF NOT EXISTS idx_card_catalog_frame_type ON card_catalog(frame_type);
CREATE INDEX IF NOT EXISTS idx_card_catalog_has_animation ON card_catalog(has_animation);
CREATE INDEX IF NOT EXISTS idx_card_catalog_card_set ON card_catalog(card_set_id);

-- Create frame_types table for frame management
CREATE TABLE IF NOT EXISTS frame_types (
    id SERIAL PRIMARY KEY,
    frame_code VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    rarity VARCHAR(20) NOT NULL,
    mana_color VARCHAR(20),
    file_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert standard frame types
INSERT INTO frame_types (frame_code, display_name, category, rarity, mana_color, file_path) VALUES
-- Creature frames
('common_creature_crimson', 'Common Creature - Crimson', 'CREATURE', 'COMMON', 'CRIMSON', 'frames/common_creature_crimson.png'),
('common_creature_azure', 'Common Creature - Azure', 'CREATURE', 'COMMON', 'AZURE', 'frames/common_creature_azure.png'),
('common_creature_verdant', 'Common Creature - Verdant', 'CREATURE', 'COMMON', 'VERDANT', 'frames/common_creature_verdant.png'),
('common_creature_obsidian', 'Common Creature - Obsidian', 'CREATURE', 'COMMON', 'OBSIDIAN', 'frames/common_creature_obsidian.png'),
('common_creature_radiant', 'Common Creature - Radiant', 'CREATURE', 'COMMON', 'RADIANT', 'frames/common_creature_radiant.png'),
('common_creature_aether', 'Common Creature - Aether', 'CREATURE', 'COMMON', 'AETHER', 'frames/common_creature_aether.png'),

-- Rare creature frames
('rare_creature_crimson', 'Rare Creature - Crimson', 'CREATURE', 'RARE', 'CRIMSON', 'frames/rare_creature_crimson.png'),
('rare_creature_azure', 'Rare Creature - Azure', 'CREATURE', 'RARE', 'AZURE', 'frames/rare_creature_azure.png'),
('rare_creature_verdant', 'Rare Creature - Verdant', 'CREATURE', 'RARE', 'VERDANT', 'frames/rare_creature_verdant.png'),
('rare_creature_obsidian', 'Rare Creature - Obsidian', 'CREATURE', 'RARE', 'OBSIDIAN', 'frames/rare_creature_obsidian.png'),
('rare_creature_radiant', 'Rare Creature - Radiant', 'CREATURE', 'RARE', 'RADIANT', 'frames/rare_creature_radiant.png'),
('rare_creature_aether', 'Rare Creature - Aether', 'CREATURE', 'RARE', 'AETHER', 'frames/rare_creature_aether.png'),

-- Epic creature frames
('epic_creature_crimson', 'Epic Creature - Crimson', 'CREATURE', 'EPIC', 'CRIMSON', 'frames/epic_creature_crimson.png'),
('epic_creature_azure', 'Epic Creature - Azure', 'CREATURE', 'EPIC', 'AZURE', 'frames/epic_creature_azure.png'),
('epic_creature_verdant', 'Epic Creature - Verdant', 'CREATURE', 'EPIC', 'VERDANT', 'frames/epic_creature_verdant.png'),
('epic_creature_obsidian', 'Epic Creature - Obsidian', 'CREATURE', 'EPIC', 'OBSIDIAN', 'frames/epic_creature_obsidian.png'),
('epic_creature_radiant', 'Epic Creature - Radiant', 'CREATURE', 'EPIC', 'RADIANT', 'frames/epic_creature_radiant.png'),
('epic_creature_aether', 'Epic Creature - Aether', 'CREATURE', 'EPIC', 'AETHER', 'frames/epic_creature_aether.png'),

-- Legendary creature frames
('legendary_creature_crimson', 'Legendary Creature - Crimson', 'CREATURE', 'LEGENDARY', 'CRIMSON', 'frames/legendary_creature_crimson.png'),
('legendary_creature_azure', 'Legendary Creature - Azure', 'CREATURE', 'LEGENDARY', 'AZURE', 'frames/legendary_creature_azure.png'),
('legendary_creature_verdant', 'Legendary Creature - Verdant', 'CREATURE', 'LEGENDARY', 'VERDANT', 'frames/legendary_creature_verdant.png'),
('legendary_creature_obsidian', 'Legendary Creature - Obsidian', 'CREATURE', 'LEGENDARY', 'OBSIDIAN', 'frames/legendary_creature_obsidian.png'),
('legendary_creature_radiant', 'Legendary Creature - Radiant', 'CREATURE', 'LEGENDARY', 'RADIANT', 'frames/legendary_creature_radiant.png'),
('legendary_creature_aether', 'Legendary Creature - Aether', 'CREATURE', 'LEGENDARY', 'AETHER', 'frames/legendary_creature_aether.png'),

-- Action frames (Fast)
('common_action_fast_crimson', 'Common Fast Action - Crimson', 'ACTION_FAST', 'COMMON', 'CRIMSON', 'frames/common_action_fast_crimson.png'),
('rare_action_fast_azure', 'Rare Fast Action - Azure', 'ACTION_FAST', 'RARE', 'AZURE', 'frames/rare_action_fast_azure.png'),
('epic_action_fast_verdant', 'Epic Fast Action - Verdant', 'ACTION_FAST', 'EPIC', 'VERDANT', 'frames/epic_action_fast_verdant.png'),

-- Action frames (Slow)
('common_action_slow_crimson', 'Common Slow Action - Crimson', 'ACTION_SLOW', 'COMMON', 'CRIMSON', 'frames/common_action_slow_crimson.png'),
('rare_action_slow_azure', 'Rare Slow Action - Azure', 'ACTION_SLOW', 'RARE', 'AZURE', 'frames/rare_action_slow_azure.png'),
('epic_action_slow_verdant', 'Epic Slow Action - Verdant', 'ACTION_SLOW', 'EPIC', 'VERDANT', 'frames/epic_action_slow_verdant.png'),

-- Structure frames
('common_structure_crimson', 'Common Structure - Crimson', 'STRUCTURE', 'COMMON', 'CRIMSON', 'frames/common_structure_crimson.png'),
('rare_structure_azure', 'Rare Structure - Azure', 'STRUCTURE', 'RARE', 'AZURE', 'frames/rare_structure_azure.png'),
('epic_structure_verdant', 'Epic Structure - Verdant', 'STRUCTURE', 'EPIC', 'VERDANT', 'frames/epic_structure_verdant.png'),
('legendary_structure_obsidian', 'Legendary Structure - Obsidian', 'STRUCTURE', 'LEGENDARY', 'OBSIDIAN', 'frames/legendary_structure_obsidian.png'),

-- Equipment frames
('common_equipment_neutral', 'Common Equipment', 'EQUIPMENT', 'COMMON', NULL, 'frames/common_equipment_neutral.png'),
('rare_equipment_neutral', 'Rare Equipment', 'EQUIPMENT', 'RARE', NULL, 'frames/rare_equipment_neutral.png'),
('epic_equipment_neutral', 'Epic Equipment', 'EQUIPMENT', 'EPIC', NULL, 'frames/epic_equipment_neutral.png'),
('legendary_equipment_neutral', 'Legendary Equipment', 'EQUIPMENT', 'LEGENDARY', NULL, 'frames/legendary_equipment_neutral.png'),

-- Special card frames
('legendary_special_unique', 'Legendary Special - Unique', 'SPECIAL', 'LEGENDARY', NULL, 'frames/legendary_special_unique.png'),
('mythic_special_unique', 'Mythic Special - Unique', 'SPECIAL', 'LEGENDARY', NULL, 'frames/mythic_special_unique.png')

ON CONFLICT (frame_code) DO NOTHING;

-- Create card_generation_queue table for batch processing
CREATE TABLE IF NOT EXISTS card_generation_queue (
    id SERIAL PRIMARY KEY,
    card_catalog_id INTEGER NOT NULL REFERENCES card_catalog(id) ON DELETE CASCADE,
    generation_type VARCHAR(50) NOT NULL CHECK (generation_type IN ('art', 'video', 'frame', 'composite', 'all')),
    priority INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress_percent INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generation_queue_status ON card_generation_queue(status);
CREATE INDEX IF NOT EXISTS idx_generation_queue_priority ON card_generation_queue(priority DESC);

-- Update existing cards with default frame assignments
UPDATE card_catalog 
SET 
    frame_type = CASE 
        WHEN category = 'CREATURE' AND rarity = 'COMMON' THEN 'common_creature_' || LOWER(COALESCE(base_stats->>'mana_color', 'crimson'))
        WHEN category = 'CREATURE' AND rarity = 'RARE' THEN 'rare_creature_' || LOWER(COALESCE(base_stats->>'mana_color', 'azure'))
        WHEN category = 'CREATURE' AND rarity = 'EPIC' THEN 'epic_creature_' || LOWER(COALESCE(base_stats->>'mana_color', 'verdant'))
        WHEN category = 'CREATURE' AND rarity = 'LEGENDARY' THEN 'legendary_creature_' || LOWER(COALESCE(base_stats->>'mana_color', 'obsidian'))
        WHEN category = 'STRUCTURE' AND rarity = 'COMMON' THEN 'common_structure_' || LOWER(COALESCE(base_stats->>'mana_color', 'crimson'))
        WHEN category = 'STRUCTURE' AND rarity = 'RARE' THEN 'rare_structure_' || LOWER(COALESCE(base_stats->>'mana_color', 'azure'))
        WHEN category = 'STRUCTURE' AND rarity = 'EPIC' THEN 'epic_structure_' || LOWER(COALESCE(base_stats->>'mana_color', 'verdant'))
        WHEN category = 'STRUCTURE' AND rarity = 'LEGENDARY' THEN 'legendary_structure_' || LOWER(COALESCE(base_stats->>'mana_color', 'obsidian'))
        WHEN category = 'ACTION' AND rarity = 'COMMON' THEN 'common_action_fast_' || LOWER(COALESCE(base_stats->>'mana_color', 'crimson'))
        WHEN category = 'ACTION' AND rarity = 'RARE' THEN 'rare_action_fast_' || LOWER(COALESCE(base_stats->>'mana_color', 'azure'))
        WHEN category = 'ACTION' AND rarity = 'EPIC' THEN 'epic_action_fast_' || LOWER(COALESCE(base_stats->>'mana_color', 'verdant'))
        ELSE 'common_creature_crimson'
    END,
    static_url = artwork_url,
    card_set_id = 'open_portal',
    action_speed = CASE 
        WHEN category = 'ACTION' THEN 'FAST'
        ELSE NULL
    END
WHERE frame_type IS NULL;

-- Create function to auto-assign frame types for new cards
CREATE OR REPLACE FUNCTION assign_frame_type()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.frame_type IS NULL THEN
        NEW.frame_type := CASE 
            WHEN NEW.category = 'CREATURE' AND NEW.rarity = 'COMMON' THEN 'common_creature_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'crimson'))
            WHEN NEW.category = 'CREATURE' AND NEW.rarity = 'RARE' THEN 'rare_creature_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'azure'))
            WHEN NEW.category = 'CREATURE' AND NEW.rarity = 'EPIC' THEN 'epic_creature_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'verdant'))
            WHEN NEW.category = 'CREATURE' AND NEW.rarity = 'LEGENDARY' THEN 'legendary_creature_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'obsidian'))
            WHEN NEW.category = 'STRUCTURE' THEN LOWER(NEW.rarity::text) || '_structure_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'neutral'))
            WHEN NEW.category IN ('ACTION', 'ACTION_FAST') THEN LOWER(NEW.rarity::text) || '_action_fast_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'neutral'))
            WHEN NEW.category = 'ACTION_SLOW' THEN LOWER(NEW.rarity::text) || '_action_slow_' || LOWER(COALESCE(NEW.base_stats->>'mana_color', 'neutral'))
            WHEN NEW.category = 'EQUIPMENT' THEN LOWER(NEW.rarity::text) || '_equipment_neutral'
            WHEN NEW.category = 'SPECIAL' THEN 'legendary_special_unique'
            ELSE 'common_creature_crimson'
        END;
    END IF;
    
    IF NEW.static_url IS NULL AND NEW.artwork_url IS NOT NULL THEN
        NEW.static_url := NEW.artwork_url;
    END IF;
    
    IF NEW.card_set_id IS NULL THEN
        NEW.card_set_id := 'open_portal';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-assignment
DROP TRIGGER IF EXISTS trigger_assign_frame_type ON card_catalog;
CREATE TRIGGER trigger_assign_frame_type
    BEFORE INSERT OR UPDATE ON card_catalog
    FOR EACH ROW
    EXECUTE FUNCTION assign_frame_type();

-- Add comments for documentation
COMMENT ON TABLE card_assets IS 'Stores multiple asset files (static, video, frames) for each card with different quality levels';
COMMENT ON TABLE frame_types IS 'Defines available frame types with their properties and file paths';
COMMENT ON TABLE card_generation_queue IS 'Queue system for batch card generation processing';
COMMENT ON COLUMN card_catalog.frame_type IS 'Frame style identifier for this card (e.g., rare_creature_azure)';
COMMENT ON COLUMN card_catalog.video_url IS 'URL to animated video background for this card';
COMMENT ON COLUMN card_catalog.static_url IS 'URL to static image version (fallback)';
COMMENT ON COLUMN card_catalog.has_animation IS 'Whether this card has animated video assets';
COMMENT ON COLUMN card_catalog.frame_data IS 'JSON data for frame customization and effects';

-- Create view for easy card asset management
CREATE OR REPLACE VIEW card_assets_summary AS
SELECT 
    cc.id,
    cc.name,
    cc.category,
    cc.rarity,
    cc.frame_type,
    cc.has_animation,
    COUNT(ca.id) as total_assets,
    COUNT(ca.id) FILTER (WHERE ca.asset_type = 'static') as static_assets,
    COUNT(ca.id) FILTER (WHERE ca.asset_type = 'video') as video_assets,
    COUNT(ca.id) FILTER (WHERE ca.asset_type = 'frame') as frame_assets,
    MAX(ca.created_at) as last_asset_created
FROM card_catalog cc
LEFT JOIN card_assets ca ON cc.id = ca.card_catalog_id
GROUP BY cc.id, cc.name, cc.category, cc.rarity, cc.frame_type, cc.has_animation;

COMMENT ON VIEW card_assets_summary IS 'Summary view showing asset counts for each card';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON card_assets TO deckport_api;
-- GRANT SELECT ON frame_types TO deckport_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON card_generation_queue TO deckport_api;

-- Migration completed successfully
SELECT 'Enhanced card schema migration completed successfully' as status;
