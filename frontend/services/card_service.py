"""
Card Service for Deckport Admin Panel
Integrates cardmaker.ai functionality for card generation and rendering
"""

import os
import json
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageMath
import logging

from .comfyui_service import get_comfyui_service

logger = logging.getLogger(__name__)

# Configuration
CARDMAKER_OUTPUT_DIR = os.environ.get("CARDMAKER_OUTPUT_DIR", "/home/jp/deckport.ai/cardmaker.ai/cards_output")
CARDMAKER_ELEMENTS_DIR = os.environ.get("CARDMAKER_ELEMENTS_DIR", "/home/jp/deckport.ai/cardmaker.ai/card_elements")
CARDMAKER_FONT_PATH = os.environ.get("CARDMAKER_FONT_PATH", "/home/jp/deckport.ai/cardmaker.ai/Chakra_Petch/ChakraPetch-SemiBold.ttf")

# Canvas dimensions
CANVAS_WIDTH = 1500
CANVAS_HEIGHT = 2100

# Color mappings
MANA_COLORS = {
    'CRIMSON': {'name': 'Crimson', 'icon': 'mana_red.png', 'color': '#DC2626'},
    'AZURE': {'name': 'Azure', 'icon': 'mana_blue.png', 'color': '#2563EB'},
    'VERDANT': {'name': 'Verdant', 'icon': 'mana_green.png', 'color': '#16A34A'},
    'OBSIDIAN': {'name': 'Obsidian', 'icon': 'mana_black.png', 'color': '#1F2937'},
    'RADIANT': {'name': 'Radiant', 'icon': 'mana_white.png', 'color': '#F59E0B'},
    'AETHER': {'name': 'Aether', 'icon': 'mana_orange.png', 'color': '#EA580C'}
}


