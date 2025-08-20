#!/usr/bin/env python3
"""
Database initialization script
Creates tables and adds sample data for development
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import create_tables, SessionLocal
from shared.models.base import Player, CardCatalog, CardRarity, CardCategory
from shared.utils.crypto import hash_password

def init_database():
    """Initialize database with tables and sample data"""
    print("🗄️  Initializing database...")
    
    # Create all tables
    print("📋 Creating tables...")
    create_tables()
    print("✅ Tables created successfully")
    
    # Add sample data
    print("📦 Adding sample data...")
    
    with SessionLocal() as session:
        # Add sample cards
        sample_cards = [
            CardCatalog(
                product_sku="RADIANT-001",
                name="Solar Vanguard",
                rarity=CardRarity.epic,
                category=CardCategory.creature,
                base_stats={
                    "attack": 3,
                    "defense": 2, 
                    "health": 5,
                    "mana_cost": {"RADIANT": 3},
                    "energy_cost": 0
                }
            ),
            CardCatalog(
                product_sku="AZURE-014",
                name="Tidecaller Sigil",
                rarity=CardRarity.rare,
                category=CardCategory.enchantment,
                base_stats={
                    "duration": 3,
                    "mana_cost": {"AZURE": 2},
                    "energy_cost": 1
                }
            ),
            CardCatalog(
                product_sku="VERDANT-007",
                name="Forest Guardian", 
                rarity=CardRarity.common,
                category=CardCategory.creature,
                base_stats={
                    "attack": 2,
                    "defense": 3,
                    "health": 4,
                    "mana_cost": {"VERDANT": 2},
                    "energy_cost": 0
                }
            ),
            CardCatalog(
                product_sku="OBSIDIAN-003",
                name="Shadow Strike",
                rarity=CardRarity.common,
                category=CardCategory.action_fast,
                base_stats={
                    "damage": 3,
                    "mana_cost": {"OBSIDIAN": 1},
                    "energy_cost": 2
                }
            ),
            CardCatalog(
                product_sku="CRIMSON-012",
                name="Flame Burst",
                rarity=CardRarity.rare,
                category=CardCategory.action_slow,
                base_stats={
                    "damage": 4,
                    "area_effect": True,
                    "mana_cost": {"CRIMSON": 3},
                    "energy_cost": 1
                }
            )
        ]
        
        # Check if cards already exist
        existing_cards = session.query(CardCatalog).count()
        if existing_cards == 0:
            session.add_all(sample_cards)
            session.commit()
            print(f"✅ Added {len(sample_cards)} sample cards")
        else:
            print(f"ℹ️  Database already has {existing_cards} cards, skipping sample data")
        
        # Add sample admin user
        existing_admin = session.query(Player).filter(Player.email == "admin@deckport.ai").first()
        if not existing_admin:
            admin_user = Player(
                email="admin@deckport.ai",
                display_name="Admin",
                password_hash=hash_password("admin123"),
                elo_rating=1500
            )
            session.add(admin_user)
            session.commit()
            print("✅ Added admin user (admin@deckport.ai / admin123)")
        else:
            print("ℹ️  Admin user already exists")
    
    print("🎉 Database initialization complete!")
    print("")
    print("You can now:")
    print("  - Login as admin@deckport.ai / admin123")
    print("  - Browse the card catalog")
    print("  - Test the API endpoints")

if __name__ == "__main__":
    init_database()
