"""
PostgreSQL Card Service for Deckport Admin Panel
Integrates with the main platform database using SQLAlchemy
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Import database connection
import sys
sys.path.append('/home/jp/deckport.ai')
from shared.database.connection import SessionLocal
from shared.models.card_templates import (
    CardSet, CardTemplate, CardTemplateStats, CardTemplateManaCost, 
    CardTemplateTargeting, CardTemplateLimits, CardTemplateArtGeneration,
    TemplateCategory, TemplateRarity, ManaColor, ArtGenerationStatus
)
from shared.models.nfc_card_instances import (
    NFCCardInstance, CardEvolution, CardMatchParticipation
)

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


class PostgreSQLCardService:
    """Service for card generation, rendering, and database operations using PostgreSQL"""
    
    def __init__(self):
        self.comfyui = get_comfyui_service()
        
        # Ensure output directory exists
        os.makedirs(CARDMAKER_OUTPUT_DIR, exist_ok=True)
    
    def get_db_session(self) -> Session:
        """Get SQLAlchemy database session"""
        return SessionLocal()
    
    def create_card_template(self, card_data: Dict[str, Any], admin_user: str = None, card_set_slug: str = "open-portal") -> Optional[int]:
        """
        Create a new card template in the PostgreSQL database
        
        Args:
            card_data: Dictionary containing card information
            admin_user: Username of admin creating the template
            card_set_slug: Slug of the card set to add this template to
            
        Returns:
            Template ID if successful, None otherwise
        """
        db = self.get_db_session()
        try:
            # Get or create card set
            card_set = db.query(CardSet).filter(CardSet.slug == card_set_slug).first()
            if not card_set:
                # Create default set if it doesn't exist
                card_set = CardSet(
                    slug=card_set_slug,
                    name="Open Portal",
                    description="The inaugural card set for Deckport",
                    version="1.0",
                    created_by_admin=admin_user or "system"
                )
                db.add(card_set)
                db.flush()
            
            # Generate slug from name
            slug = card_data['name'].lower().replace(' ', '-').replace("'", "")
            
            # Create card template
            template = CardTemplate(
                card_set_id=card_set.id,
                slug=slug,
                name=card_data['name'],
                category=TemplateCategory(card_data['category']),
                rarity=TemplateRarity(card_data['rarity']),
                legendary=card_data['rarity'] == 'LEGENDARY',
                primary_color=ManaColor(card_data['color_code']),
                energy_cost=card_data.get('energy_cost', 0),
                equipment_slots=card_data.get('equipment_slots', 0),
                keywords=card_data.get('keywords', ''),
                description=card_data.get('description', ''),
                flavor_text=card_data.get('flavor_text', ''),
                created_by_admin=admin_user
            )
            
            db.add(template)
            db.flush()  # Get the ID
            
            # Create stats (for creatures/structures)
            if card_data['category'] in ['CREATURE', 'STRUCTURE']:
                stats = CardTemplateStats(
                    template_id=template.id,
                    attack=card_data.get('attack', 0),
                    defense=card_data.get('defense', 0),
                    health=card_data.get('health', 0),
                    base_energy_per_turn=card_data.get('base_energy_per_turn', 0)
                )
                db.add(stats)
            
            # Create mana cost
            if card_data.get('mana_cost', 0) > 0:
                mana_cost = CardTemplateManaCost(
                    template_id=template.id,
                    color=ManaColor(card_data['color_code']),
                    amount=card_data['mana_cost']
                )
                db.add(mana_cost)
            
            # Create targeting (default values)
            targeting = CardTemplateTargeting(
                template_id=template.id,
                target_friendly=False,
                target_enemy=True,
                target_self=False
            )
            db.add(targeting)
            
            db.commit()
            logger.info(f"Created card template: {card_data['name']} (ID: {template.id})")
            return template.id
            
        except Exception as e:
            logger.error(f"Failed to create card template: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def create_nfc_card_from_template(self, template_id: int, ntag_uid: str, 
                                    owner_id: Optional[int] = None, 
                                    batch_id: Optional[int] = None) -> Optional[int]:
        """
        Create a unique NFC card instance from a template
        
        Args:
            template_id: ID of the card template to instantiate
            ntag_uid: Unique NFC tag identifier
            owner_id: Player ID who owns this card
            batch_id: Production batch ID
            
        Returns:
            NFC card instance ID if successful, None otherwise
        """
        db = self.get_db_session()
        try:
            # Verify template exists
            template = db.query(CardTemplate).filter(CardTemplate.id == template_id).first()
            if not template:
                logger.error(f"Template {template_id} not found")
                return None
            
            # Generate serial number
            import time
            serial_number = f"{template.slug.upper()}-{int(time.time())}"
            
            # Create NFC card instance
            nfc_card = NFCCardInstance(
                template_id=template_id,
                ntag_uid=ntag_uid,
                batch_id=batch_id,
                instance_name=template.name,  # Start with template name
                serial_number=serial_number,
                current_owner_id=owner_id,
                status="mint",  # Newly created
                evolution_level=0,
                experience_points=0,
                total_matches_played=0,
                total_wins=0
            )
            
            db.add(nfc_card)
            db.commit()
            
            logger.info(f"Created NFC card instance: {template.name} (ID: {nfc_card.id}, UID: {ntag_uid})")
            return nfc_card.id
            
        except Exception as e:
            logger.error(f"Failed to create NFC card instance: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    # Alias for backward compatibility
    def create_card(self, card_data: Dict[str, Any], admin_user: str = None) -> Optional[int]:
        """Create a card template (backward compatibility)"""
        return self.create_card_template(card_data, admin_user)
    
    def get_card(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Get card data by ID"""
        db = self.get_db_session()
        try:
            card = db.query(GeneratedCard).filter(GeneratedCard.id == card_id).first()
            if not card:
                return None
            
            # Convert to dictionary with related data
            card_dict = {
                'id': card.id,
                'slug': card.slug,
                'name': card.name,
                'category': card.category.value,
                'rarity': card.rarity.value,
                'legendary': card.legendary,
                'color_code': card.primary_color.value,
                'energy_cost': card.energy_cost,
                'equipment_slots': card.equipment_slots,
                'keywords': card.keywords,
                'created_at': card.created_at.isoformat(),
                'updated_at': card.updated_at.isoformat(),
                'created_by_admin': card.created_by_admin
            }
            
            # Add stats if available
            if card.stats:
                card_dict.update({
                    'attack': card.stats.attack,
                    'defense': card.stats.defense,
                    'health': card.stats.health,
                    'base_energy_per_turn': card.stats.base_energy_per_turn
                })
            
            # Add mana costs
            if card.mana_costs:
                card_dict['mana_cost'] = card.mana_costs[0].amount
                card_dict['mana_color'] = card.mana_costs[0].color.value
            
            # Add targeting
            if card.targeting:
                card_dict.update({
                    'target_friendly': card.targeting.target_friendly,
                    'target_enemy': card.targeting.target_enemy,
                    'target_self': card.targeting.target_self
                })
            
            # Check for art files
            art_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card.slug}.png")
            card_dict['has_art'] = os.path.exists(art_path)
            card_dict['art_url'] = f"/static/cards/{card.slug}.png" if card_dict['has_art'] else None
            
            return card_dict
            
        except Exception as e:
            logger.error(f"Failed to get card {card_id}: {e}")
            return None
        finally:
            db.close()
    
    def get_cards(self, filters: Dict[str, Any] = None, 
                  page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
        """
        Get cards with optional filtering and pagination
        
        Returns:
            Tuple of (cards_list, total_count)
        """
        db = self.get_db_session()
        try:
            filters = filters or {}
            
            # Build query
            query = db.query(GeneratedCard)
            
            # Apply filters
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    (GeneratedCard.name.ilike(search_term)) |
                    (GeneratedCard.slug.ilike(search_term))
                )
            
            if filters.get('category'):
                query = query.filter(GeneratedCard.category == GeneratedCardCategory(filters['category']))
            
            if filters.get('rarity'):
                query = query.filter(GeneratedCard.rarity == GeneratedCardRarity(filters['rarity']))
            
            if filters.get('color'):
                query = query.filter(GeneratedCard.primary_color == ManaColor(filters['color']))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            cards = query.order_by(desc(GeneratedCard.created_at)).offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to dictionaries
            cards_list = []
            for card in cards:
                card_dict = {
                    'id': card.id,
                    'slug': card.slug,
                    'name': card.name,
                    'category': card.category.value,
                    'rarity': card.rarity.value,
                    'legendary': card.legendary,
                    'color_code': card.primary_color.value,
                    'energy_cost': card.energy_cost,
                    'equipment_slots': card.equipment_slots,
                    'created_at': card.created_at.isoformat()
                }
                
                # Add stats if available
                if card.stats:
                    card_dict.update({
                        'attack': card.stats.attack,
                        'defense': card.stats.defense,
                        'health': card.stats.health,
                        'base_energy_per_turn': card.stats.base_energy_per_turn
                    })
                
                # Add mana cost
                if card.mana_costs:
                    card_dict['mana_cost'] = card.mana_costs[0].amount
                
                # Check for art
                art_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card.slug}.png")
                card_dict['has_art'] = os.path.exists(art_path)
                
                cards_list.append(card_dict)
            
            return cards_list, total_count
            
        except Exception as e:
            logger.error(f"Failed to get cards: {e}")
            return [], 0
        finally:
            db.close()
    
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
        db = self.get_db_session()
        try:
            # Get card data
            card = db.query(GeneratedCard).filter(GeneratedCard.id == card_id).first()
            if not card:
                logger.error(f"Card {card_id} not found")
                return False
            
            # Create art generation record
            art_gen = CardArtGeneration(
                card_id=card_id,
                prompt=prompt,
                seed=seed,
                status=ArtGenerationStatus.PENDING
            )
            db.add(art_gen)
            db.commit()
            
            # Update status to generating
            art_gen.status = ArtGenerationStatus.GENERATING
            art_gen.started_at = datetime.utcnow()
            db.commit()
            
            # Generate art via ComfyUI
            logger.info(f"Generating art for card {card.name}")
            image_data = self.comfyui.generate_card_art(prompt, seed)
            
            if not image_data:
                art_gen.status = ArtGenerationStatus.FAILED
                art_gen.error_message = "ComfyUI generation failed"
                db.commit()
                logger.error(f"ComfyUI generation failed for card {card.name}")
                return False
            
            # Save raw art
            raw_art_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"raw_{card.slug}.png")
            with open(raw_art_path, 'wb') as f:
                f.write(image_data)
            
            art_gen.raw_art_path = raw_art_path
            
            # Compose final card (simplified version - you can expand this)
            final_card_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{card.slug}.png")
            
            # For now, just copy the raw art as final card
            # You can integrate the full card composition logic here
            with open(final_card_path, 'wb') as f:
                f.write(image_data)
            
            # Update art generation record
            art_gen.status = ArtGenerationStatus.COMPLETED
            art_gen.final_card_path = final_card_path
            art_gen.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Card art generated successfully: {final_card_path}")
            return True
                
        except Exception as e:
            logger.error(f"Art generation failed for card {card_id}: {e}")
            if 'art_gen' in locals():
                art_gen.status = ArtGenerationStatus.FAILED
                art_gen.error_message = str(e)
                db.commit()
            return False
        finally:
            db.close()
    
    def delete_card(self, card_id: int) -> bool:
        """Delete a card and its associated files"""
        db = self.get_db_session()
        try:
            card = db.query(GeneratedCard).filter(GeneratedCard.id == card_id).first()
            if not card:
                return False
            
            # Delete associated files
            for prefix in ['', 'raw_']:
                file_path = os.path.join(CARDMAKER_OUTPUT_DIR, f"{prefix}{card.slug}.png")
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete from database (cascade will handle related tables)
            db.delete(card)
            db.commit()
            
            logger.info(f"Deleted card: {card.name} (ID: {card_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete card {card_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get card database statistics"""
        db = self.get_db_session()
        try:
            # Total cards
            total_cards = db.query(GeneratedCard).count()
            
            # By category
            category_stats = {}
            for category in GeneratedCardCategory:
                count = db.query(GeneratedCard).filter(GeneratedCard.category == category).count()
                category_stats[category.value] = count
            
            # By rarity
            rarity_stats = {}
            for rarity in GeneratedCardRarity:
                count = db.query(GeneratedCard).filter(GeneratedCard.rarity == rarity).count()
                rarity_stats[rarity.value] = count
            
            # By color
            color_stats = {}
            for color in ManaColor:
                count = db.query(GeneratedCard).filter(GeneratedCard.primary_color == color).count()
                color_stats[color.value] = count
            
            # Recent cards
            recent_cards = db.query(GeneratedCard).order_by(desc(GeneratedCard.created_at)).limit(10).all()
            recent_cards_data = []
            for card in recent_cards:
                recent_cards_data.append({
                    'name': card.name,
                    'category': card.category.value,
                    'rarity': card.rarity.value,
                    'color_code': card.primary_color.value,
                    'created_at': card.created_at.isoformat()
                })
            
            return {
                'total_cards': total_cards,
                'category_stats': category_stats,
                'rarity_stats': rarity_stats,
                'color_stats': color_stats,
                'recent_cards': recent_cards_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
        finally:
            db.close()


# Global service instance
postgres_card_service = PostgreSQLCardService()


def get_postgres_card_service() -> PostgreSQLCardService:
    """Get the global PostgreSQL card service instance"""
    return postgres_card_service
