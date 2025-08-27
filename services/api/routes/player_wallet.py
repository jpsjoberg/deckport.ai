"""
Player wallet management routes
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.base import Player
from shared.models.tournaments import (
    PlayerWallet, WalletTransaction, TransactionType
)
from shared.auth.decorators import player_required
from stripe_service import stripe_service
import logging

logger = logging.getLogger(__name__)

player_wallet_bp = Blueprint('player_wallet', __name__, url_prefix='/v1/wallet')

@player_wallet_bp.route('/', methods=['GET'])
@player_required
def get_wallet():
    """Get player's wallet information"""
    try:
        with SessionLocal() as session:
            player_id = g.user_id
            
            # Get or create wallet
            wallet = session.query(PlayerWallet).filter(PlayerWallet.player_id == player_id).first()
            
            if not wallet:
                # Create wallet for new player
                wallet = PlayerWallet(
                    player_id=player_id,
                    balance=Decimal('0.00'),
                    currency='USD'
                )
                session.add(wallet)
                session.commit()
                session.refresh(wallet)
            
            # Get recent transactions
            recent_transactions = session.query(WalletTransaction).filter(
                WalletTransaction.wallet_id == wallet.id
            ).order_by(desc(WalletTransaction.created_at)).limit(10).all()
            
            transactions = []
            for tx in recent_transactions:
                transactions.append({
                    'id': tx.id,
                    'type': tx.transaction_type.value,
                    'amount': float(tx.amount),
                    'currency': tx.currency,
                    'status': tx.status.value,
                    'description': tx.description,
                    'balance_before': float(tx.balance_before),
                    'balance_after': float(tx.balance_after),
                    'created_at': tx.created_at.isoformat(),
                    'processed_at': tx.processed_at.isoformat() if tx.processed_at else None
                })
            
            wallet_data = {
                'id': wallet.id,
                'balance': float(wallet.balance),
                'currency': wallet.currency,
                'is_active': wallet.is_active,
                'daily_deposit_limit': float(wallet.daily_deposit_limit) if wallet.daily_deposit_limit else None,
                'daily_withdrawal_limit': float(wallet.daily_withdrawal_limit) if wallet.daily_withdrawal_limit else None,
                'recent_transactions': transactions,
                'created_at': wallet.created_at.isoformat(),
                'updated_at': wallet.updated_at.isoformat()
            }
            
            return jsonify(wallet_data)
            
    except Exception as e:
        logger.error(f"Error getting wallet: {e}")
        return jsonify({'error': 'Failed to retrieve wallet information'}), 500

