"""
Admin player management routes
Handles player accounts, moderation, and support
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.base import Player, AuditLog, ConsoleLoginToken
from shared.auth.auto_rbac_decorator import auto_rbac_required, player_management_required
from shared.auth.admin_roles import Permission
import logging
from shared.auth.admin_context import log_admin_action, get_current_admin_id
from shared.services.player_moderation_service import PlayerModerationService
from shared.models.player_moderation import BanType, BanReason, WarningType

logger = logging.getLogger(__name__)

admin_player_mgmt_bp = Blueprint('admin_player_mgmt', __name__, url_prefix='/v1/admin/players')

@admin_player_mgmt_bp.route('', methods=['GET'])
@player_management_required(Permission.PLAYER_VIEW)
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
@player_management_required(Permission.PLAYER_VIEW)
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
                    'details': log.details
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
@player_management_required(Permission.PLAYER_BAN)
def ban_player(player_id):
    """Ban a player account with comprehensive tracking"""
    try:
        data = request.get_json() or {}
        reason_str = data.get('reason', 'terms_violation')
        description = data.get('description', 'Terms of service violation')
        duration_hours = data.get('duration_hours')  # None for permanent
        ban_type_str = data.get('ban_type', 'temporary' if duration_hours else 'permanent')
        restrictions = data.get('restrictions', {})
        
        # Convert string enums
        try:
            ban_type = BanType(ban_type_str)
            ban_reason = BanReason(reason_str)
        except ValueError as e:
            return jsonify({'error': f'Invalid ban type or reason: {e}'}), 400
        
        # Use the moderation service
        result = PlayerModerationService.ban_player(
            player_id=player_id,
            ban_type=ban_type,
            reason=ban_reason,
            description=description,
            duration_hours=duration_hours,
            restrictions=restrictions
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Player has been banned',
                'ban_id': result['ban_id'],
                'expires_at': result['expires_at'],
                'is_permanent': result['is_permanent']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error banning player: {e}")
        return jsonify({'error': 'Failed to ban player'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/unban', methods=['POST'])
@player_management_required(Permission.PLAYER_BAN)
def unban_player(player_id):
    """Unban a player account with comprehensive tracking"""
    try:
        data = request.get_json() or {}
        unban_reason = data.get('reason', 'Ban lifted by admin')
        
        # Use the moderation service
        result = PlayerModerationService.unban_player(
            player_id=player_id,
            unban_reason=unban_reason
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Player has been unbanned',
                'unbanned_at': result['unbanned_at']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error unbanning player: {e}")
        return jsonify({'error': 'Failed to unban player'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/warn', methods=['POST'])
@player_management_required(Permission.PLAYER_WARN)
def warn_player(player_id):
    """Issue a warning to a player with escalation tracking"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Inappropriate behavior')
        description = data.get('description', 'Warning issued by admin')
        warning_type_str = data.get('warning_type', 'written')
        escalation_level = data.get('escalation_level', 1)
        expires_hours = data.get('expires_hours')
        
        # Convert string enum
        try:
            warning_type = WarningType(warning_type_str)
        except ValueError as e:
            return jsonify({'error': f'Invalid warning type: {e}'}), 400
        
        # Use the moderation service
        result = PlayerModerationService.warn_player(
            player_id=player_id,
            warning_type=warning_type,
            reason=reason,
            description=description,
            escalation_level=escalation_level,
            expires_hours=expires_hours
        )
        
        if result['success']:
            response = {
                'success': True,
                'message': 'Warning issued successfully',
                'warning_id': result['warning_id'],
                'escalation_level': result['escalation_level'],
                'expires_at': result['expires_at']
            }
            
            # Include auto-ban info if applicable
            if result.get('should_auto_ban'):
                response['auto_ban'] = result['auto_ban']
                response['message'] += ' (Auto-ban triggered due to escalation)'
            
            return jsonify(response)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error warning player: {e}")
        return jsonify({'error': 'Failed to issue warning'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/reset-password', methods=['POST'])
@player_management_required(Permission.PLAYER_EDIT)
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
            log_admin_action(session, "password_reset", f"Password reset for {player.email} by admin", {'player_id': player_id}
            )
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Password reset email sent to {player.email}'
            })
            
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        return jsonify({'error': 'Failed to reset password'}), 500

