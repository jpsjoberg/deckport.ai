-- Migration: Add CMS (Content Management System) tables
-- Date: 2024-12-15
-- Description: Add tables for news articles, videos, and content management

-- Create content status enum
CREATE TYPE content_status AS ENUM ('draft', 'published', 'archived', 'scheduled');

-- Create content type enum
CREATE TYPE content_type AS ENUM ('news', 'update', 'tournament', 'card_reveal', 'community', 'developer');

-- Create video type enum
CREATE TYPE video_type AS ENUM ('tutorial', 'gameplay', 'card_reveal', 'tournament', 'developer', 'community');

-- Create video platform enum
CREATE TYPE video_platform AS ENUM ('youtube', 'vimeo', 'twitch', 'direct');

-- Content categories table
CREATE TABLE content_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50), -- Font Awesome icon class
    parent_id INTEGER REFERENCES content_categories(id),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Content tags table
CREATE TABLE content_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- News articles table
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    excerpt TEXT,
    content TEXT NOT NULL,
    content_type content_type NOT NULL,
    featured_image_url VARCHAR(500),
    gallery_images JSONB,
    status content_status NOT NULL DEFAULT 'draft',
    is_featured BOOLEAN NOT NULL DEFAULT false,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    meta_title VARCHAR(200),
    meta_description VARCHAR(500),
    tags JSONB,
    published_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    view_count INTEGER NOT NULL DEFAULT 0,
    like_count INTEGER NOT NULL DEFAULT 0,
    share_count INTEGER NOT NULL DEFAULT 0,
    author_admin_id INTEGER NOT NULL REFERENCES admins(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    extra_data JSONB
);

-- Video content table
CREATE TABLE video_content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    video_type video_type NOT NULL,
    platform video_platform NOT NULL,
    video_url VARCHAR(500) NOT NULL,
    embed_code TEXT,
    thumbnail_url VARCHAR(500),
    duration_seconds INTEGER,
    status content_status NOT NULL DEFAULT 'draft',
    is_featured BOOLEAN NOT NULL DEFAULT false,
    is_trending BOOLEAN NOT NULL DEFAULT false,
    meta_title VARCHAR(200),
    meta_description VARCHAR(500),
    tags JSONB,
    published_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    view_count INTEGER NOT NULL DEFAULT 0,
    like_count INTEGER NOT NULL DEFAULT 0,
    share_count INTEGER NOT NULL DEFAULT 0,
    watch_time_seconds INTEGER NOT NULL DEFAULT 0,
    author_admin_id INTEGER NOT NULL REFERENCES admins(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    extra_data JSONB
);

