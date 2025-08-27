#!/usr/bin/env python3
"""
Direct test script to generate 3 cards using the database models
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import CardCatalog
import json
from datetime import datetime, timezone

def create_test_card(session, name, rarity, category, color_code, description, stats, image_prompt):
    """Create a test card in catalog"""
    
    # Generate a unique product SKU
    import time
    sku = f"TEST-{int(time.time())}-{name.replace(' ', '').upper()[:8]}"
    
    card = CardCatalog(
        product_sku=sku,
        name=name,
        description=description,
        flavor_text=f"A {rarity.lower()} {category.lower()} from the test set.",
        rarity=rarity.lower(),  # CardCatalog uses lowercase
        category=category.lower(),  # CardCatalog uses lowercase
        color_code=color_code,
        base_stats=stats,
        image_prompt=image_prompt,
        image_url=None,  # Will be generated later
        is_published=True
    )
    
    session.add(card)
    return card

def main():
    """Generate 3 test cards with different properties"""
    
    print("🎴 Generating 3 Test Cards")
    print("=" * 40)
    
    try:
        with SessionLocal() as session:
            print(f"📦 Adding cards to catalog...")
            
            # Card 1: Common Red Creature
            card1 = create_test_card(
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
                image_prompt="A muscular warrior in red armor holding flaming weapons, fantasy art style"
            )
            
            # Card 2: Rare Blue Spell  
            card2 = create_test_card(
                session=session,
                name="Arcane Disruption",
                rarity="RARE", 
                category="SPELL",
                color_code="BLUE",
                description="Disrupts enemy spells and draws cards. Strategic timing can turn the tide of battle.",
                stats={
                    "effect_power": 4,
                    "mana_cost": 3,
                    "duration": 1,
                    "card_draw": 2
                },
                image_prompt="Swirling blue magical energy disrupting reality, mystical spell effect"
            )
            
            # Card 3: Epic Neutral Artifact
            card3 = create_test_card(
                session=session,
                name="Crystal of Eternal Power",
                rarity="EPIC",
                category="ARTIFACT", 
                color_code="NEUTRAL",
                description="An ancient crystal that provides ongoing mana generation and protects its wielder.",
                stats={
                    "mana_generation": 2,
                    "defense_bonus": 3,
                    "durability": 8,
                    "mana_cost": 5
                },
                image_prompt="A glowing crystal artifact floating with energy, surrounded by protective aura"
            )
            
            # Commit all cards
            session.commit()
            
            print(f"\n✅ Successfully generated 3 cards:")
            print(f"   1. {card1.name} ({card1.rarity} {card1.category})")
            print(f"   2. {card2.name} ({card2.rarity} {card2.category})")  
            print(f"   3. {card3.name} ({card3.rarity} {card3.category})")
            
            # Show card details
            print(f"\n📊 Card Details:")
            for i, card in enumerate([card1, card2, card3], 1):
                print(f"\n   Card {i}: {card.name}")
                print(f"      Rarity: {card.rarity}")
                print(f"      Category: {card.category}")
                print(f"      Color: {card.color_code}")
                print(f"      Stats: {json.dumps(card.base_stats, indent=8)}")
                print(f"      Description: {card.description}")
                print(f"      Image Prompt: {card.image_prompt}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error generating cards: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎯 SUCCESS!' if success else '💥 FAILED!'}")
    sys.exit(0 if success else 1)
