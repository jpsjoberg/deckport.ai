"""
Enhanced audit logging system for admin actions
Provides comprehensive logging with security context and monitoring
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timezone, timedelta
from flask import request, g
from sqlalchemy.exc import SQLAlchemyError
from shared.database.connection import SessionLocal
from shared.models.base import AuditLog

logger = logging.getLogger(__name__)

class AdminAuditLogger:
    """Enhanced audit logger for admin actions"""
    
    # Security-sensitive actions that require detailed logging
    SENSITIVE_ACTIONS = {
        'admin_login', 'admin_logout', 'admin_login_failed',
        'player_banned', 'player_unbanned', 'player_warned',
        'console_approved', 'console_rejected', 'console_rebooted', 'console_shutdown',
        'admin_created', 'admin_deactivated', 'admin_role_changed',
        'system_maintenance_triggered', 'tournament_started', 'tournament_cancelled',
        'bulk_operation', 'data_export', 'configuration_changed'
    }
    
    @staticmethod
    def log_admin_action(
        action: str,
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Log an admin action with full security context
        
        Args:
            action: Action performed (e.g., 'player_banned', 'console_approved')
            details: Additional details about the action
            resource_type: Type of resource affected (e.g., 'player', 'console')
            resource_id: ID of the resource affected
            admin_id: ID of admin performing action (auto-detected if not provided)
            success: Whether the action was successful
            error_message: Error message if action failed
        """
        try:
            # Get admin context
            if not admin_id:
                admin_id = getattr(g, 'admin_id', None)
            
            admin_email = getattr(g, 'admin_email', None)
            admin_username = getattr(g, 'admin_username', None)
            is_super_admin = getattr(g, 'is_super_admin', False)
            
            # Get request context
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')[:500]
            endpoint = request.endpoint
            method = request.method
            
            # Build comprehensive details
            audit_details = {
                'success': success,
                'endpoint': endpoint,
                'method': method,
                'admin_context': {
                    'admin_id': admin_id,
                    'admin_email': admin_email,
                    'admin_username': admin_username,
                    'is_super_admin': is_super_admin
                },
                'request_context': {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Add custom details
            if details:
                audit_details.update(details)
            
            # Add error information if failed
            if not success and error_message:
                audit_details['error'] = error_message
            
            # Mark sensitive actions
            if action in AdminAuditLogger.SENSITIVE_ACTIONS:
                audit_details['sensitive'] = True
            
            # Store in database
            with SessionLocal() as session:
                audit_log = AuditLog(
                    actor_type="admin",
                    actor_id=admin_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=audit_details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(audit_log)
                session.commit()
            
            # Log to application logger for immediate monitoring
            log_level = logging.WARNING if not success else logging.INFO
            logger.log(
                log_level,
                f"Admin action: {action}",
                extra={
                    'admin_id': admin_id,
                    'action': action,
                    'success': success,
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'ip_address': ip_address,
                    'sensitive': action in AdminAuditLogger.SENSITIVE_ACTIONS
                }
            )
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error logging admin action: {e}")
            return False
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
            return False
    
    @staticmethod
    def log_login_attempt(admin_email: str, success: bool, reason: Optional[str] = None):
        """Log admin login attempt"""
        action = 'admin_login' if success else 'admin_login_failed'
        details = {
            'admin_email': admin_email,
            'login_attempt': True
        }
        
        if not success and reason:
            details['failure_reason'] = reason
        
        AdminAuditLogger.log_admin_action(
            action=action,
            details=details,
            success=success,
            error_message=reason if not success else None
        )
    
    @staticmethod
    def log_logout(admin_id: int, session_id: Optional[str] = None):
        """Log admin logout"""
        details = {'logout': True}
        if session_id:
            details['session_id'] = session_id
        
        AdminAuditLogger.log_admin_action(
            action='admin_logout',
            details=details,
            admin_id=admin_id
        )
    
    @staticmethod
    def log_player_action(action: str, player_id: int, details: Optional[Dict] = None):
        """Log player management actions"""
        AdminAuditLogger.log_admin_action(
            action=action,
            resource_type='player',
            resource_id=player_id,
            details=details or {}
        )
    
    @staticmethod
    def log_console_action(action: str, console_id: int, details: Optional[Dict] = None):
        """Log console management actions"""
        AdminAuditLogger.log_admin_action(
            action=action,
            resource_type='console',
            resource_id=console_id,
            details=details or {}
        )
    
    @staticmethod
    def log_system_action(action: str, details: Optional[Dict] = None):
        """Log system-level actions"""
        AdminAuditLogger.log_admin_action(
            action=action,
            resource_type='system',
            details=details or {}
        )
    
    @staticmethod
    def log_bulk_operation(operation_type: str, affected_count: int, details: Optional[Dict] = None):
        """Log bulk operations"""
        bulk_details = {
            'operation_type': operation_type,
            'affected_count': affected_count,
            'bulk_operation': True
        }
        
        if details:
            bulk_details.update(details)
        
        AdminAuditLogger.log_admin_action(
            action='bulk_operation',
            details=bulk_details
        )
    
    @staticmethod
    def log_security_event(event_type: str, severity: str, details: Optional[Dict] = None):
        """Log security-related events"""
        security_details = {
            'security_event': True,
            'event_type': event_type,
            'severity': severity
        }
        
        if details:
            security_details.update(details)
        
        AdminAuditLogger.log_admin_action(
            action=f'security_{event_type}',
            details=security_details
        )
    
    @staticmethod
    def get_admin_activity(admin_id: int, hours: int = 24) -> list:
        """Get recent activity for an admin"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with SessionLocal() as session:
                logs = session.query(AuditLog).filter(
                    AuditLog.actor_type == 'admin',
                    AuditLog.actor_id == admin_id,
                    AuditLog.created_at >= cutoff_time
                ).order_by(AuditLog.created_at.desc()).limit(100).all()
                
                return [{
                    'id': log.id,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat()
                } for log in logs]
                
        except Exception as e:
            logger.error(f"Error getting admin activity: {e}")
            return []
    
    @staticmethod
    def get_security_events(hours: int = 24) -> list:
        """Get recent security events"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with SessionLocal() as session:
                logs = session.query(AuditLog).filter(
                    AuditLog.actor_type == 'admin',
                    AuditLog.created_at >= cutoff_time,
                    AuditLog.details.op('->>')('sensitive') == 'true'
                ).order_by(AuditLog.created_at.desc()).limit(50).all()
                
                return [{
                    'id': log.id,
                    'action': log.action,
                    'actor_id': log.actor_id,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat()
                } for log in logs]
                
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []

# Convenience function for easy access
def log_admin_action(*args, **kwargs):
    """Convenience function for logging admin actions"""
    return AdminAuditLogger.log_admin_action(*args, **kwargs)
