"""
Card Production Workflow Service
Complete pipeline: Database → Static Art → Video → Transparent Frame → CDN
Integrates with admin interface for full card asset generation
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from PIL import Image

from .comfyui_service import get_comfyui_service
from .card_service import get_card_service

logger = logging.getLogger(__name__)

class CardProductionService:
    """Production service for complete card asset generation"""
    
    def __init__(self):
        self.comfyui = get_comfyui_service()
        self.card_service = get_card_service()
        
        # CDN directory structure
        self.cdn_base = '/home/jp/deckport.ai/static/cards'
        self.cdn_dirs = {
            'static': os.path.join(self.cdn_base, 'static'),
            'videos': os.path.join(self.cdn_base, 'videos'),
            'frames': os.path.join(self.cdn_base, 'frames'),
            'composite': os.path.join(self.cdn_base, 'composite'),
            'thumbnails': os.path.join(self.cdn_base, 'thumbnails')
        }
        
        # Ensure CDN directories exist
        for dir_path in self.cdn_dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Workflow paths
        self.art_workflow_path = '/home/jp/deckport.ai/cardmaker.ai/art-generation.json'
        self.video_workflow_path = '/home/jp/deckport.ai/cardmaker.ai/CardVideo.json'
    
    def generate_complete_card_assets(self, card_id: int, art_prompt: str) -> Dict[str, str]:
        """
        Generate all assets for a card: static art, video, frame overlay, composite
        
        Args:
            card_id: Database card ID
            art_prompt: Detailed image generation prompt
            
        Returns:
            Dictionary of generated asset paths
        """
        logger.info(f"Starting complete asset generation for card ID {card_id}")
        
        assets = {
            'static_art': None,
            'video_background': None,
            'frame_overlay': None,
            'full_composite': None,
            'thumbnail': None
        }
        
        try:
            # Get card data from database
            import sys; sys.path.append("/home/jp/deckport.ai"); from shared.database.connection import SessionLocal
            from sqlalchemy import text
            
            session = SessionLocal()
            try:
                result = session.execute(text('''
                    SELECT c.id, c.name, c.product_sku, c.base_stats, c.rules_text, 
                           c.mana_colors, c.rarity, c.category
                    FROM card_catalog c WHERE c.id = :card_id
                '''), {'card_id': card_id})
                
                card_row = result.fetchone()
                if not card_row:
                    logger.error(f"Card {card_id} not found in database")
                    return assets
                
                # Extract primary mana color for compatibility with card_service
                mana_colors = card_row[5] or ['AETHER']
                primary_mana = mana_colors[0] if mana_colors else 'AETHER'
                
                card_data = {
                    'id': card_row[0],
                    'name': card_row[1],
                    'product_sku': card_row[2],
                    'slug': card_row[1].lower().replace(' ', '_').replace("'", ""),
                    'base_stats': card_row[3] or {},
                    'rules_text': card_row[4] or '',
                    'mana_colors': card_row[5] or ['AETHER'],
                    'color_code': primary_mana,  # Add color_code for compatibility
                    'rarity': card_row[6].upper(),  # Ensure uppercase
                    'category': card_row[7].upper()  # Ensure uppercase
                }
            finally:
                session.close()
            
            logger.info(f"Processing card: {card_data['name']} ({card_data['rarity']} {card_data['category']})")
            
            # Step 1: Generate static art
            static_path = self._generate_static_art(card_data, art_prompt)
            if static_path:
                assets['static_art'] = static_path
                logger.info(f"✅ Static art generated: {static_path}")
            else:
                logger.error(f"❌ Static art generation failed")
                return assets
            
            # Step 2: Generate video from static art
            video_path = self._generate_video_background(card_data, static_path)
            if video_path:
                assets['video_background'] = video_path
                logger.info(f"✅ Video background generated: {video_path}")
            else:
                logger.warning(f"⚠️ Video generation failed, continuing without video")
            
            # Step 3: Generate transparent frame overlay
            frame_path = self._generate_frame_overlay(card_data)
            if frame_path:
                assets['frame_overlay'] = frame_path
                logger.info(f"✅ Frame overlay generated: {frame_path}")
            
            # Step 4: Generate full composite
            composite_path = self._generate_full_composite(card_data, static_path)
            if composite_path:
                assets['full_composite'] = composite_path
                logger.info(f"✅ Full composite generated: {composite_path}")
            
            # Step 5: Generate thumbnail
            thumbnail_path = self._generate_thumbnail(card_data, composite_path or static_path)
            if thumbnail_path:
                assets['thumbnail'] = thumbnail_path
                logger.info(f"✅ Thumbnail generated: {thumbnail_path}")
            
            # Step 6: Update database with CDN URLs
            self._update_database_with_assets(card_data, assets)
            
            logger.info(f"Complete asset generation finished for {card_data['name']}")
            return assets
            
        except Exception as e:
            logger.error(f"Complete asset generation failed for card {card_id}: {e}")
            return assets
    
    def _generate_static_art(self, card_data: Dict, art_prompt: str) -> Optional[str]:
        """Generate static artwork using ComfyUI"""
        try:
            logger.info(f"Generating static art for {card_data['name']}")
            
            # Generate with ComfyUI
            image_data = self.comfyui.generate_card_art(
                prompt=art_prompt,
                seed=hash(card_data['name']) % 100000  # Deterministic seed
            )
            
            if not image_data:
                return None
            
            # Save to CDN
            filename = f"{card_data['product_sku'].lower()}.png"
            static_path = os.path.join(self.cdn_dirs['static'], filename)
            
            with open(static_path, 'wb') as f:
                f.write(image_data)
            
            return static_path
            
        except Exception as e:
            logger.error(f"Static art generation failed: {e}")
            return None
    
    def _generate_video_background(self, card_data: Dict, static_art_path: str) -> Optional[str]:
        """Generate video background using CardVideo.json workflow"""
        try:
            logger.info(f"Generating video background for {card_data['name']}")
            
            # Load video workflow
            with open(self.video_workflow_path, 'r') as f:
                workflow = json.load(f)
            
            # Create video prompt
            video_prompt = self._create_video_prompt(card_data)
            
            # Prepare output filename
            output_filename = card_data['name'].lower().replace(' ', '_').replace("'", "")
            
            # Update workflow
            workflow = self._inject_video_workflow_data(workflow, static_art_path, video_prompt, output_filename)
            
            # Submit to ComfyUI
            prompt_id = self.comfyui.submit_prompt(workflow)
            if not prompt_id:
                logger.error(f"Failed to submit video generation")
                return None
            
            # Wait for completion (videos take longer)
            video_data = self.comfyui.wait_for_completion(prompt_id, max_wait=300)
            
            if video_data:
                # Save to CDN
                video_filename = f"{output_filename}.mp4"
                video_path = os.path.join(self.cdn_dirs['videos'], video_filename)
                
                with open(video_path, 'wb') as f:
                    f.write(video_data)
                
                return video_path
            else:
                logger.error(f"Video generation failed or timed out")
                return None
                
        except Exception as e:
            logger.error(f"Video background generation failed: {e}")
            return None
    
    def _generate_frame_overlay(self, card_data: Dict) -> Optional[str]:
        """Generate transparent frame overlay"""
        try:
            logger.info(f"Generating frame overlay for {card_data['name']}")
            
            # Create transparent 1x1 pixel as "art"
            transparent_art = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            temp_art_path = '/tmp/transparent_pixel.png'
            transparent_art.save(temp_art_path, format='PNG')
            
            # Use card service to compose frame with transparent background
            frame_composite = self.card_service.compose_card(
                card_data, temp_art_path, transparent_bg=True
            )
            
            if frame_composite:
                # Save to CDN
                filename = f"{card_data['product_sku'].lower()}_frame.png"
                frame_path = os.path.join(self.cdn_dirs['frames'], filename)
                frame_composite.save(frame_path, format='PNG')
                
                # Clean up temp file
                if os.path.exists(temp_art_path):
                    os.remove(temp_art_path)
                
                return frame_path
            
            return None
            
        except Exception as e:
            logger.error(f"Frame overlay generation failed: {e}")
            return None
    
    def _generate_full_composite(self, card_data: Dict, static_art_path: str) -> Optional[str]:
        """Generate full composite card"""
        try:
            logger.info(f"Generating full composite for {card_data['name']}")
            
            # Use card service to compose full card with black background
            full_composite = self.card_service.compose_card(
                card_data, static_art_path, transparent_bg=False
            )
            
            if full_composite:
                # Save to CDN
                filename = f"{card_data['product_sku'].lower()}_full.png"
                composite_path = os.path.join(self.cdn_dirs['composite'], filename)
                full_composite.convert('RGB').save(composite_path, format='PNG', quality=95)
                
                return composite_path
            
            return None
            
        except Exception as e:
            logger.error(f"Full composite generation failed: {e}")
            return None
    
    def _generate_thumbnail(self, card_data: Dict, source_path: str) -> Optional[str]:
        """Generate thumbnail from composite or static art"""
        try:
            logger.info(f"Generating thumbnail for {card_data['name']}")
            
            # Load source image
            source_img = Image.open(source_path)
            
            # Create thumbnail
            thumbnail = source_img.copy()
            thumbnail.thumbnail((300, 420), Image.Resampling.LANCZOS)
            
            # Save to CDN
            filename = f"{card_data['product_sku'].lower()}_thumb.png"
            thumb_path = os.path.join(self.cdn_dirs['thumbnails'], filename)
            thumbnail.convert('RGB').save(thumb_path, format='PNG', quality=85)
            
            return thumb_path
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None
    
    def _create_video_prompt(self, card_data: Dict) -> str:
        """Create video prompt based on card properties"""
        name = card_data['name']
        category = card_data.get('category', 'creature').lower()
        rarity = card_data.get('rarity', 'common').lower()
        mana_color = card_data.get('mana_colors', ['AETHER'])[0]
        
        # Special detailed prompt for Burn Knight
        if name == "Burn Knight":
            return """A powerful fire knight in legendary armor, subtle breathing animation with chest rising and falling gently. Flames dancing softly around the armor edges, sword blade glowing with inner fire that pulses slowly. Eyes glowing with warm orange light that intensifies and dims rhythmically. Cape flowing gently in magical wind. Ember particles floating upward slowly and continuously. Armor plates gleaming with reflected firelight. Background flames swaying hypnotically. Seamless 3-second loop, cinemagraph style with most elements static but key fire elements in constant subtle motion. No abrupt changes, smooth continuous animation."""
        
        # Generate prompt based on card properties
        category_effects = {
            'hero': 'subtle breathing, armor gleaming, eyes glowing with inner power, cape flowing softly in magical wind',
            'creature': 'natural breathing animation, ambient magical aura pulsing, environmental elements responding to presence',
            'action_fast': 'energy crackling and building, spell effects forming, dynamic magical forces swirling rapidly',
            'action_slow': 'grand magical ritual energy building, environmental transformation, epic scale magical effects',
            'equipment': 'magical gleaming and pulsing, energy flowing through item, mystical aura effects radiating',
            'enchantment': 'magical energy swirling continuously, mystical patterns forming and dissolving, ethereal effects',
            'artifact': 'ancient power humming with energy, mystical energy radiating outward, otherworldly presence',
            'structure': 'ambient magical atmosphere, architectural elements responding to magical energy'
        }
        
        color_effects = {
            'CRIMSON': 'fire particles dancing upward, warm glow pulsing rhythmically, flame effects flickering',
            'AZURE': 'frost crystals slowly forming, cool mist swirling gently, water droplets condensing',
            'VERDANT': 'leaves rustling softly, natural energy flowing like wind, growth effects pulsing',
            'OBSIDIAN': 'shadow tendrils moving hypnotically, dark energy crackling, void effects rippling',
            'RADIANT': 'divine light pulsing warmly, golden particles floating upward, holy aura glowing',
            'AETHER': 'cosmic energy flowing like aurora, prismatic effects shifting, ethereal mist swirling'
        }
        
        base_effects = category_effects.get(category, 'subtle magical effects')
        color_fx = color_effects.get(mana_color, 'mystical energy')
        
        return f"{name}, {rarity} {category}, {base_effects}, {color_fx}. Seamless 3-second loop, cinemagraph style with most elements static but key magical elements in constant subtle motion. No abrupt changes, smooth continuous animation maintaining original composition and lighting."
    
    def _inject_video_workflow_data(self, workflow: Dict, image_path: str, video_prompt: str, output_filename: str) -> Dict:
        """Inject data into CardVideo.json workflow"""
        updated = workflow.copy()
        
        # Update image input (LoadImage nodes "148" and "73")
        image_filename = os.path.basename(image_path)
        if "148" in updated:
            updated["148"]["inputs"]["image"] = image_filename
        if "73" in updated:
            updated["73"]["inputs"]["image"] = image_filename
        
        # Update video prompt (CLIPTextEncode node "105")
        if "105" in updated:
            updated["105"]["inputs"]["text"] = video_prompt
        
        # Update output filename (SaveVideo node "69")
        if "69" in updated:
            updated["69"]["inputs"]["filename_prefix"] = f"video/{output_filename}"
        
        return updated
    
    def _update_database_with_assets(self, card_data: Dict, assets: Dict[str, str]):
        """Update database with generated asset URLs"""
        try:
            import sys; sys.path.append("/home/jp/deckport.ai"); from shared.database.connection import SessionLocal
            from sqlalchemy import text
            
            # Create CDN URLs
            base_url = "https://deckport.ai/static/cards"  # Replace with actual domain
            cdn_urls = {}
            
            for asset_type, local_path in assets.items():
                if local_path and os.path.exists(local_path):
                    relative_path = os.path.relpath(local_path, self.cdn_base)
                    cdn_urls[asset_type] = f"{base_url}/{relative_path}"
            
            # Update database
            session = SessionLocal()
            try:
                update_sql = text('''
                    UPDATE card_catalog 
                    SET artwork_url = :artwork_url,
                        static_url = :static_url,
                        video_url = :video_url,
                        has_animation = :has_animation,
                        updated_at = NOW()
                    WHERE id = :card_id
                ''')
                
                session.execute(update_sql, {
                    'card_id': card_data['id'],
                    'artwork_url': cdn_urls.get('full_composite'),
                    'static_url': cdn_urls.get('static_art'),
                    'video_url': cdn_urls.get('video_background'),
                    'has_animation': bool(cdn_urls.get('video_background'))
                })
                
                session.commit()
                logger.info(f"Database updated with CDN URLs for {card_data['name']}")
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Database update failed: {e}")
    
    def batch_generate_cards(self, card_ids: List[int], progress_callback=None) -> Dict[str, Any]:
        """
        Generate assets for multiple cards in batch
        
        Args:
            card_ids: List of card IDs to process
            progress_callback: Optional function to report progress
            
        Returns:
            Summary of batch generation results
        """
        logger.info(f"Starting batch generation for {len(card_ids)} cards")
        
        results = {
            'total_cards': len(card_ids),
            'successful': 0,
            'failed': 0,
            'generated_assets': {
                'static_art': 0,
                'videos': 0,
                'frames': 0,
                'composites': 0,
                'thumbnails': 0
            },
            'failed_cards': [],
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        # Load art prompts CSV
        art_prompts = self._load_art_prompts()
        
        for i, card_id in enumerate(card_ids):
            try:
                if progress_callback:
                    progress_callback(i + 1, len(card_ids), f"Processing card {card_id}")
                
                # Get card name for prompt lookup
                import sys; sys.path.append("/home/jp/deckport.ai"); from shared.database.connection import SessionLocal
                from sqlalchemy import text
                
                session = SessionLocal()
                try:
                    result = session.execute(text('SELECT name FROM card_catalog WHERE id = :id'), {'id': card_id})
                    card_row = result.fetchone()
                    if not card_row:
                        results['failed_cards'].append({'card_id': card_id, 'error': 'Card not found'})
                        results['failed'] += 1
                        continue
                    
                    card_name = card_row[0]
                finally:
                    session.close()
                
                # Get art prompt
                art_prompt = art_prompts.get(card_name)
                if not art_prompt:
                    logger.warning(f"No art prompt found for {card_name}, skipping")
                    results['failed_cards'].append({'card_id': card_id, 'error': 'No art prompt'})
                    results['failed'] += 1
                    continue
                
                # Generate complete assets
                assets = self.generate_complete_card_assets(card_id, art_prompt)
                
                # Count successful assets
                asset_count = sum(1 for path in assets.values() if path and os.path.exists(path))
                
                if asset_count >= 3:  # At least static, frame, composite
                    results['successful'] += 1
                    
                    # Update asset counts
                    for asset_type in assets:
                        if assets[asset_type]:
                            if asset_type == 'static_art':
                                results['generated_assets']['static_art'] += 1
                            elif asset_type == 'video_background':
                                results['generated_assets']['videos'] += 1
                            elif asset_type == 'frame_overlay':
                                results['generated_assets']['frames'] += 1
                            elif asset_type == 'full_composite':
                                results['generated_assets']['composites'] += 1
                            elif asset_type == 'thumbnail':
                                results['generated_assets']['thumbnails'] += 1
                else:
                    results['failed'] += 1
                    results['failed_cards'].append({'card_id': card_id, 'error': 'Asset generation failed'})
                
                logger.info(f"Processed card {i+1}/{len(card_ids)}: {card_name}")
                
            except Exception as e:
                logger.error(f"Failed to process card {card_id}: {e}")
                results['failed'] += 1
                results['failed_cards'].append({'card_id': card_id, 'error': str(e)})
        
        results['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Batch generation complete: {results['successful']}/{results['total_cards']} successful")
        return results
    
    def _load_art_prompts(self) -> Dict[str, str]:
        """Load art prompts from production CSV"""
        try:
            art_prompts = {}
            csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_art_production_ready.csv'
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                import csv
                reader = csv.DictReader(f)
                for row in reader:
                    art_prompts[row['name']] = row['image_prompt']
            
            logger.info(f"Loaded {len(art_prompts)} art prompts")
            return art_prompts
            
        except Exception as e:
            logger.error(f"Failed to load art prompts: {e}")
            return {}
    
    def get_generation_status(self) -> Dict[str, Any]:
        """Get current generation status and statistics"""
        try:
            import sys; sys.path.append("/home/jp/deckport.ai"); from shared.database.connection import SessionLocal
            from sqlalchemy import text
            
            session = SessionLocal()
            try:
                # Count cards with different asset types
                result = session.execute(text('''
                    SELECT 
                        COUNT(*) as total_cards,
                        COUNT(artwork_url) as has_artwork,
                        COUNT(static_url) as has_static,
                        COUNT(video_url) as has_video,
                        COUNT(CASE WHEN has_animation = true THEN 1 END) as has_animation
                    FROM card_catalog
                '''))
                
                stats = result.fetchone()
                
                return {
                    'total_cards': stats[0],
                    'cards_with_artwork': stats[1],
                    'cards_with_static': stats[2],
                    'cards_with_video': stats[3],
                    'cards_with_animation': stats[4],
                    'completion_percentage': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
                }
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to get generation status: {e}")
            return {}


# Global service instance
card_production_service = CardProductionService()


def get_card_production_service() -> CardProductionService:
    """Get the global card production service instance"""
    return card_production_service
