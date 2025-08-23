"""
Gameplay API Routes
Handles match creation, game actions, and state management
"""

from flask import Blueprint, request, jsonify, g
from typing import Optional
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Match, MatchParticipant, MatchStatus, MMQueue, Player
from shared.auth.decorators import admin_required
from shared.utils.logging import setup_logging
from game_engine.match_manager import MatchManager
from matchmaking.queue_manager import QueueManager

logger = setup_logging("gameplay_api", "INFO")

gameplay_bp = Blueprint('gameplay', __name__, url_prefix='/v1/gameplay')

# Global instances
match_manager = MatchManager()
queue_manager = QueueManager(match_manager)

# Start queue manager
import asyncio
try:
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        loop.run_until_complete(queue_manager.start())
except:
    # If no loop is running, start will be called later
    pass

@gameplay_bp.route('/matches', methods=['POST'])
def create_match():
    """Create a new match (admin/testing)"""
    data = request.get_json() or {}
    
    try:
        with SessionLocal() as session:
            # Create match
            match = Match(
                mode=data.get('mode', '1v1'),
                status=MatchStatus.queued
            )
            session.add(match)
            session.flush()
            
            # Add participants
            players = data.get('players', [])
            for i, player_data in enumerate(players):
                participant = MatchParticipant(
                    match_id=match.id,
                    player_id=player_data.get('player_id'),
                    console_id=None,  # Set to None since we don't have real console IDs
                    team=i
                )
                session.add(participant)
            
            session.commit()
            
            return jsonify({
                "success": True,
                "match_id": match.id,
                "status": match.status.value
            })
            
    except Exception as e:
        logger.error(f"Error creating match: {e}")
        return jsonify({"error": "Failed to create match"}), 500

