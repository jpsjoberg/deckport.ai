-- Simple video streaming tables creation (no triggers)

-- Create enum types
CREATE TYPE video_stream_type AS ENUM ('battle_stream', 'admin_surveillance', 'console_monitoring');
CREATE TYPE video_stream_status AS ENUM ('starting', 'active', 'paused', 'ended', 'failed');
CREATE TYPE video_call_participant_role AS ENUM ('player', 'admin', 'observer');

-- Create admins table if it doesn't exist
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert test admin
INSERT INTO admins (username, email, password_hash, is_super_admin)
SELECT 'admin', 'admin@deckport.ai', 'test_hash', true
WHERE NOT EXISTS (SELECT 1 FROM admins WHERE username = 'admin');

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
    stream_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

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

-- Create indexes
CREATE INDEX ix_video_streams_status ON video_streams(status);
CREATE INDEX ix_video_streams_type ON video_streams(stream_type);
CREATE INDEX ix_video_streams_created ON video_streams(created_at);
CREATE INDEX ix_video_stream_participants_stream ON video_stream_participants(stream_id);
CREATE INDEX ix_video_stream_participants_console ON video_stream_participants(console_id);
CREATE INDEX ix_video_stream_logs_stream ON video_stream_logs(stream_id);
CREATE INDEX ix_video_stream_logs_timestamp ON video_stream_logs(timestamp);
CREATE INDEX ix_video_stream_logs_event_type ON video_stream_logs(event_type);

-- Add video columns to arenas table
ALTER TABLE arenas ADD COLUMN IF NOT EXISTS video_background_url VARCHAR(500);
ALTER TABLE arenas ADD COLUMN IF NOT EXISTS video_battle_url VARCHAR(500);
ALTER TABLE arenas ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);
ALTER TABLE arenas ADD COLUMN IF NOT EXISTS battles_played INTEGER DEFAULT 0;
ALTER TABLE arenas ADD COLUMN IF NOT EXISTS average_rating FLOAT DEFAULT 0.0;

-- Update existing arenas with video URLs
UPDATE arenas SET 
    video_background_url = '/v1/arenas/' || id || '/video/background',
    video_battle_url = '/v1/arenas/' || id || '/video/battle',
    thumbnail_url = '/v1/arenas/' || id || '/thumbnail',
    battles_played = COALESCE(battles_played, 0),
    average_rating = COALESCE(average_rating, 0.0)
WHERE video_background_url IS NULL;

SELECT 'Video streaming tables created successfully!' as result;
