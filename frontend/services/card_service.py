"""
Card Service for Deckport Admin Panel
Integrates cardmaker.ai functionality for card generation and rendering
"""

import os
import json
import sqlite3
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import logging

from .comfyui_service import get_comfyui_service

logger = logging.getLogger(__name__)

# Configuration
CARDMAKER_DB_PATH = os.environ.get("CARDMAKER_DB_PATH", "/home/jp/deckport.ai/cardmaker.ai/deckport.sqlite3")
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
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or CARDMAKER_DB_PATH
        self.comfyui = get_comfyui_service()
        
        # PostgreSQL connection config for main database
        self.pg_config = {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'deckport',
            'user': 'deckport_app',
            'password': 'N0D3-N0D3-N0D3#M0nk3y33'
        }
        
        # Ensure output directory exists
        os.makedirs(CARDMAKER_OUTPUT_DIR, exist_ok=True)
    
    def get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Get SQLite database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
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
        Create a new card in the database
        
        Args:
            card_data: Dictionary containing card information
            
        Returns:
            Card ID if successful, None otherwise
        """
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Generate slug from name
            slug = card_data['name'].lower().replace(' ', '-').replace("'", "")
            
            # Insert main card record
            cursor.execute("""
                INSERT INTO cards (slug, name, category, rarity, legendary, color_code, 
                                 energy_cost, equipment_slots, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug,
                card_data['name'],
                card_data['category'],
                card_data['rarity'],
                1 if card_data['rarity'] == 'LEGENDARY' else 0,
                card_data['color_code'],
                card_data.get('energy_cost', 0),
                card_data.get('equipment_slots', 0),
                datetime.now().isoformat()
            ))
            
            card_id = cursor.lastrowid
            
            # Insert stats (for creatures/structures)
            if card_data['category'] in ['CREATURE', 'STRUCTURE']:
                cursor.execute("""
                    INSERT INTO card_stats (card_id, attack, defense, health, base_energy_per_turn)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    card_id,
                    card_data.get('attack', 0),
                    card_data.get('defense', 0),
                    card_data.get('health', 0),
                    card_data.get('base_energy_per_turn', 0)
                ))
            
            # Insert mana cost
            cursor.execute("""
                INSERT INTO card_mana_costs (card_id, color_code, amount)
                VALUES (?, ?, ?)
            """, (card_id, card_data['color_code'], card_data.get('mana_cost', 0)))
            
            # Insert targeting (default values)
            cursor.execute("""
                INSERT INTO card_targeting (card_id, target_friendly, target_enemy, target_self)
                VALUES (?, ?, ?, ?)
            """, (card_id, 0, 1, 0))
            
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
        """Get card data by ID"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, s.attack, s.defense, s.health, s.base_energy_per_turn,
                       mc.amount as mana_cost, mc.color_code as mana_color,
                       t.target_friendly, t.target_enemy, t.target_self
                FROM cards c
                LEFT JOIN card_stats s ON c.id = s.card_id
                LEFT JOIN card_mana_costs mc ON c.id = mc.card_id
                LEFT JOIN card_targeting t ON c.id = t.card_id
                WHERE c.id = ?
            """, (card_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get card {card_id}: {e}")
            return None
        finally:
            conn.close()
    
    def get_cards(self, filters: Dict[str, Any] = None, 
                  page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
        """
        Get cards with optional filtering and pagination
        
        Returns:
            Tuple of (cards_list, total_count)
        """
        conn = self.get_db_connection()
        if not conn:
            return [], 0
        
        try:
            cursor = conn.cursor()
            filters = filters or {}
            
            # Build WHERE clause
            where_clauses = []
            params = []
            
            if filters.get('search'):
                where_clauses.append("(c.name LIKE ? OR c.slug LIKE ?)")
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
            
            if filters.get('category'):
                where_clauses.append("c.category = ?")
                params.append(filters['category'])
            
            if filters.get('rarity'):
                where_clauses.append("c.rarity = ?")
                params.append(filters['rarity'])
            
            if filters.get('color'):
                where_clauses.append("c.color_code = ?")
                params.append(filters['color'])
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM cards c WHERE {where_sql}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get cards with pagination
            offset = (page - 1) * per_page
            query = f"""
                SELECT c.*, s.attack, s.defense, s.health, s.base_energy_per_turn,
                       mc.amount as mana_cost
                FROM cards c
                LEFT JOIN card_stats s ON c.id = s.card_id
                LEFT JOIN card_mana_costs mc ON c.id = mc.card_id
                WHERE {where_sql}
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])
            cursor.execute(query, params)
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            # Add art status for each card
            for card in cards:
                art_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card['slug']}.png")
                card['has_art'] = os.path.exists(art_path)
            
            return cards, total_count
            
        except Exception as e:
            logger.error(f"Failed to get cards: {e}")
            return [], 0
        finally:
            conn.close()
    
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
            
            # Compose final card
            final_card = self.compose_card(card, art_path)
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
    
    def compose_card(self, card: Dict[str, Any], art_path: str) -> Optional[Image.Image]:
        """
        Compose final card image with art, frame, and text elements
        
        Args:
            card: Card data dictionary
            art_path: Path to generated artwork
            
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
            
            # Create canvas
            canvas = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 255))
            
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
        """Apply glow effect using screen blend mode"""
        try:
            from PIL import ImageChops, ImageMath
            
            # Apply two passes of screen blend for intensity
            for _ in range(2):
                base_rgb = base.convert('RGB')
                glow_rgb = glow.convert('RGB')
                screened = ImageChops.screen(base_rgb, glow_rgb)
                base = Image.merge('RGBA', (*screened.split(), base.split()[3]))
            
            return base
        except Exception:
            return base
    
    def _add_card_text(self, canvas: Image.Image, card: Dict[str, Any]) -> Image.Image:
        """Add text elements to the card"""
        try:
            draw = ImageDraw.Draw(canvas)
            
            # Load fonts
            try:
                font_name = ImageFont.truetype(CARDMAKER_FONT_PATH, size=int(CANVAS_HEIGHT * 0.035))
                font_label = ImageFont.truetype(CARDMAKER_FONT_PATH, size=int(CANVAS_HEIGHT * 0.024))
            except Exception:
                font_name = ImageFont.load_default()
                font_label = ImageFont.load_default()
            
            # Card name (centered, blue color)
            name_x = CANVAS_WIDTH // 2
            name_y = int(179.7) + 15
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
        """Delete a card and its associated files"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            # Get card info first
            card = self.get_card(card_id)
            if not card:
                return False
            
            cursor = conn.cursor()
            
            # Delete from database (cascade will handle related tables)
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
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
            return False
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get card database statistics"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Total cards
            cursor.execute("SELECT COUNT(*) FROM cards")
            total_cards = cursor.fetchone()[0]
            
            # By category
            cursor.execute("SELECT category, COUNT(*) FROM cards GROUP BY category")
            category_stats = dict(cursor.fetchall())
            
            # By rarity
            cursor.execute("SELECT rarity, COUNT(*) FROM cards GROUP BY rarity")
            rarity_stats = dict(cursor.fetchall())
            
            # By color
            cursor.execute("SELECT color_code, COUNT(*) FROM cards GROUP BY color_code")
            color_stats = dict(cursor.fetchall())
            
            # Recent cards
            cursor.execute("""
                SELECT name, category, rarity, color_code, created_at
                FROM cards 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            recent_cards = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_cards': total_cards,
                'category_stats': category_stats,
                'rarity_stats': rarity_stats,
                'color_stats': color_stats,
                'recent_cards': recent_cards
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get card system statistics from PostgreSQL database"""
        conn = self.get_pg_connection()
        if not conn:
            return {}
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                stats = {}
                
                # Card catalog stats (using actual table name)
                cursor.execute("SELECT COUNT(*) as total FROM card_catalog")
                stats['total_templates'] = cursor.fetchone()['total']
                
                # All cards in catalog are considered "published"
                stats['published_templates'] = stats['total_templates']
                
                cursor.execute("SELECT rarity, COUNT(*) as count FROM card_catalog GROUP BY rarity")
                raw_rarity = {row['rarity']: row['count'] for row in cursor.fetchall()}
                
                # Map database rarity values to template expected values
                stats['by_rarity'] = {
                    'COMMON': raw_rarity.get('common', 0),
                    'RARE': raw_rarity.get('rare', 0),
                    'EPIC': raw_rarity.get('epic', 0),
                    'LEGENDARY': raw_rarity.get('legendary', 0)
                }
                
                cursor.execute("SELECT category, COUNT(*) as count FROM card_catalog GROUP BY category")
                raw_category = {row['category']: row['count'] for row in cursor.fetchall()}
                
                # Map database category values to template expected values (mana colors)
                stats['by_category'] = {
                    'CRIMSON': raw_category.get('creature', 0),  # Map creature to crimson for demo
                    'AZURE': raw_category.get('action_fast', 0),  # Map action_fast to azure
                    'VERDANT': raw_category.get('enchantment', 0),  # Map enchantment to verdant
                    'OBSIDIAN': raw_category.get('action_slow', 0),  # Map action_slow to obsidian
                    'RADIANT': 0,  # No mapping available
                    'AETHER': 0   # No mapping available
                }
                
                # NFC card stats (using actual table name)
                cursor.execute("SELECT COUNT(*) as total FROM nfc_cards")
                stats['total_nfc_cards'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT status, COUNT(*) as count FROM nfc_cards GROUP BY status")
                stats['nfc_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
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
