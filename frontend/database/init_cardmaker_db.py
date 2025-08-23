#!/usr/bin/env python3
"""
Initialize cardmaker database with proper schema
Ensures the SQLite database exists with all required tables
"""

import os
import sqlite3
from pathlib import Path

# Database schema (SQLite version)
SCHEMA_SQL = """
-- Deckport SQLite schema for card management

PRAGMA foreign_keys = ON;

-- Core cards table
CREATE TABLE IF NOT EXISTS cards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT NOT NULL,           -- CREATURE | STRUCTURE | ACTION | SPECIAL | EQUIPMENT
  rarity TEXT NOT NULL,             -- COMMON | RARE | EPIC | LEGENDARY
  legendary INTEGER NOT NULL DEFAULT 0, -- 0/1 boolean
  color_code TEXT NOT NULL,         -- CRIMSON|AZURE|VERDANT|OBSIDIAN|RADIANT|AETHER
  energy_cost INTEGER NOT NULL DEFAULT 0,
  equipment_slots INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Hero/Structure combat stats
CREATE TABLE IF NOT EXISTS card_stats (
  card_id INTEGER PRIMARY KEY,
  attack INTEGER NOT NULL DEFAULT 0,
  defense INTEGER NOT NULL DEFAULT 0,
  health INTEGER NOT NULL DEFAULT 0,
  base_energy_per_turn INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Mana cost per color (supports future multi-color)
CREATE TABLE IF NOT EXISTS card_mana_costs (
  card_id INTEGER NOT NULL,
  color_code TEXT NOT NULL,
  amount INTEGER NOT NULL,
  PRIMARY KEY (card_id, color_code),
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Card limits and charge rules (JSON stored as TEXT)
CREATE TABLE IF NOT EXISTS card_limits (
  card_id INTEGER PRIMARY KEY,
  max_uses_per_match INTEGER,
  charges_max INTEGER,
  charge_rule TEXT,  -- JSON
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Targeting flags
CREATE TABLE IF NOT EXISTS card_targeting (
  card_id INTEGER PRIMARY KEY,
  target_friendly INTEGER NOT NULL DEFAULT 0,
  target_enemy INTEGER NOT NULL DEFAULT 1,
  target_self INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Card effects (for complex cards)
CREATE TABLE IF NOT EXISTS card_effects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id INTEGER NOT NULL,
  trigger TEXT NOT NULL,  -- on_play, on_basic_attack, etc.
  speed TEXT NOT NULL DEFAULT 'SLOW',  -- FAST | SLOW
  order_index INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Effect conditions
CREATE TABLE IF NOT EXISTS card_effect_conditions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  effect_id INTEGER NOT NULL,
  condition_type TEXT NOT NULL,
  payload TEXT NOT NULL,  -- JSON
  FOREIGN KEY(effect_id) REFERENCES card_effects(id) ON DELETE CASCADE
);

-- Effect actions
CREATE TABLE IF NOT EXISTS card_effect_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  effect_id INTEGER NOT NULL,
  action_type TEXT NOT NULL,
  payload TEXT NOT NULL,  -- JSON
  order_index INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(effect_id) REFERENCES card_effects(id) ON DELETE CASCADE
);

-- Card abilities (including ultimates)
CREATE TABLE IF NOT EXISTS card_abilities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  is_ultimate INTEGER NOT NULL DEFAULT 0,
  charges_max INTEGER NOT NULL DEFAULT 1,
  charge_rule TEXT,  -- JSON
  trigger TEXT,
  speed TEXT NOT NULL DEFAULT 'FAST',
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Ability actions
CREATE TABLE IF NOT EXISTS card_ability_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ability_id INTEGER NOT NULL,
  action_type TEXT NOT NULL,
  payload TEXT NOT NULL,  -- JSON
  order_index INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(ability_id) REFERENCES card_abilities(id) ON DELETE CASCADE
);

-- Art generation tracking
CREATE TABLE IF NOT EXISTS card_art_generation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id INTEGER NOT NULL,
  prompt TEXT NOT NULL,
  comfyui_prompt_id TEXT,
  seed INTEGER,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending, generating, completed, failed
  created_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  error_message TEXT,
  FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_cards_rarity ON cards(rarity);
CREATE INDEX IF NOT EXISTS idx_cards_color ON cards(color_code);
CREATE INDEX IF NOT EXISTS idx_cards_created ON cards(created_at);
CREATE INDEX IF NOT EXISTS idx_art_generation_status ON card_art_generation(status);
"""


def init_database(db_path: str) -> bool:
    """
    Initialize the cardmaker database with required schema
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # Connect and create schema
        conn = sqlite3.connect(db_path)
        try:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            print(f"Database initialized successfully: {db_path}")
            return True
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False


def main():
    """Initialize the default cardmaker database"""
    default_db_path = "/home/jp/deckport.ai/cardmaker.ai/deckport.sqlite3"
    
    if init_database(default_db_path):
        print("✅ Cardmaker database ready for use")
    else:
        print("❌ Failed to initialize database")
        exit(1)


if __name__ == "__main__":
    main()
