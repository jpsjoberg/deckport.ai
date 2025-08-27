"""
Admin game operations routes
Handles matchmaking, live matches, tournaments, and game balance
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.base import Player, CardCatalog, AuditLog, Match, MMQueue
from shared.models.tournaments import Tournament, TournamentParticipant, TournamentStatus
from shared.auth.auto_rbac_decorator import auto_rbac_required, system_admin_required
from shared.auth.admin_roles import Permission
import logging
from shared.auth.admin_context import log_admin_action, get_current_admin_id

logger = logging.getLogger(__name__)

admin_game_ops_bp = Blueprint('admin_game_ops', __name__, url_prefix='/v1/admin/game-operations')

@admin_game_ops_bp.route('/dashboard', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_game_operations_dashboard():
    """Get game operations dashboard data"""
    try:
        with SessionLocal() as session:
            # Get current timestamp
            now = datetime.now(timezone.utc)
            
            # Get real data from database
            
            # Live matches data
            active_matches = session.query(Match).filter(Match.status == 'active').count()
            queued_players = session.query(MMQueue).count()
            
            # Tournament data
            active_tournaments = session.query(Tournament).filter(
                Tournament.status == TournamentStatus.active
            ).count()
            scheduled_tournaments = session.query(Tournament).filter(
                Tournament.status == TournamentStatus.scheduled
            ).count()
            
            # Get today's participants
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            participants_today = session.query(TournamentParticipant).filter(
                TournamentParticipant.joined_at >= today_start
            ).count()
            
            # Calculate total prize pool for active tournaments
            total_prize_pool = session.query(func.sum(Tournament.prize_pool)).filter(
                Tournament.status == TournamentStatus.active
            ).scalar() or 0
            
            # Card balance data
            total_cards = session.query(CardCatalog).count()
            
            # Player activity data
            # Count players who have been active in the last 30 minutes (approximate online count)
            online_threshold = now - timedelta(minutes=30)
            
            # Get matches today
            matches_today = session.query(Match).filter(
                Match.created_at >= today_start
            ).count()
            
            # Get new players today
            new_players_today = session.query(Player).filter(
                Player.created_at >= today_start
            ).count()
            
            dashboard_data = {
                'live_matches': {
                    'active': active_matches,
                    'queued_players': queued_players,
                    'avg_wait_time': 45,  # Could be calculated from historical data
                    'peak_concurrent': active_matches + 20  # Approximation
                },
                'tournaments': {
                    'active': active_tournaments,
                    'scheduled': scheduled_tournaments,
                    'participants_today': participants_today,
                    'prize_pool': int(total_prize_pool)
                },
                'game_balance': {
                    'cards_monitored': total_cards,
                    'imbalanced_cards': 0,  # Would need balance analysis logic
                    'meta_diversity': 78.5,  # Would need meta analysis
                    'last_balance_hours': 24  # Could track from audit logs
                },
                'player_activity': {
                    'online_now': queued_players + active_matches * 2,  # Approximation
                    'matches_today': matches_today,
                    'new_players_today': new_players_today,
                    'retention_rate': 85.0  # Would need retention analysis
                }
            }
            
            return jsonify(dashboard_data)
            
    except Exception as e:
        logger.error(f"Error getting game operations dashboard: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard data'}), 500

@admin_game_ops_bp.route('/matches/live', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_MATCHES])
def get_live_matches():
    """Get currently active matches"""
    try:
        with SessionLocal() as session:
            # Get real active matches from database
            matches = session.query(Match).filter(
                Match.status == 'active'
            ).order_by(desc(Match.created_at)).limit(50).all()
            
            live_matches = []
            for match in matches:
                # Calculate duration
                duration_minutes = int((datetime.now(timezone.utc) - match.created_at).total_seconds() / 60)
                
                match_data = {
                    'match_id': f"match_{match.id}",
                    'mode': match.match_type or '1v1',
                    'players': [
                        {
                            'id': match.player1_id,
                            'display_name': match.player1.display_name if match.player1 else f'Player {match.player1_id}',
                            'rating': getattr(match.player1, 'rating', 1200) if match.player1 else 1200,
                            'console_id': match.console_id or 'Unknown'
                        },
                        {
                            'id': match.player2_id,
                            'display_name': match.player2.display_name if match.player2 else f'Player {match.player2_id}',
                            'rating': getattr(match.player2, 'rating', 1200) if match.player2 else 1200,
                            'console_id': match.console_id or 'Unknown'
                        }
                    ],
                    'started_at': match.created_at.isoformat(),
                    'duration_minutes': duration_minutes,
                    'phase': match.current_phase or 'main',
                    'turn': match.current_turn or 1,
                    'status': match.status,
                    'spectators': 0  # Would need spectator tracking
                }
                live_matches.append(match_data)
        
        return jsonify({
            'matches': live_matches,
            'total': len(live_matches)
        })
        
    except Exception as e:
        logger.error(f"Error getting live matches: {e}")
        return jsonify({'error': 'Failed to retrieve live matches'}), 500

@admin_game_ops_bp.route('/matches/<match_id>', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_MATCHES])
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
@auto_rbac_required(override_permissions=[Permission.GAME_MATCHES])
def terminate_match(match_id):
    """Terminate a match (admin intervention)"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Admin intervention')
        
        # Log the termination
        with SessionLocal() as session:
            log_admin_action(session, "match_terminated", f"Match {match_id} terminated by admin: {reason}", {'match_id': match_id, 'reason': reason}
            )
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
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_matchmaking_queue():
    """Get current matchmaking queue status"""
    try:
        with SessionLocal() as session:
            # Get real queue data from database
            queue_entries = session.query(MMQueue).all()
            
            # Count by mode (if mode field exists, otherwise default to '1v1')
            by_mode = {'1v1': 0, 'tournament': 0, 'casual': 0}
            queue_list = []
            total_wait_time = 0
            longest_wait = 0
            
            now = datetime.now(timezone.utc)
            
            for entry in queue_entries:
                # Calculate wait time
                wait_seconds = int((now - entry.created_at).total_seconds())
                total_wait_time += wait_seconds
                longest_wait = max(longest_wait, wait_seconds)
                
                # Determine mode (default to 1v1 if not specified)
                mode = getattr(entry, 'mode', '1v1')
                if mode in by_mode:
                    by_mode[mode] += 1
                else:
                    by_mode['1v1'] += 1
                
                queue_list.append({
                    'player_id': entry.player_id,
                    'display_name': entry.player.display_name if entry.player else f'Player {entry.player_id}',
                    'rating': getattr(entry.player, 'rating', 1200) if entry.player else 1200,
                    'mode': mode,
                    'wait_time_seconds': wait_seconds,
                    'console_id': 'Unknown',  # Would need console tracking
                    'queued_at': entry.created_at.isoformat()
                })
            
            # Calculate average wait time
            avg_wait_time = int(total_wait_time / len(queue_entries)) if queue_entries else 0
            
            # Get matches created in the last hour
            hour_ago = now - timedelta(hours=1)
            matches_created_hour = session.query(Match).filter(
                Match.created_at >= hour_ago
            ).count()
            
            queue_data = {
                'total_queued': len(queue_entries),
                'by_mode': by_mode,
                'avg_wait_time': avg_wait_time,
                'longest_wait': longest_wait,
                'matches_created_hour': matches_created_hour,
                'queue_entries': queue_list
            }
        
        return jsonify(queue_data)
        
    except Exception as e:
        logger.error(f"Error getting matchmaking queue: {e}")
        return jsonify({'error': 'Failed to retrieve queue data'}), 500

