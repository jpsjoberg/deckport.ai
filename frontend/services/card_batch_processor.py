"""
Card Batch Processor - Production Pipeline
Automated processing from CSV → Graphics → Database with all assets
"""

import os
import csv
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
import sys; sys.path.append("/home/jp/deckport.ai"); from shared.models.base import CardCatalog, CardAsset
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class CardProcessingResult:
    """Result of processing a single card"""
    success: bool
    card_name: str
    card_id: Optional[int] = None
    assets: Dict[str, str] = None
    errors: List[str] = None
    processing_time: float = 0.0

@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    max_workers: int = 4
    comfyui_timeout: int = 300
    quality_checks: bool = True
    generate_videos: bool = True
    generate_thumbnails: bool = True
    output_base_dir: str = "/home/jp/deckport.ai/static/cards"
    backup_existing: bool = True

class CardBatchProcessor:
    """Production-ready batch processor for card asset generation"""
    
    def __init__(self, config: BatchProcessingConfig = None):
        self.config = config or BatchProcessingConfig()
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
    
    def process_csv_batch(self, art_csv_path: str, gameplay_csv_path: str, 
                         start_index: int = 0, end_index: int = None,
                         resume_from_existing: bool = True) -> List[CardProcessingResult]:
        """
        Process batch of cards from CSV files
        
        Args:
            art_csv_path: Path to cards_art.csv
            gameplay_csv_path: Path to cards_gameplay.csv  
            start_index: Starting card index (for resuming)
            end_index: Ending card index (None for all)
            resume_from_existing: Skip cards that already exist in database
            
        Returns:
            List of processing results
        """
        logger.info(f"Starting batch processing from CSV files")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Load CSV data
            art_data = self._load_csv_data(art_csv_path)
            gameplay_data = self._load_csv_data(gameplay_csv_path)
            
            # Merge data by card name
            merged_cards = self._merge_card_data(art_data, gameplay_data)
            
            # Filter by index range
            if end_index:
                merged_cards = merged_cards[start_index:end_index]
            else:
                merged_cards = merged_cards[start_index:]
            
            self.stats['total_cards'] = len(merged_cards)
            logger.info(f"Processing {len(merged_cards)} cards")
            
            # Process cards in parallel batches
            results = self._process_cards_parallel(merged_cards, resume_from_existing)
            
            self.stats['end_time'] = datetime.now()
            self._log_final_statistics(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return []
    
    def _load_csv_data(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load CSV data into list of dictionaries"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Failed to load CSV {csv_path}: {e}")
            return []
    
    def _merge_card_data(self, art_data: List[Dict], gameplay_data: List[Dict]) -> List[Dict]:
        """Merge art and gameplay data by card name"""
        try:
            # Create lookup by name for gameplay data
            gameplay_lookup = {}
            for row in gameplay_data:
                # Handle both 'name' and 'uname' columns
                name = row.get('name') or row.get('uname', '')
                if name:
                    gameplay_lookup[name] = row
            
            merged_cards = []
            for art_row in art_data:
                # Handle both 'name' and 'uname' columns
                name = art_row.get('name') or art_row.get('uname', '')
                if not name:
                    continue
                
                gameplay_row = gameplay_lookup.get(name)
                if not gameplay_row:
                    logger.warning(f"No gameplay data found for card: {name}")
                    continue
                
                # Merge the data
                merged_card = {**art_row, **gameplay_row}
                merged_card['name'] = name  # Ensure consistent name field
                merged_cards.append(merged_card)
            
            logger.info(f"Merged {len(merged_cards)} cards from CSV data")
            return merged_cards
            
        except Exception as e:
            logger.error(f"Failed to merge card data: {e}")
            return []
    
    def _process_cards_parallel(self, cards: List[Dict], resume_from_existing: bool) -> List[CardProcessingResult]:
        """Process cards in parallel using thread pool"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all card processing jobs
            future_to_card = {}
            for i, card_data in enumerate(cards):
                future = executor.submit(self._process_single_card, card_data, i, resume_from_existing)
                future_to_card[future] = card_data
            
            # Collect results as they complete
            for future in as_completed(future_to_card):
                card_data = future_to_card[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        self.stats['successful'] += 1
                        logger.info(f"✅ Processed: {result.card_name} ({self.stats['successful']}/{len(cards)})")
                    else:
                        self.stats['failed'] += 1
                        logger.error(f"❌ Failed: {result.card_name} - {result.errors}")
                        
                except Exception as e:
                    self.stats['failed'] += 1
                    error_result = CardProcessingResult(
                        success=False,
                        card_name=card_data.get('name', 'Unknown'),
                        errors=[str(e)]
                    )
                    results.append(error_result)
                    logger.error(f"❌ Exception processing {card_data.get('name')}: {e}")
        
        return results
    
    def _process_single_card(self, card_data: Dict, index: int, resume_from_existing: bool) -> CardProcessingResult:
        """Process a single card through the complete pipeline"""
        start_time = time.time()
        card_name = card_data.get('name', f'Card_{index}')
        
        try:
            logger.info(f"Processing card {index}: {card_name}")
            
            # Check if card already exists in database
            if resume_from_existing:
                existing_card = self._check_existing_card(card_name)
                if existing_card:
                    logger.info(f"Skipping existing card: {card_name}")
                    self.stats['skipped'] += 1
                    return CardProcessingResult(
                        success=True,
                        card_name=card_name,
                        card_id=existing_card.id,
                        assets={},
                        processing_time=time.time() - start_time
                    )
            
            # Step 1: Generate artwork via ComfyUI
            artwork_path = self._generate_artwork(card_data)
            if not artwork_path:
                return CardProcessingResult(
                    success=False,
                    card_name=card_name,
                    errors=["Artwork generation failed"],
                    processing_time=time.time() - start_time
                )
            
            # Step 2: Generate all asset variants
            assets = self._generate_all_assets(card_data, artwork_path)
            
            # Step 3: Save to database with all metadata
            card_id = self._save_to_database(card_data, assets)
            
            if card_id:
                return CardProcessingResult(
                    success=True,
                    card_name=card_name,
                    card_id=card_id,
                    assets=assets,
                    processing_time=time.time() - start_time
                )
            else:
                return CardProcessingResult(
                    success=False,
                    card_name=card_name,
                    errors=["Database save failed"],
                    assets=assets,
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"Failed to process card {card_name}: {e}")
            return CardProcessingResult(
                success=False,
                card_name=card_name,
                errors=[str(e)],
                processing_time=time.time() - start_time
            )
    
    def _check_existing_card(self, card_name: str) -> Optional[CardCatalog]:
        """Check if card already exists in database"""
        try:
            session = SessionLocal()
            try:
                card = session.query(CardCatalog).filter(CardCatalog.name == card_name).first()
                return card
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Database check failed for {card_name}: {e}")
            return None
    
    def _generate_artwork(self, card_data: Dict) -> Optional[str]:
        """Generate artwork using ComfyUI"""
        try:
            card_name = card_data.get('name', 'Unknown')
            image_prompt = card_data.get('image_prompt', '')
            
            if not image_prompt:
                logger.error(f"No image prompt for {card_name}")
                return None
            
            # Generate deterministic seed from card name
            seed = hash(card_name) % 100000
            
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
    
    def _generate_all_assets(self, card_data: Dict, artwork_path: str) -> Dict[str, str]:
        """Generate all asset variants for a card"""
        assets = {}
        card_name = card_data.get('name', 'Unknown')
        safe_name = self._sanitize_filename(card_name)
        
        try:
            # Asset 1: Raw artwork (already generated)
            assets['artwork'] = artwork_path
            
            # Asset 2: Full composite card
            composite_path = self._generate_composite(card_data, artwork_path, safe_name)
            if composite_path:
                assets['composite'] = composite_path
            
            # Asset 3: Transparent frame overlay
            frame_path = self._generate_frame_overlay(card_data, safe_name)
            if frame_path:
                assets['frame'] = frame_path
            
            # Asset 4: Thumbnail
            if self.config.generate_thumbnails and composite_path:
                thumbnail_path = self._generate_thumbnail(composite_path, safe_name)
                if thumbnail_path:
                    assets['thumbnail'] = thumbnail_path
            
            # Asset 5: Video background (if enabled)
            if self.config.generate_videos:
                video_path = self._generate_video_background(card_data, artwork_path, safe_name)
                if video_path:
                    assets['video'] = video_path
            
            logger.info(f"Generated {len(assets)} assets for {card_name}")
            return assets
            
        except Exception as e:
            logger.error(f"Asset generation failed for {card_name}: {e}")
            return assets
    
    def _generate_composite(self, card_data: Dict, artwork_path: str, safe_name: str) -> Optional[str]:
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
    
    def _generate_frame_overlay(self, card_data: Dict, safe_name: str) -> Optional[str]:
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
    
    def _generate_thumbnail(self, source_path: str, safe_name: str) -> Optional[str]:
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
    
    def _generate_video_background(self, card_data: Dict, artwork_path: str, safe_name: str) -> Optional[str]:
        """Generate video background using CardVideo.json workflow"""
        try:
            # Load video workflow
            video_workflow_path = '/home/jp/deckport.ai/cardmaker.ai/CardVideo.json'
            with open(video_workflow_path, 'r') as f:
                workflow = json.load(f)
            
            # Create video prompt
            video_prompt = self._create_video_prompt(card_data)
            
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
    
    def _create_video_prompt(self, card_data: Dict) -> str:
        """Create video prompt based on card properties"""
        name = card_data.get('name', 'Unknown')
        category = card_data.get('category', 'CREATURE').lower()
        rarity = card_data.get('rarity', 'COMMON').lower()
        mana_color = card_data.get('mana_color_code', 'AETHER')
        
        # Category-specific effects
        category_effects = {
            'creature': 'natural breathing animation, ambient magical aura pulsing',
            'action_fast': 'energy crackling and building, spell effects forming',
            'action_slow': 'grand magical ritual energy building, epic scale effects',
            'equipment': 'magical gleaming and pulsing, energy flowing through item',
            'enchantment': 'magical energy swirling continuously, mystical patterns',
            'structure': 'ambient magical atmosphere, architectural elements responding'
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
    
    def _save_to_database(self, card_data: Dict, assets: Dict[str, str]) -> Optional[int]:
        """Save card and assets to database"""
        try:
            session = SessionLocal()
            try:
                # Create card catalog entry
                card = CardCatalog(
                    product_sku=self._generate_sku(card_data.get('name', '')),
                    name=card_data.get('name', ''),
                    rarity=card_data.get('rarity', 'COMMON').lower(),
                    category=card_data.get('category', 'CREATURE').lower(),
                    base_stats={
                        'mana_cost': int(card_data.get('mana_cost', 0)),
                        'energy_cost': int(card_data.get('energy_cost', 0)),
                        'attack': int(card_data.get('attack', 0)),
                        'defense': int(card_data.get('defense', 0)),
                        'health': int(card_data.get('health', 0)),
                    },
                    mana_colors=[card_data.get('mana_color_code', 'AETHER')],
                    generation_prompt=card_data.get('image_prompt', ''),
                    video_prompt=self._create_video_prompt(card_data) if self.config.generate_videos else None,
                    artwork_url=self._path_to_url(assets.get('composite')),
                    static_url=self._path_to_url(assets.get('artwork')),
                    video_url=self._path_to_url(assets.get('video')),
                    has_animation=bool(assets.get('video')),
                    card_set_id=card_data.get('card_set', 'open_portal')
                )
                
                session.add(card)
                session.flush()  # Get the card ID
                
                # Create asset records
                for asset_type, asset_path in assets.items():
                    if asset_path and os.path.exists(asset_path):
                        asset = CardAsset(
                            card_id=card.id,
                            asset_type=asset_type,
                            file_path=asset_path,
                            file_url=self._path_to_url(asset_path),
                            file_size=os.path.getsize(asset_path)
                        )
                        session.add(asset)
                
                session.commit()
                logger.info(f"Saved card to database: {card.name} (ID: {card.id})")
                return card.id
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database save failed: {e}")
                return None
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def _generate_sku(self, name: str) -> str:
        """Generate product SKU from card name"""
        return name.upper().replace(' ', '_').replace("'", "").replace('"', '')[:64]
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize card name for filename"""
        return name.lower().replace(' ', '_').replace("'", "").replace('"', '').replace('/', '_')
    
    def _path_to_url(self, file_path: str) -> Optional[str]:
        """Convert local file path to CDN URL"""
        if not file_path:
            return None
        
        try:
            # Convert to relative path from static directory
            static_base = "/home/jp/deckport.ai/static"
            if file_path.startswith(static_base):
                relative_path = os.path.relpath(file_path, static_base)
                return f"/static/{relative_path}"
            
            return file_path
        except Exception:
            return file_path
    
    def _log_final_statistics(self, results: List[CardProcessingResult]):
        """Log final processing statistics"""
        total_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("="*60)
        logger.info("BATCH PROCESSING COMPLETE")
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
_batch_processor = None

def get_card_batch_processor(config: BatchProcessingConfig = None) -> CardBatchProcessor:
    """Get global batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = CardBatchProcessor(config)
    return _batch_processor
