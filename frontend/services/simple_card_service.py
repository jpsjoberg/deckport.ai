"""
Simple Card Service for PostgreSQL
Works with the new card template and NFC instance tables
"""

import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleCardService:
    """Simple PostgreSQL-based card service"""
    
    def __init__(self):
        self.db_config = {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'deckport',
            'user': 'deckport_app',
            'password': 'N0D3-N0D3-N0D3#M0nk3y33'
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get card system statistics"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                stats = {}
                
                # Card template stats
                cursor.execute("SELECT COUNT(*) as total FROM card_templates")
                stats['total_templates'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as published FROM card_templates WHERE is_published = true")
                stats['published_templates'] = cursor.fetchone()['published']
                
                cursor.execute("SELECT rarity, COUNT(*) as count FROM card_templates GROUP BY rarity")
                stats['by_rarity'] = {row['rarity']: row['count'] for row in cursor.fetchall()}
                
                cursor.execute("SELECT category, COUNT(*) as count FROM card_templates GROUP BY category")
                stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
                
                # NFC instance stats
                cursor.execute("SELECT COUNT(*) as total FROM nfc_card_instances")
                stats['total_nfc_cards'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT status, COUNT(*) as count FROM nfc_card_instances GROUP BY status")
                stats['nfc_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
        finally:
            conn.close()
    
    def create_card_template(self, template_data: Dict[str, Any]) -> Optional[int]:
        """Create a new card template"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                # Insert card template
                insert_sql = """
                INSERT INTO card_templates 
                (name, slug, description, flavor_text, rarity, category, color_code, 
                 art_prompt, art_style, is_published)
                VALUES (%(name)s, %(slug)s, %(description)s, %(flavor_text)s, %(rarity)s, 
                        %(category)s, %(color_code)s, %(art_prompt)s, %(art_style)s, %(is_published)s)
                RETURNING id
                """
                
                cursor.execute(insert_sql, template_data)
                template_id = cursor.fetchone()[0]
                
                # Insert stats if provided
                if 'stats' in template_data:
                    stats = template_data['stats']
                    stats_sql = """
                    INSERT INTO card_template_stats 
                    (template_id, attack, defense, health, base_energy_per_turn)
                    VALUES (%(template_id)s, %(attack)s, %(defense)s, %(health)s, %(base_energy_per_turn)s)
                    """
                    stats['template_id'] = template_id
                    cursor.execute(stats_sql, stats)
                
                # Insert mana costs if provided
                if 'mana_costs' in template_data:
                    for mana_cost in template_data['mana_costs']:
                        mana_sql = """
                        INSERT INTO card_template_mana_costs 
                        (template_id, color_code, amount)
                        VALUES (%(template_id)s, %(color_code)s, %(amount)s)
                        """
                        mana_cost['template_id'] = template_id
                        cursor.execute(mana_sql, mana_cost)
                
                # Insert targeting if provided
                if 'targeting' in template_data:
                    targeting = template_data['targeting']
                    targeting_sql = """
                    INSERT INTO card_template_targeting 
                    (template_id, target_friendly, target_enemy, target_self)
                    VALUES (%(template_id)s, %(target_friendly)s, %(target_enemy)s, %(target_self)s)
                    """
                    targeting['template_id'] = template_id
                    cursor.execute(targeting_sql, targeting)
                
                conn.commit()
                return template_id
                
        except Exception as e:
            logger.error(f"Error creating card template: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_card_templates(self, filters: Dict[str, Any] = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get card templates with filtering and pagination"""
        conn = self.get_connection()
        if not conn:
            return {'templates': [], 'pagination': {}}
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Build WHERE clause
                where_clauses = []
                params = {}
                
                if filters:
                    if filters.get('search'):
                        where_clauses.append("(ct.name ILIKE %(search)s OR ct.slug ILIKE %(search)s)")
                        params['search'] = f"%{filters['search']}%"
                    
                    if filters.get('category'):
                        where_clauses.append("ct.category = %(category)s")
                        params['category'] = filters['category']
                    
                    if filters.get('rarity'):
                        where_clauses.append("ct.rarity = %(rarity)s")
                        params['rarity'] = filters['rarity']
                    
                    if filters.get('color'):
                        where_clauses.append("ct.color_code = %(color)s")
                        params['color'] = filters['color']
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                # Get total count
                count_sql = f"SELECT COUNT(*) as total FROM card_templates ct WHERE {where_sql}"
                cursor.execute(count_sql, params)
                total_count = cursor.fetchone()['total']
                
                # Get templates with stats
                offset = (page - 1) * per_page
                params.update({'limit': per_page, 'offset': offset})
                
                templates_sql = f"""
                SELECT ct.*, cts.attack, cts.defense, cts.health, cts.base_energy_per_turn,
                       ctmc.color_code as mana_color, ctmc.amount as mana_cost
                FROM card_templates ct
                LEFT JOIN card_template_stats cts ON ct.id = cts.template_id
                LEFT JOIN card_template_mana_costs ctmc ON ct.id = ctmc.template_id
                WHERE {where_sql}
                ORDER BY ct.created_at DESC
                LIMIT %(limit)s OFFSET %(offset)s
                """
                
                cursor.execute(templates_sql, params)
                templates = cursor.fetchall()
                
                # Calculate pagination
                total_pages = (total_count + per_page - 1) // per_page
                
                pagination = {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                }
                
                return {
                    'templates': [dict(template) for template in templates],
                    'pagination': pagination
                }
                
        except Exception as e:
            logger.error(f"Error getting card templates: {e}")
            return {'templates': [], 'pagination': {}}
        finally:
            conn.close()
    
    def get_card_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a single card template with all related data"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get template with stats
                template_sql = """
                SELECT ct.*, cts.attack, cts.defense, cts.health, cts.base_energy_per_turn,
                       ctmc.color_code as mana_color, ctmc.amount as mana_cost,
                       ctt.target_friendly, ctt.target_enemy, ctt.target_self
                FROM card_templates ct
                LEFT JOIN card_template_stats cts ON ct.id = cts.template_id
                LEFT JOIN card_template_mana_costs ctmc ON ct.id = ctmc.template_id
                LEFT JOIN card_template_targeting ctt ON ct.id = ctt.template_id
                WHERE ct.id = %(template_id)s
                """
                
                cursor.execute(template_sql, {'template_id': template_id})
                template = cursor.fetchone()
                
                if template:
                    return dict(template)
                return None
                
        except Exception as e:
            logger.error(f"Error getting card template: {e}")
            return None
        finally:
            conn.close()
    
    def create_nfc_card_instance(self, template_id: int, nfc_uid: str, **kwargs) -> Optional[int]:
        """Create NFC card instance from template"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                insert_sql = """
                INSERT INTO nfc_card_instances 
                (template_id, nfc_uid, serial_number, status, owner_player_id)
                VALUES (%(template_id)s, %(nfc_uid)s, %(serial_number)s, %(status)s, %(owner_player_id)s)
                RETURNING id
                """
                
                data = {
                    'template_id': template_id,
                    'nfc_uid': nfc_uid,
                    'serial_number': kwargs.get('serial_number'),
                    'status': kwargs.get('status', 'provisioned'),
                    'owner_player_id': kwargs.get('owner_player_id')
                }
                
                cursor.execute(insert_sql, data)
                instance_id = cursor.fetchone()[0]
                
                conn.commit()
                return instance_id
                
        except Exception as e:
            logger.error(f"Error creating NFC card instance: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()


# Service instance
_card_service = None

def get_simple_card_service() -> SimpleCardService:
    """Get the card service instance"""
    global _card_service
    if _card_service is None:
        _card_service = SimpleCardService()
    return _card_service
