-- Deckport PostgreSQL schema

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums
CREATE TYPE card_category AS ENUM ('CREATURE','STRUCTURE','ACTION','SPECIAL','EQUIPMENT');
CREATE TYPE mana_color AS ENUM ('CRIMSON','AZURE','VERDANT','OBSIDIAN','RADIANT','AETHER');
CREATE TYPE rarity AS ENUM ('COMMON','RARE','EPIC','LEGENDARY');
CREATE TYPE effect_trigger AS ENUM ('on_play','on_basic_attack','on_damage_taken','end_phase');
CREATE TYPE action_speed AS ENUM ('FAST','SLOW');

-- Core cards
CREATE TABLE cards (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug              TEXT UNIQUE NOT NULL,
  name              TEXT NOT NULL,
  category          card_category NOT NULL,
  rarity            rarity NOT NULL,
  legendary         BOOLEAN NOT NULL DEFAULT FALSE,
  colors            mana_color[] NOT NULL,
  energy_cost       INTEGER NOT NULL DEFAULT 0 CHECK (energy_cost >= 0),
  equipment_slots   INTEGER NOT NULL DEFAULT 0 CHECK (equipment_slots BETWEEN 0 AND 3),
  keywords          TEXT[] NOT NULL DEFAULT '{}',
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Hero/Structure combat stats
CREATE TABLE card_stats (
  card_id                 UUID PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
  attack                  INTEGER NOT NULL DEFAULT 0 CHECK (attack >= 0),
  defense                 INTEGER NOT NULL DEFAULT 0 CHECK (defense >= 0),
  health                  INTEGER NOT NULL DEFAULT 0 CHECK (health >= 0),
  base_energy_per_turn    INTEGER NOT NULL DEFAULT 0 CHECK (base_energy_per_turn >= 0)
);

-- Mana cost per color
CREATE TABLE card_mana_costs (
  card_id     UUID REFERENCES cards(id) ON DELETE CASCADE,
  color       mana_color NOT NULL,
  amount      INTEGER NOT NULL CHECK (amount >= 0),
  PRIMARY KEY (card_id, color)
);

-- Match limits and charge rules
CREATE TABLE card_limits (
  card_id              UUID PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
  max_uses_per_match   INTEGER CHECK (max_uses_per_match IS NULL OR max_uses_per_match >= 1),
  charges_max          INTEGER CHECK (charges_max IS NULL OR charges_max >= 0),
  charge_rule          JSONB,
  CHECK ( (charges_max IS NULL) = (charge_rule IS NULL) )
);

-- Targeting flags
CREATE TABLE card_targeting (
  card_id   UUID PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
  target_friendly  BOOLEAN NOT NULL DEFAULT FALSE,
  target_enemy     BOOLEAN NOT NULL DEFAULT TRUE,
  target_self      BOOLEAN NOT NULL DEFAULT FALSE
);

-- Effect headers
CREATE TABLE card_effects (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id      UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
  trigger      effect_trigger NOT NULL,
  speed        action_speed NOT NULL DEFAULT 'SLOW',
  order_index  INTEGER NOT NULL DEFAULT 0
);

-- Effect conditions
CREATE TABLE card_effect_conditions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effect_id       UUID NOT NULL REFERENCES card_effects(id) ON DELETE CASCADE,
  condition_type  TEXT NOT NULL,
  payload         JSONB NOT NULL
);

-- Effect actions
CREATE TABLE card_effect_actions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effect_id    UUID NOT NULL REFERENCES card_effects(id) ON DELETE CASCADE,
  action_type  TEXT NOT NULL,
  payload      JSONB NOT NULL,
  order_index  INTEGER NOT NULL DEFAULT 0
);

-- Abilities / Ultimates
CREATE TABLE card_abilities (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id      UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  is_ultimate  BOOLEAN NOT NULL DEFAULT FALSE,
  charges_max  INTEGER NOT NULL DEFAULT 1 CHECK (charges_max >= 0),
  charge_rule  JSONB,
  trigger      effect_trigger,
  speed        action_speed NOT NULL DEFAULT 'FAST'
);

CREATE TABLE card_ability_actions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ability_id     UUID NOT NULL REFERENCES card_abilities(id) ON DELETE CASCADE,
  action_type    TEXT NOT NULL,
  payload        JSONB NOT NULL,
  order_index    INTEGER NOT NULL DEFAULT 0
);

-- Arenas
CREATE TABLE arenas (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug         TEXT UNIQUE NOT NULL,
  name         TEXT NOT NULL,
  color        mana_color NOT NULL,
  passive      JSONB NOT NULL,
  objective    JSONB,
  hazard       JSONB,
  is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

-- Physical/NFC minting (optional)
CREATE TABLE card_mints (
  minted_id     TEXT PRIMARY KEY,
  card_id       UUID NOT NULL REFERENCES cards(id) ON DELETE RESTRICT,
  season        INTEGER NOT NULL,
  signature     BYTEA NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Helpful indexes
CREATE INDEX idx_cards_colors_gin ON cards USING GIN (colors);
CREATE INDEX idx_cards_keywords_gin ON cards USING GIN (keywords);
CREATE INDEX idx_effect_actions_type ON card_effect_actions (action_type);
CREATE INDEX idx_effect_conditions_type ON card_effect_conditions (condition_type);

