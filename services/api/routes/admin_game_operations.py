"""
Admin game operations routes
Handles matchmaking, live matches, tournaments, and game balance
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.base import Player, CardCatalog, AuditLog
from shared.auth.decorators import admin_required
import logging
import random

logger = logging.getLogger(__name__)

admin_game_ops_bp = Blueprint('admin_game_ops', __name__, url_prefix='/v1/admin/game-operations')

@admin_game_ops_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_game_operations_dashboard():
    """Get game operations dashboard data"""
    try:
        with SessionLocal() as session:
            # Get current timestamp
            now = datetime.now(timezone.utc)
            
            # Mock data for now - in real implementation, these would come from actual game tables
            dashboard_data = {
                'live_matches': {
                    'active': random.randint(15, 45),
                    'queued_players': random.randint(8, 25),
                    'avg_wait_time': random.randint(30, 120),
                    'peak_concurrent': random.randint(50, 100)
                },
                'tournaments': {
                    'active': random.randint(2, 5),
                    'scheduled': random.randint(3, 8),
                    'participants_today': random.randint(150, 300),
                    'prize_pool': random.randint(5000, 15000)
                },
                'game_balance': {
                    'cards_monitored': 347,
                    'imbalanced_cards': random.randint(5, 12),
                    'meta_diversity': round(random.uniform(65, 85), 1),
                    'last_balance_hours': random.randint(6, 72)
                },
                'player_activity': {
                    'online_now': random.randint(80, 200),
                    'matches_today': random.randint(500, 1200),
                    'new_players_today': random.randint(15, 45),
                    'retention_rate': round(random.uniform(75, 90), 1)
                }
            }
            
            return jsonify(dashboard_data)
            
    except Exception as e:
        logger.error(f"Error getting game operations dashboard: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard data'}), 500

@admin_game_ops_bp.route('/matches/live', methods=['GET'])
@admin_required
def get_live_matches():
    """Get currently active matches"""
    try:
        # Mock live matches data
        live_matches = []
        for i in range(random.randint(10, 30)):
            match_id = f"match_{random.randint(10000, 99999)}"
            live_matches.append({
                'match_id': match_id,
                'mode': random.choice(['1v1', 'tournament', 'casual']),
                'players': [
                    {
                        'id': random.randint(1, 1000),
                        'display_name': random.choice(['DragonMaster', 'CardWizard', 'FireStorm', 'IceQueen', 'ShadowBlade']),
                        'rating': random.randint(800, 2200),
                        'console_id': f"DECK_{random.choice(['NYC', 'LA', 'CHI', 'SF'])}_{random.randint(1, 20):02d}"
                    },
                    {
                        'id': random.randint(1, 1000),
                        'display_name': random.choice(['LightBringer', 'DarkMage', 'StormCaller', 'EarthShaker', 'VoidWalker']),
                        'rating': random.randint(800, 2200),
                        'console_id': f"DECK_{random.choice(['NYC', 'LA', 'CHI', 'SF'])}_{random.randint(1, 20):02d}"
                    }
                ],
                'started_at': (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 45))).isoformat(),
                'duration_minutes': random.randint(1, 45),
                'phase': random.choice(['setup', 'main', 'combat', 'ending']),
                'turn': random.randint(1, 20),
                'status': 'active',
                'spectators': random.randint(0, 15)
            })
        
        return jsonify({
            'matches': live_matches,
            'total': len(live_matches)
        })
        
    except Exception as e:
        logger.error(f"Error getting live matches: {e}")
        return jsonify({'error': 'Failed to retrieve live matches'}), 500

@admin_game_ops_bp.route('/matches/<match_id>', methods=['GET'])
@admin_required
def get_match_details(match_id):
    """Get detailed information about a specific match"""
    try:
        # Mock match details
        match_details = {
            'match_id': match_id,
            'mode': '1v1',
            'status': 'active',
            'created_at': (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            'started_at': (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
            'duration_minutes': 25,
            'phase': 'main',
            'turn': 12,
            'players': [
                {
                    'id': 123,
                    'display_name': 'DragonMaster',
                    'rating': 1850,
                    'console_id': 'DECK_NYC_01',
                    'cards_played': 8,
                    'life_points': 15,
                    'mana': 7,
                    'hand_size': 4,
                    'deck_size': 32,
                    'graveyard_size': 8
                },
                {
                    'id': 456,
                    'display_name': 'IceQueen',
                    'rating': 1920,
                    'console_id': 'DECK_LA_03',
                    'cards_played': 7,
                    'life_points': 12,
                    'mana': 6,
                    'hand_size': 5,
                    'deck_size': 35,
                    'graveyard_size': 7
                }
            ],
            'game_state': {
                'battlefield': [
                    {'card': 'Crimson Dragon', 'owner': 123, 'attack': 8, 'defense': 6},
                    {'card': 'Ice Elemental', 'owner': 456, 'attack': 4, 'defense': 8},
                    {'card': 'Lightning Bolt', 'owner': 123, 'type': 'spell', 'target': 'Ice Elemental'}
                ],
                'recent_actions': [
                    {'turn': 12, 'player': 123, 'action': 'cast', 'card': 'Lightning Bolt', 'target': 'Ice Elemental'},
                    {'turn': 11, 'player': 456, 'action': 'summon', 'card': 'Ice Elemental'},
                    {'turn': 10, 'player': 123, 'action': 'attack', 'attacker': 'Crimson Dragon', 'target': 'player'}
                ]
            },
            'spectators': random.randint(0, 15),
            'tournament_id': None
        }
        
        return jsonify(match_details)
        
    except Exception as e:
        logger.error(f"Error getting match details: {e}")
        return jsonify({'error': 'Failed to retrieve match details'}), 500

@admin_game_ops_bp.route('/matches/<match_id>/terminate', methods=['POST'])
@admin_required
def terminate_match(match_id):
    """Terminate a match (admin intervention)"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Admin intervention')
        
        # Log the termination
        with SessionLocal() as session:
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="match_terminated",
                details=f"Match {match_id} terminated by admin: {reason}",
                meta={'match_id': match_id, 'reason': reason}
            )
            session.add(audit_log)
            session.commit()
        
        # TODO: Implement actual match termination logic
        return jsonify({
            'success': True,
            'message': f'Match {match_id} has been terminated',
            'reason': reason
        })
        
    except Exception as e:
        logger.error(f"Error terminating match: {e}")
        return jsonify({'error': 'Failed to terminate match'}), 500

