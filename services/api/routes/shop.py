"""
Shop Customer API Routes
Handles customer-facing shop operations: browsing products, checkout, orders
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload
import logging
import secrets
import string
import json
import hashlib

from shared.database.connection import SessionLocal
from shared.models.shop import (
    ShopProduct, ShopOrder, ShopOrderItem, ProductDiscount, GiftCard, GiftCardUsage,
    OrderStatus, ProductType, ProductStatus, PaymentMethod
)
from shared.models.base import Player
from shared.auth.decorators import player_required, optional_player_auth
from stripe_service import stripe_service

logger = logging.getLogger(__name__)

# Configuration
import os
SESSION_SECRET_KEY = os.getenv("SHOP_SESSION_SECRET", "dev-session-secret-change-in-production")

shop_bp = Blueprint('shop', __name__, url_prefix='/v1/shop')

# === PUBLIC SHOP BROWSING ===

@shop_bp.route('/products', methods=['GET'])
def get_shop_products():
    """Get public shop products with filtering and pagination"""
    try:
        with SessionLocal() as session:
            # Get query parameters
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 20)), 100)
            search = request.args.get('search', '').strip()
            
            # Use raw SQL to avoid model mismatch issues
            from sqlalchemy import text
            
            # Build base query
            base_query = """
                SELECT id, sku, name, description, price, product_type, 
                       is_featured, created_at, status
                FROM shop_products 
                WHERE status = 'active'
            """
            
            params = {}
            
            # Add search filter if provided
            if search:
                base_query += " AND (name ILIKE :search OR description ILIKE :search)"
                params['search'] = f'%{search}%'
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS filtered_products"
            total = session.execute(text(count_query), params).scalar()
            
            # Add pagination
            base_query += " ORDER BY is_featured DESC, created_at DESC LIMIT :limit OFFSET :offset"
            params['limit'] = page_size
            params['offset'] = (page - 1) * page_size
            
            # Execute query
            result = session.execute(text(base_query), params)
            products = result.fetchall()
            
            # Format response
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'sku': product.sku,
                    'name': product.name,
                    'description': product.description,
                    'price': float(product.price),
                    'product_type': product.product_type,
                    'is_featured': product.is_featured,
                    'status': product.status
                })
            
            total_pages = (total + page_size - 1) // page_size
            
            return jsonify({
                'products': products_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            })
            
    except Exception as e:
        logger.error(f"Error getting shop products: {e}")
        return jsonify({'error': 'Failed to get products'}), 500

@shop_bp.route('/products/<product_sku>', methods=['GET'])
def get_product_details(product_sku):
    """Get detailed product information"""
    try:
        with SessionLocal() as session:
            product = session.query(ShopProduct).filter(
                ShopProduct.sku == product_sku,
                ShopProduct.status == 'active',
                ShopProduct.is_active == True
            ).options(joinedload(ShopProduct.category)).first()
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            # Check stock availability
            is_available = True
            if product.track_inventory:
                is_available = product.stock_quantity > 0
            
            return jsonify({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'slug': product.slug,
                'description': product.description,
                'short_description': product.short_description,
                'price': float(product.price),
                'compare_at_price': float(product.compare_at_price) if product.compare_at_price else None,
                'currency': product.currency,
                'product_type': product.product_type,
                'category_name': product.category.name if product.category else None,
                'category_id': product.category_id,
                'image_url': product.image_url,
                'gallery_images': product.gallery_images or [],
                'meta_title': product.meta_title,
                'meta_description': product.meta_description,
                'tags': product.tags or [],
                'card_skus': product.card_skus or [],
                'is_featured': product.is_featured,
                'is_bestseller': product.is_bestseller,
                'is_available': is_available,
                'stock_quantity': product.stock_quantity if product.track_inventory else None,
                'low_stock_threshold': product.low_stock_threshold if product.track_inventory else None
            })
            
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        return jsonify({'error': 'Failed to get product details'}), 500

@shop_bp.route('/categories', methods=['GET'])
def get_shop_categories():
    """Get active product categories"""
    try:
        with SessionLocal() as session:
            categories = session.query(ShopCategory).filter(
                ShopCategory.is_active == True
            ).order_by(ShopCategory.sort_order, ShopCategory.name).all()
            
            categories_data = []
            for category in categories:
                # Count active products in category
                product_count = session.query(ShopProduct).filter(
                    ShopProduct.category_id == category.id,
                    ShopProduct.status == 'active',
                    ShopProduct.is_active == True
                ).count()
                
                categories_data.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'image_url': None,  # TODO: Add image_url field to ShopCategory model
                    'product_count': product_count
                })
            
            return jsonify({
                'categories': categories_data
            })
            
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Failed to get categories'}), 500

# === CHECKOUT AND ORDERS ===

@shop_bp.route('/checkout/create-session', methods=['POST'])
@optional_player_auth  # Allow both guest and authenticated checkout
def create_checkout_session():
    """Create a checkout session for cart items"""
    try:
        data = request.get_json()
        items = data.get('items', [])  # [{'product_sku': 'BUNDLE-001', 'quantity': 1}]
        
        if not items:
            return jsonify({'error': 'No items provided'}), 400
        
        with SessionLocal() as session:
            # Validate all products and calculate totals
            checkout_items = []
            subtotal = Decimal('0.00')
            
            for item in items:
                product_sku = item.get('product_sku')
                quantity = int(item.get('quantity', 1))
                
                if quantity <= 0:
                    return jsonify({'error': f'Invalid quantity for {product_sku}'}), 400
                
                # Find product
                product = session.query(ShopProduct).filter(
                    ShopProduct.sku == product_sku,
                    ShopProduct.status == ProductStatus.ACTIVE,
                    ShopProduct.is_active == True
                ).first()
                
                if not product:
                    return jsonify({'error': f'Product {product_sku} not found'}), 404
                
                # Check stock
                if product.track_inventory and product.stock_quantity < quantity:
                    return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
                
                item_total = product.price * quantity
                subtotal += item_total
                
                checkout_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': product.price,
                    'total_price': item_total
                })
            
            # Calculate tax and shipping (simplified for now)
            tax_rate = Decimal('0.08')  # 8% tax
            tax_amount = subtotal * tax_rate
            shipping_amount = Decimal('5.99') if subtotal < 50 else Decimal('0.00')  # Free shipping over $50
            total_amount = subtotal + tax_amount + shipping_amount
            
            # Create secure checkout session
            session_id = generate_secure_session_id()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
            
            # Prepare session data
            session_data = {
                'items': [{
                    'product_sku': item['product'].sku,
                    'product_name': item['product'].name,
                    'quantity': item['quantity'],
                    'unit_price': float(item['unit_price']),
                    'total_price': float(item['total_price'])
                } for item in checkout_items],
                'subtotal': float(subtotal),
                'tax_amount': float(tax_amount),
                'shipping_amount': float(shipping_amount),
                'total_amount': float(total_amount),
                'currency': 'USD',
                'expires_at': expires_at.isoformat(),
                'customer_id': g.current_player.id if hasattr(g, 'current_player') and g.current_player else None
            }
            
            # Create Stripe Payment Intent
            customer_email = g.current_player.email if hasattr(g, 'current_player') and g.current_player else None
            
            stripe_result = stripe_service.create_payment_intent(
                amount=total_amount,
                currency='USD',
                customer_email=customer_email,
                metadata={
                    'session_id': session_id,
                    'customer_id': g.current_player.id if hasattr(g, 'current_player') and g.current_player else None,
                    'item_count': len(checkout_items)
                }
            )
            
            if not stripe_result['success']:
                return jsonify({
                    'error': 'Payment processing unavailable',
                    'details': stripe_result.get('error', 'Unknown error')
                }), 500
            
            # Add Stripe payment intent ID to session data
            session_data['stripe_payment_intent_id'] = stripe_result['payment_intent_id']
            session_data['stripe_client_secret'] = stripe_result['client_secret']
            
            # Create integrity hash
            session_hash = create_session_hash(session_data, SESSION_SECRET_KEY)
            
            # Store in database
            checkout_session_record = ShopCheckoutSession(
                session_id=session_id,
                session_data=session_data,
                session_hash=session_hash,
                customer_id=g.current_player.id if hasattr(g, 'current_player') and g.current_player else None,
                customer_ip=request.remote_addr,
                expires_at=expires_at
            )
            
            session.add(checkout_session_record)
            session.commit()
            
            # Return checkout URL with Stripe integration
            checkout_url = f"/checkout/process?session_id={session_id}"
            
            return jsonify({
                'url': checkout_url,  # Frontend expects this field
                'session_id': session_id,
                'expires_at': expires_at.isoformat(),
                'payment_methods': ['stripe'],  # Now using Stripe
                'requires_shipping': any(item['product'].product_type == ProductType.PHYSICAL for item in checkout_items),
                'total_amount': float(total_amount),
                'currency': 'USD',
                'stripe_client_secret': stripe_result['client_secret'],
                'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY')
            })
            
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@shop_bp.route('/checkout/session/<session_id>', methods=['GET'])
def get_checkout_session(session_id):
    """Get checkout session data for frontend"""
    try:
        with SessionLocal() as db_session:
            checkout_session_record = db_session.query(ShopCheckoutSession).filter(
                ShopCheckoutSession.session_id == session_id,
                ShopCheckoutSession.is_used == False,
                ShopCheckoutSession.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if not checkout_session_record:
                return jsonify({'error': 'Invalid or expired checkout session'}), 404
            
            # Validate session integrity
            expected_hash = create_session_hash(checkout_session_record.session_data, SESSION_SECRET_KEY)
            if expected_hash != checkout_session_record.session_hash:
                return jsonify({'error': 'Session integrity check failed'}), 400
            
            session_data = checkout_session_record.session_data
            
            return jsonify({
                'session_id': session_id,
                'items': session_data.get('items', []),
                'subtotal': session_data.get('subtotal', 0),
                'tax_amount': session_data.get('tax_amount', 0),
                'shipping_amount': session_data.get('shipping_amount', 0),
                'total_amount': session_data.get('total_amount', 0),
                'currency': session_data.get('currency', 'USD'),
                'expires_at': session_data.get('expires_at'),
                'stripe_client_secret': session_data.get('stripe_client_secret'),
                'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY')
            })
            
    except Exception as e:
        logger.error(f"Error getting checkout session: {e}")
        return jsonify({'error': 'Failed to get checkout session'}), 500

@shop_bp.route('/checkout/process', methods=['POST'])
@optional_player_auth
def process_checkout():
    """Process checkout and create order"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        payment_method = data.get('payment_method')
        payment_token = data.get('payment_token')  # From Stripe/PayPal
        
        # Customer information
        customer_info = data.get('customer', {})
        billing_address = data.get('billing_address', {})
        shipping_address = data.get('shipping_address', {})
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        with SessionLocal() as db_session:
            # Retrieve and validate checkout session
            checkout_session_record = db_session.query(ShopCheckoutSession).filter(
                ShopCheckoutSession.session_id == session_id,
                ShopCheckoutSession.is_used == False,
                ShopCheckoutSession.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if not checkout_session_record:
                return jsonify({'error': 'Invalid or expired checkout session'}), 400
            
            # Validate session integrity
            expected_hash = create_session_hash(checkout_session_record.session_data, SESSION_SECRET_KEY)
            if expected_hash != checkout_session_record.session_hash:
                logger.error(f"Session integrity check failed for session {session_id}")
                return jsonify({'error': 'Session integrity check failed'}), 400
            
            # Get items from validated session
            session_data = checkout_session_record.session_data
            items = session_data.get('items', [])
            if not items:
                return jsonify({'error': 'No items in checkout session'}), 400
            # Validate and lock inventory
            order_items = []
            subtotal = Decimal('0.00')
            
            for item_data in items:
                product = db_session.query(ShopProduct).filter(
                    ShopProduct.sku == item_data['product_sku']
                ).with_for_update().first()  # Lock for inventory update
                
                if not product:
                    return jsonify({'error': f'Product {item_data["product_sku"]} not found'}), 404
                
                quantity = item_data['quantity']
                
                # Final stock check
                if product.track_inventory and product.stock_quantity < quantity:
                    return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
                
                # Reserve inventory
                if product.track_inventory:
                    product.stock_quantity -= quantity
                
                item_total = product.price * quantity
                subtotal += item_total
                
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': product.price,
                    'total_price': item_total
                })
            
            # Calculate final totals
            tax_amount = subtotal * Decimal('0.08')
            shipping_amount = Decimal('5.99') if subtotal < 50 else Decimal('0.00')
            total_amount = subtotal + tax_amount + shipping_amount
            
            # Process payment with Stripe
            stripe_payment_intent_id = session_data.get('stripe_payment_intent_id')
            if not stripe_payment_intent_id:
                return jsonify({'error': 'Invalid checkout session - no payment intent'}), 400
            
            # Verify payment intent status with Stripe
            payment_intent = stripe_service.retrieve_payment_intent(stripe_payment_intent_id)
            if not payment_intent:
                return jsonify({'error': 'Payment verification failed'}), 400
            
            # Check if payment was successful
            payment_success = payment_intent['status'] == 'succeeded'
            if not payment_success:
                logger.warning(f"Payment not completed: {payment_intent['status']} for intent {stripe_payment_intent_id}")
                return jsonify({
                    'error': 'Payment not completed',
                    'payment_status': payment_intent['status']
                }), 400
            
            # Payment was successful, continue with order creation
            
            # Create order
            order = ShopOrder(
                order_number=generate_order_number(),
                customer_id=g.current_player.id if hasattr(g, 'current_player') and g.current_player else None,
                customer_email=customer_info.get('email'),
                customer_name=customer_info.get('name'),
                customer_phone=customer_info.get('phone'),
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                total_amount=total_amount,
                currency='USD',
                order_status=OrderStatus.CONFIRMED,
                payment_status='paid',
                shipping_status=ShippingStatus.NOT_SHIPPED,
                billing_address=billing_address,
                shipping_address=shipping_address,
                payment_method='stripe',
                payment_reference=stripe_payment_intent_id,
                paid_at=datetime.now(timezone.utc),
                requires_shipping=any(item['product'].product_type == ProductType.PHYSICAL for item in order_items)
            )
            
            db_session.add(order)
            db_session.flush()  # Get order ID
            
            # Create order items
            for item in order_items:
                order_item = ShopOrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    product_sku=item['product'].sku,
                    product_name=item['product'].name,
                    product_image_url=item['product'].image_url,
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
                db_session.add(order_item)
            
            # Log inventory changes
            for item in order_items:
                if item['product'].track_inventory:
                    inventory_log = ShopInventoryLog(
                        product_id=item['product'].id,
                        change_type='sale',
                        quantity_before=item['product'].stock_quantity + item['quantity'],
                        quantity_change=-item['quantity'],
                        quantity_after=item['product'].stock_quantity,
                        reason=f'Sold in order {order.order_number}',
                        order_id=order.id
                    )
                    db_session.add(inventory_log)
            
            # Mark checkout session as used
            checkout_session_record.is_used = True
            
            db_session.commit()
            
            return jsonify({
                'success': True,
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount),
                    'currency': order.currency,
                    'status': order.order_status.value,
                    'created_at': order.created_at.isoformat()
                },
                'redirect_url': f'/checkout/success?order={order.order_number}'
            })
            
    except Exception as e:
        logger.error(f"Error processing checkout: {e}")
        return jsonify({'error': 'Failed to process checkout'}), 500

