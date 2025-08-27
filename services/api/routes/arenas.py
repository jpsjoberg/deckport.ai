"""
Arena management routes - Basic arena system
"""

from flask import Blueprint, request, jsonify
from shared.database.connection import SessionLocal
from shared.models.arena import Arena

arenas_bp = Blueprint('arenas', __name__, url_prefix='/v1/arenas')

@arenas_bp.route('/list', methods=['GET'])
def get_arena_list():
    """Get list of available arenas"""
    try:
        with SessionLocal() as session:
            arenas = session.query(Arena).all()
            
            arena_list = []
            for arena in arenas:
                arena_data = {
                    "id": arena.id,
                    "name": arena.name,
                    "mana_color": arena.mana_color,
                    "difficulty": arena.difficulty_rating,
                    "story_text": arena.story_text,
                    "flavor_text": arena.flavor_text
                }
                arena_list.append(arena_data)
            
            return jsonify({
                "arenas": arena_list,
                "total": len(arena_list)
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to fetch arena list"}), 500

@arenas_bp.route('/random', methods=['GET'])
def get_random_arena():
    """Get a random arena"""
    try:
        with SessionLocal() as session:
            from sqlalchemy import func
            arena = session.query(Arena).order_by(func.random()).first()
            
            if not arena:
                return jsonify({"error": "No arenas available"}), 404
            
            arena_data = {
                "id": arena.id,
                "name": arena.name,
                "mana_color": arena.mana_color,
                "difficulty": arena.difficulty_rating,
                "story_text": arena.story_text,
                "flavor_text": arena.flavor_text
            }
            
            return jsonify(arena_data)
            
    except Exception as e:
        return jsonify({"error": "Failed to get random arena"}), 500

@arenas_bp.route('/weighted', methods=['POST'])
def get_weighted_arena():
    """Get arena based on player preferences"""
    try:
        with SessionLocal() as session:
            # For now, just return a random arena
            from sqlalchemy import func
            arena = session.query(Arena).order_by(func.random()).first()
            
            if not arena:
                return jsonify({"error": "No arenas available"}), 404
            
            arena_data = {
                "id": arena.id,
                "name": arena.name,
                "mana_color": arena.mana_color,
                "difficulty": arena.difficulty_rating,
                "story_text": arena.story_text,
                "flavor_text": arena.flavor_text,
                "selection_reason": "random"
            }
            
            return jsonify(arena_data)
            
    except Exception as e:
        return jsonify({"error": "Failed to get weighted arena"}), 500