#!/usr/bin/env python3
"""
Card System Example
Shows how the two-tier system works with Lightning Phoenix as an example
"""

def show_lightning_phoenix_example():
    """Show how Lightning Phoenix would exist in the two-tier system"""
    print("🎮 Lightning Phoenix - Two-Tier System Example")
    print("=" * 60)
    
    print("📚 TIER 1: CARD TEMPLATE (Raw Card Design)")
    print("-" * 40)
    print("""
🎨 Template: Lightning Phoenix
├── ID: 1
├── Slug: lightning-phoenix
├── Set: Open Portal (card_set_id: 1)
├── Category: CREATURE
├── Rarity: EPIC
├── Color: CRIMSON
├── Base Stats: 4 ATK / 0 DEF / 6 HP / 2 Energy
├── Mana Cost: 5 CRIMSON
├── Created by: admin
└── AI Art: Generated via ComfyUI

📊 Template Stats Table:
template_id | attack | defense | health | base_energy_per_turn
1          | 4      | 0       | 6      | 2

💎 Template Mana Costs:
template_id | color   | amount
1          | CRIMSON | 5

🎯 Template Targeting:
template_id | target_friendly | target_enemy | target_self
1          | false          | true         | false
""")
    
    print("\n🎴 TIER 2: NFC CARD INSTANCES (Unique Physical Cards)")
    print("-" * 50)
    print("""
🏷️  Instance #1: "Lightning Phoenix Alpha"
├── Instance ID: 101
├── Template ID: 1 (links to Lightning Phoenix template)
├── NFC UID: A1B2C3D4E5F6G7H8
├── Serial: LIGHTNING-PHOENIX-1672531200
├── Owner: Player #42
├── Status: ACTIVE
├── Evolution Level: 2
├── Experience: 1,250 XP
├── Matches Played: 15
├── Wins: 9
└── Custom Stats: +1 ATK from evolution

🏷️  Instance #2: "Lightning Phoenix Beta" 
├── Instance ID: 102
├── Template ID: 1 (same template, different instance!)
├── NFC UID: H8G7F6E5D4C3B2A1
├── Serial: LIGHTNING-PHOENIX-1672531201
├── Owner: Player #73
├── Status: ACTIVE
├── Evolution Level: 0 (still base template stats)
├── Experience: 200 XP
├── Matches Played: 3
├── Wins: 1
└── Custom Stats: None (uses template stats)

📈 Evolution History for Instance #101:
evolution_id | instance_id | level | trigger        | stat_changes
1           | 101         | 1     | battle_exp     | {"attack": +1}
2           | 101         | 2     | achievement    | {"health": +1}

🎯 Match Participation for Instance #101:
participation_id | instance_id | match_id | damage_dealt | won | xp_gained
1               | 101         | 50       | 8           | true| 100
2               | 101         | 51       | 12          | true| 150
...             | ...         | ...      | ...         | ... | ...
""")
    
    print("\n🔗 KEY RELATIONSHIPS:")
    print("-" * 20)
    print("""
• 1 Template → Many NFC Instances
• Same card name/design → Multiple unique physical cards
• Each NFC card can evolve independently
• Templates provide baseline, instances can customize
• Complete history tracking for each physical card
""")
    
    print("\n💡 PRACTICAL BENEFITS:")
    print("-" * 20)
    print("""
✅ Efficient Design: Create one Lightning Phoenix template
✅ Unique Cards: Each physical card is truly unique
✅ Evolution: Cards become more powerful through play
✅ Trading Value: Evolved cards worth more than base
✅ Analytics: Track performance of each individual card
✅ Flexibility: Same template, different abilities over time
""")

def show_admin_workflow():
    """Show the admin workflow for card management"""
    print("\n🛠️  ADMIN WORKFLOW")
    print("=" * 60)
    
    print("""
📋 STEP 1: Create Card Templates (Raw Designs)
├── Admin Panel: /admin/cards/generate
├── Input: Card stats, properties, AI art prompt
├── ComfyUI: Generates artwork automatically
├── Database: Stores in card_templates table
└── Result: Template ready for NFC production

📋 STEP 2: Manage Card Sets
├── Admin Panel: /admin/cards/sets
├── Create: New themed collections
├── Organize: Group related templates
├── Publish: Mark sets ready for production
└── Version: Track set releases and updates

📋 STEP 3: NFC Card Production
├── Admin Panel: /admin/nfc-cards/production
├── Select: Templates to manufacture
├── Generate: Unique NFC UIDs for each card
├── Database: Create NFCCardInstance records
└── Result: Physical cards ready for distribution

📋 STEP 4: Monitor Card Ecosystem
├── Templates: Track usage and popularity
├── Instances: Monitor evolution and performance
├── Analytics: Balance analysis and player engagement
└── Evolution: Manage card progression system
""")

def main():
    """Show the complete card system example"""
    show_lightning_phoenix_example()
    show_admin_workflow()
    
    print("\n🎯 NEXT STEPS:")
    print("=" * 60)
    print("""
1. Run database migration to create the new structure
2. Update admin panel to work with templates vs instances
3. Create NFC card production interface
4. Implement card evolution mechanics
5. Build analytics for both tiers

This system provides the foundation for a truly dynamic
trading card game where each physical card can become unique! 🚀
""")

if __name__ == "__main__":
    main()

