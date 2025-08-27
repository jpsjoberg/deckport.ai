"""
Admin Context Management
Provides utilities for extracting and managing admin context from JWT tokens
"""

from flask import g
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AdminContext:
    """Utility class for managing admin context in requests"""
    
    @staticmethod
    def get_current_admin_id() -> Optional[int]:
        """
        Get the current admin ID from Flask g context
        
        Returns:
            Admin ID if available, None otherwise
        """
        return getattr(g, 'admin_id', None)
    
    @staticmethod
    def get_current_admin_email() -> Optional[str]:
        """
        Get the current admin email from Flask g context
        
        Returns:
            Admin email if available, None otherwise
        """
        return getattr(g, 'admin_email', None)
    
    @staticmethod
    def get_current_admin_username() -> Optional[str]:
        """
        Get the current admin username from Flask g context
        
        Returns:
            Admin username if available, None otherwise
        """
        return getattr(g, 'admin_username', None)
    
    @staticmethod
    def get_current_admin_role() -> Optional[str]:
        """
        Get the current admin role from Flask g context
        
        Returns:
            Admin role if available, None otherwise
        """
        return getattr(g, 'admin_role', None)
    
    @staticmethod
    def is_super_admin() -> bool:
        """
        Check if current admin is a super admin
        
        Returns:
            True if super admin, False otherwise
        """
        return getattr(g, 'is_super_admin', False)
    
    @staticmethod
    def is_admin_authenticated() -> bool:
        """
        Check if an admin is currently authenticated
        
        Returns:
            True if admin is authenticated, False otherwise
        """
        return getattr(g, 'is_admin', False) and AdminContext.get_current_admin_id() is not None
    
    @staticmethod
    def get_admin_context() -> Dict[str, Any]:
        """
        Get complete admin context as a dictionary
        
        Returns:
            Dictionary containing all admin context information
        """
        return {
            'admin_id': AdminContext.get_current_admin_id(),
            'admin_email': AdminContext.get_current_admin_email(),
            'admin_username': AdminContext.get_current_admin_username(),
            'admin_role': AdminContext.get_current_admin_role(),
            'is_super_admin': AdminContext.is_super_admin(),
            'is_authenticated': AdminContext.is_admin_authenticated()
        }
    
    @staticmethod
    def require_admin_id() -> int:
        """
        Get current admin ID, raising exception if not available
        
        Returns:
            Admin ID
            
        Raises:
            ValueError: If admin ID is not available
        """
        admin_id = AdminContext.get_current_admin_id()
        if admin_id is None:
            raise ValueError("Admin ID not available in request context")
        return admin_id
    
    @staticmethod
    def get_admin_id_or_default(default: int = 1) -> int:
        """
        Get current admin ID or return default value
        
        Args:
            default: Default admin ID to return if none available
            
        Returns:
            Admin ID or default value
        """
        admin_id = AdminContext.get_current_admin_id()
        if admin_id is None:
            logger.warning(f"Admin ID not available, using default: {default}")
            return default
        return admin_id

class AdminAuditContext:
    """Specialized context for audit logging"""
    
    @staticmethod
    def create_audit_log_entry(
        action: str,
        details: str,
        meta: Optional[Dict[str, Any]] = None,
        actor_type: str = "admin"
    ) -> Dict[str, Any]:
        """
        Create a standardized audit log entry with proper admin context
        
        Args:
            action: Action being performed
            details: Details about the action
            meta: Additional metadata
            actor_type: Type of actor (default: "admin")
            
        Returns:
            Dictionary ready for AuditLog creation
        """
        admin_context = AdminContext.get_admin_context()
        
        audit_entry = {
            'actor_type': actor_type,
            'actor_id': AdminContext.get_admin_id_or_default(),
            'action': action,
            'details': details,
            'meta': meta or {}
        }
        
        # Add admin context to meta
        audit_entry['meta']['admin_context'] = {
            'admin_email': admin_context['admin_email'],
            'admin_username': admin_context['admin_username'],
            'admin_role': admin_context['admin_role'],
            'is_super_admin': admin_context['is_super_admin']
        }
        
        return audit_entry
    
    @staticmethod
    def log_admin_action(
        session,
        action: str,
        details: str,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Create and save an audit log entry with proper admin context
        
        Args:
            session: Database session
            action: Action being performed
            details: Details about the action
            meta: Additional metadata
        """
        from shared.models.base import AuditLog
        
        audit_data = AdminAuditContext.create_audit_log_entry(action, details, meta)
        
        audit_log = AuditLog(
            actor_type=audit_data['actor_type'],
            actor_id=audit_data['actor_id'],
            action=audit_data['action'],
            details=audit_data['details'],
            meta=audit_data['meta']
        )
        
        session.add(audit_log)
        
        # Log for debugging/monitoring
        logger.info(f"Admin action logged: {action} by admin_id={audit_data['actor_id']}")

# Convenience functions for common use cases
def get_current_admin_id() -> Optional[int]:
    """Convenience function to get current admin ID"""
    return AdminContext.get_current_admin_id()

def require_admin_id() -> int:
    """Convenience function to get admin ID or raise exception"""
    return AdminContext.require_admin_id()

def get_admin_context() -> Dict[str, Any]:
    """Convenience function to get full admin context"""
    return AdminContext.get_admin_context()

def create_audit_entry(action: str, details: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to create audit log entry"""
    return AdminAuditContext.create_audit_log_entry(action, details, meta)

def log_admin_action(session, action: str, details: str, meta: Optional[Dict[str, Any]] = None):
    """Convenience function to log admin action"""
    return AdminAuditContext.log_admin_action(session, action, details, meta)
