-- Deckport SQLite schema

PRAGMA foreign_keys = ON;

-- Core cards
CREATE TABLE IF NOT EXISTS cards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT NOT NULL,           -- CREATURE | STRUCTURE | ACTION
  rarity TEXT NOT NULL,             -- COMMON | RARE | EPIC | LEGENDARY
  legendary INTEGER NOT NULL DEFAULT 0, -- 0/1
  color_code TEXT NOT NULL,         -- CRIMSON|AZURE|VERDANT|OBSIDIAN|RADIANT|AETHER
  energy_cost INTEGER NOT NULL DEFAULT 0,
  equipment_slots INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Hero/Structure stats
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

-- Limits and charge rules (JSON stored as TEXT)
CREATE TABLE IF NOT EXISTS card_limits (
  card_id INTEGER PRIMARY KEY,
  max_uses_per_match INTEGER,
  charges_max INTEGER,
  charge_rule TEXT,
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

