#!/usr/bin/env python3
"""
Populate Arena Database
Creates sample arena data and missing database tables
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal, engine
from shared.models.base import Base, MMQueue
from shared.models.arena import Arena
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all missing database tables"""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False
    return True

def populate_arenas():
    """Populate database with sample arena data"""
    logger.info("Populating arena data...")
    
    sample_arenas = [
        {
            'name': 'Sunspire Plateau',
            'mana_color': 'RADIANT',
            'passive_effect': {
                'name': 'First Match Discount',
                'description': 'First card played each turn costs 1 less mana',
                'type': 'mana_discount'
            },
            'objective': {
                'name': 'Solar Convergence',
                'description': 'Deal 5 damage in a single turn to gain +2 mana next turn',
                'reward': 'mana_bonus'
            },
            'hazard': {
                'name': 'Blinding Light',
                'description': 'Every 3rd turn, all creatures have -1 attack',
                'trigger': 'turn_multiple',
                'effect': 'attack_reduction'
            },
            'story_text': 'High above the clouds, where the sun never sets, ancient spires pierce the sky. This sacred ground has witnessed countless battles between light and shadow.',
            'flavor_text': 'Where light touches stone, legends are born.',
            'background_music': 'sunspire_ambient.ogg',
            'ambient_sounds': 'wind_chimes.ogg',
            'special_rules': {
                'starting_mana': 3,
                'mana_generation_bonus': 1
            },
            'difficulty_rating': 2
        },
        {
            'name': 'Crimson Foundry',
            'mana_color': 'CRIMSON',
            'passive_effect': {
                'name': 'Forge Heat',
                'description': 'Equipment cards cost 1 less mana to play',
                'type': 'equipment_discount'
            },
            'objective': {
                'name': 'Master Smith',
                'description': 'Equip 3 different equipment to gain +1 card draw',
                'reward': 'card_draw'
            },
            'hazard': {
                'name': 'Molten Overflow',
                'description': 'Every 4th turn, deal 1 damage to all creatures',
                'trigger': 'turn_multiple',
                'effect': 'area_damage'
            },
            'story_text': 'Deep beneath the mountains, where fire meets metal, the greatest weapons are forged. The heat here shapes both steel and destiny.',
            'flavor_text': 'In fire, we find strength. In strength, we find victory.',
            'background_music': 'foundry_ambient.ogg',
            'ambient_sounds': 'forge_hammering.ogg',
            'special_rules': {
                'equipment_bonus': True,
                'fire_immunity': True
            },
            'difficulty_rating': 3
        },
        {
            'name': 'Azure Depths',
            'mana_color': 'AZURE',
            'passive_effect': {
                'name': 'Tidal Knowledge',
                'description': 'Draw an extra card at the start of each turn',
                'type': 'card_draw'
            },
            'objective': {
                'name': 'Deep Currents',
                'description': 'Have 7+ cards in hand to gain spell power +1',
                'reward': 'spell_power'
            },
            'hazard': {
                'name': 'Crushing Depths',
                'description': 'Players with 8+ cards in hand take 1 damage',
                'trigger': 'hand_size',
                'effect': 'hand_limit_damage'
            },
            'story_text': 'Beneath the endless ocean, where pressure creates diamonds and wisdom flows like water, ancient secrets wait to be discovered.',
            'flavor_text': 'The deeper you dive, the greater the treasures you find.',
            'background_music': 'depths_ambient.ogg',
            'ambient_sounds': 'underwater_currents.ogg',
            'special_rules': {
                'extra_card_draw': 1,
                'spell_power_bonus': True
            },
            'difficulty_rating': 4
        },
        {
            'name': 'Verdant Grove',
            'mana_color': 'VERDANT',
            'passive_effect': {
                'name': 'Natural Growth',
                'description': 'Creatures gain +1/+1 when played',
                'type': 'creature_buff'
            },
            'objective': {
                'name': 'Circle of Life',
                'description': 'Control 4+ creatures to heal 2 health',
                'reward': 'healing'
            },
            'hazard': {
                'name': 'Overgrowth',
                'description': 'Players with 5+ creatures lose 1 mana per turn',
                'trigger': 'creature_count',
                'effect': 'mana_drain'
            },
            'story_text': 'In the heart of the ancient forest, where life flows eternal and every leaf tells a story, nature reigns supreme.',
            'flavor_text': 'Life finds a way, always.',
            'background_music': 'grove_ambient.ogg',
            'ambient_sounds': 'forest_sounds.ogg',
            'special_rules': {
                'creature_buff': True,
                'healing_bonus': 2
            },
            'difficulty_rating': 2
        },
        {
            'name': 'Obsidian Citadel',
            'mana_color': 'OBSIDIAN',
            'passive_effect': {
                'name': 'Dark Mastery',
                'description': 'Destroyed creatures return to hand instead of graveyard',
                'type': 'creature_recursion'
            },
            'objective': {
                'name': 'Shadow Lord',
                'description': 'Destroy 3 enemy creatures to gain +2 mana permanently',
                'reward': 'permanent_mana'
            },
            'hazard': {
                'name': 'Soul Drain',
                'description': 'Each creature destroyed drains 1 health from its owner',
                'trigger': 'creature_death',
                'effect': 'life_drain'
            },
            'story_text': 'Within walls of black glass, where shadows dance and whispers echo, power comes to those who embrace the darkness.',
            'flavor_text': 'In darkness, we find truth. In truth, we find power.',
            'background_music': 'citadel_ambient.ogg',
            'ambient_sounds': 'dark_whispers.ogg',
            'special_rules': {
                'creature_recursion': True,
                'shadow_bonus': True
            },
            'difficulty_rating': 5
        }
    ]
    
    try:
        with SessionLocal() as session:
            # Check if arenas already exist
            existing_count = session.query(Arena).count()
            if existing_count > 0:
                logger.info(f"⚠️ {existing_count} arenas already exist, skipping population")
                return True
            
            # Create arenas
            for arena_data in sample_arenas:
                arena = Arena(
                    name=arena_data['name'],
                    mana_color=arena_data['mana_color'],
                    passive_effect=arena_data['passive_effect'],
                    objective=arena_data['objective'],
                    hazard=arena_data['hazard'],
                    story_text=arena_data['story_text'],
                    flavor_text=arena_data['flavor_text'],
                    background_music=arena_data['background_music'],
                    ambient_sounds=arena_data['ambient_sounds'],
                    special_rules=arena_data['special_rules'],
                    difficulty_rating=arena_data['difficulty_rating'],
                    created_at=datetime.now(timezone.utc)
                )
                session.add(arena)
                logger.info(f"✅ Created arena: {arena_data['name']}")
            
            session.commit()
            logger.info(f"✅ Successfully created {len(sample_arenas)} arenas")
            
    except Exception as e:
        logger.error(f"❌ Error populating arenas: {e}")
        return False
    
    return True

