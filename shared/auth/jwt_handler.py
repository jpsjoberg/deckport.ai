"""
JWT token handling for user authentication
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

def create_access_token(user_id: int, email: str, additional_claims: Dict = None) -> str:
    """Create a JWT access token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_device_token(device_uid: str, console_id: int, additional_claims: Dict = None) -> str:
    """Create a JWT token for console devices"""
    payload = {
        "device_uid": device_uid,
        "console_id": console_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
        "type": "device"
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user_id(token: str) -> Optional[int]:
    """Extract user ID from token"""
    payload = verify_token(token)
    if payload and payload.get("type") == "access":
        return payload.get("user_id")
    return None

def get_current_device_uid(token: str) -> Optional[str]:
    """Extract device UID from device token"""
    payload = verify_token(token)
    if payload and payload.get("type") == "device":
        return payload.get("device_uid")
    return None

def get_console_id(token: str) -> Optional[int]:
    """Extract console ID from device token"""
    payload = verify_token(token)
    if payload and payload.get("type") == "device":
        return payload.get("console_id")
    return None

def create_admin_token(user_id: int, email: str, additional_claims: Dict = None) -> str:
    """Create a JWT access token for admin users"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_admin_token(token: str) -> Optional[Dict]:
    """Verify and decode an admin JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("role") == "admin" and payload.get("type") == "access":
            return {
                "admin_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role")
            }
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