@admin_game_ops_bp.route('/tournaments', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])
def get_tournaments():
    """Get tournament information with real data"""
    try:
        with SessionLocal() as session:
            # Get all tournaments
            tournaments = session.query(Tournament).order_by(desc(Tournament.created_at)).all()
            
            tournament_list = []
            for tournament in tournaments:
                # Count participants
                participant_count = len(tournament.participants)
                active_participants = len([p for p in tournament.participants if p.is_active])
                
                # Count matches
                total_matches = len(tournament.matches)
                completed_matches = len([m for m in tournament.matches if m.status == 'completed'])
                active_matches = len([m for m in tournament.matches if m.status == 'active'])
                
                tournament_data = {
                    'id': tournament.id,
                    'name': tournament.name,
                    'status': tournament.status.value,
                    'format': tournament.format.value,
                    'participants': participant_count,
                    'max_participants': tournament.max_participants,
                    'prize_pool': float(tournament.prize_pool),
                    'entry_fee': float(tournament.entry_fee),
                    'fee_type': tournament.fee_type.value,
                    'house_percentage': float(tournament.house_percentage),
                    'current_round': tournament.current_round,
                    'total_rounds': tournament.total_rounds,
                    'matches_active': active_matches,
                    'matches_completed': completed_matches,
                    'started_at': tournament.start_time.isoformat(),
                    'registration_deadline': tournament.registration_end.isoformat() if tournament.registration_end else None,
                    'estimated_end': tournament.end_time.isoformat() if tournament.end_time else None,
                    'auto_start_when_full': tournament.auto_start_when_full,
                    'public_registration': tournament.public_registration
                }
                tournament_list.append(tournament_data)
            
            return jsonify({
                'tournaments': tournament_list,
                'total': len(tournament_list)
            })
        
    except Exception as e:
        logger.error(f"Error getting tournaments: {e}")
        return jsonify({'error': 'Failed to retrieve tournaments'}), 500