# === ORDER MANAGEMENT ===

@shop_bp.route('/orders/<order_number>', methods=['GET'])
@optional_player_auth
def get_order_details(order_number):
    """Get order details (for customer)"""
    try:
        with SessionLocal() as session:
            query = session.query(ShopOrder).filter(
                ShopOrder.order_number == order_number
            ).options(
                joinedload(ShopOrder.order_items).joinedload(ShopOrderItem.product)
            )
            
            # If authenticated, filter by customer
            if hasattr(g, 'current_player') and g.current_player:
                query = query.filter(ShopOrder.customer_id == g.current_player.id)
            
            order = query.first()
            
            if not order:
                return jsonify({'error': 'Order not found'}), 404
            
            return jsonify({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'subtotal': float(order.subtotal),
                'tax_amount': float(order.tax_amount),
                'shipping_amount': float(order.shipping_amount),
                'total_amount': float(order.total_amount),
                'currency': order.currency,
                'order_status': order.order_status.value,
                'payment_status': order.payment_status.value,
                'shipping_status': order.shipping_status.value,
                'shipping_address': order.shipping_address,
                'tracking_number': order.tracking_number,
                'created_at': order.created_at.isoformat(),
                'items': [{
                    'product_name': item.product_name,
                    'product_sku': item.product_sku,
                    'product_image_url': item.product_image_url,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price)
                } for item in order.order_items]
            })
            
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        return jsonify({'error': 'Failed to get order details'}), 500

