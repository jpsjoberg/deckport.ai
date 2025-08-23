#!/usr/bin/env python3
import os
from typing import List

try:
    from .config import settings
    from .generate_cards_and_insert import (
        load_rows,
        comfyui_generate,
        ensure_dir,
        load_image,
        compose_card,
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
    )


def pick_names(gp_names: List[str]) -> List[str]:
    # Choose two deterministic names if available
    preferred = [
        "Tide Manta",
        "Wave Leviathan",
    ]
    result: List[str] = []
    for p in preferred:
        if p in gp_names:
            result.append(p)
        if len(result) == 2:
            return result
    # Fallback: first two
    return gp_names[:2]


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    names = pick_names(list(gp_rows.keys()))
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    for name in names:
        art = art_rows[name]
        gp = gp_rows[name]
        base_art_path = os.path.join(settings.PROJECT_ROOT, art.output_path)
        ensure_dir(base_art_path)
        if not os.path.exists(base_art_path):
            img_bytes = comfyui_generate(art.image_prompt)
            if img_bytes:
                with open(base_art_path, 'wb') as w:
                    w.write(img_bytes)
            else:
                print(f"ComfyUI generation failed for {name}, skipping")
                continue

        art_img = load_image(base_art_path)
        frame_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png'))
        glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
        mana_file = color_to_file.get(gp.color_code.upper(), 'mana_white.png')
        mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
        card_img = compose_card(art_img, frame_img, glow_img, mana_icon, gp)

        final_path = os.path.join(settings.OUTPUT_DIR, f"sample_{gp.slug}.png")
        card_img.convert('RGB').save(final_path, format='PNG')
        print(f"Rendered sample card {name} -> {final_path}")


if __name__ == '__main__':
    main()

