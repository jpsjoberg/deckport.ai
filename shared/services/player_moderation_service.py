"""
Player Moderation Service
Comprehensive service for managing player bans, warnings, and moderation actions
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from shared.database.connection import SessionLocal
from shared.models.base import Player
from shared.models.player_moderation import (
    PlayerBan, PlayerWarning, PlayerActivityLog, PlayerSecurityLog, PlayerReport,
    BanType, BanReason, WarningType, ActivityType, PlayerLogLevel,
    log_player_activity, log_security_event
)
from shared.auth.admin_context import get_current_admin_id, log_admin_action
import logging

logger = logging.getLogger(__name__)

class PlayerModerationService:
    """Service for player moderation operations"""
    
    @staticmethod
    def ban_player(
        player_id: int,
        ban_type: BanType,
        reason: BanReason,
        description: str,
        duration_hours: Optional[int] = None,
        restrictions: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Ban a player with comprehensive logging and tracking
        
        Args:
            player_id: ID of player to ban
            ban_type: Type of ban (temporary, permanent, etc.)
            reason: Reason for ban
            description: Detailed description
            duration_hours: Duration in hours (None for permanent)
            restrictions: Additional restrictions
            session: Database session (optional)
            
        Returns:
            Dictionary with ban result
        """
        should_close_session = session is None
        if session is None:
            session = SessionLocal()
        
        try:
            # Get player
            player = session.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {'success': False, 'error': 'Player not found'}
            
            # Check if already banned
            existing_ban = session.query(PlayerBan).filter(
                PlayerBan.player_id == player_id,
                PlayerBan.is_active == True,
                or_(PlayerBan.expires_at.is_(None), PlayerBan.expires_at > datetime.now(timezone.utc))
            ).first()
            
            if existing_ban:
                return {'success': False, 'error': 'Player is already banned'}
            
            # Calculate expiration
            expires_at = None
            if duration_hours and ban_type == BanType.TEMPORARY:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            
            # Get admin ID
            admin_id = get_current_admin_id()
            if not admin_id:
                return {'success': False, 'error': 'Admin context not available'}
            
            # Create ban record
            ban = PlayerBan(
                player_id=player_id,
                ban_type=ban_type,
                reason=reason,
                description=description,
                expires_at=expires_at,
                banned_by_admin_id=admin_id,
                restrictions=restrictions or {}
            )
            session.add(ban)
            
            # Update player status
            player.is_banned = True
            player.ban_expires_at = expires_at
            player.ban_reason = reason.value
            player.status = "banned"
            
            # Log admin action
            log_admin_action(session, "player_banned", 
                f"Player {player.email} banned: {description}", {
                    'player_id': player_id,
                    'ban_type': ban_type.value,
                    'reason': reason.value,
                    'duration_hours': duration_hours,
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'restrictions': restrictions
                })
            
            # Log player activity
            log_player_activity(
                player_id=player_id,
                activity_type=ActivityType.LOGIN,  # Will be blocked
                description=f"Account banned: {description}",
                log_level=PlayerLogLevel.ADMIN,
                success=False,
                metadata={
                    'ban_type': ban_type.value,
                    'reason': reason.value,
                    'admin_id': admin_id
                }
            )
            
            session.commit()
            
            return {
                'success': True,
                'ban_id': ban.id,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'is_permanent': expires_at is None
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error banning player {player_id}: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if should_close_session:
                session.close()
    
    @staticmethod
    def unban_player(
        player_id: int,
        unban_reason: str,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Unban a player
        
        Args:
            player_id: ID of player to unban
            unban_reason: Reason for unbanning
            session: Database session (optional)
            
        Returns:
            Dictionary with unban result
        """
        should_close_session = session is None
        if session is None:
            session = SessionLocal()
        
        try:
            # Get player
            player = session.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {'success': False, 'error': 'Player not found'}
            
            # Get active ban
            active_ban = session.query(PlayerBan).filter(
                PlayerBan.player_id == player_id,
                PlayerBan.is_active == True
            ).first()
            
            if not active_ban:
                return {'success': False, 'error': 'Player is not banned'}
            
            # Get admin ID
            admin_id = get_current_admin_id()
            if not admin_id:
                return {'success': False, 'error': 'Admin context not available'}
            
            # Update ban record
            active_ban.is_active = False
            active_ban.unbanned_by_admin_id = admin_id
            active_ban.unbanned_at = datetime.now(timezone.utc)
            active_ban.unban_reason = unban_reason
            
            # Update player status
            player.is_banned = False
            player.ban_expires_at = None
            player.ban_reason = None
            player.status = "active"
            
            # Log admin action
            log_admin_action(session, "player_unbanned",
                f"Player {player.email} unbanned: {unban_reason}", {
                    'player_id': player_id,
                    'ban_id': active_ban.id,
                    'unban_reason': unban_reason
                })
            
            # Log player activity
            log_player_activity(
                player_id=player_id,
                activity_type=ActivityType.LOGIN,
                description=f"Account unbanned: {unban_reason}",
                log_level=PlayerLogLevel.ADMIN,
                success=True,
                metadata={
                    'unban_reason': unban_reason,
                    'admin_id': admin_id
                }
            )
            
            session.commit()
            
            return {'success': True, 'unbanned_at': active_ban.unbanned_at.isoformat()}
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error unbanning player {player_id}: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if should_close_session:
                session.close()
    
    @staticmethod
    def warn_player(
        player_id: int,
        warning_type: WarningType,
        reason: str,
        description: str,
        escalation_level: int = 1,
        expires_hours: Optional[int] = None,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Issue a warning to a player
        
        Args:
            player_id: ID of player to warn
            warning_type: Type of warning
            reason: Reason for warning
            description: Detailed description
            escalation_level: Warning escalation level (1-5)
            expires_hours: Hours until warning expires
            session: Database session (optional)
            
        Returns:
            Dictionary with warning result
        """
        should_close_session = session is None
        if session is None:
            session = SessionLocal()
        
        try:
            # Get player
            player = session.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {'success': False, 'error': 'Player not found'}
            
            # Get admin ID
            admin_id = get_current_admin_id()
            if not admin_id:
                return {'success': False, 'error': 'Admin context not available'}
            
            # Calculate expiration
            expires_at = None
            if expires_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            
            # Get previous warning for escalation
            previous_warning = session.query(PlayerWarning).filter(
                PlayerWarning.player_id == player_id,
                PlayerWarning.is_active == True
            ).order_by(desc(PlayerWarning.created_at)).first()
            
            # Create warning
            warning = PlayerWarning(
                player_id=player_id,
                warning_type=warning_type,
                reason=reason,
                description=description,
                escalation_level=escalation_level,
                expires_at=expires_at,
                issued_by_admin_id=admin_id,
                previous_warning_id=previous_warning.id if previous_warning else None
            )
            session.add(warning)
            
            # Update player warning count
            player.warning_count += 1
            player.last_warning_at = datetime.now(timezone.utc)
            
            # Check for auto-escalation to ban
            should_auto_ban = False
            if escalation_level >= 3 and player.warning_count >= 3:
                should_auto_ban = True
            
            # Log admin action
            log_admin_action(session, "player_warned",
                f"Player {player.email} warned: {description}", {
                    'player_id': player_id,
                    'warning_type': warning_type.value,
                    'reason': reason,
                    'escalation_level': escalation_level,
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'should_auto_ban': should_auto_ban
                })
            
            # Log player activity
            log_player_activity(
                player_id=player_id,
                activity_type=ActivityType.LOGIN,
                description=f"Warning issued: {description}",
                log_level=PlayerLogLevel.WARNING,
                metadata={
                    'warning_type': warning_type.value,
                    'reason': reason,
                    'escalation_level': escalation_level,
                    'admin_id': admin_id
                }
            )
            
            session.commit()
            
            result = {
                'success': True,
                'warning_id': warning.id,
                'escalation_level': escalation_level,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'should_auto_ban': should_auto_ban
            }
            
            # Auto-ban if escalation threshold reached
            if should_auto_ban:
                ban_result = PlayerModerationService.ban_player(
                    player_id=player_id,
                    ban_type=BanType.TEMPORARY,
                    reason=BanReason.MULTIPLE_ACCOUNTS,  # Or appropriate reason
                    description=f"Auto-ban after {player.warning_count} warnings",
                    duration_hours=24 * 7,  # 7 days
                    session=session
                )
                result['auto_ban'] = ban_result
            
            return result
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error warning player {player_id}: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if should_close_session:
                session.close()
    
    @staticmethod
    def check_player_access(player_id: int) -> Dict[str, Any]:
        """
        Check if player has access to the system
        
        Args:
            player_id: ID of player to check
            
        Returns:
            Dictionary with access status
        """
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {'has_access': False, 'reason': 'Player not found'}
            
            # Check ban status
            if player.is_banned:
                active_ban = session.query(PlayerBan).filter(
                    PlayerBan.player_id == player_id,
                    PlayerBan.is_active == True,
                    or_(PlayerBan.expires_at.is_(None), PlayerBan.expires_at > datetime.now(timezone.utc))
                ).first()
                
                if active_ban:
                    return {
                        'has_access': False,
                        'reason': 'banned',
                        'ban_type': active_ban.ban_type.value,
                        'ban_reason': active_ban.reason.value,
                        'description': active_ban.description,
                        'expires_at': active_ban.expires_at.isoformat() if active_ban.expires_at else None,
                        'can_appeal': not active_ban.appeal_submitted
                    }
                else:
                    # Ban expired, update player status
                    player.is_banned = False
                    player.ban_expires_at = None
                    player.ban_reason = None
                    player.status = "active"
                    session.commit()
            
            # Check account lock
            if player.account_locked_until and player.account_locked_until > datetime.now(timezone.utc):
                return {
                    'has_access': False,
                    'reason': 'account_locked',
                    'locked_until': player.account_locked_until.isoformat()
                }
            
            # Check account status
            if player.status not in ['active', 'verified']:
                return {
                    'has_access': False,
                    'reason': 'account_inactive',
                    'status': player.status
                }
            
            return {'has_access': True}
    
    @staticmethod
    def get_player_moderation_history(player_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        Get moderation history for a player
        
        Args:
            player_id: ID of player
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with moderation history
        """
        with SessionLocal() as session:
            # Get bans
            bans = session.query(PlayerBan).filter(
                PlayerBan.player_id == player_id
            ).order_by(desc(PlayerBan.created_at)).limit(limit).all()
            
            # Get warnings
            warnings = session.query(PlayerWarning).filter(
                PlayerWarning.player_id == player_id
            ).order_by(desc(PlayerWarning.created_at)).limit(limit).all()
            
            # Get reports
            reports = session.query(PlayerReport).filter(
                PlayerReport.reported_player_id == player_id
            ).order_by(desc(PlayerReport.created_at)).limit(limit).all()
            
            return {
                'bans': [{
                    'id': ban.id,
                    'type': ban.ban_type.value,
                    'reason': ban.reason.value,
                    'description': ban.description,
                    'is_active': ban.is_active,
                    'starts_at': ban.starts_at.isoformat(),
                    'expires_at': ban.expires_at.isoformat() if ban.expires_at else None,
                    'unbanned_at': ban.unbanned_at.isoformat() if ban.unbanned_at else None,
                    'unban_reason': ban.unban_reason
                } for ban in bans],
                'warnings': [{
                    'id': warning.id,
                    'type': warning.warning_type.value,
                    'reason': warning.reason,
                    'description': warning.description,
                    'escalation_level': warning.escalation_level,
                    'is_active': warning.is_active,
                    'acknowledged': warning.acknowledged,
                    'created_at': warning.created_at.isoformat(),
                    'expires_at': warning.expires_at.isoformat() if warning.expires_at else None
                } for warning in warnings],
                'reports': [{
                    'id': report.id,
                    'type': report.report_type,
                    'description': report.description,
                    'status': report.status,
                    'priority': report.priority,
                    'created_at': report.created_at.isoformat(),
                    'resolved_at': report.resolved_at.isoformat() if report.resolved_at else None
                } for report in reports]
            }
    
    @staticmethod
    def update_player_login_tracking(
        player_id: int,
        ip_address: str,
        user_agent: Optional[str] = None,
        success: bool = True,
        session_id: Optional[str] = None
    ):
        """
        Update player login tracking
        
        Args:
            player_id: ID of player
            ip_address: IP address of login attempt
            user_agent: User agent string
            success: Whether login was successful
            session_id: Session ID
        """
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            if not player:
                return
            
            if success:
                # Update successful login tracking
                player.last_login_at = datetime.now(timezone.utc)
                player.last_login_ip = ip_address
                player.login_count += 1
                player.failed_login_attempts = 0  # Reset failed attempts
                
                # Log successful login
                log_player_activity(
                    player_id=player_id,
                    activity_type=ActivityType.LOGIN,
                    description="Successful login",
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
            else:
                # Update failed login tracking
                player.failed_login_attempts += 1
                player.last_failed_login_at = datetime.now(timezone.utc)
                
                # Lock account if too many failed attempts
                if player.failed_login_attempts >= 5:
                    player.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                    
                    # Log security event
                    log_security_event(
                        event_type="account_locked_failed_logins",
                        description=f"Account locked after {player.failed_login_attempts} failed login attempts",
                        ip_address=ip_address,
                        player_id=player_id,
                        severity="high",
                        user_agent=user_agent,
                        detection_method="automated"
                    )
                
                # Log failed login
                log_player_activity(
                    player_id=player_id,
                    activity_type=ActivityType.LOGIN,
                    description="Failed login attempt",
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    log_level=PlayerLogLevel.WARNING
                )
            
            session.commit()

# Convenience functions
def ban_player(player_id: int, ban_type: BanType, reason: BanReason, description: str, **kwargs):
    """Convenience function to ban a player"""
    return PlayerModerationService.ban_player(player_id, ban_type, reason, description, **kwargs)

def unban_player(player_id: int, unban_reason: str):
    """Convenience function to unban a player"""
    return PlayerModerationService.unban_player(player_id, unban_reason)

def warn_player(player_id: int, warning_type: WarningType, reason: str, description: str, **kwargs):
    """Convenience function to warn a player"""
    return PlayerModerationService.warn_player(player_id, warning_type, reason, description, **kwargs)

def check_player_access(player_id: int):
    """Convenience function to check player access"""
    return PlayerModerationService.check_player_access(player_id)
