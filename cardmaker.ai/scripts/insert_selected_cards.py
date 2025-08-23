#!/usr/bin/env python3
import os
import sqlite3

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
    from .generate_cards_and_insert_sqlite import upsert_card_sqlite
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
    from generate_cards_and_insert_sqlite import upsert_card_sqlite


def main() -> None:
    # Pick three diverse cards
    desired = [
        "Tide Manta",            # AZURE / CREATURE
        "Magma Bastion",         # CRIMSON / STRUCTURE
        "Tide Surge Shatter",    # AZURE / ACTION
    ]

    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    color_to_file = {
        'CRIMSON': 'mana_red.png',
        'AZURE': 'mana_blue.png',
        'VERDANT': 'mana_green.png',
        'OBSIDIAN': 'mana_black.png',
        'RADIANT': 'mana_white.png',
        'AETHER': 'mana_orange.png',
    }

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    db_path = os.path.join(settings.PROJECT_ROOT, 'deckport.sqlite3')
    conn = sqlite3.connect(db_path)
    try:
        # Ensure schema exists
        schema_path = os.path.join(settings.PROJECT_ROOT, 'db', 'schema.sqlite.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

        for name in desired:
            art = art_rows[name]
            gp = gp_rows[name]
            # Match sqlite script expectation: base art at output/<slug>.png
            base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', f"{gp.slug}.png")
            ensure_dir(base_art_path)
            if not os.path.exists(base_art_path):
                _ = comfyui_generate(art.image_prompt, seed=999000, save_path=base_art_path, fetch_bytes=False)
                if not _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S):
                    print(f"ComfyUI generation failed (no file) for {name}, skipping")
                    continue

            art_img = load_image(base_art_path)
            frame_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png'))
            glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
            mana_file = color_to_file.get(gp.color_code.upper(), 'mana_white.png')
            mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
            card_img = compose_card(art_img, frame_img, glow_img, mana_icon, gp)

            out_path = os.path.join(settings.OUTPUT_DIR, f"{gp.slug}.png")
            card_img.convert('RGB').save(out_path, format='PNG')

            upsert_card_sqlite(conn, art, gp)
            conn.commit()
            print(f"Inserted {gp.slug} ({gp.name}) into sqlite and rendered -> {out_path}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()

