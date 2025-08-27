"""
Admin Arena Management Routes
Handles arena CRUD operations, console assignments, and game environment management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.base import Console, Match, ConsoleStatus
from shared.models.arena import Arena
from shared.auth.auto_rbac_decorator import auto_rbac_required
from shared.auth.admin_roles import Permission
import logging

logger = logging.getLogger(__name__)

admin_arenas_bp = Blueprint('admin_arenas', __name__, url_prefix='/v1/admin/arenas')

@admin_arenas_bp.route('', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_arenas():
    """Get list of all arenas with statistics"""
    try:
        with SessionLocal() as session:
            # Get all arenas
            arenas = session.query(Arena).order_by(Arena.name).all()
            
            arena_list = []
            for arena in arenas:
                # Get console count for this arena
                console_count = session.query(Console).filter(
                    Console.current_arena_id == arena.id,
                    Console.status == ConsoleStatus.active
                ).count()
                
                # Get match count in last 24 hours
                yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
                matches_24h = session.query(Match).filter(
                    Match.arena_id == arena.id,
                    Match.created_at >= yesterday
                ).count()
                
                arena_data = {
                    'id': arena.id,
                    'name': arena.name,
                    'mana_color': arena.mana_color,
                    'passive_effect': arena.passive_effect,
                    'objective': arena.objective,
                    'hazard': arena.hazard,
                    'story_text': arena.story_text,
                    'flavor_text': arena.flavor_text,
                    'background_music': arena.background_music,
                    'ambient_sounds': arena.ambient_sounds,
                    'special_rules': arena.special_rules,
                    'difficulty_rating': arena.difficulty_rating,
                    'created_at': arena.created_at.isoformat(),
                    'console_count': console_count,
                    'matches_24h': matches_24h,
                    'status': 'active' if console_count > 0 else 'inactive'
                }
                
                arena_list.append(arena_data)
            
            return jsonify({
                'arenas': arena_list,
                'total': len(arena_list)
            })
            
    except Exception as e:
        logger.error(f"Error getting arenas: {e}")
        return jsonify({'error': 'Failed to retrieve arenas'}), 500

@admin_arenas_bp.route('/stats', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_arena_stats():
    """Get arena usage statistics"""
    try:
        with SessionLocal() as session:
            # Get match count in last 24 hours
            yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
            matches_24h = session.query(Match).filter(
                Match.created_at >= yesterday
            ).count()
            
            return jsonify({
                'matches_24h': matches_24h
            })
            
    except Exception as e:
        logger.error(f"Error getting arena stats: {e}")
        return jsonify({'error': 'Failed to retrieve arena statistics'}), 500

@admin_arenas_bp.route('/<int:arena_id>', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_arena_detail(arena_id):
    """Get detailed information about a specific arena"""
    try:
        with SessionLocal() as session:
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            # Get assigned consoles
            assigned_consoles = session.query(Console).filter(
                Console.current_arena_id == arena_id,
                Console.status == ConsoleStatus.active
            ).all()
            
            # Get recent matches
            recent_matches = session.query(Match).filter(
                Match.arena_id == arena_id
            ).order_by(desc(Match.created_at)).limit(10).all()
            
            arena_data = {
                'id': arena.id,
                'name': arena.name,
                'mana_color': arena.mana_color,
                'passive_effect': arena.passive_effect,
                'objective': arena.objective,
                'hazard': arena.hazard,
                'story_text': arena.story_text,
                'flavor_text': arena.flavor_text,
                'background_music': arena.background_music,
                'ambient_sounds': arena.ambient_sounds,
                'special_rules': arena.special_rules,
                'difficulty_rating': arena.difficulty_rating,
                'created_at': arena.created_at.isoformat(),
                'assigned_consoles': [
                    {
                        'id': console.id,
                        'device_uid': console.device_uid,
                        'status': console.status.value,
                        'registered_at': console.registered_at.isoformat()
                    }
                    for console in assigned_consoles
                ],
                'recent_matches': [
                    {
                        'id': match.id,
                        'status': match.status.value,
                        'created_at': match.created_at.isoformat(),
                        'ended_at': match.ended_at.isoformat() if match.ended_at else None
                    }
                    for match in recent_matches
                ]
            }
            
            return jsonify(arena_data)
            
    except Exception as e:
        logger.error(f"Error getting arena detail: {e}")
        return jsonify({'error': 'Failed to retrieve arena details'}), 500

@admin_arenas_bp.route('/<int:arena_id>/consoles', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_arena_consoles(arena_id):
    """Get consoles assigned to specific arena"""
    try:
        with SessionLocal() as session:
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            consoles = session.query(Console).filter(
                Console.current_arena_id == arena_id,
                Console.status == ConsoleStatus.active
            ).all()
            
            console_list = []
            for console in consoles:
                console_data = {
                    'id': console.id,
                    'device_uid': console.device_uid,
                    'status': console.status.value,
                    'registered_at': console.registered_at.isoformat(),
                    'owner_player_id': console.owner_player_id
                }
                console_list.append(console_data)
            
            return jsonify({
                'consoles': console_list,
                'arena_name': arena.name,
                'total': len(console_list)
            })
            
    except Exception as e:
        logger.error(f"Error getting arena consoles: {e}")
        return jsonify({'error': 'Failed to retrieve arena consoles'}), 500

@admin_arenas_bp.route('/<int:arena_id>/matches', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_arena_matches(arena_id):
    """Get matches played in specific arena"""
    try:
        limit = int(request.args.get('limit', 20))
        
        with SessionLocal() as session:
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            matches = session.query(Match).filter(
                Match.arena_id == arena_id
            ).order_by(desc(Match.created_at)).limit(limit).all()
            
            match_list = []
            for match in matches:
                match_data = {
                    'id': match.id,
                    'status': match.status.value,
                    'created_at': match.created_at.isoformat(),
                    'ended_at': match.ended_at.isoformat() if match.ended_at else None,
                    'winner_team': match.winner_team,
                    'duration_minutes': int((match.ended_at - match.created_at).total_seconds() / 60) if match.ended_at else None
                }
                match_list.append(match_data)
            
            return jsonify({
                'matches': match_list,
                'arena_name': arena.name,
                'total': len(match_list)
            })
            
    except Exception as e:
        logger.error(f"Error getting arena matches: {e}")
        return jsonify({'error': 'Failed to retrieve arena matches'}), 500

@admin_arenas_bp.route('/<int:arena_id>/assign-console', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def assign_console_to_arena(arena_id):
    """Assign a console to an arena"""
    try:
        data = request.get_json()
        device_uid = data.get('device_uid')
        
        if not device_uid:
            return jsonify({'error': 'Device UID required'}), 400
        
        with SessionLocal() as session:
            # Check if arena exists
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            # Check if console exists
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Assign arena to console
            console.current_arena_id = arena_id
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} assigned to arena {arena.name}'
            })
            
    except Exception as e:
        logger.error(f"Error assigning console to arena: {e}")
        return jsonify({'error': 'Failed to assign console to arena'}), 500

@admin_arenas_bp.route('/<int:arena_id>/unassign-console', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def unassign_console_from_arena(arena_id):
    """Remove console assignment from arena"""
    try:
        data = request.get_json()
        device_uid = data.get('device_uid')
        
        if not device_uid:
            return jsonify({'error': 'Device UID required'}), 400
        
        with SessionLocal() as session:
            # Check if console exists and is assigned to this arena
            console = session.query(Console).filter(
                Console.device_uid == device_uid,
                Console.current_arena_id == arena_id
            ).first()
            
            if not console:
                return jsonify({'error': 'Console not found or not assigned to this arena'}), 404
            
            # Remove arena assignment
            console.current_arena_id = None
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} unassigned from arena'
            })
            
    except Exception as e:
        logger.error(f"Error unassigning console from arena: {e}")
        return jsonify({'error': 'Failed to unassign console from arena'}), 500

@admin_arenas_bp.route('/<int:arena_id>/activate', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def activate_arena(arena_id):
    """Activate an arena for use"""
    try:
        with SessionLocal() as session:
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            # For now, we'll just return success since we don't have an active/inactive status field
            # In a full implementation, you might add an 'active' boolean field to the Arena model
            
            return jsonify({
                'success': True,
                'message': f'Arena {arena.name} activated'
            })
            
    except Exception as e:
        logger.error(f"Error activating arena: {e}")
        return jsonify({'error': 'Failed to activate arena'}), 500

@admin_arenas_bp.route('/<int:arena_id>/deactivate', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def deactivate_arena(arena_id):
    """Deactivate an arena"""
    try:
        with SessionLocal() as session:
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            # For now, we'll just return success since we don't have an active/inactive status field
            # In a full implementation, you might add an 'active' boolean field to the Arena model
            
            return jsonify({
                'success': True,
                'message': f'Arena {arena.name} deactivated'
            })
            
    except Exception as e:
        logger.error(f"Error deactivating arena: {e}")
        return jsonify({'error': 'Failed to deactivate arena'}), 500
