"""
Admin player management routes
Handles player accounts, moderation, and support
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.base import Player, AuditLog, ConsoleLoginToken
from shared.auth.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

admin_player_mgmt_bp = Blueprint('admin_player_mgmt', __name__, url_prefix='/v1/admin/players')

@admin_player_mgmt_bp.route('', methods=['GET'])
@admin_required
def get_players():
    """Get list of players with optional filtering"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 50)), 100)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        with SessionLocal() as session:
            query = session.query(Player)
            
            # Apply search filter
            if search:
                query = query.filter(
                    or_(
                        Player.email.ilike(f'%{search}%'),
                        Player.display_name.ilike(f'%{search}%')
                    )
                )
            
            # Apply status filter (for now, all players are active)
            # TODO: Add status field to Player model
            
            # Apply sorting
            if sort_by == 'email':
                order_col = Player.email
            elif sort_by == 'display_name':
                order_col = Player.display_name
            elif sort_by == 'elo_rating':
                order_col = Player.elo_rating
            else:
                order_col = Player.created_at
            
            if sort_order == 'desc':
                order_col = desc(order_col)
            
            query = query.order_by(order_col)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            players = query.offset(offset).limit(page_size).all()
            
            # Enrich player data
            player_data = []
            for player in players:
                # Get recent activity
                recent_activity = session.query(AuditLog).filter(
                    AuditLog.actor_type == "player",
                    AuditLog.actor_id == player.id
                ).order_by(desc(AuditLog.created_at)).first()
                
                last_activity = None
                if recent_activity:
                    last_activity = recent_activity.created_at.isoformat()
                
                # Get console login history
                console_logins = session.query(ConsoleLoginToken).filter(
                    ConsoleLoginToken.confirmed_player_id == player.id
                ).count()
                
                player_info = {
                    'id': player.id,
                    'email': player.email,
                    'display_name': player.display_name,
                    'elo_rating': player.elo_rating,
                    'created_at': player.created_at.isoformat(),
                    'updated_at': player.updated_at.isoformat(),
                    'last_activity': last_activity,
                    'console_logins': console_logins,
                    'status': 'active',  # TODO: Add actual status field
                    # Mock additional data
                    'matches_played': player.elo_rating // 10,  # Rough estimate
                    'win_rate': min(max((player.elo_rating - 1000) / 10, 30), 70),  # Mock win rate
                    'account_age_days': (datetime.now(timezone.utc) - player.created_at).days,
                    'is_premium': False,  # TODO: Add premium status
                    'warnings': 0,  # TODO: Add moderation system
                    'last_ip': '192.168.1.100',  # TODO: Track IP addresses
                }
                
                player_data.append(player_info)
            
            return jsonify({
                'players': player_data,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            })
            
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        return jsonify({'error': 'Failed to retrieve players'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>', methods=['GET'])
@admin_required
def get_player_detail(player_id):
    """Get detailed information about a specific player"""
    try:
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # Get player's activity logs
            activity_logs = session.query(AuditLog).filter(
                AuditLog.actor_type == "player",
                AuditLog.actor_id == player.id
            ).order_by(desc(AuditLog.created_at)).limit(50).all()
            
            logs = []
            for log in activity_logs:
                logs.append({
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'details': log.details,
                    'meta': log.meta
                })
            
            # Get console login history
            console_logins = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.confirmed_player_id == player.id
            ).order_by(desc(ConsoleLoginToken.created_at)).limit(20).all()
            
            login_history = []
            for login in console_logins:
                login_history.append({
                    'timestamp': login.created_at.isoformat(),
                    'console_id': login.console_id,
                    'status': login.status.value
                })
            
            # Calculate statistics
            account_age = (datetime.now(timezone.utc) - player.created_at).days
            matches_played = player.elo_rating // 10  # Mock calculation
            
            player_detail = {
                'id': player.id,
                'email': player.email,
                'display_name': player.display_name,
                'elo_rating': player.elo_rating,
                'created_at': player.created_at.isoformat(),
                'updated_at': player.updated_at.isoformat(),
                'status': 'active',
                'account_age_days': account_age,
                'matches_played': matches_played,
                'win_rate': min(max((player.elo_rating - 1000) / 10, 30), 70),
                'console_logins_count': len(login_history),
                'activity_logs': logs,
                'console_login_history': login_history,
                # Mock additional data
                'is_premium': False,
                'subscription_expires': None,
                'warnings': 0,
                'bans': 0,
                'last_ip': '192.168.1.100',
                'country': 'US',
                'preferred_language': 'en',
                'marketing_consent': True,
                'two_factor_enabled': False,
                'cards_owned': 0,  # TODO: Calculate from player_cards
                'total_spent': 0.0,  # TODO: Calculate from transactions
            }
            
            return jsonify(player_detail)
            
    except Exception as e:
        logger.error(f"Error getting player detail: {e}")
        return jsonify({'error': 'Failed to retrieve player details'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/ban', methods=['POST'])
@admin_required
def ban_player(player_id):
    """Ban a player account"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Terms of service violation')
        duration_hours = data.get('duration_hours')  # None for permanent
        
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # TODO: Add ban system to Player model
            # For now, just log the action
            
            ban_until = None
            if duration_hours:
                ban_until = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            
            # Log the ban
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="player_banned",
                details=f"Player {player.email} banned: {reason}",
                meta={
                    'player_id': player_id,
                    'reason': reason,
                    'duration_hours': duration_hours,
                    'ban_until': ban_until.isoformat() if ban_until else None
                }
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Player {player.email} has been banned',
                'ban_until': ban_until.isoformat() if ban_until else None
            })
            
    except Exception as e:
        logger.error(f"Error banning player: {e}")
        return jsonify({'error': 'Failed to ban player'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/unban', methods=['POST'])
@admin_required
def unban_player(player_id):
    """Unban a player account"""
    try:
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # TODO: Implement actual unban logic
            
            # Log the unban
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="player_unbanned",
                details=f"Player {player.email} unbanned by admin",
                meta={'player_id': player_id}
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Player {player.email} has been unbanned'
            })
            
    except Exception as e:
        logger.error(f"Error unbanning player: {e}")
        return jsonify({'error': 'Failed to unban player'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/warn', methods=['POST'])
@admin_required
def warn_player(player_id):
    """Issue a warning to a player"""
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'error': 'Warning message required'}), 400
        
        message = data['message']
        severity = data.get('severity', 'low')  # low, medium, high
        
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # Log the warning
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="player_warned",
                details=f"Warning issued to {player.email}: {message}",
                meta={
                    'player_id': player_id,
                    'message': message,
                    'severity': severity
                }
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Warning issued to {player.email}'
            })
            
    except Exception as e:
        logger.error(f"Error warning player: {e}")
        return jsonify({'error': 'Failed to issue warning'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/reset-password', methods=['POST'])
@admin_required
def reset_player_password(player_id):
    """Reset a player's password"""
    try:
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # TODO: Implement password reset logic
            # For now, just log the action
            
            # Log the password reset
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="password_reset",
                details=f"Password reset for {player.email} by admin",
                meta={'player_id': player_id}
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Password reset email sent to {player.email}'
            })
            
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        return jsonify({'error': 'Failed to reset password'}), 500

@admin_player_mgmt_bp.route('/statistics', methods=['GET'])
@admin_required
def get_player_statistics():
    """Get player statistics for dashboard"""
    try:
        with SessionLocal() as session:
            # Get basic counts
            total_players = session.query(Player).count()
            
            # Players registered in last 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            new_players_30d = session.query(Player).filter(
                Player.created_at >= thirty_days_ago
            ).count()
            
            # Players registered in last 7 days
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            new_players_7d = session.query(Player).filter(
                Player.created_at >= seven_days_ago
            ).count()
            
            # Players with recent activity (console logins in last 7 days)
            active_players = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.created_at >= seven_days_ago,
                ConsoleLoginToken.confirmed_player_id.isnot(None)
            ).distinct(ConsoleLoginToken.confirmed_player_id).count()
            
            # Average ELO rating
            avg_elo = session.query(func.avg(Player.elo_rating)).scalar() or 1000
            
            # Top players
            top_players = session.query(Player).order_by(desc(Player.elo_rating)).limit(10).all()
            
            top_players_data = []
            for player in top_players:
                top_players_data.append({
                    'id': player.id,
                    'display_name': player.display_name,
                    'email': player.email,
                    'elo_rating': player.elo_rating
                })
            
            statistics = {
                'total_players': total_players,
                'new_players_30d': new_players_30d,
                'new_players_7d': new_players_7d,
                'active_players_7d': active_players,
                'avg_elo_rating': round(avg_elo, 1),
                'retention_rate': round((active_players / max(total_players, 1)) * 100, 1),
                'top_players': top_players_data,
                # Mock additional statistics
                'banned_players': 0,  # TODO: Implement ban system
                'warned_players': 0,  # TODO: Count warnings
                'premium_players': 0,  # TODO: Implement premium system
                'support_tickets_open': 0,  # TODO: Implement support system
            }
            
            return jsonify(statistics)
            
    except Exception as e:
        logger.error(f"Error getting player statistics: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@admin_player_mgmt_bp.route('/search', methods=['GET'])
@admin_required
def search_players():
    """Search players by various criteria"""
    try:
        query_text = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query_text:
            return jsonify({'players': []})
        
        with SessionLocal() as session:
            # Search by email, display name, or ID
            query = session.query(Player)
            
            # Try to parse as ID first
            try:
                player_id = int(query_text)
                query = query.filter(Player.id == player_id)
            except ValueError:
                # Search by email or display name
                query = query.filter(
                    or_(
                        Player.email.ilike(f'%{query_text}%'),
                        Player.display_name.ilike(f'%{query_text}%')
                    )
                )
            
            players = query.limit(limit).all()
            
            results = []
            for player in players:
                results.append({
                    'id': player.id,
                    'email': player.email,
                    'display_name': player.display_name,
                    'elo_rating': player.elo_rating,
                    'created_at': player.created_at.isoformat(),
                    'status': 'active'  # TODO: Add actual status
                })
            
            return jsonify({'players': results})
            
    except Exception as e:
        logger.error(f"Error searching players: {e}")
        return jsonify({'error': 'Failed to search players'}), 500
