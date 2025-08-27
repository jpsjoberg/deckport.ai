-- Sample Shop Data for Testing
-- Adds sample products and categories for the shop system

-- Insert sample categories
INSERT INTO shop_categories (name, slug, description, sort_order, is_active) VALUES
('Card Bundles', 'card-bundles', 'Pre-made collections of cards', 1, TRUE),
('Starter Decks', 'starter-decks', 'Complete decks for new players', 2, TRUE),
('Booster Packs', 'booster-packs', 'Random card packs', 3, TRUE),
('Accessories', 'accessories', 'Card sleeves, playmats, and more', 4, TRUE)
ON CONFLICT (slug) DO NOTHING;

-- Insert sample products
INSERT INTO shop_products (
    sku, name, slug, description, price, currency, product_type, 
    category_id, stock_quantity, is_featured, is_active, status,
    image_url, card_skus, tags
) VALUES
(
    'BUNDLE-STARTER',
    'Starter Bundle',
    'starter-bundle',
    'Perfect for new players! Contains 20 carefully selected cards including creatures, actions, and equipment to get you started.',
    49.99,
    'USD',
    'bundle',
    (SELECT id FROM shop_categories WHERE slug = 'card-bundles'),
    50,
    TRUE,
    TRUE,
    'active',
    'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400',
    '["RADIANT-001", "RADIANT-002", "SHADOW-001", "NATURE-001", "TECH-001"]'::jsonb,
    '["starter", "beginner", "bundle"]'::jsonb
),
(
    'BUNDLE-RADIANT',
    'Radiant Bundle',
    'radiant-bundle',
    'Harness the power of light! This bundle contains 15 Radiant-themed cards with powerful light-based abilities.',
    39.99,
    'USD',
    'bundle',
    (SELECT id FROM shop_categories WHERE slug = 'card-bundles'),
    25,
    TRUE,
    TRUE,
    'active',
    'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400',
    '["RADIANT-001", "RADIANT-002", "RADIANT-003", "RADIANT-004", "RADIANT-005"]'::jsonb,
    '["radiant", "light", "bundle"]'::jsonb
),
(
    'DECK-SHADOW',
    'Shadow Starter Deck',
    'shadow-starter-deck',
    'Master the darkness with this complete 40-card Shadow deck. Includes powerful shadow creatures and dark magic.',
    34.99,
    'USD',
    'starter_deck',
    (SELECT id FROM shop_categories WHERE slug = 'starter-decks'),
    30,
    FALSE,
    TRUE,
    'active',
    'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400',
    '["SHADOW-001", "SHADOW-002", "SHADOW-003", "SHADOW-004"]'::jsonb,
    '["shadow", "dark", "starter", "deck"]'::jsonb
),
(
    'PACK-BOOSTER-CORE',
    'Core Set Booster Pack',
    'core-set-booster-pack',
    'Contains 15 random cards from the Core Set. Guaranteed at least 1 rare or better!',
    12.99,
    'USD',
    'booster_pack',
    (SELECT id FROM shop_categories WHERE slug = 'booster-packs'),
    100,
    FALSE,
    TRUE,
    'active',
    'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400',
    '[]'::jsonb,
    '["booster", "random", "core"]'::jsonb
),
(
    'ACC-PLAYMAT-RADIANT',
    'Radiant Playmat',
    'radiant-playmat',
    'Premium playmat featuring stunning Radiant artwork. Perfect for tournament play.',
    24.99,
    'USD',
    'accessory',
    (SELECT id FROM shop_categories WHERE slug = 'accessories'),
    15,
    FALSE,
    TRUE,
    'active',
    'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400',
    '[]'::jsonb,
    '["playmat", "accessory", "radiant"]'::jsonb
);

-- Update timestamps
UPDATE shop_products SET 
    created_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE sku IN ('BUNDLE-STARTER', 'BUNDLE-RADIANT', 'DECK-SHADOW', 'PACK-BOOSTER-CORE', 'ACC-PLAYMAT-RADIANT');