@admin_game_ops_bp.route('/balance/cards', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_BALANCE])
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
@auto_rbac_required(override_permissions=[Permission.GAME_BALANCE])
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
                actor_id=get_current_admin_id() or 1,
                action="card_balance_update",
                details=f"Card {card.name} balanced: {', '.join(changes)}",
                meta={
                    'product_sku': product_sku,
                    'changes': changes,
                    'reason': data.get('reason', 'Balance adjustment')
                }
            )
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
@auto_rbac_required(override_permissions=[Permission.ANALYTICS_PLAYERS])
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
@system_admin_required(Permission.SYSTEM_MAINTENANCE)
def trigger_maintenance():
    """Trigger system maintenance mode"""
    try:
        data = request.get_json() or {}
        maintenance_type = data.get('type', 'scheduled')
        duration_minutes = data.get('duration_minutes', 30)
        message = data.get('message', 'System maintenance in progress')
        
        # Log maintenance trigger
        with SessionLocal() as session:
            log_admin_action(session, "maintenance_triggered", f"System maintenance triggered: {maintenance_type} for {duration_minutes} minutes", {
                    'type': maintenance_type,
                    'duration_minutes': duration_minutes,
                    'message': message
                }
            )
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


@admin_game_ops_bp.route('/matches', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])
def get_active_matches():
    """Get currently active matches"""
    try:
        with SessionLocal() as session:
            # Get active matches
            active_matches = session.query(Match).filter(
                Match.status == 'active'
            ).order_by(desc(Match.started_at)).all()
            
            matches = []
            for match in active_matches:
                # Get player information
                player1 = session.query(Player).filter(Player.id == match.player1_id).first()
                player2 = session.query(Player).filter(Player.id == match.player2_id).first()
                
                # Calculate match duration
                duration_minutes = 0
                if match.started_at:
                    duration = datetime.now(timezone.utc) - match.started_at
                    duration_minutes = int(duration.total_seconds() / 60)
                
                match_data = {
                    'id': match.id,
                    'match_type': match.match_type.value if hasattr(match.match_type, 'value') else str(match.match_type),
                    'status': match.status,
                    'player1': {
                        'id': player1.id if player1 else None,
                        'username': player1.username if player1 else 'Unknown'
                    },
                    'player2': {
                        'id': player2.id if player2 else None,
                        'username': player2.username if player2 else 'Unknown'
                    },
                    'started_at': match.started_at.isoformat() if match.started_at else None,
                    'duration_minutes': duration_minutes,
                    'current_turn': getattr(match, 'current_turn', 1),
                    'arena_id': getattr(match, 'arena_id', None),
                    'tournament_id': getattr(match, 'tournament_id', None)
                }
                matches.append(match_data)
            
            # Get queued players (all players in matchmaking queue)
            queued_players = session.query(MMQueue).count()
            
            return jsonify({
                'active_matches': matches,
                'total_active': len(matches),
                'queued_players': queued_players,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error getting active matches: {e}")
        return jsonify({'error': str(e)}), 500
