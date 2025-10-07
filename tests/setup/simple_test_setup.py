#!/usr/bin/env python3
"""
Simple Test Data Setup for Deckport Gameplay System
Creates minimal test data using direct SQL to avoid model compatibility issues
"""

import sys
import os
import psycopg2
from datetime import datetime, timezone

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

from shared.utils.crypto import hash_password

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'deckport',
    'user': 'deckport_app',
    'password': os.getenv('DB_PASS', 'your_password_here')
}

def get_db_connection():
    """Get database connection"""
    try:
        # Try to read password from file
        with open('/home/jp/deckport.ai/.env/DB_pass', 'r') as f:
            content = f.read()
            # Extract password from DB_PASS='...' line
            for line in content.split('\n'):
                if line.startswith('DB_PASS='):
                    password = line.split('=', 1)[1].strip("'\"")
                    break
            else:
                password = 'N0D3-N0D3-N0D3#M0nk3y33'  # Fallback
        
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=password
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def create_test_players():
    """Create test players using direct SQL"""
    print("🧑‍🤝‍🧑 Creating test players...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if test players already exist
        cur.execute("SELECT COUNT(*) FROM players WHERE email LIKE '%testplayer%'")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"   Test players already exist ({existing_count} found), skipping creation")
            return True
        
        # Create test players
        test_players = [
            ("testplayer1@deckport.ai", "Test Player 1", "testplayer1", hash_password("testpass123"), 1000),
            ("testplayer2@deckport.ai", "Test Player 2", "testplayer2", hash_password("testpass123"), 1050),
            ("testplayer3@deckport.ai", "Test Player 3", "testplayer3", hash_password("testpass123"), 950),
            ("testplayer4@deckport.ai", "Test Player 4", "testplayer4", hash_password("testpass123"), 1100)
        ]
        
        insert_query = """
        INSERT INTO players (email, display_name, username, password_hash, elo_rating, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now(timezone.utc)
        for email, display_name, username, password_hash, elo in test_players:
            cur.execute(insert_query, (email, display_name, username, password_hash, elo, now, now))
        
        conn.commit()
        print(f"   ✅ Created {len(test_players)} test players")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating test players: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_sample_cards():
    """Create sample cards using direct SQL"""
    print("🃏 Creating sample cards...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if sample cards already exist
        cur.execute("SELECT COUNT(*) FROM card_catalog WHERE product_sku LIKE 'TEST-%'")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"   Sample cards already exist ({existing_count} found), skipping creation")
            return True
        
        # Create sample cards
        sample_cards = [
            # Creatures (Heroes)
            ("TEST-RADIANT-001", "Solar Champion", "epic", "creature", '{"attack": 4, "defense": 3, "health": 8, "energy_per_turn": 2, "energy_cost": 0}'),
            ("TEST-AZURE-001", "Frost Guardian", "rare", "creature", '{"attack": 3, "defense": 5, "health": 7, "energy_per_turn": 1, "energy_cost": 0}'),
            ("TEST-VERDANT-001", "Forest Warden", "common", "creature", '{"attack": 2, "defense": 4, "health": 6, "energy_per_turn": 1, "energy_cost": 0}'),
            
            # Structures
            ("TEST-CRIMSON-001", "Fire Tower", "rare", "structure", '{"attack": 0, "defense": 6, "health": 10, "energy_per_turn": 2, "energy_cost": 0}'),
            
            # Actions
            ("TEST-ACTION-001", "Lightning Bolt", "common", "action_fast", '{"damage": 3, "energy_cost": 2}'),
            ("TEST-ACTION-002", "Healing Potion", "common", "action_slow", '{"healing": 4, "energy_cost": 1}'),
            
            # Equipment
            ("TEST-EQUIP-001", "Steel Sword", "common", "equipment", '{"attack_bonus": 2, "energy_cost": 2}'),
            ("TEST-EQUIP-002", "Magic Shield", "rare", "equipment", '{"defense_bonus": 3, "energy_cost": 3}'),
            
            # Enchantments
            ("TEST-ENCHANT-001", "Blessing of Strength", "rare", "enchantment", '{"attack_bonus": 1, "energy_cost": 2}')
        ]
        
        insert_query = """
        INSERT INTO card_catalog (product_sku, name, rarity, category, base_stats, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now(timezone.utc)
        for sku, name, rarity, category, base_stats in sample_cards:
            cur.execute(insert_query, (sku, name, rarity, category, base_stats, now))
        
        conn.commit()
        print(f"   ✅ Created {len(sample_cards)} sample cards")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating sample cards: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_test_arenas():
    """Create test arenas using direct SQL"""
    print("🏟️ Creating test arenas...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if arenas already exist
        cur.execute("SELECT COUNT(*) FROM arenas")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"   Arenas already exist ({existing_count} found), skipping creation")
            return True
        
        # Create test arenas
        test_arenas = [
            ("Test Arena - Sunspire Plateau", "RADIANT", "first_match_card_discount", "A radiant plateau bathed in eternal sunlight", "Test arena for gameplay testing"),
            ("Test Arena - Frost Caverns", "AZURE", "ice_shield_bonus", "Frozen caverns of ancient ice", "Test arena for gameplay testing"),
            ("Test Arena - Verdant Grove", "VERDANT", "nature_healing", "A lush forest grove teeming with life", "Test arena for gameplay testing")
        ]
        
        insert_query = """
        INSERT INTO arenas (name, primary_color, passive_effect, description, lore, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now(timezone.utc)
        for name, color, passive, description, lore in test_arenas:
            cur.execute(insert_query, (name, color, passive, description, lore, now, now))
        
        conn.commit()
        print(f"   ✅ Created {len(test_arenas)} test arenas")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating test arenas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def print_test_data_summary():
    """Print summary of created test data"""
    print("\n📊 Test Data Summary:")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Count test data
        cur.execute("SELECT COUNT(*) FROM players WHERE email LIKE '%testplayer%'")
        player_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM card_catalog WHERE product_sku LIKE 'TEST-%'")
        card_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM arenas")
        arena_count = cur.fetchone()[0]
        
        print(f"   👥 Test Players: {player_count}")
        print(f"   🃏 Sample Cards: {card_count}")
        print(f"   🏟️ Arenas: {arena_count}")
        
        # Print player details
        if player_count > 0:
            print("\n👥 Test Player Details:")
            cur.execute("SELECT id, display_name, elo_rating FROM players WHERE email LIKE '%testplayer%' ORDER BY id")
            players = cur.fetchall()
            for player_id, display_name, elo_rating in players:
                print(f"   ID: {player_id}, Name: {display_name}, ELO: {elo_rating}")
        
        # Print card details
        if card_count > 0:
            print("\n🃏 Sample Card Details:")
            cur.execute("SELECT product_sku, name, category FROM card_catalog WHERE product_sku LIKE 'TEST-%' ORDER BY product_sku")
            cards = cur.fetchall()
            for sku, name, category in cards:
                print(f"   SKU: {sku}, Name: {name}, Type: {category}")
        
    except Exception as e:
        print(f"   ❌ Error getting test data summary: {e}")
    finally:
        conn.close()

def main():
    """Main setup function"""
    print("🎮 Setting up Deckport Test Data (Simple Version)")
    print("=" * 60)
    
    success = True
    
    if not create_test_players():
        success = False
    
    if not create_sample_cards():
        success = False
    
    if not create_test_arenas():
        success = False
    
    print_test_data_summary()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Test data setup completed successfully!")
        print("\nYou can now:")
        print("1. Run the gameplay test suite: python3 test_gameplay_system.py")
        print("2. Test the Godot console with GameplayTest scene")
        print("3. Create matches with real player data")
        print("\n💡 Test Player Credentials:")
        print("   Email: testplayer1@deckport.ai, Password: testpass123")
        print("   Email: testplayer2@deckport.ai, Password: testpass123")
        print("   (Players 3 and 4 also available)")
    else:
        print("\n❌ Some errors occurred during test data setup")
        print("Check the error messages above and ensure the database is accessible")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
