-- Add featured products with images for the landing page

-- Update existing products to be featured and add images
UPDATE shop_products 
SET 
    is_featured = TRUE,
    image_url = 'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400&h=300&fit=crop&crop=center',
    short_description = 'Perfect starter bundle for new players with 20 NFC-enabled cards',
    gallery_images = '["https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"]',
    tags = '["starter", "beginner", "nfc", "bundle"]',
    meta_title = 'Starter Bundle - Perfect for New Players',
    meta_description = 'Get started with Portal One with this comprehensive starter bundle containing 20 NFC-enabled cards.'
WHERE sku = 'BUNDLE-STARTER';

UPDATE shop_products 
SET 
    is_featured = TRUE,
    image_url = 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop&crop=center',
    short_description = 'Radiant-themed premium bundle with rare and epic cards',
    gallery_images = '["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]',
    tags = '["radiant", "premium", "rare", "epic"]',
    meta_title = 'Radiant Bundle - Premium Card Collection',
    meta_description = 'Discover powerful radiant-themed cards with enhanced abilities and stunning artwork.'
WHERE sku = 'BUNDLE-RADIANT';

-- Add more featured products if they don't exist
INSERT INTO shop_products (
    sku, name, slug, description, short_description, price, currency, 
    product_type, stock_quantity, image_url, gallery_images, 
    is_featured, is_active, status, tags, meta_title, meta_description,
    created_at, updated_at
) VALUES 
(
    'BUNDLE-CHAMPION', 'Champion Bundle', 'champion-bundle',
    'The ultimate collection for competitive players. Contains 30 NFC-enabled cards including legendary and mythic rarities, plus exclusive champion accessories.',
    'Ultimate competitive bundle with 30 cards including legendaries',
    89.99, 'USD', 'bundle', 50,
    'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400&h=300&fit=crop&crop=faces',
    '["https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop"]',
    TRUE, TRUE, 'active',
    '["champion", "competitive", "legendary", "mythic", "premium"]',
    'Champion Bundle - Ultimate Competitive Collection',
    'Dominate the competition with legendary and mythic cards in this premium champion bundle.',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
),
(
    'PACK-BOOSTER', 'Booster Pack', 'booster-pack',
    'Expand your collection with this booster pack containing 5 random NFC-enabled cards. Each pack guarantees at least one rare card.',
    'Random booster pack with 5 NFC cards, guaranteed rare',
    12.99, 'USD', 'booster_pack', 200,
    'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop&crop=entropy',
    '["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]',
    TRUE, TRUE, 'active',
    '["booster", "random", "rare", "expansion"]',
    'Booster Pack - Expand Your Collection',
    'Get 5 random NFC-enabled cards with guaranteed rare in every booster pack.',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
),
(
    'DECK-ELEMENTAL', 'Elemental Deck', 'elemental-deck',
    'Pre-constructed competitive deck focused on elemental magic. Contains 40 NFC-enabled cards optimized for tournament play.',
    'Pre-built competitive elemental deck with 40 cards',
    59.99, 'USD', 'starter_deck', 75,
    'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300&fit=crop&crop=center',
    '["https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"]',
    TRUE, TRUE, 'active',
    '["elemental", "deck", "competitive", "tournament", "magic"]',
    'Elemental Deck - Tournament Ready',
    'Master the elements with this tournament-optimized deck featuring powerful elemental magic cards.',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
),
(
    'ACCESSORY-PLAYMAT', 'Premium Playmat', 'premium-playmat',
    'Official Portal One playmat with NFC reading zones and premium artwork. Essential for competitive play.',
    'Official playmat with NFC zones and premium artwork',
    29.99, 'USD', 'accessory', 100,
    'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400&h=300&fit=crop&crop=top',
    '["https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]',
    FALSE, TRUE, 'active',
    '["playmat", "accessory", "nfc", "competitive", "official"]',
    'Premium Playmat - Official Tournament Mat',
    'Enhance your gameplay with the official Portal One playmat featuring NFC reading zones.',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
)
ON CONFLICT (sku) DO NOTHING;

-- Update published dates for featured products
UPDATE shop_products 
SET published_at = CURRENT_TIMESTAMP 
WHERE is_featured = TRUE AND published_at IS NULL;