@admin_game_ops_bp.route('/matchmaking/queue', methods=['GET'])
@admin_required
def get_matchmaking_queue():
    """Get current matchmaking queue status"""
    try:
        # Mock queue data
        queue_data = {
            'total_queued': random.randint(5, 25),
            'by_mode': {
                '1v1': random.randint(3, 15),
                'tournament': random.randint(0, 5),
                'casual': random.randint(2, 8)
            },
            'avg_wait_time': random.randint(30, 120),
            'longest_wait': random.randint(180, 600),
            'matches_created_hour': random.randint(15, 45),
            'queue_entries': []
        }
        
        # Generate mock queue entries
        for i in range(queue_data['total_queued']):
            queue_data['queue_entries'].append({
                'player_id': random.randint(1, 1000),
                'display_name': random.choice(['PlayerOne', 'GameMaster', 'CardShark', 'ProGamer', 'Challenger']),
                'rating': random.randint(800, 2200),
                'mode': random.choice(['1v1', 'tournament', 'casual']),
                'wait_time_seconds': random.randint(10, 300),
                'console_id': f"DECK_{random.choice(['NYC', 'LA', 'CHI', 'SF'])}_{random.randint(1, 20):02d}",
                'queued_at': (datetime.now(timezone.utc) - timedelta(seconds=random.randint(10, 300))).isoformat()
            })
        
        return jsonify(queue_data)
        
    except Exception as e:
        logger.error(f"Error getting matchmaking queue: {e}")
        return jsonify({'error': 'Failed to retrieve queue data'}), 500