@player_wallet_bp.route('/deposit', methods=['POST'])
@player_required
def create_deposit():
    """Create a deposit using Stripe"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        amount = data.get('amount')
        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        with SessionLocal() as session:
            player_id = g.user_id
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # Get or create wallet
            wallet = session.query(PlayerWallet).filter(PlayerWallet.player_id == player_id).first()
            if not wallet:
                wallet = PlayerWallet(
                    player_id=player_id,
                    balance=Decimal('0.00'),
                    currency='USD'
                )
                session.add(wallet)
                session.commit()
                session.refresh(wallet)
            
            # Check daily deposit limit
            if wallet.daily_deposit_limit:
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                today_deposits = session.query(func.coalesce(func.sum(WalletTransaction.amount), 0)).filter(
                    WalletTransaction.wallet_id == wallet.id,
                    WalletTransaction.transaction_type == WalletTransactionType.DEPOSIT,
                    WalletTransaction.status == WalletTransactionStatus.COMPLETED,
                    WalletTransaction.created_at >= today_start
                ).scalar() or 0
                
                if today_deposits + Decimal(str(amount)) > wallet.daily_deposit_limit:
                    return jsonify({'error': f'Daily deposit limit exceeded. Limit: ${wallet.daily_deposit_limit}, Used: ${today_deposits}'}), 400
            
            # Create Stripe payment intent
            stripe_result = stripe_service.create_payment_intent(
                amount=Decimal(str(amount)),
                currency='usd',
                metadata={
                    'type': 'wallet_deposit',
                    'player_id': str(player_id),
                    'wallet_id': str(wallet.id)
                }
            )
            
            if not stripe_result.get('success'):
                return jsonify({'error': 'Failed to create payment intent'}), 500
            
            # Create pending transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                transaction_type=WalletTransactionType.DEPOSIT,
                amount=Decimal(str(amount)),
                currency='USD',
                status=WalletTransactionStatus.PENDING,
                description=f'Wallet deposit - ${amount}',
                payment_reference=stripe_result['payment_intent_id'],
                balance_before=wallet.balance,
                balance_after=wallet.balance  # Will be updated when payment completes
            )
            
            session.add(transaction)
            session.commit()
            
            return jsonify({
                'success': True,
                'transaction_id': transaction.id,
                'client_secret': stripe_result['client_secret'],
                'payment_intent_id': stripe_result['payment_intent_id']
            })
            
    except Exception as e:
        logger.error(f"Error creating deposit: {e}")
        return jsonify({'error': 'Failed to create deposit'}), 500

@player_wallet_bp.route('/withdraw', methods=['POST'])
@player_required
def create_withdrawal():
    """Create a withdrawal request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        amount = data.get('amount')
        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        with SessionLocal() as session:
            player_id = g.user_id
            
            # Get wallet
            wallet = session.query(PlayerWallet).filter(PlayerWallet.player_id == player_id).first()
            if not wallet:
                return jsonify({'error': 'Wallet not found'}), 404
            
            # Check balance
            if wallet.balance < Decimal(str(amount)):
                return jsonify({'error': f'Insufficient balance. Available: ${wallet.balance}'}), 400
            
            # Check daily withdrawal limit
            if wallet.daily_withdrawal_limit:
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                today_withdrawals = session.query(func.coalesce(func.sum(WalletTransaction.amount), 0)).filter(
                    WalletTransaction.wallet_id == wallet.id,
                    WalletTransaction.transaction_type == WalletTransactionType.WITHDRAWAL,
                    WalletTransaction.status == WalletTransactionStatus.COMPLETED,
                    WalletTransaction.created_at >= today_start
                ).scalar() or 0
                
                if today_withdrawals + Decimal(str(amount)) > wallet.daily_withdrawal_limit:
                    return jsonify({'error': f'Daily withdrawal limit exceeded. Limit: ${wallet.daily_withdrawal_limit}, Used: ${today_withdrawals}'}), 400
            
            # Create withdrawal transaction (pending admin approval)
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                transaction_type=WalletTransactionType.WITHDRAWAL,
                amount=Decimal(str(amount)),
                currency='USD',
                status=WalletTransactionStatus.PENDING,
                description=f'Wallet withdrawal - ${amount}',
                balance_before=wallet.balance,
                balance_after=wallet.balance - Decimal(str(amount))
            )
            
            # Update wallet balance (hold the funds)
            wallet.balance -= Decimal(str(amount))
            wallet.updated_at = datetime.now(timezone.utc)
            
            session.add(transaction)
            session.commit()
            
            logger.info(f"Withdrawal request created: ${amount} for player {player_id}")
            
            return jsonify({
                'success': True,
                'transaction_id': transaction.id,
                'message': f'Withdrawal request for ${amount} submitted. Processing may take 1-3 business days.'
            })
            
    except Exception as e:
        logger.error(f"Error creating withdrawal: {e}")
        return jsonify({'error': 'Failed to create withdrawal'}), 500

@player_wallet_bp.route('/transactions', methods=['GET'])
@player_required
def get_transactions():
    """Get wallet transaction history"""
    try:
        with SessionLocal() as session:
            player_id = g.user_id
            
            # Get wallet
            wallet = session.query(PlayerWallet).filter(PlayerWallet.player_id == player_id).first()
            if not wallet:
                return jsonify({'transactions': [], 'total': 0})
            
            # Pagination
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            offset = (page - 1) * per_page
            
            # Filter by type if specified
            transaction_type = request.args.get('type')
            query = session.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet.id)
            
            if transaction_type:
                try:
                    query = query.filter(WalletTransaction.transaction_type == WalletTransactionType(transaction_type))
                except ValueError:
                    return jsonify({'error': 'Invalid transaction type'}), 400
            
            # Get total count
            total = query.count()
            
            # Get transactions
            transactions = query.order_by(desc(WalletTransaction.created_at)).offset(offset).limit(per_page).all()
            
            transaction_list = []
            for tx in transactions:
                transaction_list.append({
                    'id': tx.id,
                    'type': tx.transaction_type.value,
                    'amount': float(tx.amount),
                    'currency': tx.currency,
                    'status': tx.status.value,
                    'description': tx.description,
                    'balance_before': float(tx.balance_before),
                    'balance_after': float(tx.balance_after),
                    'payment_reference': tx.payment_reference,
                    'created_at': tx.created_at.isoformat(),
                    'processed_at': tx.processed_at.isoformat() if tx.processed_at else None
                })
            
            return jsonify({
                'transactions': transaction_list,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            })
            
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'error': 'Failed to retrieve transactions'}), 500
