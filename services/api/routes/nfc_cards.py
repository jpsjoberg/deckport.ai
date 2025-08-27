"""
NFC Card Management API Routes
Handles NTAG 424 DNA card programming, activation, trading, and security
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import secrets
import re

from shared.database.connection import SessionLocal
from shared.models.nfc_trading_system import (
    EnhancedNFCCard, TradeOffer, CardAuction, TradingHistory,
    TradeStatus, TradeType, AuctionStatus, MarketplaceListingStatus
)
from shared.models.base import Player, Admin
from shared.auth.jwt_handler import verify_token, verify_admin_token
from shared.auth.decorators import admin_required, player_required
import logging
api_logger = logging.getLogger(__name__)

nfc_cards_bp = Blueprint('nfc_cards', __name__, url_prefix='/v1/nfc-cards')

# === ADMIN: CARD PROGRAMMING & BATCH MANAGEMENT ===

@nfc_cards_bp.route('/admin/batches', methods=['POST'])
@admin_required
def create_card_batch():
    """Create a new production batch"""
    data = request.get_json()
    
    try:
        with SessionLocal() as session:
            admin = session.query(Admin).filter(Admin.id == g.admin_id).first()
            
            batch = CardBatch(
                batch_code=data['batch_code'],
                product_sku=data['product_sku'],
                production_date=datetime.fromisoformat(data['production_date']),
                total_cards=data['total_cards'],
                created_by_admin_id=admin.id
            )
            
            session.add(batch)
            session.commit()
            
            api_logger.info(f"Created card batch {batch.batch_code} for {batch.total_cards} cards")
            
            return jsonify({
                "batch_id": batch.id,
                "batch_code": batch.batch_code,
                "total_cards": batch.total_cards,
                "status": "created"
            }), 201
            
    except Exception as e:
        api_logger.error(f"Failed to create card batch: {e}")
        return jsonify({"error": "Failed to create batch"}), 500

@nfc_cards_bp.route('/admin/program', methods=['POST'])
@admin_required
def program_card():
    """Program a single NFC card (called by local programming script)"""
    data = request.get_json()
    
    try:
        with SessionLocal() as session:
            # Check if card already exists
            existing_card = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.ntag_uid == data['ntag_uid']
            ).first()
            
            if existing_card:
                return jsonify({"error": "Card already programmed"}), 409
            
            # Create new card
            card = EnhancedNFCCard(
                ntag_uid=data['ntag_uid'],
                product_sku=data['product_sku'],
                serial_number=data.get('serial_number'),
                batch_id=data.get('batch_id'),
                security_level=SecurityLevel(data.get('security_level', 'NTAG424_DNA')),
                issuer_key_ref=data.get('issuer_key_ref'),
                status=NFCCardStatus.provisioned,
                provisioned_at=datetime.now(timezone.utc)
            )
            
            session.add(card)
            
            # Create activation code
            activation_code = generate_activation_code()
            activation_record = CardActivationCode(
                nfc_card_id=card.id,
                activation_code=activation_code,
                code_hash=hash_activation_code(activation_code),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365)  # 1 year expiry
            )
            
            session.add(activation_record)
            
            # Update batch statistics
            if card.batch_id:
                batch = session.query(CardBatch).filter(CardBatch.id == card.batch_id).first()
                if batch:
                    batch.cards_programmed += 1
            
            session.commit()
            
            api_logger.info(f"Programmed NFC card {card.ntag_uid}")
            
            return jsonify({
                "card_id": card.id,
                "ntag_uid": card.ntag_uid,
                "activation_code": activation_code,  # Only returned during programming
                "status": "programmed"
            }), 201
            
    except Exception as e:
        api_logger.error(f"Failed to program card: {e}")
        return jsonify({"error": "Failed to program card"}), 500

# === PLAYER: CARD ACTIVATION ===

@nfc_cards_bp.route('/activate', methods=['POST'])
@player_required
def activate_card():
    """Player activates their card with NFC tap + activation code"""
    data = request.get_json()
    nfc_uid = data.get('nfc_uid')
    activation_code = data.get('activation_code')
    
    if not nfc_uid or not activation_code:
        return jsonify({"error": "NFC UID and activation code required"}), 400
    
    try:
        with SessionLocal() as session:
            # Find card
            card = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.ntag_uid == nfc_uid
            ).first()
            
            if not card:
                log_security_event(session, None, "card_not_found", "error", {
                    "nfc_uid": nfc_uid,
                    "player_id": g.current_player.id
                })
                return jsonify({"error": "Card not found"}), 404
            
            # Check if already activated
            if card.status == NFCCardStatus.activated:
                return jsonify({"error": "Card already activated"}), 409
            
            # Verify activation code
            activation_record = session.query(CardActivationCode).filter(
                CardActivationCode.nfc_card_id == card.id,
                CardActivationCode.used_at.is_(None),
                CardActivationCode.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if not activation_record or not verify_activation_code(activation_code, activation_record.code_hash):
                log_security_event(session, card.id, "invalid_activation_code", "warning", {
                    "player_id": g.current_player.id,
                    "provided_code": activation_code[:2] + "****"  # Partial code for logging
                })
                return jsonify({"error": "Invalid or expired activation code"}), 400
            
            # Activate card
            card.status = NFCCardStatus.activated
            card.owner_player_id = g.current_player.id
            card.activated_at = datetime.now(timezone.utc)
            
            # Mark activation code as used
            activation_record.used_at = datetime.now(timezone.utc)
            activation_record.used_by_player_id = g.current_player.id
            
            # Create public page
            public_slug = generate_public_slug(card)
            public_page = CardPublicPage(
                nfc_card_id=card.id,
                public_slug=public_slug,
                is_public=True
            )
            session.add(public_page)
            
            # Update batch statistics
            if card.batch_id:
                batch = session.query(CardBatch).filter(CardBatch.id == card.batch_id).first()
                if batch:
                    batch.cards_activated += 1
            
            # Log successful activation
            log_security_event(session, card.id, "card_activated", "info", {
                "player_id": g.current_player.id,
                "activation_method": "nfc_tap_code"
            })
            
            session.commit()
            
            api_logger.info(f"Card {card.ntag_uid} activated by player {g.current_player.id}")
            
            return jsonify({
                "success": True,
                "card_id": card.id,
                "card_name": f"{card.product_sku} #{card.serial_number or card.id}",
                "public_url": f"/cards/public/{public_slug}",
                "activated_at": card.activated_at.isoformat()
            })
            
    except Exception as e:
        api_logger.error(f"Failed to activate card: {e}")
        return jsonify({"error": "Failed to activate card"}), 500

# === NFC AUTHENTICATION (Console) ===

@nfc_cards_bp.route('/authenticate', methods=['POST'])
def authenticate_card():
    """Authenticate NFC card for console usage (NTAG 424 DNA security)"""
    data = request.get_json()
    nfc_uid = data.get('nfc_uid')
    challenge = data.get('challenge')  # Base64 encoded challenge
    response = data.get('response')    # Base64 encoded card response
    console_id = data.get('console_id')
    
    # Verify device authentication
    device_uid = request.headers.get('X-Device-UID')
    if not device_uid:
        return jsonify({"error": "Device authentication required"}), 401
    
    try:
        with SessionLocal() as session:
            # Find card
            card = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.ntag_uid == nfc_uid
            ).first()
            
            if not card:
                log_security_event(session, None, "auth_card_not_found", "warning", {
                    "nfc_uid": nfc_uid,
                    "console_id": console_id,
                    "device_uid": device_uid
                })
                return jsonify({"error": "Card not found"}), 404
            
            # Verify card is activated
            if card.status != NFCCardStatus.activated:
                log_security_event(session, card.id, "auth_card_not_activated", "warning", {
                    "status": card.status.value,
                    "console_id": console_id
                })
                return jsonify({"error": "Card not activated"}), 403
            
            # Verify cryptographic response (NTAG 424 DNA)
            auth_valid = verify_ntag424_response(card, challenge, response)
            
            if auth_valid:
                # Update counters
                card.tap_counter += 1
                card.auth_counter += 1
                
                # Log successful authentication
                log_security_event(session, card.id, "auth_success", "info", {
                    "console_id": console_id,
                    "player_id": card.owner_player_id,
                    "tap_count": card.tap_counter
                })
                
                session.commit()
                
                # Return card and player data
                return jsonify({
                    "authenticated": True,
                    "card_data": {
                        "id": card.id,
                        "product_sku": card.product_sku,
                        "serial_number": card.serial_number,
                        "tap_counter": card.tap_counter
                    },
                    "player_data": {
                        "id": card.owner_player.id,
                        "username": card.owner_player.username if card.owner_player else None,
                        "elo_rating": card.owner_player.elo_rating if card.owner_player else None
                    } if card.owner_player else None,
                    "session_id": generate_session_id(card, console_id)
                })
            else:
                # Log failed authentication (potential cloning attempt)
                log_security_event(session, card.id, "auth_failed", "error", {
                    "console_id": console_id,
                    "challenge": challenge[:16] + "...",  # Partial challenge for logging
                    "response": response[:16] + "...",    # Partial response for logging
                    "potential_clone": True
                })
                
                session.commit()
                
                return jsonify({"error": "Authentication failed"}), 401
                
    except Exception as e:
        api_logger.error(f"Failed to authenticate card: {e}")
        return jsonify({"error": "Authentication failed"}), 500

# === CARD TRADING ===

@nfc_cards_bp.route('/trade/initiate', methods=['POST'])
@player_required
def initiate_trade():
    """Player initiates a card trade"""
    data = request.get_json()
    nfc_card_id = data.get('nfc_card_id')
    asking_price = data.get('asking_price', 0)
    
    try:
        with SessionLocal() as session:
            # Verify player owns the card
            card = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.id == nfc_card_id,
                EnhancedNFCCard.owner_player_id == g.current_player.id,
                EnhancedNFCCard.status == NFCCardStatus.activated
            ).first()
            
            if not card:
                return jsonify({"error": "Card not found or not owned"}), 404
            
            # Check if card is already being traded
            existing_trade = session.query(CardTrade).filter(
                CardTrade.nfc_card_id == nfc_card_id,
                CardTrade.status == TradeStatus.pending
            ).first()
            
            if existing_trade:
                return jsonify({"error": "Card already being traded"}), 409
            
            # Generate trade code
            trade_code = generate_trade_code()
            
            # Create trade
            trade = CardTrade(
                seller_player_id=g.current_player.id,
                nfc_card_id=nfc_card_id,
                trade_code=trade_code,
                asking_price=Decimal(str(asking_price)) if asking_price else None,
                status=TradeStatus.pending,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            
            session.add(trade)
            
            # Update card status
            card.status = NFCCardStatus.traded
            
            session.commit()
            
            api_logger.info(f"Trade initiated for card {card.id} by player {g.current_player.id}")
            
            return jsonify({
                "trade_id": trade.id,
                "trade_code": trade_code,
                "asking_price": float(trade.asking_price) if trade.asking_price else 0,
                "expires_at": trade.expires_at.isoformat(),
                "instructions": "Share this trade code with the buyer"
            })
            
    except Exception as e:
        api_logger.error(f"Failed to initiate trade: {e}")
        return jsonify({"error": "Failed to initiate trade"}), 500

@nfc_cards_bp.route('/trade/complete', methods=['POST'])
@player_required
def complete_trade():
    """Buyer completes a card trade with NFC tap + trade code"""
    data = request.get_json()
    nfc_uid = data.get('nfc_uid')
    trade_code = data.get('trade_code')
    
    try:
        with SessionLocal() as session:
            # Find trade
            trade = session.query(CardTrade).filter(
                CardTrade.trade_code == trade_code,
                CardTrade.status == TradeStatus.pending,
                CardTrade.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if not trade:
                return jsonify({"error": "Invalid or expired trade"}), 404
            
            # Verify NFC card matches trade
            if trade.nfc_card.ntag_uid != nfc_uid:
                log_security_event(session, trade.nfc_card.id, "trade_card_mismatch", "warning", {
                    "trade_id": trade.id,
                    "expected_uid": trade.nfc_card.ntag_uid,
                    "provided_uid": nfc_uid,
                    "buyer_id": g.current_player.id
                })
                return jsonify({"error": "Card mismatch"}), 400
            
            # Prevent self-trading
            if trade.seller_player_id == g.current_player.id:
                return jsonify({"error": "Cannot trade with yourself"}), 400
            
            # Process payment if required
            if trade.asking_price and trade.asking_price > 0:
                payment_result = process_trade_payment(
                    buyer_id=g.current_player.id,
                    seller_id=trade.seller_player_id,
                    amount=trade.asking_price
                )
                if not payment_result:
                    return jsonify({"error": "Payment failed"}), 400
            
            # Transfer ownership
            card = trade.nfc_card
            old_owner_id = card.owner_player_id
            
            card.owner_player_id = g.current_player.id
            card.status = NFCCardStatus.activated
            
            # Complete trade
            trade.status = TradeStatus.completed
            trade.buyer_player_id = g.current_player.id
            trade.completed_at = datetime.now(timezone.utc)
            
            # Log trade completion
            log_security_event(session, card.id, "trade_completed", "info", {
                "trade_id": trade.id,
                "seller_id": old_owner_id,
                "buyer_id": g.current_player.id,
                "price": float(trade.asking_price) if trade.asking_price else 0
            })
            
            session.commit()
            
            api_logger.info(f"Trade {trade.id} completed - card {card.id} transferred to player {g.current_player.id}")
            
            return jsonify({
                "success": True,
                "card_name": f"{card.product_sku} #{card.serial_number or card.id}",
                "previous_owner": trade.seller.username,
                "price_paid": float(trade.asking_price) if trade.asking_price else 0,
                "completed_at": trade.completed_at.isoformat()
            })
            
    except Exception as e:
        api_logger.error(f"Failed to complete trade: {e}")
        return jsonify({"error": "Failed to complete trade"}), 500

# === PUBLIC CARD PAGES ===

@nfc_cards_bp.route('/public/<string:public_slug>', methods=['GET'])
def view_public_card(public_slug):
    """View public card page"""
    try:
        with SessionLocal() as session:
            public_page = session.query(CardPublicPage).filter(
                CardPublicPage.public_slug == public_slug,
                CardPublicPage.is_public == True
            ).first()
            
            if not public_page:
                return jsonify({"error": "Card not found"}), 404
            
            card = public_page.nfc_card
            
            # Update view count
            public_page.view_count += 1
            public_page.last_viewed_at = datetime.now(timezone.utc)
            session.commit()
            
            # Get card upgrades
            upgrades = session.query(CardUpgrade).filter(
                CardUpgrade.nfc_card_id == card.id
            ).order_by(CardUpgrade.upgraded_at.desc()).limit(10).all()
            
            return jsonify({
                "card": {
                    "product_sku": card.product_sku,
                    "serial_number": card.serial_number,
                    "tap_counter": card.tap_counter,
                    "activated_at": card.activated_at.isoformat() if card.activated_at else None
                },
                "owner": {
                    "username": card.owner_player.username if card.owner_player and public_page.show_owner else "Anonymous",
                    "elo_rating": card.owner_player.elo_rating if card.owner_player and public_page.show_stats else None
                } if card.owner_player else None,
                "upgrades": [
                    {
                        "type": upgrade.upgrade_type,
                        "level": upgrade.new_level,
                        "upgraded_at": upgrade.upgraded_at.isoformat()
                    } for upgrade in upgrades
                ] if public_page.show_history else [],
                "stats": {
                    "view_count": public_page.view_count,
                    "last_viewed": public_page.last_viewed_at.isoformat() if public_page.last_viewed_at else None
                }
            })
            
    except Exception as e:
        api_logger.error(f"Failed to view public card: {e}")
        return jsonify({"error": "Failed to load card"}), 500

# === UTILITY FUNCTIONS ===

def generate_activation_code() -> str:
    """Generate secure 8-digit activation code"""
    import random
    return f"{random.randint(10000000, 99999999)}"

def hash_activation_code(code: str) -> str:
    """Hash activation code for secure storage"""
    return hashlib.sha256(f"{code}:deckport_salt".encode()).hexdigest()

def verify_activation_code(provided_code: str, stored_hash: str) -> bool:
    """Verify activation code against stored hash"""
    return hash_activation_code(provided_code) == stored_hash

def generate_trade_code() -> str:
    """Generate unique 12-character trade code"""
    return secrets.token_urlsafe(9)[:12].upper()

def generate_public_slug(card) -> str:
    """Generate URL-friendly public slug for card"""
    base = f"{card.product_sku}-{card.id}"
    return re.sub(r'[^a-zA-Z0-9-]', '', base.lower())

def generate_session_id(card, console_id) -> str:
    """Generate session ID for authenticated card usage"""
    data = f"{card.id}:{console_id}:{datetime.now().timestamp()}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]

def verify_ntag424_response(card, challenge: str, response: str) -> bool:
    """Verify NTAG 424 DNA cryptographic response"""
    try:
        import base64
        from cryptography.hazmat.primitives import hashes, hmac
        from cryptography.hazmat.backends import default_backend
        
        # Decode challenge and response
        challenge_bytes = base64.b64decode(challenge)
        response_bytes = base64.b64decode(response)
        
        # Get card's cryptographic key from issuer_key_ref
        # In production, this would derive the key from master key + issuer_key_ref
        card_key = derive_card_key(card.issuer_key_ref)
        
        # Verify HMAC-SHA256 response
        h = hmac.HMAC(card_key, hashes.SHA256(), backend=default_backend())
        h.update(challenge_bytes)
        expected_response = h.finalize()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_response, response_bytes)
        
    except Exception as e:
        api_logger.error(f"NTAG 424 DNA verification failed: {e}")
        return False

def derive_card_key(issuer_key_ref: str) -> bytes:
    """Derive card's cryptographic key from issuer key reference"""
    try:
        # In production, this should use the same master key as the card programmer
        # For security, the master key should be stored in a secure key management system
        import os
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        
        # Get master key from environment or key management system
        master_key_hex = os.getenv("NFC_MASTER_KEY")
        if not master_key_hex:
            raise ValueError("NFC_MASTER_KEY not configured")
        
        master_key = bytes.fromhex(master_key_hex)
        
        # Derive card key using HKDF-like process
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(master_key)
        digest.update(issuer_key_ref.encode())
        digest.update(b"AUTH")  # Same purpose as in card programmer
        
        return digest.finalize()[:16]  # 128-bit key
        
    except Exception as e:
        api_logger.error(f"Card key derivation failed: {e}")
        raise