@admin_game_ops_bp.route('/tournaments', methods=['GET'])
@admin_required
def get_tournaments():
    """Get tournament information"""
    try:
        # Mock tournament data
        tournaments = []
        
        # Active tournaments
        for i in range(random.randint(1, 3)):
            tournaments.append({
                'id': f"tournament_{random.randint(1000, 9999)}",
                'name': f"Weekly Championship #{random.randint(1, 52)}",
                'status': 'active',
                'format': '1v1',
                'participants': random.randint(16, 64),
                'max_participants': 64,
                'prize_pool': random.randint(1000, 5000),
                'started_at': (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 6))).isoformat(),
                'estimated_end': (datetime.now(timezone.utc) + timedelta(hours=random.randint(2, 8))).isoformat(),
                'current_round': random.randint(1, 6),
                'total_rounds': 6,
                'matches_active': random.randint(2, 8),
                'matches_completed': random.randint(10, 30)
            })
        
        # Scheduled tournaments
        for i in range(random.randint(2, 5)):
            start_time = datetime.now(timezone.utc) + timedelta(hours=random.randint(6, 72))
            tournaments.append({
                'id': f"tournament_{random.randint(1000, 9999)}",
                'name': f"Daily Tournament #{random.randint(1, 365)}",
                'status': 'scheduled',
                'format': '1v1',
                'participants': random.randint(8, 32),
                'max_participants': 32,
                'prize_pool': random.randint(500, 2000),
                'scheduled_start': start_time.isoformat(),
                'registration_deadline': (start_time - timedelta(hours=1)).isoformat(),
                'estimated_duration': random.randint(2, 6),
                'entry_fee': random.randint(0, 100)
            })
        
        return jsonify({
            'tournaments': tournaments,
            'total': len(tournaments)
        })
        
    except Exception as e:
        logger.error(f"Error getting tournaments: {e}")
        return jsonify({'error': 'Failed to retrieve tournaments'}), 500

