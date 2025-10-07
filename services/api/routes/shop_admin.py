"""
Shop Administration API Routes
Handles product management, orders, inventory, and analytics for admin panel
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import func, desc, asc, and_, or_
from sqlalchemy.orm import joinedload
import logging

from shared.database.connection import SessionLocal
from shared.models.shop import (
    ShopProduct, ShopOrder, ShopOrderItem, ProductDiscount, 
    OrderStatus, ProductType, ProductStatus, PaymentMethod, DiscountType
)
from shared.models.base import Player
from shared.auth.decorators import admin_required

logger = logging.getLogger(__name__)

shop_admin_bp = Blueprint('shop_admin', __name__, url_prefix='/v1/admin/shop')

# === SHOP STATISTICS ===

@shop_admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_shop_stats():
    """Get shop overview statistics"""
    try:
        with SessionLocal() as session:
            # Product statistics
            total_products = session.query(ShopProduct).count()
            active_products = session.query(ShopProduct).filter(
                ShopProduct.status == 'active'
            ).count()
            
            # Order statistics
            total_orders = session.query(ShopOrder).count()
            
            # Revenue statistics
            today = datetime.now(timezone.utc).date()
            month_start = today.replace(day=1)
            
            revenue_today = session.query(func.sum(ShopOrder.total_amount)).filter(
                func.date(ShopOrder.created_at) == today,
                ShopOrder.payment_status == 'paid'
            ).scalar() or 0
            
            revenue_month = session.query(func.sum(ShopOrder.total_amount)).filter(
                func.date(ShopOrder.created_at) >= month_start,
                ShopOrder.payment_status == 'paid'
            ).scalar() or 0
            
            # Pending orders
            pending_orders = session.query(ShopOrder).filter(
                ShopOrder.order_status == 'pending'
            ).count()
            
            # Low stock items - simplified (products with stock_quantity < 10)
            low_stock_count = session.query(ShopProduct).filter(
                ShopProduct.stock_quantity < 10
            ).count()
            
            return jsonify({
                'total_products': total_products,
                'active_products': active_products,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'revenue_today': float(revenue_today),
                'revenue_month': float(revenue_month),
                'low_stock_count': low_stock_count
            })
            
    except Exception as e:
        logger.error(f"Error getting shop stats: {e}")
        return jsonify({'error': 'Failed to get shop statistics'}), 500

# === PRODUCT MANAGEMENT ===

@shop_admin_bp.route('/products', methods=['GET'])
@admin_required
def get_products():
    """Get products with filtering and pagination"""
    try:
        with SessionLocal() as session:
            # Get query parameters
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 20)), 100)
            status = request.args.get('status')
            category_id = request.args.get('category')
            search = request.args.get('search', '').strip()
            
            # Build query
            query = session.query(ShopProduct)
            
            # Apply filters
            if status and status != 'all':
                if status == 'active':
                    query = query.filter(ShopProduct.status == 'active')
                elif status == 'inactive':
                    query = query.filter(ShopProduct.status == 'inactive')
                elif status == 'draft':
                    query = query.filter(ShopProduct.status == 'draft')
            
            if category_id and category_id != 'all':
                query = query.filter(ShopProduct.category_id == int(category_id))
            
            if search:
                query = query.filter(or_(
                    ShopProduct.name.ilike(f'%{search}%'),
                    ShopProduct.sku.ilike(f'%{search}%'),
                    ShopProduct.description.ilike(f'%{search}%')
                ))
            
            # Get total count
            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            
            # Apply pagination and ordering
            products = query.order_by(desc(ShopProduct.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            # Format response
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'sku': product.sku,
                    'name': product.name,
                    'price': float(product.price),
                    'currency': product.currency,
                    'stock_quantity': product.stock_quantity,
                    'status': product.status,
                    'is_active': product.is_active,
                    'is_featured': product.is_featured,
                    'product_type': product.product_type,
                    'category_name': product.category.name if hasattr(product, 'category') and product.category else None,
                    'category_id': product.category_id,
                    'image_url': product.image_url,
                    'created_at': product.created_at.isoformat(),
                    'card_skus': product.card_skus or []
                })
            
            return jsonify({
                'products': products_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            })
            
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({'error': 'Failed to get products'}), 500

@shop_admin_bp.route('/products', methods=['POST'])
@admin_required
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            # Generate SKU if not provided
            sku = data.get('sku')
            if not sku:
                name_part = ''.join(c.upper() for c in data['name'] if c.isalnum())[:10]
                sku = f"PROD-{name_part}-{datetime.now().strftime('%Y%m%d')}"
            
            # Generate slug from name
            slug = data['name'].lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
            
            # Create product
            product = ShopProduct(
                sku=sku,
                name=data['name'],
                slug=slug,
                description=data.get('description', ''),
                price=Decimal(str(data['price'])),
                currency=data.get('currency', 'USD'),
                product_type=ProductType(data['product_type']),
                category_id=data.get('category') if data.get('category') else None,
                stock_quantity=data.get('quantity', 0),
                low_stock_threshold=data.get('low_stock_threshold', 5),
                card_skus=data.get('card_skus', []),
                is_active=data.get('is_active', True),
                is_featured=data.get('is_featured', False),
                status='active' if data.get('is_active', True) else 'draft',
                published_at=datetime.now(timezone.utc) if data.get('is_active', True) else None
            )
            
            session.add(product)
            session.commit()
            
            # Log inventory if tracking
            if product.track_inventory and product.stock_quantity > 0:
                inventory_log = ShopInventoryLog(
                    product_id=product.id,
                    change_type='initial_stock',
                    quantity_before=0,
                    quantity_change=product.stock_quantity,
                    quantity_after=product.stock_quantity,
                    reason='Initial stock on product creation',
                    changed_by='admin'
                )
                session.add(inventory_log)
                session.commit()
            
            return jsonify({
                'success': True,
                'product_id': product.id,
                'message': 'Product created successfully'
            })
            
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'error': 'Failed to create product'}), 500

@shop_admin_bp.route('/products/<int:product_id>', methods=['GET'])
@admin_required
def get_product(product_id):
    """Get product details"""
    try:
        with SessionLocal() as session:
            product = session.query(ShopProduct).filter(ShopProduct.id == product_id).first()
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            return jsonify({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'slug': product.slug,
                'description': product.description,
                'price': float(product.price),
                'compare_at_price': float(product.compare_at_price) if product.compare_at_price else None,
                'currency': product.currency,
                'product_type': product.product_type,
                'category_id': product.category_id,
                'category_name': product.category.name if hasattr(product, 'category') and product.category else None,
                'stock_quantity': product.stock_quantity,
                'low_stock_threshold': product.low_stock_threshold,
                'track_inventory': product.track_inventory,
                'card_skus': product.card_skus or [],
                'image_url': product.image_url,
                'gallery_images': product.gallery_images or [],
                'meta_title': product.meta_title,
                'meta_description': product.meta_description,
                'tags': product.tags or [],
                'is_active': product.is_active,
                'is_featured': product.is_featured,
                'is_bestseller': product.is_bestseller,
                'status': product.status,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return jsonify({'error': 'Failed to get product'}), 500

# === ORDER MANAGEMENT ===

@shop_admin_bp.route('/orders', methods=['GET'])
@admin_required
def get_orders():
    """Get orders with filtering and pagination"""
    try:
        with SessionLocal() as session:
            # Get query parameters
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 20)), 100)
            status = request.args.get('status')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            
            # Build query
            query = session.query(ShopOrder).options(
                joinedload(ShopOrder.order_items).joinedload(ShopOrderItem.product),
                joinedload(ShopOrder.customer)
            )
            
            # Apply filters
            if status and status != 'all':
                query = query.filter(ShopOrder.order_status == status)
            
            if date_from:
                query = query.filter(ShopOrder.created_at >= datetime.fromisoformat(date_from))
            
            if date_to:
                query = query.filter(ShopOrder.created_at <= datetime.fromisoformat(date_to))
            
            # Get total count
            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            
            # Apply pagination and ordering
            orders = query.order_by(desc(ShopOrder.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            # Format response
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'customer_email': order.customer_email,
                    'total_amount': float(order.total_amount),
                    'currency': order.currency,
                    'status': order.order_status,
                    'payment_status': order.payment_status,
                    'shipping_status': order.shipping_status,
                    'is_priority': order.is_priority,
                    'created_at': order.created_at.isoformat(),
                    'items': [{
                        'id': item.id,
                        'product_name': item.product_name,
                        'product_sku': item.product_sku,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_price': float(item.total_price)
                    } for item in order.order_items]
                })
            
            return jsonify({
                'orders': orders_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            })
            
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({'error': 'Failed to get orders'}), 500

@shop_admin_bp.route('/orders/<int:order_id>', methods=['GET'])
@admin_required
def get_order(order_id):
    """Get order details"""
    try:
        with SessionLocal() as session:
            order = session.query(ShopOrder).options(
                joinedload(ShopOrder.order_items).joinedload(ShopOrderItem.product),
                joinedload(ShopOrder.customer),
                joinedload(ShopOrder.status_history)
            ).filter(ShopOrder.id == order_id).first()
            
            if not order:
                return jsonify({'error': 'Order not found'}), 404
            
            return jsonify({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'subtotal': float(order.subtotal),
                'tax_amount': float(order.tax_amount),
                'shipping_amount': float(order.shipping_amount),
                'discount_amount': float(order.discount_amount),
                'total_amount': float(order.total_amount),
                'currency': order.currency,
                'order_status': order.order_status,
                'payment_status': order.payment_status,
                'shipping_status': order.shipping_status,
                'billing_address': order.billing_address,
                'shipping_address': order.shipping_address,
                'shipping_method': order.shipping_method,
                'tracking_number': order.tracking_number,
                'payment_method': order.payment_method,
                'notes': order.notes,
                'admin_notes': order.admin_notes,
                'is_priority': order.is_priority,
                'created_at': order.created_at.isoformat(),
                'items': [{
                    'id': item.id,
                    'product_name': item.product_name,
                    'product_sku': item.product_sku,
                    'product_image_url': item.product_image_url,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                    'is_fulfilled': item.is_fulfilled
                } for item in order.order_items],
                'status_history': [{
                    'from_status': history.from_status,
                    'to_status': history.to_status,
                    'status_type': history.status_type,
                    'reason': history.reason,
                    'notes': history.notes,
                    'changed_by': history.changed_by,
                    'created_at': history.created_at.isoformat()
                } for history in order.status_history]
            })
            
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        return jsonify({'error': 'Failed to get order'}), 500

# === INVENTORY MANAGEMENT ===

@shop_admin_bp.route('/inventory', methods=['GET'])
@admin_required
def get_inventory():
    """Get inventory overview"""
    try:
        with SessionLocal() as session:
            products = session.query(ShopProduct).filter(
                ShopProduct.track_inventory == True
            ).order_by(ShopProduct.stock_quantity.asc()).all()
            
            inventory_items = []
            for product in products:
                inventory_items.append({
                    'id': product.id,
                    'sku': product.sku,
                    'name': product.name,
                    'stock_quantity': product.stock_quantity,
                    'low_stock_threshold': product.low_stock_threshold,
                    'is_low_stock': product.stock_quantity <= product.low_stock_threshold,
                    'status': product.status
                })
            
            return jsonify({
                'items': inventory_items
            })
            
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        return jsonify({'error': 'Failed to get inventory'}), 500

@shop_admin_bp.route('/inventory/low-stock', methods=['GET'])
@admin_required
def get_low_stock_items():
    """Get products with low stock"""
    try:
        with SessionLocal() as session:
            products = session.query(ShopProduct).filter(
                ShopProduct.track_inventory == True,
                ShopProduct.stock_quantity <= ShopProduct.low_stock_threshold
            ).order_by(ShopProduct.stock_quantity.asc()).all()
            
            items = []
            for product in products:
                items.append({
                    'id': product.id,
                    'sku': product.sku,
                    'name': product.name,
                    'stock_quantity': product.stock_quantity,
                    'low_stock_threshold': product.low_stock_threshold
                })
            
            return jsonify({
                'items': items
            })
            
    except Exception as e:
        logger.error(f"Error getting low stock items: {e}")
        return jsonify({'error': 'Failed to get low stock items'}), 500

# === CATEGORIES ===

@shop_admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    """Get all product categories"""
    try:
        with SessionLocal() as session:
            categories = session.query(ShopCategory).filter(
                ShopCategory.is_active == True
            ).order_by(ShopCategory.sort_order, ShopCategory.name).all()
            
            categories_data = []
            for category in categories:
                categories_data.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'sort_order': category.sort_order
                })
            
            return jsonify({
                'categories': categories_data
            })
            
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Failed to get categories'}), 500


