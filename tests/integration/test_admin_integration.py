#!/usr/bin/env python3
"""
Test script for admin panel integration
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from frontend.services.simple_card_service import get_simple_card_service

def test_admin_integration():
    """Test the complete admin panel integration"""
    
    print("🚀 Testing Admin Panel Integration...")
    
    # Test 1: Database Connection
    print("\n1. Testing database connection...")
    try:
        service = get_simple_card_service()
        stats = service.get_statistics()
        print(f"✅ Database connected successfully")
        print(f"   Templates: {stats.get('total_templates', 0)}")
        print(f"   NFC Cards: {stats.get('total_nfc_cards', 0)}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 2: Create Card Template
    print("\n2. Testing card template creation...")
    try:
        template_data = {
            'name': 'Test Phoenix',
            'slug': 'test-phoenix',
            'description': 'A test phoenix for integration testing',
            'flavor_text': 'Testing the flames of integration.',
            'rarity': 'COMMON',
            'category': 'CREATURE',
            'color_code': 'CRIMSON',
            'art_prompt': 'A simple phoenix for testing',
            'art_style': 'fantasy_digital_art',
            'is_published': True,  # Make it available for NFC production
            'stats': {
                'attack': 3,
                'defense': 2,
                'health': 4,
                'base_energy_per_turn': 1
            },
            'mana_costs': [{
                'color_code': 'CRIMSON',
                'amount': 2
            }],
            'targeting': {
                'target_friendly': False,
                'target_enemy': True,
                'target_self': False
            }
        }
        
        template_id = service.create_card_template(template_data)
        if template_id:
            print(f"✅ Card template created successfully (ID: {template_id})")
        else:
            print("❌ Failed to create card template")
            return False
    except Exception as e:
        print(f"❌ Card template creation failed: {e}")
        return False
    
    # Test 3: Create NFC Instance
    print("\n3. Testing NFC card instance creation...")
    try:
        nfc_uid = "04:A1:B2:C3:D4:E5:F6"
        serial_number = "TEST-2024-001"
        
        instance_id = service.create_nfc_card_instance(
            template_id=template_id,
            nfc_uid=nfc_uid,
            serial_number=serial_number,
            status='provisioned'
        )
        
        if instance_id:
            print(f"✅ NFC card instance created successfully (ID: {instance_id})")
        else:
            print("❌ Failed to create NFC card instance")
            return False
    except Exception as e:
        print(f"❌ NFC card instance creation failed: {e}")
        return False
    
    # Test 4: Verify Statistics
    print("\n4. Testing updated statistics...")
    try:
        updated_stats = service.get_statistics()
        print(f"✅ Updated statistics retrieved:")
        print(f"   Templates: {updated_stats.get('total_templates', 0)}")
        print(f"   Published: {updated_stats.get('published_templates', 0)}")
        print(f"   NFC Cards: {updated_stats.get('total_nfc_cards', 0)}")
        print(f"   By Rarity: {updated_stats.get('by_rarity', {})}")
        print(f"   By Category: {updated_stats.get('by_category', {})}")
        print(f"   NFC Status: {updated_stats.get('nfc_by_status', {})}")
    except Exception as e:
        print(f"❌ Statistics retrieval failed: {e}")
        return False
    
    # Test 5: Template Retrieval
    print("\n5. Testing template retrieval...")
    try:
        templates_result = service.get_card_templates(page=1, per_page=10)
        templates = templates_result.get('templates', [])
        pagination = templates_result.get('pagination', {})
        
        print(f"✅ Templates retrieved successfully:")
        print(f"   Found {len(templates)} templates")
        print(f"   Pagination: {pagination}")
        
        if templates:
            template = templates[0]
            print(f"   Sample template: {template.get('name')} ({template.get('rarity')})")
    except Exception as e:
        print(f"❌ Template retrieval failed: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    print("\n📋 System Summary:")
    print("   ✅ PostgreSQL database connection")
    print("   ✅ Card template system")
    print("   ✅ NFC card instance system")
    print("   ✅ Statistics and reporting")
    print("   ✅ Template management")
    print("\n🚀 Admin panel is ready for use!")
    
    return True

if __name__ == "__main__":
    success = test_admin_integration()
    sys.exit(0 if success else 1)
