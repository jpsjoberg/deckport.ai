#!/usr/bin/env python3
import os
from dataclasses import dataclass

try:
    from .config import settings
    from .generate_cards_and_insert import (
        load_rows,
        comfyui_generate,
        ensure_dir,
        load_image,
        compose_card,
        _wait_for_file,
        GameplayRow,
    )
except ImportError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from config import settings
    from generate_cards_and_insert import (
        load_rows,
        comfyui_generate,
        ensure_dir,
        load_image,
        compose_card,
        _wait_for_file,
        GameplayRow,
    )


def select_legendary_creatures(gp_rows):
    """Select 2 powerful RARE creatures from different colors to treat as legendary"""
    
    # Find powerful creatures from different colors
    candidates = []
    
    for row in gp_rows.values():
        if (row.category or '').upper() == 'CREATURE' and (row.rarity or '').upper() == 'RARE':
            # Calculate power score (attack + health/2)
            power = row.attack + (row.health * 0.5)
            candidates.append((row, power))
    
    # Sort by power (descending)
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Select 2 from different colors
    selected = []
    used_colors = set()
    
    for row, power in candidates:
        if len(selected) >= 2:
            break
        
        color = row.color_code.upper()
        if color not in used_colors:
            selected.append(row)
            used_colors.add(color)
            print(f"Selected legendary creature: {row.name} ({color}) - Power: {power}")
    
    return selected


def create_legendary_version(gp_row):
    """Create a legendary version of a card"""
    # Create a copy with legendary status
    legendary_row = GameplayRow(
        slug=gp_row.slug,
        name=gp_row.name,
        category=gp_row.category,
        rarity='LEGENDARY',  # Upgrade to legendary
        legendary=True,      # Set legendary flag
        color_code=gp_row.color_code,
        mana_cost=gp_row.mana_cost,
        energy_cost=gp_row.energy_cost,
        attack=gp_row.attack,
        defense=gp_row.defense,
        health=gp_row.health,
        base_energy_per_turn=gp_row.base_energy_per_turn,
        equipment_slots=gp_row.equipment_slots,
        keywords=gp_row.keywords,
        limits_json=gp_row.limits_json,
        targeting_json=gp_row.targeting_json,
        effects_json=gp_row.effects_json,
        abilities_json=gp_row.abilities_json,
    )
    return legendary_row


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    # Select 2 powerful creatures to make legendary
    selected_creatures = select_legendary_creatures(gp_rows)

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    print("\n=== RENDERING LEGENDARY CREATURES ===")
    
    for idx, creature in enumerate(selected_creatures):
        # Create legendary version
        legendary_creature = create_legendary_version(creature)
        
        name = legendary_creature.name
        art = art_rows.get(name)
        if not art:
            print(f"No art data found for {name}, skipping")
            continue
            
        print(f"\nRendering Legendary Creature {idx+1}: {name} ({legendary_creature.color_code})")
            
        base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', f"{legendary_creature.slug}.png")
        ensure_dir(base_art_path)
        if not os.path.exists(base_art_path):
            # Use a special seed for legendary versions
            seed = 777777 + idx * 1000 + hash(name) % 1000
            _ = comfyui_generate(art.image_prompt, seed=seed, save_path=base_art_path, fetch_bytes=False)
            if not _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S):
                print(f"ComfyUI generation failed (no file) for {name}, skipping")
                continue

        art_img = load_image(base_art_path)
        frame_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png'))
        glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
        mana_file = color_to_file.get(legendary_creature.color_code.upper(), 'mana_white.png')
        mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
        
        # This will use the legendary frame because legendary=True
        card_img = compose_card(art_img, frame_img, glow_img, mana_icon, legendary_creature)

        out_path = os.path.join(settings.OUTPUT_DIR, f"legendary_creature_{idx+1}_{legendary_creature.slug}.png")
        card_img.convert('RGB').save(out_path, format='PNG')
        print(f"✓ Rendered LEGENDARY CREATURE ({legendary_creature.color_code}) {name}")
        print(f"  Stats: {legendary_creature.attack}/{legendary_creature.health} ATK/HP")
        print(f"  File: {out_path}")


if __name__ == '__main__':
    main()
