#!/usr/bin/env python3
import os

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


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    # Pick one card for each rarity
    wanted = ["COMMON", "RARE", "EPIC", "LEGENDARY"]
    pick = {}
    for rarity in wanted:
        for row in gp_rows.values():
            if (row.rarity or '').upper() == rarity:
                pick[rarity] = row.name
                break

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    for rarity in wanted:
        name = pick.get(rarity)
        if not name:
            print(f"No card found for rarity {rarity}")
            continue
        art = art_rows[name]
        gp = gp_rows[name]
        base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', f"{gp.slug}.png")
        ensure_dir(base_art_path)
        if not os.path.exists(base_art_path):
            _ = comfyui_generate(art.image_prompt, seed=555000 + wanted.index(rarity), save_path=base_art_path, fetch_bytes=False)
            if not _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S):
                print(f"ComfyUI generation failed (no file) for {name}, skipping")
                continue

        art_img = load_image(base_art_path)
        frame_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png'))
        glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
        mana_file = color_to_file.get(gp.color_code.upper(), 'mana_white.png')
        mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
        card_img = compose_card(art_img, frame_img, glow_img, mana_icon, gp)

        out_path = os.path.join(settings.OUTPUT_DIR, f"sample_{rarity.lower()}_{gp.slug}.png")
        card_img.convert('RGB').save(out_path, format='PNG')
        print(f"Rendered {rarity} card {name} -> {out_path}")


if __name__ == '__main__':
    main()

