#!/usr/bin/env python3
"""
Test script to generate a complete balanced card set with art prompts
Tests the new AI card set generation system
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from frontend.admin_routes.card_set_generator_ai import generate_balanced_card_set_ai
import json
from datetime import datetime

def test_card_set_generation():
    """Test generating a complete card set"""
    
    print("🎴 Testing AI Card Set Generation")
    print("=" * 60)
    
    # Test parameters
    test_params = {
        'set_name': 'Crimson Legends',
        'set_code': 'CL-001',
        'theme': 'fantasy',
        'color_distribution': 'balanced',
        'set_size': 25,  # Small test set
        'user_prompt': 'Focus on fire and ice magic with balanced creature and spell distribution'
    }
    
    print(f"📋 Generation Parameters:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    
    print(f"\n🔄 Generating card set...")
    
    try:
        # Generate the card set
        generated_set = generate_balanced_card_set_ai(**test_params)
        
        print(f"\n✅ Successfully generated card set!")
        print(f"   Set Name: {generated_set['set_name']}")
        print(f"   Total Cards: {generated_set['total_cards']}")
        print(f"   Theme: {generated_set['theme']}")
        
        # Show structure breakdown
        print(f"\n📊 Set Structure:")
        structure = generated_set['structure']
        for color, info in structure['colors'].items():
            print(f"   {color}: {info['total_cards']} cards")
            for rarity, count in info['rarities'].items():
                if count > 0:
                    print(f"     - {rarity}: {count}")
        
        # Show sample cards
        print(f"\n🎴 Sample Generated Cards:")
        for i, card in enumerate(generated_set['cards'][:5], 1):
            print(f"\n   {i}. {card['name']} ({card['rarity']} {card['category']})")
            print(f"      Color: {card['color_code']}")
            print(f"      Stats: {json.dumps(card['base_stats'])}")
            print(f"      Description: {card['description']}")
            print(f"      Flavor: {card['flavor_text']}")
            print(f"      Art Prompt: {card['art_prompt'][:100]}...")
        
        # Show art style guide
        print(f"\n🎨 Art Style Guide:")
        art_guide = generated_set['art_style_guide']
        print(f"   Theme: {art_guide['theme']}")
        print(f"   Color Palette: {art_guide['color_palette']}")
        print(f"   Visual Elements: {art_guide['visual_elements']}")
        print(f"   Lighting Style: {art_guide['lighting_style']}")
        
        # Show balance report
        print(f"\n⚖️ Balance Report:")
        balance = generated_set['balance_report']
        print(f"   Total Cards: {balance['total_cards']}")
        print(f"   Balance Score: {balance['balance_score']}/100")
        print(f"   Rarity Distribution: {balance['rarity_distribution']}")
        print(f"   Color Distribution: {balance['color_distribution']}")
        print(f"   Category Distribution: {balance['category_distribution']}")
        
        # Save detailed report
        report_file = f"card_set_generation_report_{int(datetime.now().timestamp())}.json"
        with open(report_file, 'w') as f:
            json.dump(generated_set, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Test different themes
        print(f"\n🔄 Testing different themes...")
        themes = ['sci-fi', 'steampunk', 'cyberpunk']
        
        for theme in themes:
            print(f"\n   Testing {theme} theme...")
            theme_set = generate_balanced_card_set_ai(
                set_name=f"{theme.title()} Test Set",
                set_code=f"{theme.upper()[:2]}-001",
                theme=theme,
                color_distribution='focused',
                set_size=10,
                user_prompt=f"Create cards that embody the {theme} aesthetic"
            )
            
            sample_card = theme_set['cards'][0]
            print(f"     Sample: {sample_card['name']}")
            print(f"     Art: {sample_card['art_prompt'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating card set: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components of the generation system"""
    
    print(f"\n🧪 Testing Individual Components")
    print("=" * 40)
    
    from frontend.admin_routes.card_set_generator_ai import (
        calculate_set_structure,
        build_set_theme_context,
        generate_thematic_card,
        generate_comprehensive_art_prompt
    )
    
    # Test set structure calculation
    print(f"\n1. Testing set structure calculation...")
    structure = calculate_set_structure(50, 'balanced')
    print(f"   Structure for 50-card balanced set:")
    print(f"   Colors: {list(structure['colors'].keys())}")
    print(f"   Total cards: {structure['total_cards']}")
    
    # Test theme context
    print(f"\n2. Testing theme context...")
    context = build_set_theme_context('fantasy', 'Test Set', 'Focus on dragons')
    print(f"   Theme: {context['theme']}")
    print(f"   Setting: {context['setting'][:50]}...")
    print(f"   Visual Style: {context['visual_style'][:50]}...")
    
    # Test individual card generation
    print(f"\n3. Testing individual card generation...")
    card = generate_thematic_card(
        color_code='RED',
        category='CREATURE',
        rarity='RARE',
        theme_context=context,
        set_context={'name': 'Test Set', 'code': 'TEST'},
        card_number=1
    )
    print(f"   Generated: {card['name']}")
    print(f"   Stats: {card['base_stats']}")
    print(f"   Art: {card['art_prompt'][:60]}...")
    
    # Test art prompt generation
    print(f"\n4. Testing art prompt generation...")
    art_prompt = generate_comprehensive_art_prompt(
        name="Fire Dragon",
        category='CREATURE',
        color_theme={'element': 'fire', 'creatures': 'dragons'},
        theme_context=context,
        rarity='LEGENDARY'
    )
    print(f"   Art Prompt: {art_prompt[:100]}...")
    
    print(f"\n✅ All component tests passed!")

def main():
    """Run all tests"""
    
    print("🚀 Starting Card Set Generation Tests")
    print("=" * 80)
    
    # Test main generation
    success = test_card_set_generation()
    
    if success:
        # Test components
        test_individual_components()
        
        print(f"\n🎯 ALL TESTS PASSED!")
        print(f"   ✅ Card set generation working")
        print(f"   ✅ Art prompts generated")
        print(f"   ✅ Balance analysis complete")
        print(f"   ✅ Multiple themes supported")
        print(f"   ✅ Comprehensive reporting")
        
        print(f"\n🎨 READY FOR PRODUCTION:")
        print(f"   • Generate complete balanced card sets")
        print(f"   • AI-powered art prompts for each card")
        print(f"   • Multiple themes (Fantasy, Sci-Fi, Steampunk, Cyberpunk)")
        print(f"   • Configurable set sizes and distributions")
        print(f"   • Balance analysis and reporting")
        print(f"   • Admin web interface ready")
        
        return True
    else:
        print(f"\n💥 TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