@admin_game_ops_bp.route('/balance/cards', methods=['GET'])
@admin_required
def get_card_balance_data():
    """Get card balance analysis data"""
    try:
        with SessionLocal() as session:
            # Get all cards from catalog
            cards = session.query(CardCatalog).all()
            
            balance_data = []
            for card in cards:
                # Mock balance statistics
                win_rate = random.uniform(35, 75)
                usage_rate = random.uniform(5, 95)
                
                # Determine balance status
                if win_rate > 60 and usage_rate > 70:
                    status = 'overpowered'
                    priority = 'high'
                elif win_rate < 40 and usage_rate < 20:
                    status = 'underpowered'
                    priority = 'medium'
                elif win_rate > 55 and usage_rate > 80:
                    status = 'popular'
                    priority = 'low'
                else:
                    status = 'balanced'
                    priority = 'none'
                
                balance_data.append({
                    'product_sku': card.product_sku,
                    'name': card.name,
                    'rarity': card.rarity.value,
                    'color': card.color.value if card.color else 'colorless',
                    'category': card.category.value if card.category else 'unknown',
                    'base_attack': card.base_attack,
                    'base_defense': card.base_defense,
                    'mana_cost': card.mana_cost,
                    'win_rate': round(win_rate, 1),
                    'usage_rate': round(usage_rate, 1),
                    'games_played': random.randint(50, 5000),
                    'status': status,
                    'priority': priority,
                    'last_changed': (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat()
                })
            
            # Sort by priority and win rate
            priority_order = {'high': 3, 'medium': 2, 'low': 1, 'none': 0}
            balance_data.sort(key=lambda x: (priority_order[x['priority']], x['win_rate']), reverse=True)
            
            return jsonify({
                'cards': balance_data,
                'total': len(balance_data),
                'summary': {
                    'total_cards': len(balance_data),
                    'overpowered': len([c for c in balance_data if c['status'] == 'overpowered']),
                    'underpowered': len([c for c in balance_data if c['status'] == 'underpowered']),
                    'balanced': len([c for c in balance_data if c['status'] == 'balanced']),
                    'meta_diversity': round(random.uniform(65, 85), 1)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting card balance data: {e}")
        return jsonify({'error': 'Failed to retrieve balance data'}), 500

@admin_game_ops_bp.route('/balance/cards/<product_sku>', methods=['POST'])
@admin_required
def update_card_balance(product_sku):
    """Update card balance (stats modification)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with SessionLocal() as session:
            card = session.query(CardCatalog).filter(CardCatalog.product_sku == product_sku).first()
            
            if not card:
                return jsonify({'error': 'Card not found'}), 404
            
            changes = []
            
            # Update stats if provided
            if 'base_attack' in data:
                old_attack = card.base_attack
                card.base_attack = data['base_attack']
                changes.append(f"Attack: {old_attack} → {card.base_attack}")
            
            if 'base_defense' in data:
                old_defense = card.base_defense
                card.base_defense = data['base_defense']
                changes.append(f"Defense: {old_defense} → {card.base_defense}")
            
            if 'mana_cost' in data:
                old_cost = card.mana_cost
                card.mana_cost = data['mana_cost']
                changes.append(f"Mana Cost: {old_cost} → {card.mana_cost}")
            
            session.commit()
            
            # Log the balance change
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="card_balance_update",
                details=f"Card {card.name} balanced: {', '.join(changes)}",
                meta={
                    'product_sku': product_sku,
                    'changes': changes,
                    'reason': data.get('reason', 'Balance adjustment')
                }
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Card {card.name} has been updated',
                'changes': changes
            })
            
    except Exception as e:
        logger.error(f"Error updating card balance: {e}")
        return jsonify({'error': 'Failed to update card balance'}), 500

@admin_game_ops_bp.route('/analytics/player-activity', methods=['GET'])
@admin_required
def get_player_activity_analytics():
    """Get player activity analytics"""
    try:
        days = int(request.args.get('days', 7))
        
        # Mock analytics data
        analytics = {
            'period_days': days,
            'total_players': random.randint(500, 2000),
            'active_players': random.randint(200, 800),
            'new_players': random.randint(20, 100),
            'retention_rate': round(random.uniform(70, 90), 1),
            'avg_session_duration': random.randint(15, 45),
            'daily_activity': [],
            'hourly_distribution': [],
            'top_players': []
        }
        
        # Generate daily activity data
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            analytics['daily_activity'].append({
                'date': date.strftime('%Y-%m-%d'),
                'active_players': random.randint(50, 200),
                'matches_played': random.randint(100, 500),
                'new_registrations': random.randint(5, 25),
                'avg_session_minutes': random.randint(20, 60)
            })
        
        # Generate hourly distribution
        for hour in range(24):
            analytics['hourly_distribution'].append({
                'hour': hour,
                'active_players': random.randint(10, 100),
                'matches': random.randint(20, 150)
            })
        
        # Generate top players
        for i in range(10):
            analytics['top_players'].append({
                'rank': i + 1,
                'player_id': random.randint(1, 1000),
                'display_name': f"Player{random.randint(1, 1000)}",
                'rating': random.randint(1500, 2500),
                'matches_played': random.randint(50, 200),
                'win_rate': round(random.uniform(45, 85), 1)
            })
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting player activity analytics: {e}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500

@admin_game_ops_bp.route('/system/maintenance', methods=['POST'])
@admin_required
def trigger_maintenance():
    """Trigger system maintenance mode"""
    try:
        data = request.get_json() or {}
        maintenance_type = data.get('type', 'scheduled')
        duration_minutes = data.get('duration_minutes', 30)
        message = data.get('message', 'System maintenance in progress')
        
        # Log maintenance trigger
        with SessionLocal() as session:
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="maintenance_triggered",
                details=f"System maintenance triggered: {maintenance_type} for {duration_minutes} minutes",
                meta={
                    'type': maintenance_type,
                    'duration_minutes': duration_minutes,
                    'message': message
                }
            )
            session.add(audit_log)
            session.commit()
        
        # TODO: Implement actual maintenance mode logic
        return jsonify({
            'success': True,
            'message': 'Maintenance mode activated',
            'type': maintenance_type,
            'duration_minutes': duration_minutes,
            'estimated_end': (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error triggering maintenance: {e}")
        return jsonify({'error': 'Failed to trigger maintenance'}), 500
