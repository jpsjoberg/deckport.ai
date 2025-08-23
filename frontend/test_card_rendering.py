#!/usr/bin/env python3
"""
End-to-End Card Rendering Test
Tests the complete card generation pipeline from prompt to final card
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai/frontend')

from services.card_service import get_card_service
from services.comfyui_service import get_comfyui_service

def test_full_card_rendering():
    """Test complete card rendering pipeline"""
    print("🎨 End-to-End Card Rendering Test")
    print("=" * 50)
    
    # Test card data
    test_card = {
        'name': 'Lightning Phoenix',
        'category': 'CREATURE',
        'rarity': 'EPIC',
        'color_code': 'CRIMSON',
        'mana_cost': 5,
        'energy_cost': 2,
        'attack': 4,
        'defense': 0,
        'health': 6,
        'base_energy_per_turn': 2,
        'equipment_slots': 2
    }
    
    # Art prompt for ComfyUI
    art_prompt = """
    Ultra-detailed hand-painted scene for a premium trading card game — 
    a majestic phoenix made of crackling lightning and flames, soaring through 
    stormy clouds. The phoenix has brilliant electric blue and golden feathers 
    that spark with energy, spread wings creating arcs of lightning between them. 
    Dark storm clouds in the background with flashes of lightning illuminating 
    the scene. Painted like a traditional oil masterpiece on canvas with layered 
    glazing, chiaroscuro lighting, natural film grain, tactile brush texture. 
    Emphasize painterly realism with rich colors - electric blues, golden yellows, 
    deep purples in the storm clouds. Epic fantasy art style, cinematic composition.
    """
    
    print(f"🔍 Creating test card: {test_card['name']}")
    print(f"   Category: {test_card['category']}")
    print(f"   Rarity: {test_card['rarity']}")
    print(f"   Color: {test_card['color_code']}")
    print(f"   Stats: {test_card['attack']}/{test_card['defense']}/{test_card['health']}")
    
    # Step 1: Create card in database
    print("\n📊 Step 1: Creating card in database...")
    card_service = get_card_service()
    card_id = card_service.create_card(test_card)
    
    if not card_id:
        print("❌ Failed to create card in database")
        return False
    
    print(f"✅ Card created with ID: {card_id}")
    
    # Step 2: Check ComfyUI connection
    print("\n🔌 Step 2: Checking ComfyUI connection...")
    comfyui_service = get_comfyui_service()
    
    if not comfyui_service.is_online():
        print("❌ ComfyUI server is offline")
        return False
    
    print("✅ ComfyUI server is online")
    
    # Step 3: Generate artwork
    print("\n🎨 Step 3: Generating artwork with ComfyUI...")
    print("   This may take 30-60 seconds...")
    print(f"   Prompt: {art_prompt[:100]}...")
    
    try:
        success = card_service.generate_card_art(card_id, art_prompt, seed=42)
        
        if not success:
            print("❌ Artwork generation failed")
            return False
        
        print("✅ Artwork generated and card composed successfully!")
        
    except Exception as e:
        print(f"❌ Artwork generation error: {e}")
        return False
    
    # Step 4: Verify final card
    print("\n🔍 Step 4: Verifying final card...")
    
    # Check if card file exists
    card_service = get_card_service()
    card = card_service.get_card(card_id)
    
    if not card:
        print("❌ Could not retrieve card from database")
        return False
    
    # Check for generated files
    output_dir = "/home/jp/deckport.ai/cardmaker.ai/cards_output"
    raw_art_file = os.path.join(output_dir, f"raw_{card['slug']}.png")
    final_card_file = os.path.join(output_dir, f"{card['slug']}.png")
    
    files_created = []
    if os.path.exists(raw_art_file):
        size = os.path.getsize(raw_art_file)
        files_created.append(f"Raw artwork: {raw_art_file} ({size:,} bytes)")
    
    if os.path.exists(final_card_file):
        size = os.path.getsize(final_card_file)
        files_created.append(f"Final card: {final_card_file} ({size:,} bytes)")
    
    if not files_created:
        print("❌ No card files were created")
        return False
    
    print("✅ Card files created successfully:")
    for file_info in files_created:
        print(f"   {file_info}")
    
    # Step 5: Display results
    print("\n🎉 CARD RENDERING COMPLETE!")
    print("=" * 50)
    print(f"Card Name: {card['name']}")
    print(f"Database ID: {card_id}")
    print(f"Slug: {card['slug']}")
    print(f"Files Location: {output_dir}")
    print(f"View your card: {final_card_file}")
    
    # Optional: Don't clean up so user can see the result
    print(f"\n💡 Card '{card['name']}' left in database for inspection")
    print("   You can view it in the admin panel or delete it manually")
    
    return True

def main():
    """Run the card rendering test"""
    print("🚀 Testing Complete Card Rendering Pipeline")
    print("This will create a real card with AI-generated artwork!")
    print()
    
    # Confirm with user
    try:
        response = input("Continue with card generation? This will use ComfyUI resources (y/N): ").strip().lower()
        if response != 'y':
            print("Test cancelled by user")
            return 0
    except (EOFError, KeyboardInterrupt):
        print("\nTest cancelled")
        return 0
    
    success = test_full_card_rendering()
    
    if success:
        print("\n🎉 Card rendering test completed successfully!")
        print("Check the generated files and database entry.")
        return 0
    else:
        print("\n❌ Card rendering test failed")
        return 1

if __name__ == "__main__":
    exit(main())