@shop_bp.route('/my-orders', methods=['GET'])
@player_required
def get_my_orders():
    """Get customer's order history"""
    try:
        with SessionLocal() as session:
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 10)), 50)
            
            query = session.query(ShopOrder).filter(
                ShopOrder.customer_id == g.current_player.id
            ).options(joinedload(ShopOrder.order_items))
            
            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            
            orders = query.order_by(desc(ShopOrder.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount),
                    'currency': order.currency,
                    'order_status': order.order_status.value,
                    'payment_status': order.payment_status.value,
                    'shipping_status': order.shipping_status.value,
                    'created_at': order.created_at.isoformat(),
                    'item_count': len(order.order_items)
                })
            
            return jsonify({
                'orders': orders_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            })
            
    except Exception as e:
        logger.error(f"Error getting customer orders: {e}")
        return jsonify({'error': 'Failed to get orders'}), 500

# === STRIPE WEBHOOKS ===

@shop_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    if not signature:
        logger.error("Missing Stripe signature header")
        return jsonify({'error': 'Missing signature'}), 400
    
    try:
        # Handle webhook with Stripe service
        result = stripe_service.handle_webhook(payload, signature)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        # Process webhook result
        action = result.get('action')
        
        if action == 'payment_confirmed':
            # Payment was confirmed via webhook
            session_id = result.get('session_id')
            payment_intent_id = result.get('payment_intent_id')
            
            if session_id:
                # Update checkout session or order status if needed
                with SessionLocal() as db_session:
                    checkout_session = db_session.query(ShopCheckoutSession).filter(
                        ShopCheckoutSession.session_id == session_id
                    ).first()
                    
                    if checkout_session:
                        logger.info(f"Payment confirmed for session {session_id}")
                        # Additional processing can be added here
        
        elif action == 'payment_failed':
            # Handle payment failure
            session_id = result.get('session_id')
            logger.warning(f"Payment failed for session {session_id}")
            
            # Could implement inventory release logic here
        
        return jsonify({'received': True})
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

