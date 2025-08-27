"""
Device authentication routes for console hardware
"""

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError
from shared.auth.jwt_handler import create_device_token
from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleStatus
# from shared.utils.crypto import verify_signature  # TODO: Implement signature verification
import hashlib
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import logging

logger = logging.getLogger(__name__)

device_auth_bp = Blueprint('device_auth', __name__, url_prefix='/v1/auth/device')

@device_auth_bp.route('/register', methods=['POST'])
def register_device():
    """Register a new console device"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    device_uid = data.get('device_uid', '').strip()
    public_key_pem = data.get('public_key', '').strip()
    
    if not device_uid:
        return jsonify({"error": "device_uid required"}), 400
    
    if not public_key_pem:
        return jsonify({"error": "public_key required"}), 400
    
    try:
        with SessionLocal() as session:
            # Check if device already exists
            existing_device = session.query(Console).filter(Console.device_uid == device_uid).first()
            if existing_device:
                if existing_device.status == ConsoleStatus.active:
                    return jsonify({"error": "Device already registered and active"}), 409
                elif existing_device.status == ConsoleStatus.pending:
                    return jsonify({"status": "pending", "message": "Registration pending admin approval"}), 200
                else:
                    return jsonify({"error": "Device registration rejected"}), 403
            
            # Validate public key format
            try:
                # Try to load as public key first
                try:
                    serialization.load_pem_public_key(public_key_pem.encode())
                except Exception:
                    # If that fails, try to load as private key and extract public key
                    private_key = serialization.load_pem_private_key(
                        public_key_pem.encode(), 
                        password=None
                    )
                    # Extract public key from private key
                    public_key = private_key.public_key()
                    public_key_pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ).decode()
            except Exception as e:
                logger.error(f"Invalid key format: {e}")
                logger.error(f"Key data preview: {public_key_pem[:100]}...")
                return jsonify({"error": "Invalid public key format"}), 400
            
            # Create new console registration
            new_console = Console(
                device_uid=device_uid,
                public_key_pem=public_key_pem,
                status=ConsoleStatus.pending
            )
            
            session.add(new_console)
            session.commit()
            
            return jsonify({
                "status": "pending",
                "message": "Device registration submitted for admin approval",
                "device_uid": device_uid
            }), 201
            
    except IntegrityError:
        return jsonify({"error": "Device already registered"}), 409
    except Exception as e:
        logger.error(f"Device registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@device_auth_bp.route('/login', methods=['POST'])
def login_device():
    """Authenticate a registered device using signed nonce"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    device_uid = data.get('device_uid', '').strip()
    nonce = data.get('nonce', '').strip()
    signature = data.get('signature', '').strip()
    
    if not all([device_uid, nonce, signature]):
        return jsonify({"error": "device_uid, nonce, and signature required"}), 400
    
    try:
        with SessionLocal() as session:
            # Find the device
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            if not console:
                return jsonify({"error": "Device not found"}), 404
            
            if console.status != ConsoleStatus.active:
                if console.status == ConsoleStatus.pending:
                    return jsonify({"error": "Device pending admin approval"}), 403
                else:
                    return jsonify({"error": "Device not approved"}), 403
            
            if not console.public_key_pem:
                return jsonify({"error": "Device public key not found"}), 500
            
            # Verify the signature
            try:
                # Load the public key
                public_key = serialization.load_pem_public_key(console.public_key_pem.encode())
                
                # Decode the signature and nonce
                nonce_bytes = nonce.encode('utf-8')
                signature_bytes = base64.b64decode(signature)
                
                # Verify signature
                public_key.verify(
                    signature_bytes,
                    nonce_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                
            except (InvalidSignature, Exception) as e:
                return jsonify({"error": "Invalid signature"}), 401
            
            # Create device JWT token
            device_token = create_device_token(device_uid, console.id)
            
            return jsonify({
                "access_token": device_token,
                "token_type": "bearer",
                "expires_in": 86400,  # 24 hours
                "device_id": console.id
            })
            
    except Exception as e:
        return jsonify({"error": "Authentication failed"}), 500

@device_auth_bp.route('/status', methods=['GET'])
def device_status():
    """Get device status (requires device authentication)"""
    # This would use device auth middleware when implemented
    device_uid = request.args.get('device_uid')
    
    if not device_uid:
        return jsonify({"error": "device_uid required"}), 400
    
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            if not console:
                return jsonify({"error": "Device not found"}), 404
            
            return jsonify({
                "device_uid": console.device_uid,
                "status": console.status.value,
                "registered_at": console.registered_at.isoformat(),
                "owner_player_id": console.owner_player_id
            })
            
    except Exception as e:
        return jsonify({"error": "Status check failed"}), 500
