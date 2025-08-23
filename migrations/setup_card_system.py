#!/usr/bin/env python3
"""
Complete Card System Migration
Sets up the two-tier card system: Templates (raw cards) + NFC Instances (unique cards)
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from sqlalchemy import create_engine, text
from shared.database.connection import DATABASE_URL, engine
from shared.models.base import Base

def create_card_system_tables():
    """Create all card system tables"""
    print("🔄 Setting up complete card system in PostgreSQL...")
    print(f"Database: {DATABASE_URL}")
    
    try:
        # Import all models to ensure they're registered
        from shared.models.card_templates import (
            CardSet, CardTemplate, CardTemplateStats, CardTemplateManaCost,
            CardTemplateTargeting, CardTemplateLimits, CardTemplateEffect,
            CardTemplateEffectCondition, CardTemplateEffectAction,
            CardTemplateAbility, CardTemplateAbilityAction, CardTemplateArtGeneration
        )
        
        from shared.models.nfc_card_instances import (
            NFCCardInstance, CardEvolution, CardMatchParticipation, CardFusion
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Card system tables created successfully!")
        
        # Create a default card set
        from shared.database.connection import SessionLocal
        db = SessionLocal()
        try:
            # Check if default set exists
            existing_set = db.execute(text("SELECT id FROM card_sets WHERE slug = 'open-portal'")).fetchone()
            
            if not existing_set:
                # Create default card set
                db.execute(text("""
                    INSERT INTO card_sets (slug, name, description, version, created_by_admin)
                    VALUES ('open-portal', 'Open Portal', 'The inaugural card set for Deckport', '1.0', 'system')
                """))
                db.commit()
                print("✅ Created default 'Open Portal' card set")
            else:
                print("✅ Default card set already exists")
                
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_table_structure():
    """Verify the table structure and relationships"""
    print("\n🔍 Verifying table structure...")
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        # Expected tables for the card system
        template_tables = [
            'card_sets',
            'card_templates', 
            'card_template_stats',
            'card_template_mana_costs',
            'card_template_targeting',
            'card_template_limits',
            'card_template_effects',
            'card_template_effect_conditions',
            'card_template_effect_actions',
            'card_template_abilities',
            'card_template_ability_actions',
            'card_template_art_generations'
        ]
        
        instance_tables = [
            'nfc_card_instances',
            'card_evolutions',
            'card_match_participations',
            'card_fusions'
        ]
        
        all_tables = template_tables + instance_tables
        existing_tables = inspector.get_table_names()
        
        print("\n📋 Template System Tables:")
        for table in template_tables:
            if table in existing_tables:
                print(f"✅ {table}")
            else:
                print(f"❌ {table} - MISSING")
        
        print("\n📋 NFC Instance Tables:")
        for table in instance_tables:
            if table in existing_tables:
                print(f"✅ {table}")
            else:
                print(f"❌ {table} - MISSING")
        
        missing_tables = [t for t in all_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"\n⚠️  Missing tables: {missing_tables}")
            return False
        else:
            print("\n🎉 All card system tables verified successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def show_architecture_summary():
    """Show the complete card system architecture"""
    print("\n" + "=" * 60)
    print("🏗️  CARD SYSTEM ARCHITECTURE")
    print("=" * 60)
    print("""
📚 CARD TEMPLATES (Raw Card Designs)
├── card_sets                     → Card collections (e.g., "Open Portal")
├── card_templates                → Base card designs (AI-generated)
├── card_template_stats           → Base combat stats
├── card_template_mana_costs      → Mana requirements
├── card_template_art_generations → ComfyUI generation history
└── card_template_*               → Effects, abilities, targeting, limits

🎴 NFC CARD INSTANCES (Unique Physical Cards)  
├── nfc_card_instances           → Unique physical cards (can evolve)
├── card_evolutions              → Evolution history and changes
├── card_match_participations    → Match performance tracking
└── card_fusions                 → Card combination events

🔗 KEY RELATIONSHIPS:
• One template → Many NFC instances
• Each NFC card starts with template stats but can evolve uniquely
• Templates are managed by admins (AI generation)
• NFC instances are owned by players and can change over time

🎯 WORKFLOW:
1. Admin creates card template with AI art
2. Templates are published to card sets
3. NFC cards are minted from templates
4. Players activate and use NFC cards
5. Cards gain experience and can evolve
6. Each NFC card becomes unique over time
""")

def main():
    """Run the complete card system setup"""
    print("🚀 Deckport Card System Migration")
    print("Setting up two-tier system: Templates + NFC Instances")
    print("=" * 60)
    
    # Create tables
    if not create_card_system_tables():
        print("Migration failed!")
        return 1
    
    # Verify structure
    if not verify_table_structure():
        print("Verification failed!")
        return 1
    
    # Show architecture
    show_architecture_summary()
    
    print("\n🎯 Migration completed successfully!")
    print("Your PostgreSQL database now supports:")
    print("• AI-generated card templates")
    print("• Unique evolving NFC card instances")
    print("• Complete card lifecycle management")
    
    return 0

if __name__ == "__main__":
    exit(main())

