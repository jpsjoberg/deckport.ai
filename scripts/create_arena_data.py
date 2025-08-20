#!/usr/bin/env python3
"""
Create Arena Data for Deckport.ai
Adds sample arenas with storytelling, mechanics, and video clips
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import create_tables, SessionLocal
from shared.models.arena import Arena, ArenaClip, ArenaClipType

def create_sample_arenas():
    """Create sample arenas with rich storytelling and mechanics"""
    print("🏛️ Creating Arena Data...")
    
    # Ensure tables exist
    create_tables()
    
    with SessionLocal() as session:
        # Check if arenas already exist
        existing_arenas = session.query(Arena).count()
        if existing_arenas > 0:
            print(f"ℹ️  Database already has {existing_arenas} arenas, skipping creation")
            return
        
        # Sample Arenas
        arenas_data = [
            {
                "name": "Sunspire Plateau",
                "mana_color": "RADIANT",
                "story_text": """High above the clouds, where the first light of dawn touches the realm, stands the Sunspire Plateau. This sacred ground pulses with radiant energy, empowering those who fight in harmony with the light. Ancient solar crystals embedded in the plateau amplify the power of radiant magic, while the eternal sunrise provides clarity and focus to those who embrace its power.""",
                "flavor_text": "Where the sun never sets, heroes are forged in eternal light.",
                "passive_effect": {
                    "type": "first_match_card_discount",
                    "amount": 1,
                    "description": "The first matching-color card you play each turn costs 1 less Mana"
                },
                "objective": {
                    "name": "Solar Convergence",
                    "rule": "control_for_turns", 
                    "turns": 2,
                    "reward": {"type": "gain_energy_next_turn", "amount": 2},
                    "description": "Control the center solar crystal for 2 turns to gain extra energy"
                },
                "hazard": {
                    "name": "Solar Flare",
                    "rule": "if_attacked_this_turn_deal_1_all",
                    "description": "When you attack, solar flares deal 1 damage to all creatures"
                },
                "background_music": "sunspire_ambient.ogg",
                "ambient_sounds": "wind_crystals.ogg"
            },
            {
                "name": "Shadowmere Depths", 
                "mana_color": "OBSIDIAN",
                "story_text": """In the deepest trenches of the shadow realm, where light has never touched, lies Shadowmere Depths. This cursed battleground feeds on fear and despair, strengthening those who embrace the darkness. Ancient obsidian spires drain the life force from the unwary, while shadow wraiths whisper forbidden knowledge to those brave enough to listen.""",
                "flavor_text": "In darkness, power grows without limit or mercy.",
                "passive_effect": {
                    "type": "damage_amplification",
                    "amount": 1,
                    "description": "All damage dealt is increased by 1"
                },
                "objective": {
                    "name": "Soul Harvest",
                    "rule": "deal_damage_total",
                    "amount": 10,
                    "reward": {"type": "draw_card", "amount": 2},
                    "description": "Deal 10 total damage to gain 2 additional cards"
                },
                "hazard": {
                    "name": "Draining Mist",
                    "rule": "end_turn_lose_energy",
                    "amount": 1,
                    "description": "At end of turn, lose 1 energy to the consuming shadows"
                },
                "background_music": "shadowmere_ambient.ogg",
                "ambient_sounds": "whispers_dripping.ogg"
            },
            {
                "name": "Verdant Sanctuary",
                "mana_color": "VERDANT", 
                "story_text": """Deep within the heart of the ancient forest, where the World Tree's roots run deepest, lies the Verdant Sanctuary. This living arena pulses with the heartbeat of nature itself. Healing springs flow with crystal-clear water, while ancient druids' magic ensures that life finds a way to flourish even in the heat of battle.""",
                "flavor_text": "Where life eternal flows, even death becomes rebirth.",
                "passive_effect": {
                    "type": "healing_bonus",
                    "amount": 1,
                    "description": "All healing effects are increased by 1"
                },
                "objective": {
                    "name": "Nature's Blessing",
                    "rule": "heal_total_amount",
                    "amount": 15,
                    "reward": {"type": "permanent_health_bonus", "amount": 5},
                    "description": "Heal 15 total health to gain +5 maximum health"
                },
                "hazard": None,  # Verdant sanctuary has no hazards
                "special_rules": {
                    "healing_amplified": True,
                    "nature_tokens": "available"
                },
                "background_music": "verdant_peaceful.ogg",
                "ambient_sounds": "forest_birds_water.ogg"
            },
            {
                "name": "Crimson Forge",
                "mana_color": "CRIMSON",
                "story_text": """Within the heart of an active volcano, where molten lava meets ancient dwarven craftsmanship, stands the Crimson Forge. This arena was built by fire giants to test warriors in the crucible of pure flame. The forge's eternal fires enhance all offensive magic, while the heat of battle pushes combatants to their absolute limits.""",
                "flavor_text": "In the forge of war, only the strongest steel survives.",
                "passive_effect": {
                    "type": "spell_damage_bonus",
                    "amount": 2,
                    "description": "All spell damage is increased by 2"
                },
                "objective": {
                    "name": "Forge Mastery",
                    "rule": "cast_spells_count",
                    "amount": 5,
                    "reward": {"type": "equipment_discount", "amount": 1},
                    "description": "Cast 5 spells to reduce equipment costs by 1"
                },
                "hazard": {
                    "name": "Lava Eruption",
                    "rule": "random_damage_each_turn",
                    "amount": 2,
                    "chance": 0.3,
                    "description": "30% chance each turn for lava to deal 2 damage to a random target"
                },
                "background_music": "crimson_forge_intense.ogg",
                "ambient_sounds": "lava_hammering.ogg"
            },
            {
                "name": "Azure Tempest",
                "mana_color": "AZURE",
                "story_text": """High above the storm-tossed seas, where lightning dances with hurricane winds, floats the Azure Tempest arena. This mystical platform rides the eternal storm, drawing power from wind and wave. The tempest's chaotic energy enhances mental magic and divination, while the ever-changing winds keep combatants on their guard.""",
                "flavor_text": "In the eye of the storm, clarity and chaos become one.",
                "passive_effect": {
                    "type": "card_draw_bonus",
                    "amount": 1,
                    "description": "Draw 1 additional card at start of turn"
                },
                "objective": {
                    "name": "Storm Control",
                    "rule": "play_different_card_types",
                    "amount": 4,
                    "reward": {"type": "extra_turn", "amount": 1},
                    "description": "Play 4 different card types to gain an extra turn"
                },
                "hazard": {
                    "name": "Lightning Strike",
                    "rule": "highest_cost_card_damage",
                    "amount": 3,
                    "description": "When you play your highest-cost card, lightning deals 3 damage to you"
                },
                "background_music": "azure_storm.ogg",
                "ambient_sounds": "thunder_rain_wind.ogg"
            }
        ]
        
        created_arenas = []
        for arena_data in arenas_data:
            arena = Arena(**arena_data)
            session.add(arena)
            session.flush()  # Get the arena ID
            created_arenas.append(arena)
            
            # Create video clips for each arena
            clip_data = [
                {
                    "arena_id": arena.id,
                    "clip_type": ArenaClipType.intro,
                    "file_path": f"arenas/{arena.name.lower().replace(' ', '_')}/intro.mp4",
                    "duration_seconds": 45,
                    "trigger_condition": {"event": "arena_reveal"}
                },
                {
                    "arena_id": arena.id,
                    "clip_type": ArenaClipType.ambient,
                    "file_path": f"arenas/{arena.name.lower().replace(' ', '_')}/ambient.mp4",
                    "duration_seconds": 120,
                    "trigger_condition": {"event": "match_active", "loop": True}
                },
                {
                    "arena_id": arena.id,
                    "clip_type": ArenaClipType.advantage,
                    "file_path": f"arenas/{arena.name.lower().replace(' ', '_')}/advantage_{arena.mana_color.lower()}.mp4",
                    "duration_seconds": 15,
                    "trigger_condition": {"event": "arena_advantage_gained"}
                },
                {
                    "arena_id": arena.id,
                    "clip_type": ArenaClipType.victory,
                    "file_path": f"arenas/{arena.name.lower().replace(' ', '_')}/victory.mp4",
                    "duration_seconds": 30,
                    "trigger_condition": {"event": "match_victory"}
                }
            ]
            
            for clip_info in clip_data:
                clip = ArenaClip(**clip_info)
                session.add(clip)
        
        session.commit()
        print(f"✅ Created {len(created_arenas)} arenas with video clips")
        
        # Print arena summary
        for arena in created_arenas:
            print(f"🏛️ {arena.name} ({arena.mana_color})")
            print(f"   📖 {arena.flavor_text}")
            print(f"   🎯 Objective: {arena.objective['name'] if arena.objective else 'None'}")
            print(f"   ⚠️  Hazard: {arena.hazard['name'] if arena.hazard else 'None'}")
            print("")

if __name__ == "__main__":
    create_sample_arenas()
    print("🎉 Arena data creation complete!")
    print("")
    print("📋 Next steps:")
    print("  1. Add video files to console/assets/videos/arenas/")
    print("  2. Implement arena selection in matchmaking")
    print("  3. Create console scenes for arena reveal")
    print("  4. Test arena storytelling and advantages")