# === HELPER FUNCTIONS ===

def generate_checkout_session_id():
    """Generate secure checkout session ID"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def process_payment(payment_method, payment_token, amount):
    """Process payment with proper validation"""
    logger.info(f"Processing {payment_method} payment for ${amount}")
    
    # Validate payment method
    if payment_method not in ['stripe', 'paypal']:
        logger.error(f"Unsupported payment method: {payment_method}")
        return False
    
    # Validate payment token
    if not payment_token or len(payment_token) < 10:
        logger.error("Invalid payment token")
        return False
    
    # Validate amount
    if amount <= 0:
        logger.error(f"Invalid payment amount: {amount}")
        return False
    
    try:
        if payment_method == 'stripe':
            return process_stripe_payment(payment_token, amount)
        elif payment_method == 'paypal':
            return process_paypal_payment(payment_token, amount)
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        return False
    
    return False

def process_stripe_payment(payment_token, amount):
    """Process Stripe payment"""
    # In production, integrate with Stripe API
    # import stripe
    # stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    # 
    # try:
    #     charge = stripe.Charge.create(
    #         amount=int(amount * 100),  # Stripe uses cents
    #         currency='usd',
    #         source=payment_token,
    #         description='Deckport Card Purchase'
    #     )
    #     return charge.paid
    # except stripe.error.StripeError as e:
    #     logger.error(f"Stripe payment failed: {e}")
    #     return False
    
    # For demo purposes, validate token format
    if payment_token.startswith('demo_') and len(payment_token) > 15:
        logger.info(f"Demo Stripe payment processed: ${amount}")
        return True
    
    logger.error("Invalid Stripe payment token")
    return False

def process_paypal_payment(payment_token, amount):
    """Process PayPal payment"""
    # In production, integrate with PayPal API
    # import paypalrestsdk
    # 
    # paypalrestsdk.configure({
    #     "mode": os.getenv("PAYPAL_MODE", "sandbox"),
    #     "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    #     "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
    # })
    # 
    # payment = paypalrestsdk.Payment({
    #     "intent": "sale",
    #     "payer": {"payment_method": "paypal"},
    #     "transactions": [{
    #         "amount": {"total": str(amount), "currency": "USD"},
    #         "description": "Deckport Card Purchase"
    #     }],
    #     "redirect_urls": {
    #         "return_url": "http://localhost:3000/payment/success",
    #         "cancel_url": "http://localhost:3000/payment/cancel"
    #     }
    # })
    # 
    # if payment.create():
    #     return True
    # else:
    #     logger.error(f"PayPal payment failed: {payment.error}")
    #     return False
    
    # For demo purposes, validate token format
    if payment_token.startswith('demo_') and len(payment_token) > 15:
        logger.info(f"Demo PayPal payment processed: ${amount}")
        return True
    
    logger.error("Invalid PayPal payment token")
    return False
