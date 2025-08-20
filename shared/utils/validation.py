"""
Data validation utilities
"""

import re
from typing import Optional

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(EMAIL_REGEX.match(email))

def validate_password(password: str) -> Optional[str]:
    """Validate password strength, return error message if invalid"""
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return "Password must contain at least one letter"
    
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number"
    
    return None

def validate_display_name(name: str) -> Optional[str]:
    """Validate display name, return error message if invalid"""
    if not name or len(name.strip()) < 2:
        return "Display name must be at least 2 characters long"
    
    if len(name) > 50:
        return "Display name must be less than 50 characters"
    
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
        return "Display name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return None

def validate_username(username: str) -> Optional[str]:
    """Validate username, return error message if invalid"""
    if not username or len(username.strip()) < 3:
        return "Username must be at least 3 characters long"
    
    if len(username) > 30:
        return "Username must be less than 30 characters"
    
    if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
        return "Username can only contain letters, numbers, hyphens, and underscores"
    
    if username.startswith(('-', '_')) or username.endswith(('-', '_')):
        return "Username cannot start or end with hyphens or underscores"
    
    return None

def validate_phone_number(phone: str) -> Optional[str]:
    """Validate phone number, return error message if invalid"""
    if not phone:
        return None  # Phone is optional
    
    # Remove common formatting characters
    cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if it's all digits after cleaning
    if not cleaned_phone.isdigit():
        return "Phone number can only contain digits, spaces, hyphens, parentheses, and plus signs"
    
    # Check length (international format: 7-15 digits)
    if len(cleaned_phone) < 7 or len(cleaned_phone) > 15:
        return "Phone number must be between 7 and 15 digits"
    
    return None
