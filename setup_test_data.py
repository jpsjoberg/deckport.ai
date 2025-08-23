#!/usr/bin/env python3
"""
Setup Test Data for Deckport Gameplay System
Creates test players, sample cards, and other necessary data for testing
"""

import sys
import os
from datetime import datetime, timezone

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Player, CardCatalog, CardRarity, CardCategory, NFCCard, NFCCardStatus, CardBatch
from shared.models.arena import Arena
from shared.utils.crypto import hash_password

def create_test_players():
    """Create test players for gameplay testing"""
    print("🧑‍🤝‍🧑 Creating test players...")
    
    with SessionLocal() as session:
        # Check if test players already exist
        existing_player = session.query(Player).filter(Player.email == "testplayer1@deckport.ai").first()
        if existing_player:
            print("   Test players already exist, skipping creation")
            return
        
        # Create test players
        test_players = [
            {
                "email": "testplayer1@deckport.ai",
                "display_name": "Test Player 1",
                "username": "testplayer1",
                "password_hash": hash_password("testpass123"),
                "elo_rating": 1000
            },
            {
                "email": "testplayer2@deckport.ai", 
                "display_name": "Test Player 2",
                "username": "testplayer2",
                "password_hash": hash_password("testpass123"),
                "elo_rating": 1050
            },
            {
                "email": "testplayer3@deckport.ai",
                "display_name": "Test Player 3", 
                "username": "testplayer3",
                "password_hash": hash_password("testpass123"),
                "elo_rating": 950
            },
            {
                "email": "testplayer4@deckport.ai",
                "display_name": "Test Player 4",
                "username": "testplayer4", 
                "password_hash": hash_password("testpass123"),
                "elo_rating": 1100
            }
        ]
        
        for player_data in test_players:
            player = Player(**player_data)
            session.add(player)
        
        session.commit()
        print(f"   ✅ Created {len(test_players)} test players")

def create_sample_cards():
    """Create sample cards for gameplay testing"""
    print("🃏 Creating sample cards...")
    
    with SessionLocal() as session:
        # Check if sample cards already exist
        existing_card = session.query(CardCatalog).filter(CardCatalog.product_sku == "TEST-RADIANT-001").first()
        if existing_card:
            print("   Sample cards already exist, skipping creation")
            return
        
        # Create sample cards for testing
        sample_cards = [
            # Creatures (Heroes)
            {
                "product_sku": "TEST-RADIANT-001",
                "name": "Solar Champion",
                "rarity": CardRarity.epic,
                "category": CardCategory.creature,
                "base_stats": {
                    "attack": 4,
                    "defense": 3,
                    "health": 8,
                    "energy_per_turn": 2
                },
                "display_label": "Epic Creature"
            },
            {
                "product_sku": "TEST-AZURE-001", 
                "name": "Frost Guardian",
                "rarity": CardRarity.rare,
                "category": CardCategory.creature,
                "base_stats": {
                    "attack": 3,
                    "defense": 5,
                    "health": 7,
                    "energy_per_turn": 1
                },
                "display_label": "Rare Creature"
            },
            {
                "product_sku": "TEST-VERDANT-001",
                "name": "Forest Warden", 
                "rarity": CardRarity.common,
                "category": CardCategory.creature,
                "base_stats": {
                    "attack": 2,
                    "defense": 4,
                    "health": 6,
                    "energy_per_turn": 1
                },
                "display_label": "Common Creature"
            },
            
            # Structures
            {
                "product_sku": "TEST-CRIMSON-001",
                "name": "Fire Tower",
                "rarity": CardRarity.rare,
                "category": CardCategory.structure,
                "base_stats": {
                    "attack": 0,
                    "defense": 6,
                    "health": 10,
                    "energy_per_turn": 2
                },
                "display_label": "Rare Structure"
            },
            
            # Actions
            {
                "product_sku": "TEST-ACTION-001",
                "name": "Lightning Bolt",
                "rarity": CardRarity.common,
                "category": CardCategory.action_fast,
                "base_stats": {
                    "damage": 3,
                    "energy_cost": 2
                },
                "display_label": "Common Instant"
            },
            {
                "product_sku": "TEST-ACTION-002",
                "name": "Healing Potion",
                "rarity": CardRarity.common,
                "category": CardCategory.action_slow,
                "base_stats": {
                    "healing": 4,
                    "energy_cost": 1
                },
                "display_label": "Common Sorcery"
            },
            
            # Equipment
            {
                "product_sku": "TEST-EQUIP-001",
                "name": "Steel Sword",
                "rarity": CardRarity.common,
                "category": CardCategory.equipment,
                "base_stats": {
                    "attack_bonus": 2,
                    "energy_cost": 2
                },
                "display_label": "Common Equipment"
            },
            {
                "product_sku": "TEST-EQUIP-002",
                "name": "Magic Shield",
                "rarity": CardRarity.rare,
                "category": CardCategory.equipment,
                "base_stats": {
                    "defense_bonus": 3,
                    "energy_cost": 3
                },
                "display_label": "Rare Equipment"
            },
            
            # Enchantments
            {
                "product_sku": "TEST-ENCHANT-001",
                "name": "Blessing of Strength",
                "rarity": CardRarity.rare,
                "category": CardCategory.enchantment,
                "base_stats": {
                    "attack_bonus": 1,
                    "energy_cost": 2
                },
                "display_label": "Rare Enchantment"
            }
        ]
        
        for card_data in sample_cards:
            card = CardCatalog(**card_data)
            session.add(card)
        
        session.commit()
        print(f"   ✅ Created {len(sample_cards)} sample cards")

