#!/usr/bin/env python3
import os
from collections import defaultdict

try:
    from .config import settings
    from .generate_cards_and_insert import (
        load_rows,
        comfyui_generate,
        ensure_dir,
        load_image,
        compose_card,
        _wait_for_file,
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
    )


def find_perfect_rarity_samples(gp_rows):
    """Find perfect samples: one of each rarity with different colors and card types"""
    
    # Manual selection for perfect diversity
    selections = {
        'COMMON': None,
        'RARE': None, 
        'EPIC': None,
        'LEGENDARY': None
    }
    
    # Find a COMMON ACTION card (different colors)
    for row in gp_rows.values():
        if (row.rarity or '').upper() == 'COMMON' and (row.category or '').upper() == 'ACTION':
            if row.color_code.upper() == 'RADIANT':  # Different from AZURE we used before
                selections['COMMON'] = row
                break
    
    # If no RADIANT ACTION, pick any ACTION
    if not selections['COMMON']:
        for row in gp_rows.values():
            if (row.rarity or '').upper() == 'COMMON' and (row.category or '').upper() == 'ACTION':
                selections['COMMON'] = row
                break
    
    # Find a RARE CREATURE (different color)
    for row in gp_rows.values():
        if (row.rarity or '').upper() == 'RARE' and (row.category or '').upper() == 'CREATURE':
            if row.color_code.upper() == 'AETHER':  # Different from others
                selections['RARE'] = row
                break
    
    # If no AETHER CREATURE, pick any RARE CREATURE
    if not selections['RARE']:
        for row in gp_rows.values():
            if (row.rarity or '').upper() == 'RARE' and (row.category or '').upper() == 'CREATURE':
                selections['RARE'] = row
                break
    
    # Find an EPIC STRUCTURE (different color)
    for row in gp_rows.values():
        if (row.rarity or '').upper() == 'EPIC' and (row.category or '').upper() == 'STRUCTURE':
            if row.color_code.upper() == 'OBSIDIAN':  # Dark color for epic
                selections['EPIC'] = row
                break
    
    # If no OBSIDIAN STRUCTURE, pick any EPIC
    if not selections['EPIC']:
        for row in gp_rows.values():
            if (row.rarity or '').upper() == 'EPIC':
                selections['EPIC'] = row
                break
    
    # Find a LEGENDARY (any type, different color)
    for row in gp_rows.values():
        if (row.rarity or '').upper() == 'LEGENDARY':
            if row.color_code.upper() == 'VERDANT':  # Nature/green for legendary
                selections['LEGENDARY'] = row
                break
    
    # If no VERDANT LEGENDARY, pick any LEGENDARY
    if not selections['LEGENDARY']:
        for row in gp_rows.values():
            if (row.rarity or '').upper() == 'LEGENDARY':
                selections['LEGENDARY'] = row
                break
    
    return selections


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    # Get perfect diversity samples
    selected_cards = find_perfect_rarity_samples(gp_rows)

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    print("=== PERFECT RARITY SAMPLES ===")
    
    for rarity in ['COMMON', 'RARE', 'EPIC', 'LEGENDARY']:
        gp = selected_cards.get(rarity)
        if not gp:
            print(f"No {rarity} card found")
            continue
            
        name = gp.name
        art = art_rows.get(name)
        if not art:
            print(f"No art data found for {name}, skipping")
            continue
            
        print(f"Rendering {rarity}: {name} ({gp.color_code}/{gp.category})")
            
        base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', f"{gp.slug}.png")
        ensure_dir(base_art_path)
        if not os.path.exists(base_art_path):
            seed = 999000 + hash(rarity + name) % 10000
            _ = comfyui_generate(art.image_prompt, seed=seed, save_path=base_art_path, fetch_bytes=False)
            if not _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S):
                print(f"ComfyUI generation failed (no file) for {name}, skipping")
                continue

        art_img = load_image(base_art_path)
        frame_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png'))
        glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
        mana_file = color_to_file.get(gp.color_code.upper(), 'mana_white.png')
        mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
        card_img = compose_card(art_img, frame_img, glow_img, mana_icon, gp)

        out_path = os.path.join(settings.OUTPUT_DIR, f"perfect_{rarity.lower()}_{gp.slug}.png")
        card_img.convert('RGB').save(out_path, format='PNG')
        print(f"✓ Rendered {rarity} {gp.category} ({gp.color_code}) {name} -> {out_path}")


if __name__ == '__main__':
    main()