-- Content views table for analytics
CREATE TABLE content_views (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES news_articles(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES video_content(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    ip_address VARCHAR(45) NOT NULL, -- IPv6 compatible
    user_agent TEXT,
    referrer VARCHAR(500),
    viewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER -- For videos
);

-- Create indexes for performance
CREATE INDEX ix_content_categories_parent ON content_categories(parent_id);
CREATE INDEX ix_news_articles_status ON news_articles(status);
CREATE INDEX ix_news_articles_type ON news_articles(content_type);
CREATE INDEX ix_news_articles_published ON news_articles(published_at);
CREATE INDEX ix_news_articles_featured ON news_articles(is_featured);
CREATE INDEX ix_video_content_status ON video_content(status);
CREATE INDEX ix_video_content_type ON video_content(video_type);
CREATE INDEX ix_video_content_platform ON video_content(platform);
CREATE INDEX ix_video_content_published ON video_content(published_at);
CREATE INDEX ix_video_content_featured ON video_content(is_featured);
CREATE INDEX ix_content_views_article ON content_views(article_id);
CREATE INDEX ix_content_views_video ON content_views(video_id);
CREATE INDEX ix_content_views_date ON content_views(viewed_at);
CREATE INDEX ix_content_views_ip ON content_views(ip_address);

-- Insert some sample data
INSERT INTO content_categories (name, slug, description, color, icon) VALUES
('News', 'news', 'General news and announcements', '#3B82F6', 'fas fa-newspaper'),
('Updates', 'updates', 'Game updates and patches', '#10B981', 'fas fa-download'),
('Tournaments', 'tournaments', 'Tournament announcements and results', '#F59E0B', 'fas fa-trophy'),
('Community', 'community', 'Community highlights and events', '#8B5CF6', 'fas fa-users');

INSERT INTO content_tags (name, slug, description, color) VALUES
('Breaking', 'breaking', 'Breaking news and urgent updates', '#EF4444'),
('Featured', 'featured', 'Featured content', '#3B82F6'),
('Beginner', 'beginner', 'Content for new players', '#10B981'),
('Advanced', 'advanced', 'Advanced strategies and tips', '#F59E0B'),
('Meta', 'meta', 'Meta game analysis', '#8B5CF6');

-- Insert sample news articles
INSERT INTO news_articles (
    title, slug, excerpt, content, content_type, status, is_featured, 
    featured_image_url, tags, published_at, author_admin_id
) VALUES
(
    'World Championship Tournament Announced',
    'world-championship-tournament-announced',
    'The biggest Deckport tournament yet is coming this spring with a $100,000 prize pool and exclusive card rewards.',
    'We are thrilled to announce the inaugural Deckport World Championship Tournament, scheduled for Spring 2025. This groundbreaking event will feature the largest prize pool in trading card game history, with $100,000 in total prizes and exclusive limited-edition cards for participants.

The tournament will be held both online and at select physical locations, allowing players from around the world to compete for the ultimate title. Registration opens January 1st, 2025, and will be limited to the first 1,000 qualified players.

Key details:
- Prize Pool: $100,000 total
- Registration: January 1st, 2025
- Tournament Dates: March 15-17, 2025
- Format: Swiss rounds followed by single elimination
- Exclusive rewards for all participants

Stay tuned for more details on qualification requirements and registration procedures.',
    'tournament',
    'published',
    true,
    'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&h=400&fit=crop&crop=center',
    '["tournament", "championship", "featured"]',
    NOW(),
    1
),
(
    'New Elemental Series Released',
    'new-elemental-series-released',
    'Discover the power of the elements with 50 new cards featuring stunning artwork and unique abilities.',
    'The highly anticipated Elemental Series is now available! This expansion introduces 50 new cards that harness the raw power of fire, water, earth, and air elements.

Each element brings unique mechanics:
- Fire: Burn effects and direct damage
- Water: Flow abilities and card draw
- Earth: Defensive barriers and resource generation  
- Air: Swift attacks and evasion mechanics

The series includes 5 new legendary cards, each representing a different elemental master. These cards feature revolutionary NFC technology that unlocks special animations and effects when played.

Available now in the shop as individual packs or the complete Elemental Master collection.',
    'card_reveal',
    'published',
    false,
    'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=200&fit=crop&crop=center',
    '["cards", "elemental", "new-release"]',
    NOW() - INTERVAL '3 days',
    1
),
(
    'Game Update 2.1 Now Live',
    'game-update-2-1-now-live',
    'Enhanced matchmaking, new arena modes, improved NFC card detection, and balance changes.',
    'Update 2.1 is now live across all platforms! This major update brings significant improvements to the core gameplay experience.

New Features:
- Enhanced matchmaking algorithm for fairer matches
- Two new arena modes: Blitz and Endurance
- Improved NFC card detection with 99.9% accuracy
- New spectator mode for tournaments
- Enhanced mobile interface

Balance Changes:
- Over 30 cards have received balance adjustments
- New synergy mechanics for elemental combinations
- Improved AI difficulty scaling

Bug Fixes:
- Fixed rare crash during card evolution
- Resolved connectivity issues on some devices
- Improved performance on older hardware

Download the update now to experience these improvements!',
    'update',
    'published',
    false,
    'https://images.unsplash.com/photo-1556438064-2d7646166914?w=300&h=200&fit=crop&crop=center',
    '["update", "patch", "improvements"]',
    NOW() - INTERVAL '5 days',
    1
);

-- Insert sample videos
INSERT INTO video_content (
    title, slug, description, video_type, platform, video_url, thumbnail_url,
    duration_seconds, status, is_featured, tags, published_at, author_admin_id
) VALUES
(
    'Complete Beginner''s Guide to Deckport',
    'complete-beginners-guide-to-deckport',
    'Learn everything you need to know to start playing Deckport. This comprehensive tutorial covers basic gameplay, card mechanics, deck building, and winning strategies.',
    'tutorial',
    'youtube',
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600&h=400&fit=crop&crop=center',
    754,
    'published',
    true,
    '["tutorial", "beginner", "guide"]',
    NOW() - INTERVAL '3 days',
    1
),
(
    'Legendary Card Reveal: Void Dragon',
    'legendary-card-reveal-void-dragon',
    'Discover the most powerful legendary card in the new Elemental series with unique void abilities.',
    'card_reveal',
    'youtube',
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?w=400&h=225&fit=crop&crop=center',
    342,
    'published',
    false,
    '["card-reveal", "legendary", "void-dragon"]',
    NOW() - INTERVAL '1 week',
    1
),
(
    'Championship Finals Highlights',
    'championship-finals-highlights',
    'The most intense matches from the recent championship tournament with expert commentary.',
    'tournament',
    'youtube',
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://images.unsplash.com/photo-1556438064-2d7646166914?w=400&h=225&fit=crop&crop=center',
    923,
    'published',
    false,
    '["tournament", "highlights", "championship"]',
    NOW() - INTERVAL '2 weeks',
    1
);

-- Add update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_content_categories_updated_at BEFORE UPDATE ON content_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_tags_updated_at BEFORE UPDATE ON content_tags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_news_articles_updated_at BEFORE UPDATE ON news_articles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_video_content_updated_at BEFORE UPDATE ON video_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
