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
        build_card_filename,
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
        build_card_filename,
    )


def pick_varied_names(gp_rows, max_count=10):
    # Group by (color, category)
    buckets = defaultdict(list)
    for row in gp_rows.values():
        key = (row.color_code.upper(), (row.category or '').upper())
        buckets[key].append(row.name)

    # Preferred order of colors and categories
    colors = ["CRIMSON", "AZURE", "VERDANT", "OBSIDIAN", "RADIANT", "AETHER"]
    categories = ["CREATURE", "STRUCTURE", "ACTION"]

    selected = []
    # First pass: one per color-category where available
    for cat in categories:
        for col in colors:
            if len(selected) >= max_count:
                break
            names = buckets.get((col, cat))
            if names:
                selected.append(names[0])
        if len(selected) >= max_count:
            break

    # Fill up remaining slots with any not yet chosen, preferring different colors
    if len(selected) < max_count:
        seen = set(selected)
        for col in colors:
            for cat in categories:
                for n in buckets.get((col, cat), []):
                    if n not in seen:
                        selected.append(n)
                        seen.add(n)
                        if len(selected) >= max_count:
                            break
                if len(selected) >= max_count:
                    break
            if len(selected) >= max_count:
                break
    return selected[:max_count]


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    names = pick_varied_names(gp_rows, max_count=10)

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    for idx, name in enumerate(names):
        art = art_rows[name]
        gp = gp_rows[name]
        base_art_file = build_card_filename(gp)
        base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', base_art_file)
        ensure_dir(base_art_path)
        if not os.path.exists(base_art_path):
            _ = comfyui_generate(art.image_prompt, seed=987654321 + idx, save_path=base_art_path, fetch_bytes=False)
            if not _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S):
                print(f"ComfyUI generation failed (no file) for {name}, skipping")
                continue

        art_img = load_image(base_art_path)
        frame_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png'))
        glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
        mana_file = color_to_file.get(gp.color_code.upper(), 'mana_white.png')
        mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
        card_img = compose_card(art_img, frame_img, glow_img, mana_icon, gp)

        out_file = build_card_filename(gp)
        out_path = os.path.join(settings.OUTPUT_DIR, out_file)
        card_img.convert('RGB').save(out_path, format='PNG')
        print(f"Generated card {name} ({gp.color_code}/{gp.category}) -> {out_path}")


if __name__ == '__main__':
    main()