def process_trade_payment(buyer_id: int, seller_id: int, amount: Decimal) -> bool:
    """Process payment for card trade"""
    try:
        # In production, integrate with payment processor
        # This is a placeholder for payment processing logic
        
        if amount <= 0:
            api_logger.error("Invalid payment amount")
            return False
        
        # TODO: Implement actual payment processing
        # Example integrations:
        # - Stripe: stripe.PaymentIntent.create()
        # - PayPal: paypalrestsdk.Payment.create()
        # - Crypto: Web3 smart contract interaction
        # - Internal credits: Database balance transfer
        
        # For now, log the transaction attempt
        api_logger.info(f"Payment processing required: ${amount} from user {buyer_id} to user {seller_id}")
        api_logger.warning("Payment processing not implemented - trade will fail")
        
        # Return False to prevent trades until payment system is implemented
        return False
        
    except Exception as e:
        api_logger.error(f"Payment processing error: {e}")
        return False

def log_security_event(session, card_id: int, event_type: str, severity: str, details: dict):
    """Log security event"""
    log_entry = NFCSecurityLog(
        nfc_card_id=card_id,
        event_type=event_type,
        severity=severity,
        console_id=details.get('console_id'),
        player_id=details.get('player_id'),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        error_details=details
    )
    session.add(log_entry)
