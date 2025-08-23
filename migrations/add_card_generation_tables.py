#!/usr/bin/env python3
"""
Database migration to add card generation tables to PostgreSQL
Run this to add the AI card generation system to your existing database
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from sqlalchemy import create_engine
from shared.database.connection import DATABASE_URL, engine
from shared.models.card_generation import Base as CardGenerationBase
from shared.models.base import Base

def create_card_generation_tables():
    """Create all card generation tables"""
    print("🔄 Creating card generation tables in PostgreSQL...")
    
    try:
        # Import all models to ensure they're registered
        from shared.models.card_generation import (
            GeneratedCard, GeneratedCardStats, GeneratedCardManaCost,
            GeneratedCardTargeting, GeneratedCardLimits, GeneratedCardEffect,
            GeneratedCardEffectCondition, GeneratedCardEffectAction,
            GeneratedCardAbility, GeneratedCardAbilityAction, CardArtGeneration
        )
        
        # Create tables
        CardGenerationBase.metadata.create_all(bind=engine)
        
        print("✅ Card generation tables created successfully!")
        print("\nCreated tables:")
        print("- generated_cards")
        print("- generated_card_stats") 
        print("- generated_card_mana_costs")
        print("- generated_card_targeting")
        print("- generated_card_limits")
        print("- generated_card_effects")
        print("- generated_card_effect_conditions")
        print("- generated_card_effect_actions")
        print("- generated_card_abilities")
        print("- generated_card_ability_actions")
        print("- card_art_generations")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def verify_tables():
    """Verify that tables were created successfully"""
    print("\n🔍 Verifying table creation...")
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        expected_tables = [
            'generated_cards',
            'generated_card_stats',
            'generated_card_mana_costs',
            'generated_card_targeting',
            'generated_card_limits',
            'generated_card_effects',
            'generated_card_effect_conditions',
            'generated_card_effect_actions',
            'generated_card_abilities',
            'generated_card_ability_actions',
            'card_art_generations'
        ]
        
        existing_tables = inspector.get_table_names()
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                print(f"✅ {table}")
            else:
                print(f"❌ {table} - MISSING")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️  Missing tables: {missing_tables}")
            return False
        else:
            print("\n🎉 All card generation tables verified successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Run the migration"""
    print("🚀 Card Generation Database Migration")
    print("=" * 50)
    print(f"Database: {DATABASE_URL}")
    print()
    
    # Create tables
    if not create_card_generation_tables():
        print("Migration failed!")
        return 1
    
    # Verify tables
    if not verify_tables():
        print("Verification failed!")
        return 1
    
    print("\n🎯 Migration completed successfully!")
    print("Your PostgreSQL database is now ready for AI card generation.")
    
    return 0

if __name__ == "__main__":
    exit(main())

