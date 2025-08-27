-- Update product images with better card game themed images

-- Update existing products with better images
UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400&h=300&fit=crop&crop=center',
    gallery_images = '["https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop"]'
WHERE sku = 'BUNDLE-STARTER';

UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop&crop=center',
    gallery_images = '["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]'
WHERE sku = 'BUNDLE-RADIANT';

UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300&fit=crop&crop=center',
    gallery_images = '["https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"]'
WHERE sku = 'BUNDLE-CHAMPION';

UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop&crop=entropy',
    gallery_images = '["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]'
WHERE sku = 'PACK-BOOSTER';

UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300&fit=crop&crop=faces',
    gallery_images = '["https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop", "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"]'
WHERE sku = 'DECK-ELEMENTAL';

UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400&h=300&fit=crop&crop=top',
    gallery_images = '["https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]'
WHERE sku = 'ACCESSORY-PLAYMAT';

-- Update any existing products that don't have images
UPDATE shop_products 
SET 
    image_url = 'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=400&h=300&fit=crop&crop=center',
    gallery_images = '["https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=800&h=600&fit=crop"]'
WHERE image_url IS NULL AND is_featured = TRUE;
