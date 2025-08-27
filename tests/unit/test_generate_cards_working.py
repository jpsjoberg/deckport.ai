#!/usr/bin/env python3
"""
Working test script to generate 3 cards using the card_templates system
Based on the actual database schema and existing models
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
import json
from datetime import datetime, timezone
import time

def create_card_template(session, name, rarity, category, color_code, description, stats, art_prompt):
    """Create a card template using raw SQL to avoid model issues"""
    
    # Generate unique slug
    slug = name.lower().replace(' ', '-').replace("'", "")
    timestamp = int(time.time())
    unique_slug = f"{slug}-{timestamp}"
    
    # Insert using raw SQL to avoid model complications
    insert_sql = """
    INSERT INTO card_templates (
        card_set_id, name, slug, description, flavor_text, 
        rarity, category, color_code, base_stats, art_prompt,
        is_published, created_at, updated_at,
        is_design_complete, is_balanced, is_ready_for_production,
        balance_weight, generation_context, generation_prompt_history
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) RETURNING id, name, rarity, category;
    """
    
    values = (
        1,  # card_set_id (Test Set Alpha)
        name,
        unique_slug,
        description,
        f"A {rarity.lower()} {category.lower()} from the test generation.",
        rarity.upper(),
        category.upper(), 
        color_code.upper(),
        json.dumps(stats),
        art_prompt,
        True,  # is_published
        datetime.now(timezone.utc),  # created_at
        datetime.now(timezone.utc),  # updated_at
        True,  # is_design_complete
        True,  # is_balanced
        True,  # is_ready_for_production
        50,    # balance_weight
        json.dumps({"test": True, "generated_by": "test_script"}),
        json.dumps([f"Generate a {rarity} {category} card"])
    )
    
    result = session.execute(insert_sql, values)
    card_data = result.fetchone()
    session.commit()
    
    return {
        'id': card_data[0],
        'name': card_data[1], 
        'rarity': card_data[2],
        'category': card_data[3],
        'stats': stats,
        'art_prompt': art_prompt
    }

def main():
    """Generate 3 test cards with different properties"""
    
    print("🎴 Testing Card Template Generation")
    print("=" * 50)
    
    try:
        with SessionLocal() as session:
            print("📦 Creating card templates...")
            
            # Card 1: Common Red Creature
            print("\n🔄 Generating Common Red Creature...")
            card1 = create_card_template(
                session=session,
                name="Flame Warrior",
                rarity="COMMON",
                category="CREATURE",
                color_code="RED",
                description="A fierce warrior wielding flames as weapons. Quick to attack but vulnerable to magic.",
                stats={
                    "attack": 3,
                    "defense": 2,
                    "health": 4,
                    "mana_cost": 2,
                    "speed": 3
                },
                art_prompt="A muscular warrior in red armor holding flaming weapons, fantasy art style, dramatic lighting"
            )
            print(f"✅ Created: {card1['name']} (ID: {card1['id']})")
            
            # Card 2: Rare Blue Spell  
            print("\n🔄 Generating Rare Blue Spell...")
            card2 = create_card_template(
                session=session,
                name="Arcane Disruption",
                rarity="RARE", 
                category="ACTION",
                color_code="BLUE",
                description="Disrupts enemy spells and draws cards. Strategic timing can turn the tide of battle.",
                stats={
                    "effect_power": 4,
                    "mana_cost": 3,
                    "duration": 1,
                    "card_draw": 2
                },
                art_prompt="Swirling blue magical energy disrupting reality, mystical spell effect, ethereal glow"
            )
            print(f"✅ Created: {card2['name']} (ID: {card2['id']})")
            
            # Card 3: Epic Neutral Artifact
            print("\n🔄 Generating Epic Neutral Artifact...")
            card3 = create_card_template(
                session=session,
                name="Crystal of Eternal Power",
                rarity="EPIC",
                category="EQUIPMENT", 
                color_code="NEUTRAL",
                description="An ancient crystal that provides ongoing mana generation and protects its wielder.",
                stats={
                    "mana_generation": 2,
                    "defense_bonus": 3,
                    "durability": 8,
                    "mana_cost": 5
                },
                art_prompt="A glowing crystal artifact floating with energy, surrounded by protective aura, magical radiance"
            )
            print(f"✅ Created: {card3['name']} (ID: {card3['id']})")
            
            print(f"\n🎯 Generation Summary:")
            print(f"   ✅ Successfully generated 3 cards")
            print(f"   📊 Cards created in card_templates table")
            print(f"   🎨 Art prompts ready for image generation")
            
            # Show detailed results
            print(f"\n📋 Generated Cards:")
            for i, card in enumerate([card1, card2, card3], 1):
                print(f"\n   {i}. {card['name']}")
                print(f"      Rarity: {card['rarity']}")
                print(f"      Category: {card['category']}")
                print(f"      Stats: {json.dumps(card['stats'], indent=10)}")
                print(f"      Art Prompt: {card['art_prompt']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error generating cards: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎯 SUCCESS! Cards ready for production workflow.' if success else '💥 FAILED!'}")
    sys.exit(0 if success else 1)



