#!/usr/bin/env python3
import csv
import io
import json
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from copy import deepcopy

import requests
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageMath

try:
    from .config import settings
except ImportError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from config import settings


@dataclass
class ArtRow:
    name: str
    category: str
    color_style: str
    color_code: str
    mana_cost: int
    energy_cost: int
    art_path: str
    frame_path: str
    mana_icon_path: str
    image_prompt: str
    output_path: str
    card_set: str = "Open Portal"


@dataclass
class GameplayRow:
    slug: str
    name: str
    category: str
    rarity: str
    legendary: bool
    color_code: str
    mana_cost: int
    energy_cost: int
    attack: int
    defense: int
    health: int
    base_energy_per_turn: int
    equipment_slots: int
    keywords: str
    limits_json: str
    targeting_json: str
    effects_json: str
    abilities_json: str


def read_csv(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def load_rows(art_csv: str, gp_csv: str) -> Tuple[Dict[str, ArtRow], Dict[str, GameplayRow]]:
    def _safe_int(val: Optional[str], default: int = 0) -> int:
        try:
            return int(val or 0)
        except Exception:
            return default

    # Load gameplay first so we can derive art defaults (slug, color, etc.)
    gp_rows: Dict[str, GameplayRow] = {}
    def _compute_energy_cost(category: str, mana_cost: int, attack: int, defense: int, health: int, rarity: str, legendary: bool) -> int:
        cat = (category or '').upper()
        rarity_u = (rarity or '').upper()
        base_cost: int
        if cat == 'ACTION':
            # Already provided in CSV; ensure bounds 1-6
            return 0  # actions will keep their provided cost
        if cat == 'STRUCTURE':
            # Defensive focus: scale more by health/defense
            base_cost = int(round((max(0, defense) + max(0, health) / 3.0) / 3.0))
        else:
            # Creature: mix attack and health, lighter weight
            base_cost = int(round((max(0, attack) + max(0, health) / 4.0) / 4.0))
        # Nudge by mana curve
        if mana_cost >= 7:
            base_cost += 1
        # Rarity/legendary adjustments
        if rarity_u == 'EPIC':
            base_cost += 1
        if legendary:
            base_cost += 1
        # Clamp to 1..6
        return max(1, min(6, base_cost))

    def _compute_power_score(category: str, attack: int, defense: int, health: int) -> float:
        cat = (category or '').upper()
        if cat == 'CREATURE':
            return max(0, attack) * 1.0 + max(0, health) * 0.5
        if cat == 'STRUCTURE':
            return max(0, defense) * 1.0 + max(0, health) * 0.6
        # ACTION unknown power; return surrogate based on energy tier
        return 1.0

    def _estimate_action_power(effects_json: str, keywords: str) -> float:
        try:
            data = json.loads(effects_json or '[]')
            length = 0
            if isinstance(data, list):
                length = len(data)
            elif isinstance(data, dict):
                # count number of effect entries if dict
                length = len(data)
            # Sum any numeric 'amount' fields lightly
            amount_sum = 0.0
            if isinstance(data, list):
                for eff in data:
                    if isinstance(eff, dict):
                        amt = eff.get('amount')
                        try:
                            amount_sum += float(amt or 0)
                        except Exception:
                            pass
            # Keywords add small weight
            keyword_bonus = max(0, len((keywords or '').split())) * 0.10
            # Base 1.0 + effect count and scaled amounts
            return 1.0 + 0.7 * length + 0.05 * amount_sum + keyword_bonus
        except Exception:
            return 1.0

    def _compute_rarity_score(category: str, mana_cost: int, energy_cost: int, attack: int, defense: int, health: int, effects_json: str, keywords: str) -> float:
        cat = (category or '').upper()
        total_cost = max(1, mana_cost + energy_cost)
        if cat == 'ACTION':
            # Efficiency-based rarity for actions: higher power at lower total cost => higher rarity
            eff = _estimate_action_power(effects_json, keywords) / total_cost
        else:
            # Efficiency-based rarity for heroes
            eff = _compute_power_score(category, attack, defense, health) / total_cost
        return eff

    for r in read_csv(gp_csv):
        row = GameplayRow(
            slug=r['slug'],
            name=r['name'],
            category=r['category'],
            rarity=r['rarity'],
            legendary=(r['legendary'].upper() == 'TRUE'),
            color_code=r['mana_color_code'],
            mana_cost=int(r['mana_cost'] or 0),
            energy_cost=int(r['energy_cost'] or 0),
            attack=int(r['attack'] or 0),
            defense=int(r['defense'] or 0),
            health=int(r['health'] or 0),
            base_energy_per_turn=int(r['base_energy_per_turn'] or 0),
            equipment_slots=int(r['equipment_slots'] or 0),
            keywords=r.get('keywords', ''),
            limits_json=r.get('limits_json', '{}'),
            targeting_json=r.get('targeting_json', '{}'),
            effects_json=r.get('effects_json', '[]'),
            abilities_json=r.get('abilities_json', '[]'),
        )
        # Ensure every card has a non-zero energy_cost per design
        if row.energy_cost <= 0:
            row.energy_cost = _compute_energy_cost(
                row.category,
                row.mana_cost,
                row.attack,
                row.defense,
                row.health,
                row.rarity,
                row.legendary,
            )
        gp_rows[row.name] = row
    # After building all rows, assign rarities by percentiles to ensure a healthy spread
    # Compute rarity score for each
    names = list(gp_rows.keys())
    scores = []
    for n in names:
        r = gp_rows[n]
        s = _compute_rarity_score(r.category, r.mana_cost, r.energy_cost, r.attack, r.defense, r.health, r.effects_json, r.keywords)
        scores.append((n, s))
    # Sort by score ascending
    scores.sort(key=lambda x: x[1])
    total = len(scores)
    # Proportions: COMMON 60%, RARE 25%, EPIC 10%, LEGENDARY 5%
    p_common = 0.60
    p_rare = 0.25
    p_epic = 0.10
    # remaining -> legendary
    idx_common = int(total * p_common)
    idx_rare = idx_common + int(total * p_rare)
    idx_epic = idx_rare + int(total * p_epic)
    for i, (n, _) in enumerate(scores):
        if i < idx_common:
            rarity = 'COMMON'
        elif i < idx_rare:
            rarity = 'RARE'
        elif i < idx_epic:
            rarity = 'EPIC'
        else:
            rarity = 'LEGENDARY'
        r = gp_rows[n]
        r.rarity = rarity
        r.legendary = (rarity == 'LEGENDARY')
        gp_rows[n] = r
    # Helper defaults derived from gameplay/color
    def _default_frame_path(color_code: str) -> str:
        # Expected conventional path; caller can override via CSV
        return os.path.join('assets', 'frames', f"{(color_code or '').lower()}_frame.png")

    def _default_mana_icon_path(color_code: str) -> str:
        return os.path.join('assets', 'icons', f"mana_{(color_code or '').lower()}.png")

    # Load art rows; allow minimal schema (name, image_prompt, output_path)
    art_rows: Dict[str, ArtRow] = {}
    for r in read_csv(art_csv):
        name = r.get('name', '')
        gp = gp_rows.get(name)
        # Image prompt is the only strictly required art field
        image_prompt = r.get('image_prompt', '')
        # Output path defaults to cards_output/<slug>.png if missing
        default_output = f"cards_output/{gp.slug}.png" if gp else f"cards_output/{name}.png"
        output_path = r.get('output_path') or default_output
        # Derive color and category from gameplay if absent in art CSV
        color_code = r.get('mana_color_code') or (gp.color_code if gp else '')
        color_style = r.get('mana_color_style') or ''
        category = r.get('category') or (gp.category if gp else '')
        mana_cost = _safe_int(r.get('mana_cost'), 0)
        energy_cost = _safe_int(r.get('energy_cost'), 0)
        art_path = r.get('art_path') or output_path
        frame_path = r.get('frame_path') or _default_frame_path(color_code)
        mana_icon_path = r.get('mana_icon_path') or _default_mana_icon_path(color_code)
        card_set = r.get('card_set') or 'Open Portal'

        art_rows[name] = ArtRow(
            name=name,
            category=category,
            color_style=color_style,
            color_code=color_code,
            mana_cost=mana_cost,
            energy_cost=energy_cost,
            art_path=art_path,
            frame_path=frame_path,
            mana_icon_path=mana_icon_path,
            image_prompt=image_prompt,
            output_path=output_path,
            card_set=card_set,
        )
    return art_rows, gp_rows


def build_card_filename(gp: GameplayRow, prefix: str = "", suffix: str = "") -> str:
    """Create a filename that includes rarity, mana color, and slug.

    Example: rare_azure_wave-leviathan.png
    Optional prefix/suffix can be used for sample renders.
    """
    rarity = (gp.rarity or "").lower()
    color = (gp.color_code or "").lower()
    base = f"{rarity}_{color}_{gp.slug}"
    if prefix:
        base = f"{prefix}{base}"
    if suffix:
        base = f"{base}{suffix}"
    return f"{base}.png"


def _load_workflow_template() -> Optional[dict]:
    try:
        with open(settings.COMFY_WORKFLOW_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ComfyUI error: cannot read workflow at {settings.COMFY_WORKFLOW_PATH}: {e}")
        return None


def _inject_prompt_and_dims(workflow: dict, prompt_text: str, seed: Optional[int] = None, save_path: Optional[str] = None) -> dict:
    updated = deepcopy(workflow)
    # Prefer setting text on node id '6' from the provided workflow if it matches CLIPTextEncode
    node = updated.get("6") if isinstance(updated, dict) else None
    if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode" and "inputs" in node:
        if "text" in node["inputs"]:
            node["inputs"]["text"] = prompt_text
    else:
        # Fallback: Set positive prompt text on the first CLIPTextEncode node we find
        for _node_id, _node in updated.items():
            try:
                if _node.get("class_type") == "CLIPTextEncode" and "inputs" in _node and "text" in _node["inputs"]:
                    _node["inputs"]["text"] = prompt_text
                    break
            except Exception:
                continue
    # Set RandomNoise seed if provided
    if seed is not None:
        try:
            for _node_id, _node in updated.items():
                if _node.get("class_type") == "RandomNoise" and "inputs" in _node:
                    _node["inputs"]["noise_seed"] = int(seed)
                    break
        except Exception:
            pass
    # Set save path on save-to-path node if provided
    if save_path:
        try:
            for _node_id, _node in updated.items():
                if _node.get("class_type") in ("JWImageSaveToPath", "Image Save To Path") and "inputs" in _node:
                    _node["inputs"]["path"] = save_path
                    break
        except Exception:
            pass
    # Do not alter workflow resolution; only update the prompt text.
    return updated


def _post_prompt(workflow_graph: dict) -> Optional[str]:
    url = f"{settings.COMFY_HOST}/prompt"
    payload = {"prompt": workflow_graph, "client_id": settings.COMFY_CLIENT_ID}
    try:
        resp = requests.post(url, json=payload, timeout=settings.COMFY_TIMEOUT_S)
        if resp.status_code >= 400:
            print(f"ComfyUI error: HTTP {resp.status_code} at {url}. Body: {resp.text}")
            return None
        data = resp.json()
        # ComfyUI returns {'prompt_id': 'uuid', 'client_id': 'deckport-ai'}
        prompt_id = data.get("prompt_id") or data.get("id")
        if not prompt_id:
            print(f"ComfyUI error: unexpected response from {url}: {data}")
            return None
        return prompt_id
    except Exception as e:
        print(f"ComfyUI error posting prompt: {e}")
        return None


def _fetch_first_image_from_history(prompt_id: str) -> Optional[bytes]:
    # Try specific prompt history first
    endpoints = [
        f"{settings.COMFY_HOST}/history/{prompt_id}",
        f"{settings.COMFY_HOST}/history?limit=1",
    ]
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=settings.COMFY_TIMEOUT_S)
            if resp.status_code >= 400:
                continue
            history = resp.json()
            # history can be {prompt_id: {...}} or a list; normalize
            records: Dict[str, dict] = {}
            if isinstance(history, dict) and prompt_id in history:
                records = {prompt_id: history[prompt_id]}
            elif isinstance(history, dict):
                records = history
            # Walk through outputs and pick the first image
            for _, record in records.items():
                outputs = record.get("outputs", {})
                for _, node_out in outputs.items():
                    images = node_out.get("images") or []
                    for img in images:
                        filename = img.get("filename")
                        if not filename:
                            continue
                        subfolder = img.get("subfolder", "")
                        img_type = img.get("type", "output")
                        view_url = (
                            f"{settings.COMFY_HOST}/view?filename="
                            f"{requests.utils.quote(filename)}&subfolder={requests.utils.quote(subfolder)}&type={requests.utils.quote(img_type)}"
                        )
                        view_resp = requests.get(view_url, timeout=settings.COMFY_TIMEOUT_S)
                        if view_resp.status_code < 400:
                            return view_resp.content
        except Exception:
            continue
    return None


def _poll_until_image(prompt_id: str, timeout_s: int) -> Optional[bytes]:
    import time
    deadline = time.time() + max(5, timeout_s)
    sleep_s = 0.5
    while time.time() < deadline:
        img = _fetch_first_image_from_history(prompt_id)
        if img:
            return img
        time.sleep(sleep_s)
        if sleep_s < 2.0:
            sleep_s *= 1.25
    return None


def _wait_for_file(path: str, timeout_s: int) -> bool:
    import time
    from PIL import Image
    deadline = time.time() + max(5, timeout_s)
    last_size = -1
    stable_count = 0
    while time.time() < deadline:
        if os.path.exists(path):
            sz = os.path.getsize(path)
            if sz > 0:
                # require size to be stable twice
                if sz == last_size:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_size = sz
                if stable_count >= 2:
                    try:
                        with Image.open(path) as im:
                            im.verify()
                        return True
                    except Exception:
                        pass
        time.sleep(0.25)
    return False


def comfyui_generate(prompt: str, seed: Optional[int] = None, save_path: Optional[str] = None, fetch_bytes: bool = True) -> Optional[bytes]:
    # Build graph from template
    template = _load_workflow_template()
    if template is None:
        return None
    graph = _inject_prompt_and_dims(template, prompt, seed, save_path)
    # Post prompt
    prompt_id = _post_prompt(graph)
    if not prompt_id:
        return None
    # If an explicit save_path is provided and fetching is disabled, just wait for file
    if save_path and not fetch_bytes:
        ok = _wait_for_file(save_path, settings.COMFY_TIMEOUT_S)
        if not ok:
            print(f"ComfyUI error: file did not appear at {save_path} for prompt {prompt_id}")
        return None
    # Otherwise poll and fetch bytes via history
    img_bytes = _poll_until_image(prompt_id, settings.COMFY_TIMEOUT_S)
    if img_bytes is None:
        print(f"ComfyUI error: no image appeared in history for prompt {prompt_id}")
    return img_bytes


def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def open_image_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert('RGBA')


def load_image(path: str) -> Image.Image:
    return Image.open(path).convert('RGBA')


def render_text(draw: ImageDraw.ImageDraw, text: str, xy: Tuple[int, int], font: ImageFont.FreeTypeFont, fill=(255, 255, 255, 255)):
    draw.text(xy, text, font=font, fill=fill, stroke_width=2, stroke_fill=(0, 0, 0, 255))


def render_text_center(draw: ImageDraw.ImageDraw, text: str, center_xy: Tuple[int, int], font: ImageFont.FreeTypeFont, fill=(255, 255, 255, 255)):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = int(center_xy[0] - w / 2)
    y = int(center_xy[1] - h / 2)
    render_text(draw, text, (x, y), font, fill)


def _premultiply_rgb(img_rgba: Image.Image) -> Image.Image:
    r, g, b, a = img_rgba.split()
    r_p = ImageMath.eval("convert((r*a)/255, 'L')", r=r, a=a)
    g_p = ImageMath.eval("convert((g*a)/255, 'L')", g=g, a=a)
    b_p = ImageMath.eval("convert((b*a)/255, 'L')", b=b, a=a)
    return Image.merge('RGB', (r_p, g_p, b_p))


def _crop_to_alpha_content(img_rgba: Image.Image, threshold: int = 10) -> Image.Image:
    """Crop image to non-transparent alpha bounds (alpha > threshold)."""
    if img_rgba.mode != 'RGBA':
        img_rgba = img_rgba.convert('RGBA')
    a = img_rgba.split()[3]
    # Create binary mask and get bbox
    mask = a.point(lambda x: 255 if x > threshold else 0)
    bbox = mask.getbbox()
    if bbox:
        return img_rgba.crop(bbox)
    return img_rgba

def compose_card(art_img: Image.Image, frame_img: Image.Image, glow_img: Image.Image, mana_icon: Image.Image, gp: GameplayRow) -> Image.Image:
    W, H = settings.CANVAS_W, settings.CANVAS_H
    # 1) Black frame background 1500x2100
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 255))

    # 2) Generated art centered on black frame, preserving aspect
    # Scale to fit without cropping
    art_w, art_h = art_img.size
    scale = min(W / art_w, H / art_h)
    new_w = max(1, int(art_w * scale))
    new_h = max(1, int(art_h * scale))
    art_resized = art_img.resize((new_w, new_h))
    off_x = (W - new_w) // 2
    off_y = (H - new_h) // 2
    canvas.alpha_composite(art_resized, (off_x, off_y))

    # 3) Overlay glow layer under the frame
    try:
        glow_resized = glow_img.resize((W, H)).convert('RGBA')
        # Apply two premultiplied Screen passes to intensify glow
        for _ in range(2):
            base_rgb = canvas.convert('RGB')
            glow_pm_rgb = _premultiply_rgb(glow_resized)
            screened = ImageChops.screen(base_rgb, glow_pm_rgb)
            canvas = Image.merge('RGBA', (*screened.split(), canvas.split()[3]))
    except Exception:
        pass

    # 8) Card set icon overlay as full-canvas alpha composite (same as rarity overlay)
    try:
        set_file = 'set_icon.png'
        simg_path = os.path.join(settings.CARD_ELEMENTS_DIR, set_file)
        if os.path.exists(simg_path):
            simg = Image.open(simg_path).convert('RGBA').resize((W, H), Image.LANCZOS)
            canvas.alpha_composite(simg, (0, 0))
    except Exception:
        pass

    # 4) Overlay the frame; if Legendary, use the special legendary frame
    frame_to_use = frame_img
    if (gp.rarity or '').upper() == 'LEGENDARY':
        try:
            legend_frame = Image.open(os.path.join(settings.CARD_ELEMENTS_DIR, 'legendary_frame.png')).convert('RGBA')
            frame_to_use = legend_frame
        except Exception:
            frame_to_use = frame_img
    frame_resized = frame_to_use.resize((W, H))
    canvas.alpha_composite(frame_resized, (0, 0))

    # Prepare mana overlay (full-canvas). Your mana assets match the card canvas size
    mana_icon_resized = mana_icon.convert('RGBA').resize((W, H), Image.LANCZOS)
    mana_icon_xy = (0, 0)

    # Text layers
    draw = ImageDraw.Draw(canvas)
    try:
        font_big = ImageFont.truetype(settings.FONT_PATH, size=int(H * 0.08))
        font_small = ImageFont.truetype(settings.FONT_PATH, size=int(H * 0.06))
        font_name = ImageFont.truetype(settings.FONT_PATH, size=int(H * 0.07))
        font_label = ImageFont.truetype(settings.FONT_PATH, size=int(H * 0.024))
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_name = font_big
        font_label = font_small

    # Hide mana and energy numbers per request (previously top-right)

    # Hide ATK/HP/DEF/COST stats per request
    # Hide any stray dot or placeholder layers by avoiding other text draws

    # 5) Card name using Chakra Petch SemiBold at specified coordinates (centered)
    # Name size double the card type size
    try:
        font_name = ImageFont.truetype(settings.FONT_PATH, size=int(H * 0.035))
    except Exception:
        font_name = ImageFont.load_default()
    # Center horizontally on screen; keep vertical near top per prior spec
    name_center_x = W // 2
    name_center_y = int(round(179.7)) + 15
    # Name color: #00d2ff
    render_text_center(draw, gp.name, (name_center_x, name_center_y), font_name, fill=(0, 210, 255, 255))

    # Optional: Category label moved far down and same color as name
    cat_y = min(int(H * 0.13) + 1645, H - 10)
    render_text_center(draw, gp.category.title(), (int(W * 0.5), cat_y), font_label, fill=(0, 210, 255, 255))


    # 6) Place mana overlay (full-canvas)
    canvas.alpha_composite(mana_icon_resized, mana_icon_xy)

    # 7) Finally, place rarity overlay on top as full-canvas (skip for LEGENDARY which uses special frame)
    try:
        rarity = (gp.rarity or '').upper()
        if rarity != 'LEGENDARY':
            icon_map = {
                'COMMON': 'common_icon.png',
                'RARE': 'rare_icon.png',
                'EPIC': 'epic_icon.png',
            }
            icon_file = icon_map.get(rarity)
            if icon_file:
                rimg = Image.open(os.path.join(settings.CARD_ELEMENTS_DIR, icon_file)).convert('RGBA')
                rimg = rimg.resize((W, H), Image.LANCZOS)
                canvas.alpha_composite(rimg, (0, 0))
    except Exception:
        pass

    # 8) Card set icon overlay as full-canvas, drawn last (e.g., Open Portal)
    try:
        # Prefer specific per-rarity icon if present
        if (gp.rarity or '').upper() == 'LEGENDARY':
            candidates = ['set_icon_ledgendary.png', 'set_icon_legendary.png']
        else:
            candidates = ['set_icon.png', 'set_icon.png']
        for fname in candidates:
            set_path = os.path.join(settings.CARD_ELEMENTS_DIR, fname)
            if os.path.exists(set_path):
                simg = Image.open(set_path).convert('RGBA').resize((W, H), Image.LANCZOS)
                canvas.alpha_composite(simg, (0, 0))
                break
    except Exception:
        pass
    return canvas


if __name__ == '__main__':
    # This module now provides rendering and generation helpers only.
    # Use scripts/generate_cards_and_insert_sqlite.py for DB insertion.
    pass