def create_nfc_card_instances():
    """Create NFC card instances for testing"""
    print("💳 Creating NFC card instances...")
    
    with SessionLocal() as session:
        # Check if NFC instances already exist
        existing_nfc = session.query(NFCCard).filter(NFCCard.ntag_uid == "TEST-NFC-001").first()
        if existing_nfc:
            print("   NFC card instances already exist, skipping creation")
            return
        
        # Create a card batch first
        batch = CardBatch(
            product_sku="TEST-RADIANT-001",
            name="Test Batch 1",
            notes="Test batch for gameplay testing"
        )
        session.add(batch)
        session.flush()  # Get batch ID
        
        # Create NFC card instances for each sample card
        sample_cards = session.query(CardCatalog).filter(CardCatalog.product_sku.like("TEST-%")).all()
        
        nfc_instances = []
        for i, card in enumerate(sample_cards):
            for copy in range(3):  # Create 3 copies of each card
                nfc_card = NFCCard(
                    ntag_uid=f"TEST-NFC-{i:03d}-{copy:02d}",
                    product_sku=card.product_sku,
                    batch_id=batch.id,
                    status=NFCCardStatus.activated,
                    provisioned_at=datetime.now(timezone.utc),
                    activated_at=datetime.now(timezone.utc)
                )
                nfc_instances.append(nfc_card)
                session.add(nfc_card)
        
        session.commit()
        print(f"   ✅ Created {len(nfc_instances)} NFC card instances")

def create_test_arenas():
    """Create test arenas if they don't exist"""
    print("🏟️ Creating test arenas...")
    
    with SessionLocal() as session:
        # Check if arenas already exist
        existing_arena = session.query(Arena).first()
        if existing_arena:
            print("   Arenas already exist, skipping creation")
            return
        
        # Create test arenas
        test_arenas = [
            {
                "name": "Test Arena - Sunspire Plateau",
                "primary_color": "RADIANT",
                "passive_effect": "first_match_card_discount",
                "description": "A radiant plateau bathed in eternal sunlight",
                "lore": "Test arena for gameplay testing"
            },
            {
                "name": "Test Arena - Frost Caverns", 
                "primary_color": "AZURE",
                "passive_effect": "ice_shield_bonus",
                "description": "Frozen caverns of ancient ice",
                "lore": "Test arena for gameplay testing"
            },
            {
                "name": "Test Arena - Verdant Grove",
                "primary_color": "VERDANT", 
                "passive_effect": "nature_healing",
                "description": "A lush forest grove teeming with life",
                "lore": "Test arena for gameplay testing"
            }
        ]
        
        for arena_data in test_arenas:
            arena = Arena(**arena_data)
            session.add(arena)
        
        session.commit()
        print(f"   ✅ Created {len(test_arenas)} test arenas")

def print_test_data_summary():
    """Print summary of created test data"""
    print("\n📊 Test Data Summary:")
    
    with SessionLocal() as session:
        player_count = session.query(Player).filter(Player.email.like("%testplayer%")).count()
        card_count = session.query(CardCatalog).filter(CardCatalog.product_sku.like("TEST-%")).count()
        nfc_count = session.query(NFCCard).filter(NFCCard.ntag_uid.like("TEST-NFC-%")).count()
        arena_count = session.query(Arena).count()
        
        print(f"   👥 Test Players: {player_count}")
        print(f"   🃏 Sample Cards: {card_count}")
        print(f"   💳 NFC Instances: {nfc_count}")
        print(f"   🏟️ Arenas: {arena_count}")
        
        # Print player details
        print("\n👥 Test Player Details:")
        players = session.query(Player).filter(Player.email.like("%testplayer%")).all()
        for player in players:
            print(f"   ID: {player.id}, Name: {player.display_name}, ELO: {player.elo_rating}")
        
        # Print card details
        print("\n🃏 Sample Card Details:")
        cards = session.query(CardCatalog).filter(CardCatalog.product_sku.like("TEST-%")).all()
        for card in cards:
            print(f"   SKU: {card.product_sku}, Name: {card.name}, Type: {card.category.value}")

def main():
    """Main setup function"""
    print("🎮 Setting up Deckport Test Data")
    print("=" * 50)
    
    try:
        create_test_players()
        create_sample_cards()
        create_nfc_card_instances()
        create_test_arenas()
        print_test_data_summary()
        
        print("\n" + "=" * 50)
        print("✅ Test data setup completed successfully!")
        print("\nYou can now:")
        print("1. Run the gameplay test suite: python3 test_gameplay_system.py")
        print("2. Test the Godot console with GameplayTest scene")
        print("3. Create matches with real player data")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
