#!/usr/bin/env python3
import json
import os
import sqlite3
from dataclasses import dataclass  # noqa: F401
from typing import Dict, Optional, Tuple  # noqa: F401

import requests  # noqa: F401
from PIL import Image, ImageDraw, ImageFont  # noqa: F401

try:
    from .config import settings
    from .generate_cards_and_insert import (
        ArtRow,
        GameplayRow,
        load_rows,
        comfyui_generate,
        ensure_dir,
        load_image,
        compose_card,
    )
except ImportError:
    # Allow running this file directly: `python scripts/generate_cards_and_insert_sqlite.py`
    # by falling back to local imports when no package context is present.
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from config import settings
    from generate_cards_and_insert import (
        ArtRow,
        GameplayRow,
        load_rows,
        comfyui_generate,
        ensure_dir,
        load_image,
        compose_card,
    )


def upsert_card_sqlite(conn: sqlite3.Connection, art: ArtRow, gp: GameplayRow):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cards (slug, name, category, rarity, legendary, color_code, energy_cost, equipment_slots)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            name=excluded.name,
            category=excluded.category,
            rarity=excluded.rarity,
            legendary=excluded.legendary,
            color_code=excluded.color_code,
            energy_cost=excluded.energy_cost,
            equipment_slots=excluded.equipment_slots
        """,
        (
            gp.slug,
            gp.name,
            gp.category,
            gp.rarity,
            1 if gp.legendary else 0,
            gp.color_code,
            gp.energy_cost,
            gp.equipment_slots,
        ),
    )
    cur.execute("SELECT id FROM cards WHERE slug = ?", (gp.slug,))
    card_id = cur.fetchone()[0]

    # Mana cost
    cur.execute("DELETE FROM card_mana_costs WHERE card_id = ?", (card_id,))
    cur.execute(
        "INSERT INTO card_mana_costs (card_id, color_code, amount) VALUES (?, ?, ?)",
        (card_id, gp.color_code, gp.mana_cost),
    )

    # Stats
    cur.execute(
        """
        INSERT INTO card_stats (card_id, attack, defense, health, base_energy_per_turn)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(card_id) DO UPDATE SET
            attack=excluded.attack,
            defense=excluded.defense,
            health=excluded.health,
            base_energy_per_turn=excluded.base_energy_per_turn
        """,
        (card_id, gp.attack, gp.defense, gp.health, gp.base_energy_per_turn),
    )

    # Limits
    try:
        limits = json.loads(gp.limits_json or '{}')
    except Exception:
        limits = {}
    cur.execute(
        """
        INSERT INTO card_limits (card_id, max_uses_per_match, charges_max, charge_rule)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(card_id) DO UPDATE SET
            max_uses_per_match=excluded.max_uses_per_match,
            charges_max=excluded.charges_max,
            charge_rule=excluded.charge_rule
        """,
        (
            card_id,
            limits.get('max_uses_per_match'),
            limits.get('charges_max'),
            json.dumps(limits.get('charge_rule')) if limits.get('charge_rule') is not None else None,
        ),
    )

    # Targeting
    try:
        targeting = json.loads(gp.targeting_json or '{}')
    except Exception:
        targeting = {}
    cur.execute(
        """
        INSERT INTO card_targeting (card_id, target_friendly, target_enemy, target_self)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(card_id) DO UPDATE SET
            target_friendly=excluded.target_friendly,
            target_enemy=excluded.target_enemy,
            target_self=excluded.target_self
        """,
        (
            card_id,
            1 if targeting.get('friendly', False) else 0,
            1 if targeting.get('enemy', True) else 0,
            1 if targeting.get('self', False) else 0,
        ),
    )


def main():
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    db_path = os.path.join(settings.PROJECT_ROOT, 'deckport.sqlite3')
    conn = sqlite3.connect(db_path)
    try:
        # Ensure schema is loaded
        schema_path = os.path.join(settings.PROJECT_ROOT, 'db', 'schema.sqlite.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

        for name, art in art_rows.items():
            gp = gp_rows.get(name)
            if gp is None:
                print(f"Skipping {name}: no gameplay row")
                continue

            # Generate base art if missing (save via ComfyUI to output/<slug>.png)
            base_art_path = os.path.join(settings.PROJECT_ROOT, 'output', f"{gp.slug}.png")
            ensure_dir(base_art_path)
            if not os.path.exists(base_art_path):
                _ = comfyui_generate(art.image_prompt, save_path=base_art_path, fetch_bytes=False)
                # Wait until file is fully written
                from .generate_cards_and_insert import _wait_for_file
                if not _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S):
                    print(f"ComfyUI generation failed for {name}, skipping art")
                    continue

            # Compose using provided card elements
            art_img = load_image(base_art_path)
            frame_path = os.path.join(settings.CARD_ELEMENTS_DIR, 'frame.png')
            frame_img = load_image(frame_path)
            glow_img = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, 'glow.png'))
            # Map color_code -> mana file names present in card_elements
            color_to_file = {
                'CRIMSON': 'mana_red.png',
                'AZURE': 'mana_blue.png',
                'VERDANT': 'mana_green.png',
                'OBSIDIAN': 'mana_black.png',
                'RADIANT': 'mana_white.png',
                'AETHER': 'mana_orange.png',
            }
            mana_file = color_to_file.get(gp.color_code.upper(), 'mana_white.png')
            mana_icon = load_image(os.path.join(settings.CARD_ELEMENTS_DIR, mana_file))
            card_img = compose_card(art_img, frame_img, glow_img, mana_icon, gp)

            final_path = os.path.join(settings.OUTPUT_DIR, f"{gp.slug}.png")
            card_img.convert('RGB').save(final_path, format='PNG')

            upsert_card_sqlite(conn, art, gp)
            conn.commit()

            print(f"Created card {name} -> {final_path}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()

