"""
Authentication routes
"""

import logging
from flask import Blueprint, request, jsonify
from shared.auth.jwt_handler import create_access_token
from shared.utils.crypto import hash_password, verify_password
from shared.utils.validation import validate_email, validate_password, validate_display_name, validate_username, validate_phone_number
from shared.database.connection import SessionLocal
from shared.models.base import Player

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/v1/auth')

@auth_bp.route('/player/register', methods=['POST'])
def register():
    """Register a new player"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    display_name = data.get('display_name', '').strip()
    username = data.get('username', '').strip()
    phone_number = data.get('phone_number', '').strip()
    
    # Validation
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    password_error = validate_password(password)
    if password_error:
        return jsonify({"error": password_error}), 400
    
    if display_name:
        name_error = validate_display_name(display_name)
        if name_error:
            return jsonify({"error": name_error}), 400
    else:
        display_name = email.split('@')[0]  # Default display name
    
    # Validate username if provided
    if username:
        username_error = validate_username(username)
        if username_error:
            return jsonify({"error": username_error}), 400
    
    # Validate phone number if provided
    if phone_number:
        phone_error = validate_phone_number(phone_number)
        if phone_error:
            return jsonify({"error": phone_error}), 400
    
    try:
        with SessionLocal() as session:
            # Check if email already exists
            existing_user = session.query(Player).filter(Player.email == email).first()
            if existing_user:
                return jsonify({"error": "Email already registered"}), 409
            
            # Check if username already exists (if provided)
            if username:
                existing_username = session.query(Player).filter(Player.username == username).first()
                if existing_username:
                    return jsonify({"error": "Username already taken"}), 409
            
            # Create new user
            hashed_password = hash_password(password)
            new_user = Player(
                email=email,
                display_name=display_name,
                username=username if username else None,
                phone_number=phone_number if phone_number else None,
                password_hash=hashed_password
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            # Create access token
            access_token = create_access_token(new_user.id, email)
            
            return jsonify({
                "access_token": access_token,
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "display_name": new_user.display_name,
                    "username": new_user.username,
                    "phone_number": new_user.phone_number,
                    "avatar_url": new_user.avatar_url
                }
            }), 201
            
    except Exception as e:
        return jsonify({"error": "Registration failed"}), 500

@auth_bp.route('/player/login', methods=['POST'])
def login():
    """Login a player"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    try:
        with SessionLocal() as session:
            # Find user
            user = session.query(Player).filter(Player.email == email).first()
            if not user or not verify_password(password, user.password_hash):
                return jsonify({"error": "Invalid email or password"}), 401
            
            # Create access token
            access_token = create_access_token(user.id, email)
            
            return jsonify({
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "avatar_url": user.avatar_url,
                    "elo_rating": user.elo_rating
                }
            })
            
    except Exception as e:
        return jsonify({"error": "Login failed"}), 500

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Login an admin user using proper Admin model"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    try:
        with SessionLocal() as session:
            # Find admin user in Admin table
            from shared.models.base import Admin
            admin = session.query(Admin).filter(Admin.email == email).first()
            
            if not admin:
                return jsonify({"error": "Invalid email or password"}), 401
            
            # Check if admin account is active
            if not admin.is_active:
                return jsonify({"error": "Admin account is disabled"}), 403
            
            # Verify password
            if not verify_password(password, admin.password_hash):
                return jsonify({"error": "Invalid email or password"}), 401
            
            # Update last login timestamp
            from datetime import datetime, timezone
            admin.last_login = datetime.now(timezone.utc)
            session.commit()
            
            # Create admin access token with role
            from shared.auth.jwt_handler import create_admin_token
            access_token = create_admin_token(admin.id, admin.email, {
                "username": admin.username,
                "is_super_admin": admin.is_super_admin
            })
            
            return jsonify({
                "access_token": access_token,
                "admin": {
                    "id": admin.id,
                    "username": admin.username,
                    "email": admin.email,
                    "is_super_admin": admin.is_super_admin,
                    "role": "admin"
                }
            })
            
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return jsonify({"error": "Admin login failed"}), 500
