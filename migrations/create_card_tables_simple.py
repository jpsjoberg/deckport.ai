#!/usr/bin/env python3
"""
Simple migration script to create card template and NFC instance tables
Compatible with SQLAlchemy 1.4
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://deckport_app:N0D3-N0D3-N0D3#M0nk3y33@127.0.0.1:5432/deckport"
)

def create_card_tables():
    """Create card template and NFC instance tables"""
    
    engine = create_engine(DATABASE_URL)
    
    # SQL to create card template tables
    card_template_sql = """
    -- Card Sets (collections/expansions)
    CREATE TABLE IF NOT EXISTS card_sets (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        code VARCHAR(20) UNIQUE NOT NULL,
        description TEXT,
        release_date DATE,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Templates (raw card designs)
    CREATE TABLE IF NOT EXISTS card_templates (
        id SERIAL PRIMARY KEY,
        card_set_id INTEGER REFERENCES card_sets(id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        slug VARCHAR(120) UNIQUE NOT NULL,
        description TEXT,
        flavor_text TEXT,
        rarity VARCHAR(20) NOT NULL CHECK (rarity IN ('COMMON', 'RARE', 'EPIC', 'LEGENDARY')),
        category VARCHAR(30) NOT NULL CHECK (category IN ('CREATURE', 'STRUCTURE', 'ACTION', 'SPECIAL', 'EQUIPMENT')),
        color_code VARCHAR(20),
        art_prompt TEXT,
        art_style VARCHAR(50),
        is_published BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Template Stats
    CREATE TABLE IF NOT EXISTS card_template_stats (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES card_templates(id) ON DELETE CASCADE,
        attack INTEGER,
        defense INTEGER,
        health INTEGER,
        base_energy_per_turn INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Template Mana Costs
    CREATE TABLE IF NOT EXISTS card_template_mana_costs (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES card_templates(id) ON DELETE CASCADE,
        color_code VARCHAR(20) NOT NULL,
        amount INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Template Targeting
    CREATE TABLE IF NOT EXISTS card_template_targeting (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES card_templates(id) ON DELETE CASCADE,
        target_friendly BOOLEAN DEFAULT false,
        target_enemy BOOLEAN DEFAULT false,
        target_self BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Template Limits
    CREATE TABLE IF NOT EXISTS card_template_limits (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES card_templates(id) ON DELETE CASCADE,
        max_per_deck INTEGER,
        max_per_turn INTEGER,
        max_per_game INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Template Art Generation
    CREATE TABLE IF NOT EXISTS card_template_art_generation (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES card_templates(id) ON DELETE CASCADE,
        comfyui_workflow_id VARCHAR(100),
        generation_prompt TEXT,
        negative_prompt TEXT,
        art_style VARCHAR(50),
        seed INTEGER,
        generated_image_path VARCHAR(500),
        generation_metadata JSONB,
        generated_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    nfc_instance_sql = """
    -- NFC Card Instances (unique physical cards)
    CREATE TABLE IF NOT EXISTS nfc_card_instances (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES card_templates(id) ON DELETE RESTRICT,
        nfc_uid VARCHAR(32) UNIQUE NOT NULL,
        serial_number VARCHAR(50) UNIQUE,
        current_level INTEGER DEFAULT 1,
        current_xp INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'provisioned' CHECK (status IN ('provisioned', 'sold', 'activated', 'revoked')),
        owner_player_id INTEGER,
        activation_code_hash VARCHAR(255),
        provisioned_at TIMESTAMP WITH TIME ZONE,
        activated_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Evolution (tracking changes to NFC instances)
    CREATE TABLE IF NOT EXISTS card_evolutions (
        id SERIAL PRIMARY KEY,
        nfc_card_id INTEGER REFERENCES nfc_card_instances(id) ON DELETE CASCADE,
        evolution_type VARCHAR(30) NOT NULL,
        old_values JSONB,
        new_values JSONB,
        trigger_event VARCHAR(50),
        match_id INTEGER,
        evolved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Card Match Participation (tracking card usage in matches)
    CREATE TABLE IF NOT EXISTS card_match_participation (
        id SERIAL PRIMARY KEY,
        nfc_card_id INTEGER REFERENCES nfc_card_instances(id) ON DELETE CASCADE,
        match_id INTEGER,
        player_id INTEGER,
        times_played INTEGER DEFAULT 0,
        damage_dealt INTEGER DEFAULT 0,
        damage_taken INTEGER DEFAULT 0,
        abilities_used INTEGER DEFAULT 0,
        match_result VARCHAR(20),
        xp_gained INTEGER DEFAULT 0,
        participated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    index_sql = """
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_card_templates_set_id ON card_templates(card_set_id);
    CREATE INDEX IF NOT EXISTS idx_card_templates_rarity ON card_templates(rarity);
    CREATE INDEX IF NOT EXISTS idx_card_templates_category ON card_templates(category);
    CREATE INDEX IF NOT EXISTS idx_card_templates_published ON card_templates(is_published);
    
    CREATE INDEX IF NOT EXISTS idx_nfc_instances_template_id ON nfc_card_instances(template_id);
    CREATE INDEX IF NOT EXISTS idx_nfc_instances_owner ON nfc_card_instances(owner_player_id);
    CREATE INDEX IF NOT EXISTS idx_nfc_instances_status ON nfc_card_instances(status);
    
    CREATE INDEX IF NOT EXISTS idx_card_evolutions_nfc_card ON card_evolutions(nfc_card_id);
    CREATE INDEX IF NOT EXISTS idx_card_match_participation_nfc_card ON card_match_participation(nfc_card_id);
    CREATE INDEX IF NOT EXISTS idx_card_match_participation_match ON card_match_participation(match_id);
    """

    try:
        with engine.begin() as conn:
            print("Creating card template tables...")
            conn.execute(text(card_template_sql))
            
            print("Creating NFC instance tables...")
            conn.execute(text(nfc_instance_sql))
            
            print("Creating indexes...")
            conn.execute(text(index_sql))
            
            print("✅ Card system tables created successfully!")
            
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up card system tables...")
    success = create_card_tables()
    sys.exit(0 if success else 1)