@gameplay_bp.route('/matches/<int:match_id>/start', methods=['POST'])
def start_match(match_id: int):
    """Start a match"""
    try:
        # Start match using match manager
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        game_state = loop.run_until_complete(
            match_manager.start_match(match_id)
        )
        
        if not game_state:
            return jsonify({"error": "Failed to start match"}), 400
        
        return jsonify({
            "success": True,
            "match_id": match_id,
            "game_state": game_state.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error starting match {match_id}: {e}")
        return jsonify({"error": "Failed to start match"}), 500

@gameplay_bp.route('/matches/<int:match_id>/state', methods=['GET'])
def get_match_state(match_id: int):
    """Get current match state"""
    try:
        player_team = request.args.get('team', type=int)
        
        if player_team is not None:
            # Get player-specific view
            player_view = match_manager.get_player_view(str(match_id), player_team)
            if not player_view:
                return jsonify({"error": "Match not found"}), 404
            
            return jsonify(player_view)
        else:
            # Get full state (admin view)
            game_state = match_manager.get_match_state(str(match_id))
            if not game_state:
                return jsonify({"error": "Match not found"}), 404
            
            return jsonify(game_state.to_dict())
            
    except Exception as e:
        logger.error(f"Error getting match state {match_id}: {e}")
        return jsonify({"error": "Failed to get match state"}), 500

@gameplay_bp.route('/matches/<int:match_id>/play-card', methods=['POST'])
def play_card(match_id: int):
    """Play a card in a match"""
    data = request.get_json() or {}
    
    try:
        player_team = data.get('player_team')
        card_id = data.get('card_id')
        action = data.get('action', 'play')
        target = data.get('target')
        
        if player_team is None or not card_id:
            return jsonify({"error": "player_team and card_id required"}), 400
        
        # Play card using match manager
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            match_manager.play_card(str(match_id), player_team, card_id, action, target)
        )
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error playing card in match {match_id}: {e}")
        return jsonify({"error": "Failed to play card"}), 500

@gameplay_bp.route('/matches/<int:match_id>/advance-phase', methods=['POST'])
@admin_required
def force_advance_phase(match_id: int):
    """Force advance to next phase (admin/debug)"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            match_manager.force_advance_phase(str(match_id))
        )
        
        if not success:
            return jsonify({"error": "Failed to advance phase"}), 400
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Error advancing phase for match {match_id}: {e}")
        return jsonify({"error": "Failed to advance phase"}), 500

@gameplay_bp.route('/matches/<int:match_id>/end', methods=['POST'])
@admin_required
def end_match(match_id: int):
    """End a match (admin)"""
    data = request.get_json() or {}
    
    try:
        result = data.get('result', {
            "winner": None,
            "condition": "admin_end",
            "description": "Match ended by admin"
        })
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            match_manager.end_match(str(match_id), result)
        )
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Error ending match {match_id}: {e}")
        return jsonify({"error": "Failed to end match"}), 500

@gameplay_bp.route('/matches/active', methods=['GET'])
def get_active_matches():
    """Get list of active matches"""
    try:
        active_match_ids = match_manager.get_active_matches()
        
        # Get match details from database
        matches = []
        with SessionLocal() as session:
            for match_id in active_match_ids:
                match = session.query(Match).filter(Match.id == int(match_id)).first()
                if match:
                    participants = session.query(MatchParticipant).filter(
                        MatchParticipant.match_id == match.id
                    ).all()
                    
                    matches.append({
                        "id": match.id,
                        "mode": match.mode,
                        "status": match.status.value,
                        "started_at": match.started_at.isoformat() if match.started_at else None,
                        "participants": len(participants),
                        "arena": match.arena.name if match.arena else None
                    })
        
        return jsonify({
            "active_matches": matches,
            "total": len(matches)
        })
        
    except Exception as e:
        logger.error(f"Error getting active matches: {e}")
        return jsonify({"error": "Failed to get active matches"}), 500

@gameplay_bp.route('/queue/join', methods=['POST'])
def join_matchmaking_queue():
    """Join matchmaking queue"""
    data = request.get_json() or {}
    
    try:
        player_id = data.get('player_id')
        console_id = data.get('console_id')
        mode = data.get('mode', '1v1')
        
        if not player_id:
            return jsonify({"error": "player_id required"}), 400
        
        with SessionLocal() as session:
            # Get player ELO
            player = session.query(Player).filter(Player.id == player_id).first()
            if not player:
                return jsonify({"error": "Player not found"}), 404
            
            # Use queue manager to add player
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(
                queue_manager.add_player_to_queue(player_id, None, mode, player.elo_rating)
            )
            
            if not success:
                return jsonify({"error": "Failed to join queue or already in queue"}), 400
            
            # Get queue position
            queue_info = queue_manager.get_player_queue_info(player_id, mode)
            
            return jsonify({
                "success": True,
                "status": "queued",
                "position": queue_info.get("position", 1) if queue_info else 1,
                "elo": player.elo_rating
            })
            
    except Exception as e:
        logger.error(f"Error joining queue: {e}")
        return jsonify({"error": "Failed to join queue"}), 500

@gameplay_bp.route('/queue/leave', methods=['POST'])
def leave_matchmaking_queue():
    """Leave matchmaking queue"""
    data = request.get_json() or {}
    
    try:
        player_id = data.get('player_id')
        mode = data.get('mode', '1v1')
        
        if not player_id:
            return jsonify({"error": "player_id required"}), 400
        
        # Use queue manager to remove player
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            queue_manager.remove_player_from_queue(player_id, mode)
        )
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Not in queue"}), 400
                
    except Exception as e:
        logger.error(f"Error leaving queue: {e}")
        return jsonify({"error": "Failed to leave queue"}), 500

@gameplay_bp.route('/queue/status', methods=['GET'])
def get_queue_status():
    """Get matchmaking queue status"""
    try:
        player_id = request.args.get('player_id', type=int)
        mode = request.args.get('mode', '1v1')
        
        if player_id:
            # Get specific player status
            queue_info = queue_manager.get_player_queue_info(player_id, mode)
            
            if queue_info:
                return jsonify({
                    "in_queue": True,
                    "position": queue_info["position"],
                    "enqueued_at": queue_info["enqueued_at"],
                    "elo": queue_info["elo"],
                    "wait_time_seconds": queue_info["wait_time_seconds"]
                })
            else:
                return jsonify({"in_queue": False})
        else:
            # Get overall queue stats
            queue_stats = queue_manager.get_queue_stats(mode)
            return jsonify(queue_stats)
                
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return jsonify({"error": "Failed to get queue status"}), 500

# Add queue management endpoints for admin
@gameplay_bp.route('/queue/stats', methods=['GET'])
@admin_required
def get_queue_stats():
    """Get detailed queue statistics (admin)"""
    try:
        mode = request.args.get('mode')
        stats = queue_manager.get_queue_stats(mode)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return jsonify({"error": "Failed to get queue stats"}), 500

@gameplay_bp.route('/queue/clear', methods=['POST'])
@admin_required  
def clear_queue():
    """Clear matchmaking queue (admin)"""
    data = request.get_json() or {}
    mode = data.get('mode', '1v1')
    
    try:
        with SessionLocal() as session:
            deleted_count = session.query(MMQueue).filter(MMQueue.mode == mode).delete()
            session.commit()
            
            return jsonify({
                "success": True,
                "cleared_entries": deleted_count
            })
            
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({"error": "Failed to clear queue"}), 500
