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


def pick_diverse_rarity_samples(gp_rows):
    """Pick one card of each rarity, ensuring different colors and card types"""
    
    # Group cards by rarity
    rarity_groups = defaultdict(list)
    for row in gp_rows.values():
        rarity = (row.rarity or '').upper()
        if rarity in ["COMMON", "RARE", "EPIC", "LEGENDARY"]:
            rarity_groups[rarity].append(row)
    
    # Colors and categories to prioritize diversity
    colors = ["CRIMSON", "AZURE", "VERDANT", "OBSIDIAN", "RADIANT", "AETHER"]
    categories = ["CREATURE", "STRUCTURE", "ACTION"]
    
    selected = {}
    used_colors = set()
    used_categories = set()
    
    # Process rarities from least to most rare to ensure we get legendary
    rarities = ["COMMON", "RARE", "EPIC", "LEGENDARY"]
    
    for rarity in rarities:
        candidates = rarity_groups.get(rarity, [])
        if not candidates:
            print(f"Warning: No {rarity} cards found")
            continue
            
        # Try to find a card with unused color and category
        best_candidate = None
        
        # First pass: try to find card with both unused color and category
        for card in candidates:
            card_color = card.color_code.upper()
            card_category = card.category.upper()
            if card_color not in used_colors and card_category not in used_categories:
                best_candidate = card
                break
        
        # Second pass: try to find card with unused color
        if not best_candidate:
            for card in candidates:
                card_color = card.color_code.upper()
                if card_color not in used_colors:
                    best_candidate = card
                    break
        
        # Third pass: try to find card with unused category
        if not best_candidate:
            for card in candidates:
                card_category = card.category.upper()
                if card_category not in used_categories:
                    best_candidate = card
                    break
        
        # Fallback: just pick the first available card
        if not best_candidate:
            best_candidate = candidates[0]
        
        # Record selection
        selected[rarity] = best_candidate
        used_colors.add(best_candidate.color_code.upper())
        used_categories.add(best_candidate.category.upper())
        
        print(f"Selected {rarity}: {best_candidate.name} ({best_candidate.color_code}/{best_candidate.category})")
    
    return selected


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    # Pick diverse cards for each rarity
    selected_cards = pick_diverse_rarity_samples(gp_rows)

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    for rarity, gp in selected_cards.items():
        name = gp.name
        art = art_rows.get(name)
        if not art:
            print(f"No art data found for {name}, skipping")
            continue
            
        base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', f"{gp.slug}.png")
        ensure_dir(base_art_path)
        if not os.path.exists(base_art_path):
            seed = 888000 + hash(rarity) % 10000  # Deterministic but varied seed
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

        out_path = os.path.join(settings.OUTPUT_DIR, f"rarity_sample_{rarity.lower()}_{gp.slug}.png")
        card_img.convert('RGB').save(out_path, format='PNG')
        print(f"Rendered {rarity} {gp.category} ({gp.color_code}) {name} -> {out_path}")


if __name__ == '__main__':
    main()
