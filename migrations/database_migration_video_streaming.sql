-- Database Migration: Video Streaming System
-- Run this to add video streaming tables to your existing database

-- Add new enum types
CREATE TYPE video_stream_type AS ENUM ('battle_stream', 'admin_surveillance', 'console_monitoring');
CREATE TYPE video_stream_status AS ENUM ('starting', 'active', 'paused', 'ended', 'failed');
CREATE TYPE video_call_participant_role AS ENUM ('player', 'admin', 'observer');

-- Add new arena enum types
CREATE TYPE arena_theme AS ENUM ('nature', 'crystal', 'shadow', 'divine', 'fire', 'ice', 'tech', 'cosmic', 'underwater', 'desert');
CREATE TYPE arena_rarity AS ENUM ('common', 'uncommon', 'rare', 'epic', 'legendary');

-- Create arenas table
CREATE TABLE arenas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    theme arena_theme,
    rarity arena_rarity DEFAULT 'common',
    difficulty INTEGER DEFAULT 1 NOT NULL CHECK (difficulty >= 1 AND difficulty <= 10),
    video_background_url VARCHAR(500),
    video_battle_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    battles_played INTEGER DEFAULT 0,
    average_rating FLOAT DEFAULT 0.0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for arenas
CREATE INDEX ix_arenas_theme ON arenas(theme);
CREATE INDEX ix_arenas_rarity ON arenas(rarity);
CREATE INDEX ix_arenas_difficulty ON arenas(difficulty);

-- Create video_streams table
CREATE TABLE video_streams (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(64) UNIQUE NOT NULL,
    stream_type video_stream_type NOT NULL,
    status video_stream_status DEFAULT 'starting' NOT NULL,
    title VARCHAR(200),
    description TEXT,
    is_recording BOOLEAN DEFAULT FALSE NOT NULL,
    recording_path VARCHAR(500),
    stream_url VARCHAR(500),
    rtmp_key VARCHAR(100),
    quality_settings JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    initiated_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    security_flags JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for video_streams
CREATE INDEX ix_video_streams_status ON video_streams(status);
CREATE INDEX ix_video_streams_type ON video_streams(stream_type);
CREATE INDEX ix_video_streams_created ON video_streams(created_at);

-- Create video_stream_participants table
CREATE TABLE video_stream_participants (
    id SERIAL PRIMARY KEY,
    stream_id INTEGER REFERENCES video_streams(id) ON DELETE CASCADE NOT NULL,
    console_id INTEGER REFERENCES consoles(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    role video_call_participant_role NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    left_at TIMESTAMP WITH TIME ZONE,
    is_camera_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    is_screen_sharing BOOLEAN DEFAULT FALSE NOT NULL,
    is_audio_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    connection_quality VARCHAR(20),
    bandwidth_usage_mb FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for video_stream_participants
CREATE INDEX ix_video_stream_participants_stream ON video_stream_participants(stream_id);
CREATE INDEX ix_video_stream_participants_console ON video_stream_participants(console_id);

-- Create video_stream_logs table
CREATE TABLE video_stream_logs (
    id SERIAL PRIMARY KEY,
    stream_id INTEGER REFERENCES video_streams(id) ON DELETE CASCADE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' NOT NULL,
    participant_id INTEGER REFERENCES video_stream_participants(id) ON DELETE SET NULL,
    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    technical_data JSONB,
    security_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for video_stream_logs
CREATE INDEX ix_video_stream_logs_stream ON video_stream_logs(stream_id);
CREATE INDEX ix_video_stream_logs_timestamp ON video_stream_logs(timestamp);
CREATE INDEX ix_video_stream_logs_event_type ON video_stream_logs(event_type);

-- Insert sample arenas for testing
INSERT INTO arenas (name, description, theme, rarity, difficulty, metadata) VALUES
('Mystic Forest Arena', 'Ancient trees shrouded in magical mists', 'nature', 'common', 3, '{"environment": "forest", "weather": "misty"}'),
('Crystal Caverns', 'Glowing crystals illuminate underground chambers', 'crystal', 'uncommon', 5, '{"environment": "underground", "lighting": "crystal"}'),
('Shadow Realm Portal', 'Ethereal landscapes of shadow and void', 'shadow', 'rare', 7, '{"environment": "void", "danger_level": "high"}'),
('Celestial Temple', 'Sacred architecture bathed in heavenly light', 'divine', 'epic', 8, '{"environment": "temple", "blessing": "active"}'),
('Volcanic Forge', 'Molten lava flows through industrial forges', 'fire', 'legendary', 9, '{"environment": "volcanic", "temperature": "extreme"}'),
('Frozen Citadel', 'Ice-covered fortress in eternal winter', 'ice', 'rare', 6, '{"environment": "ice", "temperature": "freezing"}'),
('Cyber Grid Arena', 'Digital battleground with neon circuits', 'tech', 'epic', 8, '{"environment": "digital", "tech_level": "advanced"}'),
('Cosmic Observatory', 'Floating platform among the stars', 'cosmic', 'legendary', 10, '{"environment": "space", "gravity": "low"}'),
('Abyssal Depths', 'Underwater arena with bioluminescent creatures', 'underwater', 'uncommon', 4, '{"environment": "underwater", "pressure": "high"}'),
('Desert Oasis', 'Ancient ruins in endless sand dunes', 'desert', 'common', 2, '{"environment": "desert", "water_source": "oasis"}');

-- Create directories for video storage (these would need to be created on the file system)
-- mkdir -p arena_videos/
-- mkdir -p arena_thumbnails/
-- mkdir -p battle_recordings/
-- mkdir -p surveillance_recordings/

-- Update function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_arenas_updated_at BEFORE UPDATE ON arenas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_video_streams_updated_at BEFORE UPDATE ON video_streams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON arenas TO deckport_app;
-- GRANT ALL PRIVILEGES ON video_streams TO deckport_app;
-- GRANT ALL PRIVILEGES ON video_stream_participants TO deckport_app;
-- GRANT ALL PRIVILEGES ON video_stream_logs TO deckport_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO deckport_app;

COMMIT;
