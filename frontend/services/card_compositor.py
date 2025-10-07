"""
Unified Card Compositor - Production Ready
Consolidates all card composition logic into a single, optimized implementation
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageMath
import logging

logger = logging.getLogger(__name__)

class CardCompositor:
    """Unified card composition engine for production use"""
    
    def __init__(self, elements_dir: str = None, font_path: str = None):
        self.elements_dir = elements_dir or os.environ.get(
            "CARDMAKER_ELEMENTS_DIR", 
            "/home/jp/deckport.ai/cardmaker.ai/card_elements"
        )
        self.font_path = font_path or os.environ.get(
            "CARDMAKER_FONT_PATH",
            "/home/jp/deckport.ai/cardmaker.ai/Chakra_Petch/ChakraPetch-SemiBold.ttf"
        )
        
        # Canvas dimensions - production standard
        self.canvas_width = 1500
        self.canvas_height = 2100
        
        # Color mappings
        self.mana_colors = {
            'CRIMSON': {'name': 'Crimson', 'icon': 'mana_red.png', 'color': '#DC2626'},
            'AZURE': {'name': 'Azure', 'icon': 'mana_blue.png', 'color': '#2563EB'},
            'VERDANT': {'name': 'Verdant', 'icon': 'mana_green.png', 'color': '#16A34A'},
            'OBSIDIAN': {'name': 'Obsidian', 'icon': 'mana_black.png', 'color': '#1F2937'},
            'RADIANT': {'name': 'Radiant', 'icon': 'mana_white.png', 'color': '#F59E0B'},
            'AETHER': {'name': 'Aether', 'icon': 'mana_orange.png', 'color': '#EA580C'}
        }
        
    def compose_card(self, card_data: Dict[str, Any], artwork_path: str, 
                    transparent_bg: bool = False) -> Optional[Image.Image]:
        """
        Compose complete card with artwork, frame, and all elements
        
        Args:
            card_data: Card information (name, rarity, mana_colors, etc.)
            artwork_path: Path to generated artwork
            transparent_bg: If True, create transparent frame overlay
            
        Returns:
            Composed PIL Image or None if failed
        """
        try:
            logger.info(f"Composing card: {card_data.get('name', 'Unknown')}")
            
            # Load artwork
            if not os.path.exists(artwork_path):
                logger.error(f"Artwork not found: {artwork_path}")
                return None
                
            art_img = Image.open(artwork_path).convert('RGBA')
            
            # Load frame elements
            frame_img = self._load_frame(card_data.get('rarity', 'COMMON'))
            glow_img = self._load_glow()
            mana_img = self._load_mana_icon(card_data.get('mana_colors', ['AETHER'])[0])
            
            if not all([frame_img, glow_img, mana_img]):
                logger.error("Failed to load required frame elements")
                return None
            
            # Create canvas
            canvas = self._create_canvas(transparent_bg)
            
            # Layer composition (order matters!)
            if transparent_bg:
                # For frame templates: glow first (as base), then frame, then text/icons (skip artwork)
                canvas = self._composite_glow_as_base(canvas, glow_img)
                canvas = self._composite_frame(canvas, frame_img)
                canvas = self._composite_mana_icon(canvas, mana_img)
                canvas = self._composite_rarity_icon(canvas, card_data.get('rarity', 'COMMON'))
                canvas = self._composite_set_icon(canvas, card_data.get('rarity', 'COMMON'))
                canvas = self._composite_text(canvas, card_data)
            else:
                # For full composites: normal order with artwork
                canvas = self._composite_artwork(canvas, art_img)
                canvas = self._composite_glow(canvas, glow_img)
                canvas = self._composite_frame(canvas, frame_img)
                canvas = self._composite_mana_icon(canvas, mana_img)
                canvas = self._composite_rarity_icon(canvas, card_data.get('rarity', 'COMMON'))
                canvas = self._composite_set_icon(canvas, card_data.get('rarity', 'COMMON'))
                canvas = self._composite_text(canvas, card_data)
            
            logger.info(f"Card composition completed: {card_data.get('name', 'Unknown')}")
            return canvas
            
        except Exception as e:
            logger.error(f"Card composition failed: {e}")
            return None
    
    def _create_canvas(self, transparent_bg: bool) -> Image.Image:
        """Create canvas with appropriate background"""
        if transparent_bg:
            return Image.new('RGBA', (self.canvas_width, self.canvas_height), (0, 0, 0, 0))
        else:
            return Image.new('RGBA', (self.canvas_width, self.canvas_height), (0, 0, 0, 255))
    
    def _composite_artwork(self, canvas: Image.Image, art_img: Image.Image) -> Image.Image:
        """Composite artwork centered and scaled"""
        try:
            # Scale artwork to fit canvas while preserving aspect ratio
            art_w, art_h = art_img.size
            scale = min(self.canvas_width / art_w, self.canvas_height / art_h)
            new_w = max(1, int(art_w * scale))
            new_h = max(1, int(art_h * scale))
            
            art_resized = art_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Center artwork
            off_x = (self.canvas_width - new_w) // 2
            off_y = (self.canvas_height - new_h) // 2
            
            canvas.alpha_composite(art_resized, (off_x, off_y))
            return canvas
            
        except Exception as e:
            logger.error(f"Artwork composition failed: {e}")
            return canvas
    
    def _composite_glow(self, canvas: Image.Image, glow_img: Image.Image) -> Image.Image:
        """Apply glow effect using screen blend mode"""
        try:
            glow_resized = glow_img.resize((self.canvas_width, self.canvas_height))
            
            # Apply two screen blend passes for intensity (matches original implementation)
            for _ in range(2):
                base_rgb = canvas.convert('RGB')
                glow_pm_rgb = self._premultiply_rgb(glow_resized)
                screened = ImageChops.screen(base_rgb, glow_pm_rgb)
                canvas = Image.merge('RGBA', (*screened.split(), canvas.split()[3]))
            
            return canvas
            
        except Exception as e:
            logger.error(f"Glow composition failed: {e}")
            return canvas
    
    def _composite_glow_as_base(self, canvas: Image.Image, glow_img: Image.Image) -> Image.Image:
        """Apply glow as base layer for transparent frame templates"""
        try:
            glow_resized = glow_img.resize((self.canvas_width, self.canvas_height))
            
            # For transparent frames, use glow directly as base layer (not screen blend)
            # This preserves the glow effect in transparent frames
            canvas.alpha_composite(glow_resized, (0, 0))
            
            return canvas
            
        except Exception as e:
            logger.error(f"Glow base composition failed: {e}")
            return canvas
    
    def _composite_frame(self, canvas: Image.Image, frame_img: Image.Image) -> Image.Image:
        """Composite frame overlay"""
        try:
            frame_resized = frame_img.resize((self.canvas_width, self.canvas_height))
            canvas.alpha_composite(frame_resized, (0, 0))
            return canvas
        except Exception as e:
            logger.error(f"Frame composition failed: {e}")
            return canvas
    
    def _composite_mana_icon(self, canvas: Image.Image, mana_img: Image.Image) -> Image.Image:
        """Composite mana icon overlay"""
        try:
            mana_resized = mana_img.resize((self.canvas_width, self.canvas_height))
            canvas.alpha_composite(mana_resized, (0, 0))
            return canvas
        except Exception as e:
            logger.error(f"Mana icon composition failed: {e}")
            return canvas
    
    def _composite_rarity_icon(self, canvas: Image.Image, rarity: str) -> Image.Image:
        """Composite rarity icon (skip for legendary - uses special frame)"""
        try:
            if rarity.upper() == 'LEGENDARY':
                return canvas  # Legendary uses special frame instead
                
            rarity_icon = self._load_rarity_icon(rarity)
            if rarity_icon:
                rarity_resized = rarity_icon.resize((self.canvas_width, self.canvas_height))
                canvas.alpha_composite(rarity_resized, (0, 0))
            
            return canvas
        except Exception as e:
            logger.error(f"Rarity icon composition failed: {e}")
            return canvas
    
    def _composite_set_icon(self, canvas: Image.Image, rarity: str) -> Image.Image:
        """Composite set icon overlay"""
        try:
            set_icon = self._load_set_icon(rarity)
            if set_icon:
                set_resized = set_icon.resize((self.canvas_width, self.canvas_height))
                canvas.alpha_composite(set_resized, (0, 0))
            
            return canvas
        except Exception as e:
            logger.error(f"Set icon composition failed: {e}")
            return canvas
    
    def _composite_text(self, canvas: Image.Image, card_data: Dict[str, Any]) -> Image.Image:
        """Composite card text elements"""
        try:
            draw = ImageDraw.Draw(canvas)
            
            # Load fonts
            try:
                font_name = ImageFont.truetype(self.font_path, size=int(self.canvas_height * 0.032))
                font_category = ImageFont.truetype(self.font_path, size=int(self.canvas_height * 0.024))
            except Exception:
                font_name = ImageFont.load_default()
                font_category = ImageFont.load_default()
            
            # Card name (centered, cyan color #00d2ff)
            name = card_data.get('name', 'Unknown Card')
            name_x = self.canvas_width // 2
            name_y = int(179.7) + 15 + 2  # Optimized positioning
            self._draw_text_centered(draw, name, (name_x, name_y), font_name, (0, 210, 255, 255))
            
            # Category label (bottom, same color)
            category = card_data.get('category', 'CREATURE').title()
            cat_y = min(int(self.canvas_height * 0.13) + 1645, self.canvas_height - 10)
            self._draw_text_centered(draw, category, (self.canvas_width // 2, cat_y), 
                                   font_category, (0, 210, 255, 255))
            
            return canvas
            
        except Exception as e:
            logger.error(f"Text composition failed: {e}")
            return canvas
    
    def _load_frame(self, rarity: str) -> Optional[Image.Image]:
        """Load appropriate frame based on rarity"""
        try:
            if rarity.upper() == 'LEGENDARY':
                frame_path = os.path.join(self.elements_dir, 'legendary_frame.png')
                if os.path.exists(frame_path):
                    return Image.open(frame_path).convert('RGBA')
            
            # Default frame
            frame_path = os.path.join(self.elements_dir, 'frame.png')
            if os.path.exists(frame_path):
                return Image.open(frame_path).convert('RGBA')
                
            logger.error(f"Frame not found: {frame_path}")
            return None
            
        except Exception as e:
            logger.error(f"Frame loading failed: {e}")
            return None
    
    def _load_glow(self) -> Optional[Image.Image]:
        """Load glow effect image"""
        try:
            glow_path = os.path.join(self.elements_dir, 'glow.png')
            if os.path.exists(glow_path):
                return Image.open(glow_path).convert('RGBA')
            
            logger.error(f"Glow not found: {glow_path}")
            return None
            
        except Exception as e:
            logger.error(f"Glow loading failed: {e}")
            return None
    
    def _load_mana_icon(self, mana_color: str) -> Optional[Image.Image]:
        """Load mana icon based on color"""
        try:
            color_info = self.mana_colors.get(mana_color.upper(), self.mana_colors['AETHER'])
            icon_path = os.path.join(self.elements_dir, color_info['icon'])
            
            if os.path.exists(icon_path):
                return Image.open(icon_path).convert('RGBA')
            
            logger.error(f"Mana icon not found: {icon_path}")
            return None
            
        except Exception as e:
            logger.error(f"Mana icon loading failed: {e}")
            return None
    
    def _load_rarity_icon(self, rarity: str) -> Optional[Image.Image]:
        """Load rarity icon"""
        try:
            icon_map = {
                'COMMON': 'common_icon.png',
                'RARE': 'rare_icon.png',
                'EPIC': 'epic_icon.png',
            }
            
            icon_file = icon_map.get(rarity.upper())
            if not icon_file:
                return None
            
            icon_path = os.path.join(self.elements_dir, icon_file)
            if os.path.exists(icon_path):
                return Image.open(icon_path).convert('RGBA')
            
            return None
            
        except Exception as e:
            logger.error(f"Rarity icon loading failed: {e}")
            return None
    
    def _load_set_icon(self, rarity: str) -> Optional[Image.Image]:
        """Load set icon (with legendary variant)"""
        try:
            if rarity.upper() == 'LEGENDARY':
                candidates = ['set_icon_ledgendary.png', 'set_icon_legendary.png']
            else:
                candidates = ['set_icon.png']
            
            for filename in candidates:
                icon_path = os.path.join(self.elements_dir, filename)
                if os.path.exists(icon_path):
                    return Image.open(icon_path).convert('RGBA')
            
            return None
            
        except Exception as e:
            logger.error(f"Set icon loading failed: {e}")
            return None
    
    def _premultiply_rgb(self, img_rgba: Image.Image) -> Image.Image:
        """Premultiply RGB channels by alpha for proper blending"""
        try:
            r, g, b, a = img_rgba.split()
            r_p = ImageMath.eval("convert((r*a)/255, 'L')", r=r, a=a)
            g_p = ImageMath.eval("convert((g*a)/255, 'L')", g=g, a=a)
            b_p = ImageMath.eval("convert((b*a)/255, 'L')", b=b, a=a)
            return Image.merge('RGB', (r_p, g_p, b_p))
        except Exception:
            return img_rgba.convert('RGB')
    
    def _draw_text_centered(self, draw: ImageDraw.ImageDraw, text: str, 
                           center: Tuple[int, int], font: ImageFont.FreeTypeFont, 
                           fill: Tuple[int, int, int, int]):
        """Draw text centered at coordinates with stroke"""
        try:
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x = int(center[0] - w / 2)
            y = int(center[1] - h / 2)
            
            # Draw with stroke for readability
            draw.text((x, y), text, font=font, fill=fill, 
                     stroke_width=2, stroke_fill=(0, 0, 0, 255))
                     
        except Exception as e:
            logger.error(f"Text drawing failed: {e}")


# Global compositor instance
_card_compositor = None

def get_card_compositor() -> CardCompositor:
    """Get global card compositor instance"""
    global _card_compositor
    if _card_compositor is None:
        _card_compositor = CardCompositor()
    return _card_compositor