def add_console_arena_column():
    """Add current_arena_id column to consoles table if it doesn't exist"""
    logger.info("Adding current_arena_id column to consoles table...")
    
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'consoles' AND column_name = 'current_arena_id'
            """))
            
            if result.fetchone() is None:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE consoles 
                    ADD COLUMN current_arena_id INTEGER REFERENCES arenas(id) ON DELETE SET NULL
                """))
                conn.commit()
                logger.info("✅ Added current_arena_id column to consoles table")
            else:
                logger.info("⚠️ current_arena_id column already exists")
                
    except Exception as e:
        logger.error(f"❌ Error adding column: {e}")
        return False
    
    return True

def main():
    """Main function to set up arena system"""
    logger.info("🏔️ Setting up Arena System")
    logger.info("=" * 50)
    
    # Step 1: Create all tables
    if not create_tables():
        logger.error("Failed to create tables")
        return False
    
    # Step 2: Add console arena column
    if not add_console_arena_column():
        logger.error("Failed to add console arena column")
        return False
    
    # Step 3: Populate arenas
    if not populate_arenas():
        logger.error("Failed to populate arenas")
        return False
    
    logger.info("🎉 Arena system setup complete!")
    logger.info("=" * 50)
    
    # Show summary
    try:
        with SessionLocal() as session:
            arena_count = session.query(Arena).count()
            logger.info(f"📊 Total arenas in database: {arena_count}")
            
            for arena in session.query(Arena).all():
                logger.info(f"   🏔️ {arena.name} ({arena.mana_color}) - Difficulty: {arena.difficulty_rating}/5")
    
    except Exception as e:
        logger.error(f"Error showing summary: {e}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
