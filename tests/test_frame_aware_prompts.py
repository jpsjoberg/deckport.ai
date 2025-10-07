#!/usr/bin/env python3
"""
Test Frame-Aware Art Generation Prompts
Tests enhanced prompts that include frame composition guidance
"""

import sys
import json
sys.path.append('/home/jp/deckport.ai')
sys.path.append('/home/jp/deckport.ai/frontend')

from shared.database.connection import SessionLocal
from sqlalchemy import text
from services.comfyui_service import ComfyUIService
from dotenv import load_dotenv

load_dotenv('/home/jp/deckport.ai/frontend/.env')

def create_frame_aware_prompt(base_prompt, card_category, card_rarity):
    """Create enhanced prompt with frame composition guidance"""
    
    # Frame composition instructions based on card type
    frame_guidance = {
        'creature': "centered portrait composition, full character visible within frame borders, leave 20% margin around character, character positioned in middle 70% of image area, avoid edge cropping",
        'hero': "heroic portrait composition, character centered and fully visible, dramatic pose within frame boundaries, leave space for frame overlay, character fits in central safe area",
        'action_fast': "dynamic action scene, main subject centered, all important elements within frame borders, composition respects card frame area, avoid cropping key details",
        'action_slow': "epic scene composition, key elements in center, frame-safe composition, leave margins for card borders, balanced layout within frame",
        'structure': "architectural composition, structure centered and complete, no edge cropping, building fits within frame boundaries, leave space for frame overlay",
        'equipment': "item showcase composition, equipment centered and fully visible, product shot style within frame area, avoid edge cutoff",
        'enchantment': "magical effect composition, centered magical elements, effect contained within frame, mystical scene fits in safe area"
    }
    
    # Rarity-based composition enhancements
    rarity_guidance = {
        'common': "simple composition, clear subject placement, straightforward framing",
        'rare': "enhanced composition, dramatic angles within frame bounds, artistic framing",
        'epic': "cinematic composition, epic scale but contained within frame, heroic framing",
        'legendary': "masterpiece composition, perfect framing, legendary character positioning, museum-quality layout"
    }
    
    # Get specific guidance
    category_guide = frame_guidance.get(card_category, frame_guidance['creature'])
    rarity_guide = rarity_guidance.get(card_rarity, rarity_guidance['common'])
    
    # Compose enhanced prompt
    enhanced_prompt = f"""{base_prompt}

COMPOSITION GUIDANCE: {category_guide}, {rarity_guide}

FRAME REQUIREMENTS: Trading card game layout, character/subject must fit within central frame area, leave 15-20% padding on all edges for card frame overlay, no important elements touching image borders, composition designed for rectangular card frame, portrait orientation optimized for trading card display"""
    
    return enhanced_prompt

def test_frame_aware_generation():
    """Test frame-aware generation on a specific card"""
    
    print("🖼️ Testing Frame-Aware Art Generation")
    print("=" * 50)
    
    # Get a test card
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT id, name, product_sku, category, rarity, mana_colors, generation_prompt
            FROM card_catalog 
            WHERE name = 'Eerie Master'
            LIMIT 1
        """))
        
        card_row = result.fetchone()
        if not card_row:
            print("❌ Eerie Master card not found")
            return False
        
        card_data = {
            'id': card_row[0],
            'name': card_row[1],
            'product_sku': card_row[2],
            'category': card_row[3],
            'rarity': card_row[4],
            'mana_colors': card_row[5],
            'generation_prompt': card_row[6]
        }
        
    finally:
        session.close()
    
    print(f"✅ Test card: {card_data['name']} ({card_data['category']}, {card_data['rarity']})")
    
    # Create original prompt
    original_prompt = f"Fantasy {card_data['category']} card art, {card_data['rarity']} quality, detailed digital painting, trading card game style, {card_data['name']}"
    
    # Create frame-aware prompt
    enhanced_prompt = create_frame_aware_prompt(
        original_prompt, 
        card_data['category'], 
        card_data['rarity']
    )
    
    print(f"\n📝 Original Prompt:")
    print(f"   {original_prompt}")
    
    print(f"\n🎯 Enhanced Frame-Aware Prompt:")
    print(f"   {enhanced_prompt}")
    
    # Test ComfyUI generation
    print(f"\n🎨 Testing ComfyUI generation...")
    
    try:
        comfyui = ComfyUIService()
        
        if not comfyui.is_online():
            print("❌ ComfyUI not online")
            return False
        
        # Load workflow
        with open('/home/jp/deckport.ai/cardmaker.ai/art-generation.json', 'r') as f:
            workflow = json.load(f)
        
        # Update workflow with enhanced prompt
        if "6" in workflow and "inputs" in workflow["6"]:
            workflow["6"]["inputs"]["text"] = enhanced_prompt
        
        print("✅ Workflow updated with frame-aware prompt")
        
        # Submit to ComfyUI
        prompt_id = comfyui.submit_prompt(workflow)
        
        if prompt_id:
            print(f"✅ ComfyUI job submitted: {prompt_id}")
            print("⏳ Generating frame-aware artwork...")
            
            # Wait for completion
            result = comfyui.wait_for_completion(prompt_id, max_wait=180)
            
            if result:
                print("✅ Frame-aware artwork generated!")
                
                # Save with frame-aware suffix
                card_slug = card_data['name'].lower().replace(' ', '_').replace("'", "")
                output_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/artwork/{card_slug}_frame_aware.png"
                
                with open(output_path, 'wb') as f:
                    f.write(result)
                
                print(f"✅ Frame-aware artwork saved: {output_path}")
                print(f"🌐 Compare with original at: https://deckport.ai/static/cards/artwork/{card_slug}_frame_aware.png")
                
                return True
            else:
                print("❌ Generation failed or timed out")
                return False
        else:
            print("❌ Failed to submit to ComfyUI")
            return False
    
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

if __name__ == "__main__":
    success = test_frame_aware_generation()
    if success:
        print("\n🎉 Frame-aware prompt test successful!")
        print("   Compare the new artwork with the original to see framing improvement")
        print("   If improved, this prompt enhancement can be applied to all card generation")
    else:
        print("\n❌ Frame-aware prompt test failed")
    
    print("\n📋 Next steps if successful:")
    print("   1. Update all card generation prompts with frame guidance")
    print("   2. Regenerate cards with poor framing using enhanced prompts")
    print("   3. Implement automatic frame-aware prompt enhancement")