class CardService:
    """Service for card generation, rendering, and database operations"""
    
    def __init__(self):
        self.comfyui = get_comfyui_service()
        
        # PostgreSQL connection config
        self.pg_config = {
            'host': os.environ.get('DB_HOST', '127.0.0.1'),
            'port': int(os.environ.get('DB_PORT', '5432')),
            'database': os.environ.get('DB_NAME', 'deckport'),
            'user': os.environ.get('DB_USER', 'deckport_app'),
            'password': os.environ.get('DB_PASSWORD', 'N0D3-N0D3-N0D3#M0nk3y33')
        }
        
        # Ensure output directory exists
        os.makedirs(CARDMAKER_OUTPUT_DIR, exist_ok=True)
    
    def get_pg_connection(self):
        """Get PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            conn.autocommit = False
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return None
    
    def create_card(self, card_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new card in the PostgreSQL database
        
        Args:
            card_data: Dictionary containing card information
            
        Returns:
            Card ID if successful, None otherwise
        """
        conn = self.get_pg_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Generate product_sku from name
                product_sku = card_data['name'].upper().replace(' ', '_').replace("'", "")
                
                # Insert into card_catalog
                cursor.execute("""
                    INSERT INTO card_catalog (
                        product_sku, name, category, rarity, subtype,
                        base_stats, flavor_text, rules_text, mana_colors,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    ) RETURNING id
                """, (
                    product_sku,
                    card_data['name'],
                    card_data['category'].lower(),
                    card_data['rarity'].lower(),
                    card_data.get('subtype', ''),
                    json.dumps(card_data.get('base_stats', {})),
                    card_data.get('flavor_text', ''),
                    card_data.get('rules_text', ''),
                    card_data.get('mana_colors', ['AETHER'])
                ))
                
                result = cursor.fetchone()
                card_id = result['id']
                
                conn.commit()
                logger.info(f"Created card: {card_data['name']} (ID: {card_id})")
                return card_id
                
        except Exception as e:
            logger.error(f"Failed to create card: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_card(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Get card data by ID from PostgreSQL"""
        conn = self.get_pg_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, product_sku, name, category, rarity, subtype,
                           base_stats, flavor_text, rules_text, mana_colors,
                           artwork_url, static_url, video_url, has_animation,
                           created_at, updated_at
                    FROM card_catalog
                    WHERE id = %s
                """, (card_id,))
                
                row = cursor.fetchone()
                if row:
                    card_data = dict(row)
                    # Add compatibility fields for existing code
                    card_data['slug'] = card_data['name'].lower().replace(' ', '_').replace("'", "")
                    if card_data.get('mana_colors'):
                        card_data['color_code'] = card_data['mana_colors'][0]
                    return card_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to get card {card_id}: {e}")
            return None
        finally:
            conn.close()
    
    def get_cards(self, filters: Dict[str, Any] = None, 
                  page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
        """
        Get cards with optional filtering and pagination from PostgreSQL
        
        Returns:
            Tuple of (cards_list, total_count)
        """
        # Use the existing get_card_templates method which already handles PostgreSQL
        result = self.get_card_templates(filters, page, per_page)
        
        cards = result.get('templates', [])
        total_count = result.get('pagination', {}).get('total', 0)
        
        # Add compatibility fields and art status
        for card in cards:
            if not card.get('slug'):
                card['slug'] = card['name'].lower().replace(' ', '_').replace("'", "")
            
            # Add art status
            art_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card['slug']}.png")
            card['has_art'] = os.path.exists(art_path)
            
            # Add color compatibility
            if card.get('mana_colors') and not card.get('color_code'):
                card['color_code'] = card['mana_colors'][0] if card['mana_colors'] else 'AETHER'
        
        return cards, total_count
    
    def generate_card_art(self, card_id: int, prompt: str, seed: Optional[int] = None) -> bool:
        """
        Generate artwork for a card using ComfyUI
        
        Args:
            card_id: Database ID of the card
            prompt: Text prompt for art generation
            seed: Optional seed for reproducible generation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get card data
            card = self.get_card(card_id)
            if not card:
                logger.error(f"Card {card_id} not found")
                return False
            
            # Generate art via ComfyUI
            logger.info(f"Generating art for card {card['name']}")
            image_data = self.comfyui.generate_card_art(prompt, seed)
            
            if not image_data:
                logger.error(f"ComfyUI generation failed for card {card['name']}")
                return False
            
            # Save raw art
            art_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"raw_{card['slug']}.png")
            with open(art_path, 'wb') as f:
                f.write(image_data)
            
            # Compose final card (full composite with black background)
            final_card = self.compose_card(card, art_path, transparent_bg=False)
            if final_card:
                final_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card['slug']}.png")
                final_card.save(final_path, format='PNG')
                logger.info(f"Card art generated successfully: {final_path}")
                return True
            else:
                logger.error(f"Failed to compose final card for {card['name']}")
                return False
                
        except Exception as e:
            logger.error(f"Art generation failed for card {card_id}: {e}")
            return False
    
    def generate_frame_only(self, card_id: int) -> bool:
        """
        Generate frame-only composite for video overlay
        
        Args:
            card_id: Database ID of the card
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get card data
            card = self.get_card(card_id)
            if not card:
                logger.error(f"Card {card_id} not found")
                return False
            
            # Create transparent 1x1 pixel as "art"
            transparent_art_path = os.path.join(CARDMAKER_OUTPUT_DIR, "transparent_pixel.png")
            transparent_pixel = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            transparent_pixel.save(transparent_art_path, format='PNG')
            
            # Compose frame-only with transparent background
            logger.info(f"Generating frame-only for card {card['name']}")
            frame_only = self.compose_card(card, transparent_art_path, transparent_bg=True)
            
            if frame_only:
                frame_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card['slug']}_frame.png")
                frame_only.save(frame_path, format='PNG')
                logger.info(f"Frame-only generated successfully: {frame_path}")
                
                # Clean up temporary file
                if os.path.exists(transparent_art_path):
                    os.remove(transparent_art_path)
                
                return True
            else:
                logger.error(f"Failed to compose frame-only for {card['name']}")
                return False
                
        except Exception as e:
            logger.error(f"Frame-only generation failed for card {card_id}: {e}")
            return False
    
    def generate_video_from_static(self, card_id: int, static_art_path: str) -> bool:
        """
        Generate video background from static art using CardVideo.json workflow
        
        Args:
            card_id: Database ID of the card
            static_art_path: Path to the static artwork
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get card data
            card = self.get_card(card_id)
            if not card:
                logger.error(f"Card {card_id} not found")
                return False
            
            # Load video workflow template
            video_workflow_path = '/home/jp/deckport.ai/cardmaker.ai/CardVideo.json'
            with open(video_workflow_path, 'r') as f:
                workflow = json.load(f)
            
            # Create video prompt based on card properties
            video_prompt = self._create_video_prompt(card)
            output_filename = card['slug']
            
            # Update workflow with image and prompt
            workflow = self._inject_video_workflow_data(workflow, static_art_path, video_prompt, output_filename)
            
            logger.info(f"Generating video for card {card['name']}")
            
            # Submit to ComfyUI
            prompt_id = self.comfyui.submit_prompt(workflow)
            if not prompt_id:
                logger.error(f"Failed to submit video generation for {card['name']}")
                return False
            
            # Wait for video completion (longer timeout for video)
            video_data = self.comfyui.wait_for_completion(prompt_id, max_wait=300)  # 5 minutes
            
            if video_data:
                # Save video to CDN
                video_dir = '/home/jp/deckport.ai/static/cards/videos'
                os.makedirs(video_dir, exist_ok=True)
                
                video_filename = f"{card['slug']}.mp4"
                video_path = os.path.join(video_dir, video_filename)
                
                with open(video_path, 'wb') as f:
                    f.write(video_data)
                
                logger.info(f"Video generated successfully: {video_path}")
                return True
            else:
                logger.error(f"Video generation failed for {card['name']}")
                return False
                
        except Exception as e:
            logger.error(f"Video generation failed for card {card_id}: {e}")
            return False
    
    def _create_video_prompt(self, card: Dict[str, Any]) -> str:
        """Create video-specific prompt based on card properties"""
        name = card['name']
        category = card.get('category', 'creature').lower()
        rarity = card.get('rarity', 'common').lower()
        color_code = card.get('color_code', 'AETHER')
        
        # Special prompt for Burn Knight
        if name == "Burn Knight":
            return """A powerful fire knight in legendary armor, subtle breathing animation with chest rising and falling gently. Flames dancing softly around the armor edges, sword blade glowing with inner fire that pulses slowly. Eyes glowing with warm orange light that intensifies and dims rhythmically. Cape flowing gently in magical wind. Ember particles floating upward slowly and continuously. Armor plates gleaming with reflected firelight. Background flames swaying hypnotically. Seamless 3-second loop, cinemagraph style with most elements static but key fire elements in constant subtle motion. No abrupt changes, smooth continuous animation."""
        
        # Category-specific effects
        category_effects = {
            'hero': 'subtle breathing, armor gleaming, eyes glowing with power, cape flowing softly',
            'creature': 'natural breathing, ambient magical aura, environmental response',
            'action_fast': 'energy crackling, spell effects building, dynamic forces',
            'action_slow': 'grand magical ritual, environmental transformation, epic effects',
            'equipment': 'magical gleaming, energy pulsing, mystical aura effects',
            'enchantment': 'magical energy swirling, mystical patterns forming',
            'artifact': 'ancient power humming, mystical energy radiating',
            'structure': 'ambient atmosphere, architectural elements responding'
        }
        
        # Color-specific effects
        color_effects = {
            'CRIMSON': 'fire particles dancing, warm glow pulsing, flame effects',
            'AZURE': 'frost crystals forming, cool mist swirling, water effects',
            'VERDANT': 'leaves rustling, natural energy flowing, growth effects',
            'OBSIDIAN': 'shadow tendrils moving, dark energy crackling, void effects',
            'RADIANT': 'divine light pulsing, golden particles, holy aura',
            'AETHER': 'cosmic energy flowing, prismatic effects, ethereal mist'
        }
        
        base_effects = category_effects.get(category, 'subtle magical effects')
        color_fx = color_effects.get(color_code, 'mystical energy')
        
        return f"{name}, {rarity} {category}, {base_effects}, {color_fx}. Seamless 3-second loop, cinemagraph style with subtle continuous motion. No abrupt changes, smooth animation."
    
    def _inject_video_workflow_data(self, workflow: Dict, image_path: str, video_prompt: str, output_filename: str) -> Dict:
        """Inject data into CardVideo.json workflow"""
        updated = workflow.copy()
        
        # Update image input (LoadImage nodes)
        image_filename = os.path.basename(image_path)
        if "148" in updated:
            updated["148"]["inputs"]["image"] = image_filename
        if "73" in updated:
            updated["73"]["inputs"]["image"] = image_filename
        
        # Update prompt (CLIPTextEncode node)
        if "105" in updated:
            updated["105"]["inputs"]["text"] = video_prompt
        
        # Update output filename (SaveVideo node)
        if "69" in updated:
            updated["69"]["inputs"]["filename_prefix"] = f"video/{output_filename}"
        
        return updated
    
    def compose_card(self, card: Dict[str, Any], art_path: str, transparent_bg: bool = False) -> Optional[Image.Image]:
        """
        Compose final card image with art, frame, and text elements
        
        Args:
            card: Card data dictionary
            art_path: Path to generated artwork
            transparent_bg: If True, use transparent background for frame-only composites
            
        Returns:
            Composed PIL Image or None if failed
        """
        try:
            # Load components
            art_img = Image.open(art_path).convert('RGBA')
            frame_path = os.path.join(CARDMAKER_ELEMENTS_DIR, 'frame.png')
            frame_img = Image.open(frame_path).convert('RGBA')
            glow_path = os.path.join(CARDMAKER_ELEMENTS_DIR, 'glow.png')
            glow_img = Image.open(glow_path).convert('RGBA')
            
            # Get mana icon
            color_info = MANA_COLORS.get(card['color_code'], MANA_COLORS['RADIANT'])
            mana_path = os.path.join(CARDMAKER_ELEMENTS_DIR, color_info['icon'])
            mana_img = Image.open(mana_path).convert('RGBA')
            
            # Create canvas - transparent for frame-only, black for full cards
            if transparent_bg:
                canvas = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))  # Transparent
            else:
                canvas = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 255))  # Black
            
            # Scale and center artwork
            art_w, art_h = art_img.size
            scale = min(CANVAS_WIDTH / art_w, CANVAS_HEIGHT / art_h)
            new_w = max(1, int(art_w * scale))
            new_h = max(1, int(art_h * scale))
            art_resized = art_img.resize((new_w, new_h))
            
            off_x = (CANVAS_WIDTH - new_w) // 2
            off_y = (CANVAS_HEIGHT - new_h) // 2
            canvas.alpha_composite(art_resized, (off_x, off_y))
            
            # Add glow effect
            glow_resized = glow_img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            canvas = self._apply_glow(canvas, glow_resized)
            
            # Add frame (legendary gets special frame)
            frame_to_use = frame_img
            if card['rarity'] == 'LEGENDARY':
                legendary_path = os.path.join(CARDMAKER_ELEMENTS_DIR, 'legendary_frame.png')
                if os.path.exists(legendary_path):
                    frame_to_use = Image.open(legendary_path).convert('RGBA')
            
            frame_resized = frame_to_use.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            canvas.alpha_composite(frame_resized, (0, 0))
            
            # Add mana icon
            mana_resized = mana_img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            canvas.alpha_composite(mana_resized, (0, 0))
            
            # Add text elements
            canvas = self._add_card_text(canvas, card)
            
            # Add rarity icon (except legendary which uses special frame)
            if card['rarity'] != 'LEGENDARY':
                rarity_icon = self._get_rarity_icon(card['rarity'])
                if rarity_icon:
                    rarity_resized = rarity_icon.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
                    canvas.alpha_composite(rarity_resized, (0, 0))
            
            # Add set icon
            set_icon = self._get_set_icon(card['rarity'])
            if set_icon:
                set_resized = set_icon.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
                canvas.alpha_composite(set_resized, (0, 0))
            
            return canvas.convert('RGB')
            
        except Exception as e:
            logger.error(f"Card composition failed: {e}")
            return None
    
    def _apply_glow(self, base: Image.Image, glow: Image.Image) -> Image.Image:
        """Apply glow effect using screen blend mode (matches cardmaker implementation)"""
        try:
            from PIL import ImageChops, ImageMath
            
            # Apply two premultiplied Screen passes to intensify glow (same as cardmaker)
            for _ in range(2):
                base_rgb = base.convert('RGB')
                glow_pm_rgb = self._premultiply_rgb(glow)
                screened = ImageChops.screen(base_rgb, glow_pm_rgb)
                base = Image.merge('RGBA', (*screened.split(), base.split()[3]))
            
            return base
        except Exception:
            return base
    
    def _premultiply_rgb(self, img_rgba: Image.Image) -> Image.Image:
        """Premultiply RGB channels by alpha (matches cardmaker implementation)"""
        try:
            r, g, b, a = img_rgba.split()
            r_p = ImageMath.eval("convert((r*a)/255, 'L')", r=r, a=a)
            g_p = ImageMath.eval("convert((g*a)/255, 'L')", g=g, a=a)
            b_p = ImageMath.eval("convert((b*a)/255, 'L')", b=b, a=a)
            return Image.merge('RGB', (r_p, g_p, b_p))
        except Exception:
            return img_rgba.convert('RGB')
    
    def _add_card_text(self, canvas: Image.Image, card: Dict[str, Any]) -> Image.Image:
        """Add text elements to the card"""
        try:
            draw = ImageDraw.Draw(canvas)
            
            # Load fonts (optimized sizes)
            try:
                font_name = ImageFont.truetype(CARDMAKER_FONT_PATH, size=int(CANVAS_HEIGHT * 0.032))
                font_label = ImageFont.truetype(CARDMAKER_FONT_PATH, size=int(CANVAS_HEIGHT * 0.024))
            except Exception:
                font_name = ImageFont.load_default()
                font_label = ImageFont.load_default()
            
            # Card name (centered, blue color, moved down 2px)
            name_x = CANVAS_WIDTH // 2
            name_y = int(179.7) + 15 + 2
            self._draw_text_centered(draw, card['name'], (name_x, name_y), font_name, (0, 210, 255, 255))
            
            # Category label
            cat_y = min(int(CANVAS_HEIGHT * 0.13) + 1645, CANVAS_HEIGHT - 10)
            category_text = card['category'].title()
            self._draw_text_centered(draw, category_text, (CANVAS_WIDTH // 2, cat_y), font_label, (0, 210, 255, 255))
            
            return canvas
            
        except Exception as e:
            logger.error(f"Failed to add text: {e}")
            return canvas
    
    def _draw_text_centered(self, draw: ImageDraw.ImageDraw, text: str, center: Tuple[int, int], 
                           font: ImageFont.FreeTypeFont, fill: Tuple[int, int, int, int]):
        """Draw text centered at given coordinates with stroke"""
        try:
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x = int(center[0] - w / 2)
            y = int(center[1] - h / 2)
            
            draw.text((x, y), text, font=font, fill=fill, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        except Exception as e:
            logger.error(f"Text drawing failed: {e}")
    
    def _get_rarity_icon(self, rarity: str) -> Optional[Image.Image]:
        """Get rarity icon image"""
        try:
            icon_map = {
                'COMMON': 'common_icon.png',
                'RARE': 'rare_icon.png',
                'EPIC': 'epic_icon.png',
            }
            
            icon_file = icon_map.get(rarity)
            if icon_file:
                icon_path = os.path.join(CARDMAKER_ELEMENTS_DIR, icon_file)
                if os.path.exists(icon_path):
                    return Image.open(icon_path).convert('RGBA')
            
            return None
        except Exception:
            return None
    
    def _get_set_icon(self, rarity: str) -> Optional[Image.Image]:
        """Get set icon image"""
        try:
            if rarity == 'LEGENDARY':
                candidates = ['set_icon_ledgendary.png', 'set_icon_legendary.png']
            else:
                candidates = ['set_icon.png']
            
            for filename in candidates:
                icon_path = os.path.join(CARDMAKER_ELEMENTS_DIR, filename)
                if os.path.exists(icon_path):
                    return Image.open(icon_path).convert('RGBA')
            
            return None
        except Exception:
            return None
    
    def delete_card(self, card_id: int) -> bool:
        """Delete a card and its associated files from PostgreSQL"""
        conn = self.get_pg_connection()
        if not conn:
            return False
        
        try:
            # Get card info first
            card = self.get_card(card_id)
            if not card:
                return False
            
            with conn.cursor() as cursor:
                # Delete from database
                cursor.execute("DELETE FROM card_catalog WHERE id = %s", (card_id,))
                conn.commit()
            
            # Delete associated files
            for prefix in ['', 'raw_']:
                file_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{prefix}{card['slug']}.png")
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            logger.info(f"Deleted card: {card['name']} (ID: {card_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete card {card_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get card database statistics from PostgreSQL"""
        conn = self.get_pg_connection()
        if not conn:
            logger.error("Failed to connect to PostgreSQL database")
            return {}
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                stats = {}
                
                # Card catalog stats
                cursor.execute("SELECT COUNT(*) as total FROM card_catalog")
                stats['total_templates'] = cursor.fetchone()['total']
                
                # All cards in catalog are considered "published"
                stats['published_templates'] = stats['total_templates']
                
                # Rarity distribution
                cursor.execute("SELECT rarity, COUNT(*) as count FROM card_catalog GROUP BY rarity")
                raw_rarity = {row['rarity']: row['count'] for row in cursor.fetchall()}
                
                stats['by_rarity'] = {
                    'COMMON': raw_rarity.get('common', 0),
                    'RARE': raw_rarity.get('rare', 0),
                    'EPIC': raw_rarity.get('epic', 0),
                    'LEGENDARY': raw_rarity.get('legendary', 0)
                }
                
                # Category distribution
                cursor.execute("SELECT category, COUNT(*) as count FROM card_catalog GROUP BY category")
                raw_category = {row['category']: row['count'] for row in cursor.fetchall()}
                
                stats['by_category'] = {
                    'CREATURE': raw_category.get('creature', 0),
                    'ACTION_FAST': raw_category.get('action_fast', 0),
                    'ACTION_SLOW': raw_category.get('action_slow', 0),
                    'ENCHANTMENT': raw_category.get('enchantment', 0),
                    'EQUIPMENT': raw_category.get('equipment', 0),
                    'STRUCTURE': raw_category.get('structure', 0),
                    'HERO': raw_category.get('hero', 0)
                }
                
                # NFC card stats
                cursor.execute("SELECT COUNT(*) as total FROM nfc_cards")
                nfc_result = cursor.fetchone()
                stats['total_nfc_cards'] = nfc_result['total'] if nfc_result else 0
                
                cursor.execute("SELECT status, COUNT(*) as count FROM nfc_cards GROUP BY status")
                stats['nfc_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Recent cards
                cursor.execute("""
                    SELECT name, category, rarity, created_at
                    FROM card_catalog 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                stats['recent_cards'] = [dict(row) for row in cursor.fetchall()]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get statistics from PostgreSQL: {e}")
            return {}
        finally:
            conn.close()
    
    def get_card_templates(self, filters: Dict = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get card templates from PostgreSQL database with pagination and filtering"""
        conn = self.get_pg_connection()
        if not conn:
            return {'templates': [], 'pagination': {'page': 1, 'pages': 1, 'total': 0}}
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Build WHERE clause based on filters
                where_conditions = []
                params = []
                
                if filters:
                    if filters.get('search'):
                        where_conditions.append("(name ILIKE %s OR rules_text ILIKE %s)")
                        search_term = f"%{filters['search']}%"
                        params.extend([search_term, search_term])
                    
                    if filters.get('category'):
                        where_conditions.append("category = %s")
                        params.append(filters['category'].lower())
                    
                    if filters.get('rarity'):
                        where_conditions.append("rarity = %s")
                        params.append(filters['rarity'].lower())
                
                where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Get total count
                count_query = f"SELECT COUNT(*) as total FROM card_catalog{where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # Calculate pagination
                pages = max(1, (total + per_page - 1) // per_page)
                offset = (page - 1) * per_page
                
                # Get templates
                query = f"""
                    SELECT id, product_sku, name, rarity, category, subtype, 
                           base_stats, flavor_text, rules_text, artwork_url,
                           created_at, updated_at
                    FROM card_catalog{where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, params + [per_page, offset])
                templates = []
                
                for row in cursor.fetchall():
                    template = dict(row)
                    # Create a slug from the name for compatibility
                    template['slug'] = template['name'].lower().replace(' ', '_').replace("'", "")
                    templates.append(template)
                
                pagination = {
                    'page': page,
                    'pages': pages,
                    'total': total,
                    'per_page': per_page,
                    'has_prev': page > 1,
                    'has_next': page < pages,
                    'prev_num': page - 1 if page > 1 else None,
                    'next_num': page + 1 if page < pages else None
                }
                
                return {
                    'templates': templates,
                    'pagination': pagination
                }
                
        except Exception as e:
            logger.error(f"Error getting card templates: {e}")
            return {'templates': [], 'pagination': {'page': 1, 'pages': 1, 'total': 0}}
        finally:
            conn.close()


# Global service instance
card_service = CardService()


def get_card_service() -> CardService:
    """Get the global card service instance"""
    return card_service
