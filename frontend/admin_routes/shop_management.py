"""
Shop Management Routes for Deckport Admin Panel
Handles product creation, pricing, inventory, and order management
"""

from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime, timezone
from . import admin_bp
from services.api_service import APIService
import logging

logger = logging.getLogger(__name__)

# Initialize API service
api_service = APIService()

@admin_bp.route('/shop')
def shop_management():
    """Shop management dashboard"""
    try:
        # Get shop statistics
        stats_response = api_service.get('/v1/admin/shop/stats')
        stats = stats_response or {
            'total_products': 0,
            'active_products': 0,
            'total_orders': 0,
            'revenue_today': 0,
            'revenue_month': 0
        }
        
        # Get recent orders
        orders_response = api_service.get('/v1/admin/shop/orders?limit=10')
        recent_orders = orders_response.get('orders', []) if orders_response else []
        
        # Get low stock alerts
        low_stock_response = api_service.get('/v1/admin/shop/inventory/low-stock')
        low_stock_items = low_stock_response.get('items', []) if low_stock_response else []
        
        return render_template('admin/shop_management/dashboard.html',
                             stats=stats,
                             recent_orders=recent_orders,
                             low_stock_items=low_stock_items)
                             
    except Exception as e:
        logger.error(f"Error loading shop dashboard: {e}")
        flash(f'Error loading shop data: {str(e)}', 'error')
        return render_template('admin/shop_management/dashboard.html',
                             stats={}, recent_orders=[], low_stock_items=[])

@admin_bp.route('/shop/products')
def shop_products():
    """Manage shop products"""
    try:
        # Get query parameters
        status = request.args.get('status', 'all')
        category = request.args.get('category', 'all')
        page = int(request.args.get('page', 1))
        
        # Build query parameters
        params = {'page': page, 'page_size': 20}
        if status != 'all':
            params['status'] = status
        if category != 'all':
            params['category'] = category
        
        # Get products from API
        products_response = api_service.get('/v1/admin/shop/products', params=params)
        products_data = products_response or {}
        
        products = products_data.get('products', [])
        total_pages = products_data.get('total_pages', 1)
        
        # Get categories for filter
        categories_response = api_service.get('/v1/admin/shop/categories')
        categories = categories_response.get('categories', []) if categories_response else []
        
        return render_template('admin/shop_management/products.html',
                             products=products,
                             categories=categories,
                             current_status=status,
                             current_category=category,
                             current_page=page,
                             total_pages=total_pages)
                             
    except Exception as e:
        logger.error(f"Error loading shop products: {e}")
        flash(f'Error loading products: {str(e)}', 'error')
        return render_template('admin/shop_management/products.html',
                             products=[], categories=[], 
                             current_status='all', current_category='all',
                             current_page=1, total_pages=1)

@admin_bp.route('/shop/products/new')
def shop_product_new():
    """Create new shop product"""
    try:
        # Get card catalog for product selection
        cards_response = api_service.get('/v1/catalog/cards?page_size=100')
        cards = cards_response.get('items', []) if cards_response else []
        
        # Get categories
        categories_response = api_service.get('/v1/admin/shop/categories')
        categories = categories_response.get('categories', []) if categories_response else []
        
        return render_template('admin/shop_management/product_form.html',
                             product=None,
                             cards=cards,
                             categories=categories,
                             form_action=url_for('admin.shop_product_create'))
                             
    except Exception as e:
        logger.error(f"Error loading product form: {e}")
        flash(f'Error loading form: {str(e)}', 'error')
        return redirect(url_for('admin.shop_products'))

@admin_bp.route('/shop/products/create', methods=['POST'])
def shop_product_create():
    """Create new shop product"""
    try:
        # Get form data
        product_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price', 0)),
            'currency': request.form.get('currency', 'USD'),
            'category': request.form.get('category'),
            'product_type': request.form.get('product_type'),
            'card_skus': request.form.getlist('card_skus'),
            'quantity': int(request.form.get('quantity', 1)),
            'is_active': request.form.get('is_active') == 'on',
            'is_featured': request.form.get('is_featured') == 'on'
        }
        
        # Create product via API
        response = api_service.post('/v1/admin/shop/products', json=product_data)
        
        if response and response.get('success'):
            flash('Product created successfully!', 'success')
            return redirect(url_for('admin.shop_products'))
        else:
            flash('Failed to create product', 'error')
            return redirect(url_for('admin.shop_product_new'))
            
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        flash(f'Error creating product: {str(e)}', 'error')
        return redirect(url_for('admin.shop_product_new'))

