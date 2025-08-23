#!/usr/bin/env python3
"""
Test script for card management integration
Verifies database, services, and basic functionality
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai/frontend')

from services.card_service import get_card_service
from services.comfyui_service import get_comfyui_service

def test_database_connection():
    """Test database connectivity and schema"""
    print("🔍 Testing database connection...")
    
    card_service = get_card_service()
    conn = card_service.get_db_connection()
    
    if not conn:
        print("❌ Database connection failed")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['cards', 'card_stats', 'card_mana_costs', 'card_targeting']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print("✅ Database connection and schema OK")
        return True
        
    finally:
        conn.close()

def test_comfyui_connection():
    """Test ComfyUI server connectivity"""
    print("🔍 Testing ComfyUI connection...")
    
    comfyui = get_comfyui_service()
    
    if comfyui.is_online():
        print(f"✅ ComfyUI server online at {comfyui.host}")
        
        # Get system stats if available
        stats = comfyui.get_system_stats()
        if stats:
            print(f"   System info: {stats}")
        
        return True
    else:
        print(f"⚠️  ComfyUI server offline at {comfyui.host}")
        print("   This is expected if ComfyUI is not running")
        return False

def test_card_creation():
    """Test card creation functionality"""
    print("🔍 Testing card creation...")
    
    card_service = get_card_service()
    
    # Test card data
    test_card = {
        'name': 'Test Card',
        'category': 'CREATURE',
        'rarity': 'COMMON',
        'color_code': 'AZURE',
        'mana_cost': 2,
        'energy_cost': 1,
        'attack': 2,
        'defense': 0,
        'health': 3,
        'base_energy_per_turn': 1,
        'equipment_slots': 2
    }
    
    # Create test card
    card_id = card_service.create_card(test_card)
    
    if not card_id:
        print("❌ Failed to create test card")
        return False
    
    print(f"✅ Created test card with ID: {card_id}")
    
    # Retrieve and verify
    retrieved_card = card_service.get_card(card_id)
    if not retrieved_card:
        print("❌ Failed to retrieve created card")
        return False
    
    if retrieved_card['name'] != test_card['name']:
        print("❌ Card data mismatch")
        return False
    
    print("✅ Card retrieval and data integrity OK")
    
    # Clean up test card
    if card_service.delete_card(card_id):
        print("✅ Test card cleanup successful")
    else:
        print("⚠️  Failed to clean up test card")
    
    return True

def test_statistics():
    """Test statistics functionality"""
    print("🔍 Testing statistics...")
    
    card_service = get_card_service()
    stats = card_service.get_statistics()
    
    if not isinstance(stats, dict):
        print("❌ Statistics returned invalid data")
        return False
    
    expected_keys = ['total_cards', 'category_stats', 'rarity_stats', 'color_stats']
    missing_keys = [k for k in expected_keys if k not in stats]
    
    if missing_keys:
        print(f"❌ Missing statistics keys: {missing_keys}")
        return False
    
    print(f"✅ Statistics OK - Total cards: {stats['total_cards']}")
    return True

def main():
    """Run all tests"""
    print("🚀 Deckport Card Management Integration Test")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("ComfyUI Connection", test_comfyui_connection),
        ("Card Creation", test_card_creation),
        ("Statistics", test_statistics),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("🎉 All tests passed! Card management integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    exit(main())
