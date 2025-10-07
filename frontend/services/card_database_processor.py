"""
Card Database Processor - Database-Only Production Pipeline
Generates card assets directly from database, no CSV dependency
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from PIL import Image
from .comfyui_service import get_comfyui_service
from .card_compositor import get_card_compositor
import sys; sys.path.append("/home/jp/deckport.ai"); from shared.database.connection import SessionLocal
import sys; sys.path.append("/home/jp/deckport.ai"); from shared.models.base import CardCatalog
# CardAsset import removed - table permissions issue
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class CardProcessingResult:
    """Result of processing a single card"""
    success: bool
    card_id: int
    card_name: str
    assets: Dict[str, str] = None
    errors: List[str] = None
    processing_time: float = 0.0

@dataclass
class DatabaseProcessingConfig:
    """Configuration for database-only processing"""
    max_workers: int = 4
    comfyui_timeout: int = 300
    quality_checks: bool = True
    generate_videos: bool = True
    generate_thumbnails: bool = True
    output_base_dir: str = "/home/jp/deckport.ai/static/cards"
    backup_existing: bool = True
    skip_existing_assets: bool = True

class CardDatabaseProcessor:
    """Database-only card processor - no CSV dependency"""
    
    def __init__(self, config: DatabaseProcessingConfig = None):
        self.config = config or DatabaseProcessingConfig()
        self.comfyui = get_comfyui_service()
        self.compositor = get_card_compositor()
        
        # CDN directory structure
        self.cdn_dirs = {
            'artwork': os.path.join(self.config.output_base_dir, 'artwork'),
            'videos': os.path.join(self.config.output_base_dir, 'videos'),
            'frames': os.path.join(self.config.output_base_dir, 'frames'),
            'composite': os.path.join(self.config.output_base_dir, 'composite'),
            'thumbnails': os.path.join(self.config.output_base_dir, 'thumbnails')
        }
        
        # Ensure directories exist
        for dir_path in self.cdn_dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Processing statistics
        self.stats = {
            'total_cards': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
    
    def process_all_cards_with_prompts(self, start_index: int = 0, end_index: int = None,
                                     progress_callback=None) -> List[CardProcessingResult]:
        """
        Process all cards that have generation prompts in the database
        
        Args:
            start_index: Starting card index (for pagination)
            end_index: Ending card index (None for all)
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processing results
        """
        logger.info("Starting database-only card processing")
        self.stats['start_time'] = datetime.now()
        
        try:
            session = SessionLocal()
            try:
                # Get all cards with generation prompts
                query = session.query(CardCatalog).filter(
                    CardCatalog.generation_prompt.isnot(None)
                ).order_by(CardCatalog.id)
                
                # Apply pagination
                if end_index:
                    cards = query.offset(start_index).limit(end_index - start_index).all()
                else:
                    cards = query.offset(start_index).all()
                
                self.stats['total_cards'] = len(cards)
                logger.info(f"Processing {len(cards)} cards with prompts")
                
                # Process cards in parallel
                results = self._process_cards_parallel(cards, progress_callback)
                
                self.stats['end_time'] = datetime.now()
                self._log_final_statistics(results)
                
                return results
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Database processing failed: {e}")
            return []
    
    def process_cards_by_ids(self, card_ids: List[int], 
                           progress_callback=None) -> List[CardProcessingResult]:
        """
        Process specific cards by their database IDs
        
        Args:
            card_ids: List of card IDs to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processing results
        """
        logger.info(f"Processing {len(card_ids)} specific cards")
        self.stats['start_time'] = datetime.now()
        
        try:
            session = SessionLocal()
            try:
                # Get cards by IDs
                cards = session.query(CardCatalog).filter(
                    CardCatalog.id.in_(card_ids),
                    CardCatalog.generation_prompt.isnot(None)
                ).all()
                
                self.stats['total_cards'] = len(cards)
                logger.info(f"Found {len(cards)} cards with prompts")
                
                # Process cards
                results = self._process_cards_parallel(cards, progress_callback)
                
                self.stats['end_time'] = datetime.now()
                self._log_final_statistics(results)
                
                return results
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"ID-based processing failed: {e}")
            return []
    
    def process_single_card(self, card_id: int) -> CardProcessingResult:
        """
        Process a single card by ID
        
        Args:
            card_id: Database ID of card to process
            
        Returns:
            Processing result
        """
        try:
            session = SessionLocal()
            try:
                card = session.query(CardCatalog).filter(
                    CardCatalog.id == card_id,
                    CardCatalog.generation_prompt.isnot(None)
                ).first()
                
                if not card:
                    return CardProcessingResult(
                        success=False,
                        card_id=card_id,
                        card_name="Unknown",
                        errors=["Card not found or no generation prompt"]
                    )
                
                return self._process_single_card_db(card, 0)
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Single card processing failed: {e}")
            return CardProcessingResult(
                success=False,
                card_id=card_id,
                card_name="Unknown",
                errors=[str(e)]
            )
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status from database"""
        try:
            session = SessionLocal()
            try:
                # Count cards with prompts
                cards_with_prompts = session.query(CardCatalog).filter(
                    CardCatalog.generation_prompt.isnot(None)
                ).count()
                
                # Count cards with assets
                cards_with_artwork = session.query(CardCatalog).filter(
                    CardCatalog.artwork_url.isnot(None)
                ).count()
                
                cards_with_static = session.query(CardCatalog).filter(
                    CardCatalog.static_url.isnot(None)
                ).count()
                
                cards_with_video = session.query(CardCatalog).filter(
                    CardCatalog.video_url.isnot(None)
                ).count()
                
                total_cards = session.query(CardCatalog).count()
                
                return {
                    'total_cards': total_cards,
                    'cards_with_prompts': cards_with_prompts,
                    'cards_with_artwork': cards_with_artwork,
                    'cards_with_static': cards_with_static,
                    'cards_with_video': cards_with_video,
                    'ready_for_generation': cards_with_prompts,
                    'completion_percentage': (cards_with_artwork / cards_with_prompts * 100) if cards_with_prompts > 0 else 0,
                    'missing_prompts': total_cards - cards_with_prompts
                }
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return {}
    
    def _process_cards_parallel(self, cards: List[CardCatalog], 
                              progress_callback=None) -> List[CardProcessingResult]:
        """Process cards in parallel using thread pool"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all card processing jobs
            future_to_card = {}
            for i, card in enumerate(cards):
                future = executor.submit(self._process_single_card_db, card, i)
                future_to_card[future] = card
            
            # Collect results as they complete
            for future in as_completed(future_to_card):
                card = future_to_card[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        self.stats['successful'] += 1
                        logger.info(f"✅ Processed: {result.card_name} ({self.stats['successful']}/{len(cards)})")
                    else:
                        self.stats['failed'] += 1
                        logger.error(f"❌ Failed: {result.card_name} - {result.errors}")
                    
                    # Call progress callback
                    if progress_callback:
                        progress_callback(len(results), len(cards), result.card_name)
                        
                except Exception as e:
                    self.stats['failed'] += 1
                    error_result = CardProcessingResult(
                        success=False,
                        card_id=card.id,
                        card_name=card.name,
                        errors=[str(e)]
                    )
                    results.append(error_result)
                    logger.error(f"❌ Exception processing {card.name}: {e}")
        
        return results
    
    def _process_single_card_db(self, card: CardCatalog, index: int) -> CardProcessingResult:
        """Process a single card from database"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing card {index}: {card.name} (ID: {card.id})")
            
            # Check if card already has assets and should be skipped
            if (self.config.skip_existing_assets and 
                card.artwork_url and card.static_url):
                logger.info(f"Skipping existing card: {card.name}")
                self.stats['skipped'] += 1
                return CardProcessingResult(
                    success=True,
                    card_id=card.id,
                    card_name=card.name,
                    assets={'existing': 'skipped'},
                    processing_time=time.time() - start_time
                )
            
            # Convert database card to processing format
            card_data = self._card_to_dict(card)
            
            # Step 1: Generate artwork via ComfyUI
            artwork_path = self._generate_artwork_db(card_data)
            if not artwork_path:
                return CardProcessingResult(
                    success=False,
                    card_id=card.id,
                    card_name=card.name,
                    errors=["Artwork generation failed"],
                    processing_time=time.time() - start_time
                )
            
            # Step 2: Generate all asset variants
            assets = self._generate_all_assets_db(card_data, artwork_path)
            
            # Step 3: Update database with asset URLs
            self._update_database_with_assets_db(card.id, assets)
            
            return CardProcessingResult(
                success=True,
                card_id=card.id,
                card_name=card.name,
                assets=assets,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Failed to process card {card.name}: {e}")
            return CardProcessingResult(
                success=False,
                card_id=card.id,
                card_name=card.name,
                errors=[str(e)],
                processing_time=time.time() - start_time
            )
    
    def _card_to_dict(self, card: CardCatalog) -> Dict[str, Any]:
        """Convert CardCatalog to dictionary for processing"""
        return {
            'id': card.id,
            'name': card.name,
            'rarity': card.rarity.value if hasattr(card.rarity, 'value') else str(card.rarity),
            'category': card.category.value if hasattr(card.category, 'value') else str(card.category),
            'mana_colors': card.mana_colors or ['AETHER'],
            'color_code': (card.mana_colors or ['AETHER'])[0],
            'base_stats': card.base_stats or {},
            'generation_prompt': card.generation_prompt,
            'video_prompt': card.video_prompt,
            'frame_style': card.frame_style or 'standard',
            'rules_text': card.rules_text or '',
            'flavor_text': card.flavor_text or '',
            'card_set_id': card.card_set_id or 'open_portal'
        }
    
    def _generate_artwork_db(self, card_data: Dict[str, Any]) -> Optional[str]:
        """Generate artwork using ComfyUI from database data"""
        try:
            card_name = card_data.get('name', 'Unknown')
            image_prompt = card_data.get('generation_prompt', '')
            
            if not image_prompt:
                logger.error(f"No generation prompt for {card_name}")
                return None
            
            # Generate deterministic seed from card ID
            seed = hash(str(card_data.get('id', 0))) % 100000
            
            logger.info(f"Generating artwork for {card_name} with seed {seed}")
            
            # Generate via ComfyUI
            image_data = self.comfyui.generate_card_art(
                prompt=image_prompt,
                seed=seed
            )
            
            if not image_data:
                logger.error(f"ComfyUI generation failed for {card_name}")
                return None
            
            # Save artwork
            safe_name = self._sanitize_filename(card_name)
            artwork_filename = f"{safe_name}.png"
            artwork_path = os.path.join(self.cdn_dirs['artwork'], artwork_filename)
            
            with open(artwork_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Artwork saved: {artwork_path}")
            return artwork_path
            
        except Exception as e:
            logger.error(f"Artwork generation failed: {e}")
            return None
    
    def _generate_all_assets_db(self, card_data: Dict[str, Any], artwork_path: str) -> Dict[str, str]:
        """Generate all asset variants for a card from database data"""
        assets = {}
        card_name = card_data.get('name', 'Unknown')
        safe_name = self._sanitize_filename(card_name)
        
        try:
            # Asset 1: Raw artwork (already generated)
            assets['artwork'] = artwork_path
            
            # Asset 2: Full composite card
            composite_path = self._generate_composite_db(card_data, artwork_path, safe_name)
            if composite_path:
                assets['composite'] = composite_path
            
            # Asset 3: Transparent frame overlay
            frame_path = self._generate_frame_overlay_db(card_data, safe_name)
            if frame_path:
                assets['frame'] = frame_path
            
            # Asset 4: Thumbnail
            if self.config.generate_thumbnails and composite_path:
                thumbnail_path = self._generate_thumbnail_db(composite_path, safe_name)
                if thumbnail_path:
                    assets['thumbnail'] = thumbnail_path
            
            # Asset 5: Video background (if enabled)
            if self.config.generate_videos and card_data.get('video_prompt'):
                video_path = self._generate_video_background_db(card_data, artwork_path, safe_name)
                if video_path:
                    assets['video'] = video_path
            
            logger.info(f"Generated {len(assets)} assets for {card_name}")
            return assets
            
        except Exception as e:
            logger.error(f"Asset generation failed for {card_name}: {e}")
            return assets
    
    def _generate_composite_db(self, card_data: Dict[str, Any], artwork_path: str, safe_name: str) -> Optional[str]:
        """Generate full composite card with frame and text"""
        try:
            composite_img = self.compositor.compose_card(card_data, artwork_path, transparent_bg=False)
            if not composite_img:
                return None
            
            composite_filename = f"{safe_name}_composite.png"
            composite_path = os.path.join(self.cdn_dirs['composite'], composite_filename)
            
            composite_img.convert('RGB').save(composite_path, format='PNG', quality=95)
            return composite_path
            
        except Exception as e:
            logger.error(f"Composite generation failed: {e}")
            return None
    
    def _generate_frame_overlay_db(self, card_data: Dict[str, Any], safe_name: str) -> Optional[str]:
        """Generate transparent frame overlay"""
        try:
            # Create transparent pixel as artwork
            transparent_art = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            temp_art_path = f"/tmp/transparent_{safe_name}.png"
            transparent_art.save(temp_art_path, format='PNG')
            
            # Compose frame with transparent background
            frame_img = self.compositor.compose_card(card_data, temp_art_path, transparent_bg=True)
            if not frame_img:
                return None
            
            frame_filename = f"{safe_name}_frame.png"
            frame_path = os.path.join(self.cdn_dirs['frames'], frame_filename)
            
            frame_img.save(frame_path, format='PNG')
            
            # Clean up temp file
            if os.path.exists(temp_art_path):
                os.remove(temp_art_path)
            
            return frame_path
            
        except Exception as e:
            logger.error(f"Frame overlay generation failed: {e}")
            return None
    
    def _generate_thumbnail_db(self, source_path: str, safe_name: str) -> Optional[str]:
        """Generate thumbnail from composite"""
        try:
            source_img = Image.open(source_path)
            thumbnail = source_img.copy()
            thumbnail.thumbnail((300, 420), Image.Resampling.LANCZOS)
            
            thumbnail_filename = f"{safe_name}_thumb.png"
            thumbnail_path = os.path.join(self.cdn_dirs['thumbnails'], thumbnail_filename)
            
            thumbnail.convert('RGB').save(thumbnail_path, format='PNG', quality=85)
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None
    
    def _generate_video_background_db(self, card_data: Dict[str, Any], artwork_path: str, safe_name: str) -> Optional[str]:
        """Generate video background using database video prompt"""
        try:
            # Load video workflow
            video_workflow_path = '/home/jp/deckport.ai/cardmaker.ai/CardVideo.json'
            with open(video_workflow_path, 'r') as f:
                workflow = json.load(f)
            
            # Use video prompt from database
            video_prompt = card_data.get('video_prompt', '')
            if not video_prompt:
                # Fallback to generated prompt
                video_prompt = self._create_video_prompt_from_card(card_data)
            
            # Update workflow with image and prompt
            workflow = self._inject_video_workflow_data(workflow, artwork_path, video_prompt, safe_name)
            
            # Submit to ComfyUI
            prompt_id = self.comfyui.submit_prompt(workflow)
            if not prompt_id:
                return None
            
            # Wait for video completion (longer timeout)
            video_data = self.comfyui.wait_for_completion(prompt_id, max_wait=self.config.comfyui_timeout)
            
            if video_data:
                video_filename = f"{safe_name}.mp4"
                video_path = os.path.join(self.cdn_dirs['videos'], video_filename)
                
                with open(video_path, 'wb') as f:
                    f.write(video_data)
                
                return video_path
            
            return None
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return None
    
    def _create_video_prompt_from_card(self, card_data: Dict[str, Any]) -> str:
        """Create video prompt from card data"""
        name = card_data.get('name', 'Unknown')
        category = card_data.get('category', 'creature').lower()
        rarity = card_data.get('rarity', 'common').lower()
        mana_color = card_data.get('mana_colors', ['AETHER'])[0]
        
        # Category-specific effects
        category_effects = {
            'creature': 'natural breathing animation, ambient magical aura pulsing',
            'action_fast': 'energy crackling and building, spell effects forming',
            'action_slow': 'grand magical ritual energy building, epic scale effects',
            'equipment': 'magical gleaming and pulsing, energy flowing through item',
            'enchantment': 'magical energy swirling continuously, mystical patterns',
            'structure': 'ambient magical atmosphere, architectural elements responding',
            'hero': 'heroic presence radiating power, cape flowing in magical wind'
        }
        
        # Color-specific effects
        color_effects = {
            'CRIMSON': 'fire particles dancing upward, warm glow pulsing rhythmically',
            'AZURE': 'frost crystals slowly forming, cool mist swirling gently',
            'VERDANT': 'leaves rustling softly, natural energy flowing like wind',
            'OBSIDIAN': 'shadow tendrils moving hypnotically, dark energy crackling',
            'RADIANT': 'divine light pulsing warmly, golden particles floating upward',
            'AETHER': 'cosmic energy flowing like aurora, prismatic effects shifting'
        }
        
        base_effects = category_effects.get(category, 'subtle magical effects')
        color_fx = color_effects.get(mana_color, 'mystical energy')
        
        return f"{name}, {rarity} {category}, {base_effects}, {color_fx}. Seamless 3-second loop, cinemagraph style with most elements static but key magical elements in constant subtle motion."
    
    def _inject_video_workflow_data(self, workflow: Dict, image_path: str, video_prompt: str, output_filename: str) -> Dict:
        """Inject data into CardVideo.json workflow"""
        updated = workflow.copy()
        
        # Update image input nodes
        image_filename = os.path.basename(image_path)
        if "148" in updated:
            updated["148"]["inputs"]["image"] = image_filename
        if "73" in updated:
            updated["73"]["inputs"]["image"] = image_filename
        
        # Update video prompt
        if "105" in updated:
            updated["105"]["inputs"]["text"] = video_prompt
        
        # Update output filename
        if "69" in updated:
            updated["69"]["inputs"]["filename_prefix"] = f"video/{output_filename}"
        
        return updated
    
    def _update_database_with_assets_db(self, card_id: int, assets: Dict[str, str]):
        """Update database with generated asset URLs"""
        try:
            session = SessionLocal()
            try:
                card = session.query(CardCatalog).filter(CardCatalog.id == card_id).first()
                if not card:
                    logger.error(f"Card {card_id} not found for asset update")
                    return
                
                # Update card with asset URLs (convert file paths to web URLs)
                if assets.get('composite'):
                    card.artwork_url = self._file_path_to_url(assets['composite'])
                
                if assets.get('artwork'):
                    card.static_url = self._file_path_to_url(assets['artwork'])
                
                if assets.get('video'):
                    card.video_url = self._file_path_to_url(assets['video'])
                    card.has_animation = True
                
                card.updated_at = datetime.utcnow()
                session.commit()
                
                # Asset tracking temporarily disabled due to table permissions
                # TODO: Re-enable when card_assets table permissions are fixed
                # For now, asset URLs are stored directly in card_catalog table
                
                session.commit()
                logger.info(f"Database updated with assets for {card.name}")
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Database update failed for card {card_id}: {e}")
    
    def _file_path_to_url(self, file_path: str) -> str:
        """Convert local file path to web URL"""
        if not file_path:
            return None
        
        try:
            # Convert file path to web URL
            static_base = "/home/jp/deckport.ai/static"
            if file_path.startswith(static_base):
                # Remove the static base and prepend /static
                relative_path = os.path.relpath(file_path, static_base)
                return f"/static/{relative_path}".replace('\\', '/')
            
            return file_path
        except Exception:
            return file_path
    
    def _path_to_url(self, file_path: str, base_url: str) -> str:
        """Convert local file path to CDN URL (legacy method)"""
        return self._file_path_to_url(file_path)
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize card name for filename"""
        return name.lower().replace(' ', '_').replace("'", "").replace('"', '').replace('/', '_')
    
    def _log_final_statistics(self, results: List[CardProcessingResult]):
        """Log final processing statistics"""
        total_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("="*60)
        logger.info("DATABASE PROCESSING COMPLETE")
        logger.info("="*60)
        logger.info(f"Total Cards: {self.stats['total_cards']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Success Rate: {(self.stats['successful']/max(1,self.stats['total_cards']))*100:.1f}%")
        logger.info(f"Total Time: {total_time:.1f} seconds")
        logger.info(f"Average Time per Card: {total_time/max(1,self.stats['total_cards']):.1f} seconds")
        logger.info("="*60)
        
        # Log failed cards
        failed_cards = [r for r in results if not r.success]
        if failed_cards:
            logger.error("FAILED CARDS:")
            for result in failed_cards:
                logger.error(f"  - {result.card_name}: {result.errors}")


# Global processor instance
_database_processor = None

def get_card_database_processor(config: DatabaseProcessingConfig = None) -> CardDatabaseProcessor:
    """Get global database processor instance"""
    global _database_processor
    if _database_processor is None:
        _database_processor = CardDatabaseProcessor(config)
    return _database_processor