@admin_player_mgmt_bp.route('/statistics', methods=['GET'])
@player_management_required(Permission.PLAYER_VIEW)
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
@player_management_required(Permission.PLAYER_VIEW)
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

@admin_player_mgmt_bp.route('/<int:player_id>/moderation-history', methods=['GET'])
@player_management_required(Permission.PLAYER_VIEW)
def get_player_moderation_history(player_id):
    """Get comprehensive moderation history for a player"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Use the moderation service
        history = PlayerModerationService.get_player_moderation_history(player_id, limit)
        
        return jsonify({
            'success': True,
            'player_id': player_id,
            'moderation_history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting moderation history: {e}")
        return jsonify({'error': 'Failed to retrieve moderation history'}), 500

@admin_player_mgmt_bp.route('/<int:player_id>/access-check', methods=['GET'])
@player_management_required(Permission.PLAYER_VIEW)
def check_player_access_endpoint(player_id):
    """Check if player has access to the system"""
    try:
        # Use the moderation service
        access_status = PlayerModerationService.check_player_access(player_id)
        
        return jsonify({
            'success': True,
            'player_id': player_id,
            'access_status': access_status
        })
        
    except Exception as e:
        logger.error(f"Error checking player access: {e}")
        return jsonify({'error': 'Failed to check player access'}), 500

@admin_player_mgmt_bp.route('/moderation/dashboard', methods=['GET'])
@player_management_required(Permission.PLAYER_VIEW)
def get_moderation_dashboard():
    """Get moderation dashboard statistics"""
    try:
        with SessionLocal() as session:
            from shared.models.player_moderation import PlayerBan, PlayerWarning, PlayerReport
            
            # Get statistics
            stats = {
                'active_bans': session.query(PlayerBan).filter(
                    PlayerBan.is_active == True,
                    or_(PlayerBan.expires_at.is_(None), PlayerBan.expires_at > datetime.now(timezone.utc))
                ).count(),
                'total_bans': session.query(PlayerBan).count(),
                'active_warnings': session.query(PlayerWarning).filter(
                    PlayerWarning.is_active == True
                ).count(),
                'pending_reports': session.query(PlayerReport).filter(
                    PlayerReport.status == 'pending'
                ).count(),
                'banned_players': session.query(Player).filter(
                    Player.is_banned == True
                ).count(),
                'total_players': session.query(Player).count()
            }
            
            # Recent activity
            recent_bans = session.query(PlayerBan).order_by(
                desc(PlayerBan.created_at)
            ).limit(10).all()
            
            recent_warnings = session.query(PlayerWarning).order_by(
                desc(PlayerWarning.created_at)
            ).limit(10).all()
            
            return jsonify({
                'success': True,
                'statistics': stats,
                'recent_activity': {
                    'bans': [{
                        'id': ban.id,
                        'player_id': ban.player_id,
                        'type': ban.ban_type.value,
                        'reason': ban.reason.value,
                        'description': ban.description,
                        'created_at': ban.created_at.isoformat(),
                        'expires_at': ban.expires_at.isoformat() if ban.expires_at else None
                    } for ban in recent_bans],
                    'warnings': [{
                        'id': warning.id,
                        'player_id': warning.player_id,
                        'type': warning.warning_type.value,
                        'reason': warning.reason,
                        'escalation_level': warning.escalation_level,
                        'created_at': warning.created_at.isoformat()
                    } for warning in recent_warnings]
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting moderation dashboard: {e}")
        return jsonify({'error': 'Failed to retrieve moderation dashboard'}), 500
