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


def main() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_art.csv')
    gp_csv = os.path.join(settings.PROJECT_ROOT, 'data', 'cards_gameplay.csv')
    art_rows, gp_rows = load_rows(art_csv, gp_csv)

    # Select first five names deterministically
    names = list(gp_rows.keys())[:5]

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
            # Use a different seed and set unique save path; do NOT fetch bytes, let Comfy save to disk
            wf_save_path = base_art_path
            _ = comfyui_generate(art.image_prompt, seed=123456789 + idx, save_path=wf_save_path, fetch_bytes=False)
            # Wait for file to be fully written
            ok = _wait_for_file(base_art_path, settings.COMFY_TIMEOUT_S)
            if not ok:
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
        print(f"Generated card {name} -> {out_path}")


if __name__ == '__main__':
    main()

