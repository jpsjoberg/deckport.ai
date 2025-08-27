-- Migration to add missing columns for real data implementation
-- Run this to update the database schema

-- Add missing columns to admins table
ALTER TABLE admins ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'admin' NOT NULL;

-- Add missing columns to players table
ALTER TABLE players ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active' NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS ban_expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS ban_reason VARCHAR(200);
ALTER TABLE players ADD COLUMN IF NOT EXISTS warning_count INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS last_warning_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(45);
ALTER TABLE players ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS last_failed_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP WITH TIME ZONE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS profile_completion_score INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE NOT NULL;
ALTER TABLE players ADD COLUMN IF NOT EXISTS privacy_settings JSONB;

-- Update existing players to have default values
UPDATE players SET 
    status = 'active',
    is_verified = TRUE,
    is_premium = FALSE,
    is_banned = FALSE,
    warning_count = 0,
    login_count = 0,
    failed_login_attempts = 0,
    profile_completion_score = 50,
    email_notifications = TRUE
WHERE status IS NULL;

-- Update existing admins to have default role
UPDATE admins SET role = 'admin' WHERE role IS NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_players_status ON players(status);
CREATE INDEX IF NOT EXISTS ix_players_is_banned ON players(is_banned);
CREATE INDEX IF NOT EXISTS ix_players_last_login ON players(last_login_at);
CREATE INDEX IF NOT EXISTS ix_admins_role ON admins(role);

COMMIT;