@admin_bp.route('/shop/products/<int:product_id>')
def shop_product_detail(product_id):
    """View/edit shop product"""
    try:
        # Get product details
        product_response = api_service.get(f'/v1/admin/shop/products/{product_id}')
        product = product_response if product_response else None
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('admin.shop_products'))
        
        # Get sales data for this product
        sales_response = api_service.get(f'/v1/admin/shop/products/{product_id}/sales')
        sales_data = sales_response or {}
        
        return render_template('admin/shop_management/product_detail.html',
                             product=product,
                             sales_data=sales_data)
                             
    except Exception as e:
        logger.error(f"Error loading product detail: {e}")
        flash(f'Error loading product: {str(e)}', 'error')
        return redirect(url_for('admin.shop_products'))

@admin_bp.route('/shop/products/<int:product_id>/edit')
def shop_product_edit(product_id):
    """Edit shop product form"""
    try:
        # Get product details
        product_response = api_service.get(f'/v1/admin/shop/products/{product_id}')
        product = product_response if product_response else None
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('admin.shop_products'))
        
        # Get card catalog for product selection
        cards_response = api_service.get('/v1/catalog/cards?page_size=100')
        cards = cards_response.get('items', []) if cards_response else []
        
        # Get categories
        categories_response = api_service.get('/v1/admin/shop/categories')
        categories = categories_response.get('categories', []) if categories_response else []
        
        return render_template('admin/shop_management/product_form.html',
                             product=product,
                             cards=cards,
                             categories=categories,
                             form_action=url_for('admin.shop_product_update', product_id=product_id))
                             
    except Exception as e:
        logger.error(f"Error loading product edit form: {e}")
        flash(f'Error loading form: {str(e)}', 'error')
        return redirect(url_for('admin.shop_products'))

@admin_bp.route('/shop/products/<int:product_id>/update', methods=['POST'])
def shop_product_update(product_id):
    """Update shop product"""
    try:
        # Get form data
        product_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price', 0)),
            'currency': request.form.get('currency', 'USD'),
            'category': request.form.get('category'),
            'product_type': request.form.get('product_type'),
            'card_skus': request.form.getlist('card_skus'),
            'quantity': int(request.form.get('quantity', 1)),
            'is_active': request.form.get('is_active') == 'on',
            'is_featured': request.form.get('is_featured') == 'on'
        }
        
        # Update product via API
        response = api_service.put(f'/v1/admin/shop/products/{product_id}', json=product_data)
        
        if response and response.get('success'):
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.shop_product_detail', product_id=product_id))
        else:
            flash('Failed to update product', 'error')
            return redirect(url_for('admin.shop_product_edit', product_id=product_id))
            
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        flash(f'Error updating product: {str(e)}', 'error')
        return redirect(url_for('admin.shop_product_edit', product_id=product_id))

@admin_bp.route('/shop/orders')
def shop_orders():
    """Manage shop orders"""
    try:
        # Get query parameters
        status = request.args.get('status', 'all')
        page = int(request.args.get('page', 1))
        
        # Build query parameters
        params = {'page': page, 'page_size': 20}
        if status != 'all':
            params['status'] = status
        
        # Get orders from API
        orders_response = api_service.get('/v1/admin/shop/orders', params=params)
        orders_data = orders_response or {}
        
        orders = orders_data.get('orders', [])
        total_pages = orders_data.get('total_pages', 1)
        
        return render_template('admin/shop_management/orders.html',
                             orders=orders,
                             current_status=status,
                             current_page=page,
                             total_pages=total_pages)
                             
    except Exception as e:
        logger.error(f"Error loading shop orders: {e}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('admin/shop_management/orders.html',
                             orders=[], current_status='all',
                             current_page=1, total_pages=1)

@admin_bp.route('/shop/orders/<int:order_id>')
def shop_order_detail(order_id):
    """View order details"""
    try:
        # Get order details
        order_response = api_service.get(f'/v1/admin/shop/orders/{order_id}')
        order = order_response if order_response else None
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('admin.shop_orders'))
        
        return render_template('admin/shop_management/order_detail.html',
                             order=order)
                             
    except Exception as e:
        logger.error(f"Error loading order detail: {e}")
        flash(f'Error loading order: {str(e)}', 'error')
        return redirect(url_for('admin.shop_orders'))

@admin_bp.route('/shop/inventory')
def shop_inventory():
    """Manage inventory"""
    try:
        # Get inventory data
        inventory_response = api_service.get('/v1/admin/shop/inventory')
        inventory_data = inventory_response or {}
        
        inventory_items = inventory_data.get('items', [])
        
        # Get low stock alerts
        low_stock_response = api_service.get('/v1/admin/shop/inventory/low-stock')
        low_stock_items = low_stock_response.get('items', []) if low_stock_response else []
        
        return render_template('admin/shop_management/inventory.html',
                             inventory_items=inventory_items,
                             low_stock_items=low_stock_items)
                             
    except Exception as e:
        logger.error(f"Error loading inventory: {e}")
        flash(f'Error loading inventory: {str(e)}', 'error')
        return render_template('admin/shop_management/inventory.html',
                             inventory_items=[], low_stock_items=[])
