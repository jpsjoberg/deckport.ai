"""
IP-based access control for admin endpoints
Implements allowlist/blocklist functionality with CIDR support
"""

import os
import ipaddress
import logging
from typing import List, Set, Optional
from functools import wraps
from flask import request, jsonify
from shared.security.audit_logger import AdminAuditLogger

logger = logging.getLogger(__name__)

class IPAccessControl:
    """IP-based access control system"""
    
    def __init__(self):
        # Load IP configurations from environment
        self.admin_ip_allowlist = self._parse_ip_list(
            os.getenv("ADMIN_IP_ALLOWLIST", "")
        )
        self.admin_ip_blocklist = self._parse_ip_list(
            os.getenv("ADMIN_IP_BLOCKLIST", "")
        )
        
        # Default to allow all if no allowlist specified
        self.allowlist_enabled = bool(self.admin_ip_allowlist)
        
        logger.info(f"IP Access Control initialized - Allowlist: {self.allowlist_enabled}, "
                   f"Allowed IPs: {len(self.admin_ip_allowlist)}, "
                   f"Blocked IPs: {len(self.admin_ip_blocklist)}")
    
    def _parse_ip_list(self, ip_string: str) -> List[ipaddress.IPv4Network]:
        """Parse comma-separated IP addresses and CIDR blocks"""
        if not ip_string.strip():
            return []
        
        networks = []
        for ip_str in ip_string.split(','):
            ip_str = ip_str.strip()
            if not ip_str:
                continue
            
            try:
                # Handle single IPs and CIDR blocks
                if '/' not in ip_str:
                    ip_str += '/32'  # Single IP becomes /32 network
                
                network = ipaddress.IPv4Network(ip_str, strict=False)
                networks.append(network)
                logger.info(f"Added IP network to access control: {network}")
                
            except ipaddress.AddressValueError as e:
                logger.warning(f"Invalid IP address/network '{ip_str}': {e}")
        
        return networks
    
    def is_ip_allowed(self, ip_address: str) -> tuple:
        """
        Check if IP address is allowed to access admin endpoints
        
        Returns:
            (allowed: bool, reason: str)
        """
        try:
            ip = ipaddress.IPv4Address(ip_address)
            
            # Check blocklist first (takes precedence)
            for blocked_network in self.admin_ip_blocklist:
                if ip in blocked_network:
                    return False, f"IP {ip_address} is in blocklist ({blocked_network})"
            
            # If allowlist is enabled, check if IP is in allowlist
            if self.allowlist_enabled:
                for allowed_network in self.admin_ip_allowlist:
                    if ip in allowed_network:
                        return True, f"IP {ip_address} is in allowlist ({allowed_network})"
                
                return False, f"IP {ip_address} is not in allowlist"
            
            # If no allowlist, allow all IPs (except blocked ones)
            return True, "No allowlist configured, IP allowed"
            
        except ipaddress.AddressValueError:
            return False, f"Invalid IP address format: {ip_address}"
    
    def get_client_ip(self) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_ip = request.environ.get('HTTP_X_FORWARDED_FOR')
        if forwarded_ip:
            # Take the first IP if multiple are present
            return forwarded_ip.split(',')[0].strip()
        
        # Check other common headers
        real_ip = request.environ.get('HTTP_X_REAL_IP')
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection IP
        return request.remote_addr or '127.0.0.1'
    
    def add_to_allowlist(self, ip_or_network: str) -> bool:
        """Add IP or network to allowlist (runtime modification)"""
        try:
            if '/' not in ip_or_network:
                ip_or_network += '/32'
            
            network = ipaddress.IPv4Network(ip_or_network, strict=False)
            
            if network not in self.admin_ip_allowlist:
                self.admin_ip_allowlist.append(network)
                self.allowlist_enabled = True
                logger.info(f"Added {network} to admin IP allowlist")
                return True
            
            return False  # Already in list
            
        except ipaddress.AddressValueError as e:
            logger.error(f"Invalid IP/network for allowlist: {e}")
            return False
    
    def add_to_blocklist(self, ip_or_network: str) -> bool:
        """Add IP or network to blocklist (runtime modification)"""
        try:
            if '/' not in ip_or_network:
                ip_or_network += '/32'
            
            network = ipaddress.IPv4Network(ip_or_network, strict=False)
            
            if network not in self.admin_ip_blocklist:
                self.admin_ip_blocklist.append(network)
                logger.info(f"Added {network} to admin IP blocklist")
                return True
            
            return False  # Already in list
            
        except ipaddress.AddressValueError as e:
            logger.error(f"Invalid IP/network for blocklist: {e}")
            return False
    
    def remove_from_allowlist(self, ip_or_network: str) -> bool:
        """Remove IP or network from allowlist"""
        try:
            if '/' not in ip_or_network:
                ip_or_network += '/32'
            
            network = ipaddress.IPv4Network(ip_or_network, strict=False)
            
            if network in self.admin_ip_allowlist:
                self.admin_ip_allowlist.remove(network)
                logger.info(f"Removed {network} from admin IP allowlist")
                return True
            
            return False  # Not in list
            
        except ipaddress.AddressValueError as e:
            logger.error(f"Invalid IP/network for allowlist removal: {e}")
            return False
    
    def remove_from_blocklist(self, ip_or_network: str) -> bool:
        """Remove IP or network from blocklist"""
        try:
            if '/' not in ip_or_network:
                ip_or_network += '/32'
            
            network = ipaddress.IPv4Network(ip_or_network, strict=False)
            
            if network in self.admin_ip_blocklist:
                self.admin_ip_blocklist.remove(network)
                logger.info(f"Removed {network} from admin IP blocklist")
                return True
            
            return False  # Not in list
            
        except ipaddress.AddressValueError as e:
            logger.error(f"Invalid IP/network for blocklist removal: {e}")
            return False
    
    def get_access_lists(self) -> dict:
        """Get current allowlist and blocklist"""
        return {
            'allowlist_enabled': self.allowlist_enabled,
            'allowlist': [str(network) for network in self.admin_ip_allowlist],
            'blocklist': [str(network) for network in self.admin_ip_blocklist]
        }

# Global IP access control instance
ip_access_control = IPAccessControl()

def ip_restrict(f):
    """
    Decorator to restrict admin endpoints by IP address
    
    Usage:
        @ip_restrict
        def admin_endpoint():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = ip_access_control.get_client_ip()
        allowed, reason = ip_access_control.is_ip_allowed(client_ip)
        
        if not allowed:
            # Log security event
            AdminAuditLogger.log_security_event(
                'ip_access_denied',
                'high',
                {
                    'client_ip': client_ip,
                    'reason': reason,
                    'endpoint': request.endpoint,
                    'method': request.method
                }
            )
            
            logger.warning(f"IP access denied for {client_ip}: {reason}")
            
            return jsonify({
                'error': 'Access denied',
                'message': 'Your IP address is not authorized to access this resource'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
