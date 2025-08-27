#!/usr/bin/env python3
"""
Test script to generate 3 cards using the AI card generation system
"""

import requests
import json
import sys
from datetime import datetime

# API Configuration
API_BASE = "http://127.0.0.1:8001"  # Frontend server
CARD_SET_ID = 1  # Test Set Alpha

def generate_card(card_data):
    """Generate a single card using the AI generation endpoint"""
    
    url = f"{API_BASE}/admin/cards/generate"
    
    try:
        response = requests.post(url, json=card_data, headers={
            'Content-Type': 'application/json'
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Generated card: {result['card']['name']}")
                print(f"   Rarity: {result['card']['rarity']}")
                print(f"   Category: {result['card']['category']}")
                print(f"   Stats: {result['card']['base_stats']}")
                print(f"   Description: {result['card']['description'][:100]}...")
                return result['card']
            else:
                print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Generate 3 test cards with different properties"""
    
    print("🎴 Testing AI Card Generation - Creating 3 Cards")
    print("=" * 50)
    
    # Test Card 1: Common Creature
    card1_data = {
        "card_set_id": CARD_SET_ID,
        "rarity": "COMMON",
        "category": "CREATURE", 
        "color_code": "RED",
        "generation_prompt": "A fierce warrior with balanced attack and defense stats suitable for early game play"
    }
    
    # Test Card 2: Rare Spell
    card2_data = {
        "card_set_id": CARD_SET_ID,
        "rarity": "RARE",
        "category": "SPELL",
        "color_code": "BLUE", 
        "generation_prompt": "A powerful magic spell that can turn the tide of battle with strategic timing"
    }
    
    # Test Card 3: Epic Artifact
    card3_data = {
        "card_set_id": CARD_SET_ID,
        "rarity": "EPIC",
        "category": "ARTIFACT",
        "color_code": "NEUTRAL",
        "generation_prompt": "A legendary artifact with unique abilities that provides ongoing benefits"
    }
    
    cards_to_generate = [
        ("Common Red Creature", card1_data),
        ("Rare Blue Spell", card2_data), 
        ("Epic Neutral Artifact", card3_data)
    ]
    
    generated_cards = []
    
    for card_name, card_data in cards_to_generate:
        print(f"\n🔄 Generating {card_name}...")
        card = generate_card(card_data)
        if card:
            generated_cards.append(card)
        print("-" * 30)
    
    print(f"\n📊 Generation Summary:")
    print(f"   Requested: {len(cards_to_generate)} cards")
    print(f"   Generated: {len(generated_cards)} cards")
    print(f"   Success Rate: {len(generated_cards)/len(cards_to_generate)*100:.1f}%")
    
    if generated_cards:
        print(f"\n🎯 Generated Cards:")
        for i, card in enumerate(generated_cards, 1):
            print(f"   {i}. {card['name']} ({card['rarity']} {card['category']})")
    
    return len(generated_cards) == len(cards_to_generate)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
