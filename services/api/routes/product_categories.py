"""
Product Categories API Routes
Handles shop product category management for admin panel
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from sqlalchemy import and_, or_, desc, func
from shared.database.connection import SessionLocal
from shared.models.console_enhancements import ProductCategory
from shared.auth.auto_rbac_decorator import auto_rbac_required
from shared.auth.admin_roles import Permission
from shared.auth.admin_context import log_admin_action, get_current_admin_id
import logging

logger = logging.getLogger(__name__)

product_categories_bp = Blueprint('product_categories', __name__, url_prefix='/v1/admin/product-categories')

@product_categories_bp.route('', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.ADMIN_VIEW])
def get_categories():
    """Get all product categories with hierarchy"""
    try:
        with SessionLocal() as session:
            # Get all categories ordered by parent/child hierarchy
            categories = session.query(ProductCategory).order_by(
                ProductCategory.parent_id.asc().nullsfirst(),
                ProductCategory.sort_order.asc(),
                ProductCategory.name.asc()
            ).all()
            
            # Build hierarchical structure
            category_tree = []
            category_map = {}
            
            # First pass: create all categories
            for category in categories:
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'sort_order': category.sort_order,
                    'is_active': category.is_active,
                    'icon_url': category.icon_url,
                    'banner_url': category.banner_url,
                    'metadata': category.category_metadata or {},
                    'created_at': category.created_at.isoformat(),
                    'updated_at': category.updated_at.isoformat(),
                    'children': [],
                    'product_count': 0  # Will be populated below
                }
                category_map[category.id] = category_data
            
            # Second pass: build hierarchy
            for category in categories:
                category_data = category_map[category.id]
                if category.parent_id:
                    # Add to parent's children
                    if category.parent_id in category_map:
                        category_map[category.parent_id]['children'].append(category_data)
                else:
                    # Top-level category
                    category_tree.append(category_data)
            
            # Third pass: count products in each category
            # Note: This would require the shop_products table to have category_id
            # For now, return 0 for all categories
            
            return jsonify({
                'categories': category_tree,
                'total_categories': len(categories),
                'active_categories': len([c for c in categories if c.is_active])
            })
            
    except Exception as e:
        logger.error(f"Error getting product categories: {e}")
        return jsonify({'error': 'Failed to get categories'}), 500


@product_categories_bp.route('', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.ADMIN_EDIT])
def create_category():
    """Create a new product category"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        slug = data.get('slug', '').strip()
        
        if not name:
            return jsonify({'error': 'Category name is required'}), 400
        
        # Generate slug from name if not provided
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            # Remove special characters
            import re
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
        
        with SessionLocal() as session:
            # Check if slug already exists
            existing = session.query(ProductCategory).filter(ProductCategory.slug == slug).first()
            if existing:
                return jsonify({'error': 'Category slug already exists'}), 409
            
            # Validate parent_id if provided
            parent_id = data.get('parent_id')
            if parent_id:
                parent = session.query(ProductCategory).filter(ProductCategory.id == parent_id).first()
                if not parent:
                    return jsonify({'error': 'Parent category not found'}), 404
            
            # Create new category
            category = ProductCategory(
                name=name,
                slug=slug,
                description=data.get('description', '').strip() or None,
                parent_id=parent_id,
                sort_order=data.get('sort_order', 0),
                is_active=data.get('is_active', True),
                icon_url=data.get('icon_url', '').strip() or None,
                banner_url=data.get('banner_url', '').strip() or None,
                category_metadata=data.get('metadata', {})
            )
            
            session.add(category)
            session.commit()
            
            # Log admin action
            log_admin_action(
                action="product_category.created",
                resource_type="product_category",
                resource_id=category.id,
                details={
                    'name': category.name,
                    'slug': category.slug,
                    'parent_id': category.parent_id
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Category created successfully',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'sort_order': category.sort_order,
                    'is_active': category.is_active,
                    'icon_url': category.icon_url,
                    'banner_url': category.banner_url,
                    'metadata': category.category_metadata,
                    'created_at': category.created_at.isoformat()
                }
            }), 201
            
    except Exception as e:
        logger.error(f"Error creating product category: {e}")
        return jsonify({'error': 'Failed to create category'}), 500


@product_categories_bp.route('/<int:category_id>', methods=['PUT'])
@auto_rbac_required(override_permissions=[Permission.ADMIN_EDIT])
def update_category(category_id):
    """Update a product category"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with SessionLocal() as session:
            category = session.query(ProductCategory).filter(ProductCategory.id == category_id).first()
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            
            # Store old values for logging
            old_values = {
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'parent_id': category.parent_id,
                'is_active': category.is_active
            }
            
            # Update fields
            if 'name' in data:
                category.name = data['name'].strip()
            if 'slug' in data:
                new_slug = data['slug'].strip()
                # Check if new slug conflicts with existing
                existing = session.query(ProductCategory).filter(
                    ProductCategory.slug == new_slug,
                    ProductCategory.id != category_id
                ).first()
                if existing:
                    return jsonify({'error': 'Category slug already exists'}), 409
                category.slug = new_slug
            
            if 'description' in data:
                category.description = data['description'].strip() or None
            if 'parent_id' in data:
                parent_id = data['parent_id']
                if parent_id:
                    # Validate parent exists and prevent circular references
                    if parent_id == category_id:
                        return jsonify({'error': 'Category cannot be its own parent'}), 400
                    parent = session.query(ProductCategory).filter(ProductCategory.id == parent_id).first()
                    if not parent:
                        return jsonify({'error': 'Parent category not found'}), 404
                category.parent_id = parent_id
            
            if 'sort_order' in data:
                category.sort_order = data['sort_order']
            if 'is_active' in data:
                category.is_active = data['is_active']
            if 'icon_url' in data:
                category.icon_url = data['icon_url'].strip() or None
            if 'banner_url' in data:
                category.banner_url = data['banner_url'].strip() or None
            if 'metadata' in data:
                category.category_metadata = data['metadata']
            
            category.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            # Log admin action
            log_admin_action(
                action="product_category.updated",
                resource_type="product_category",
                resource_id=category.id,
                details={
                    'old_values': old_values,
                    'new_values': {
                        'name': category.name,
                        'slug': category.slug,
                        'description': category.description,
                        'parent_id': category.parent_id,
                        'is_active': category.is_active
                    }
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Category updated successfully',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'sort_order': category.sort_order,
                    'is_active': category.is_active,
                    'icon_url': category.icon_url,
                    'banner_url': category.banner_url,
                    'metadata': category.category_metadata,
                    'updated_at': category.updated_at.isoformat()
                }
            })
            
    except Exception as e:
        logger.error(f"Error updating product category: {e}")
        return jsonify({'error': 'Failed to update category'}), 500


@product_categories_bp.route('/<int:category_id>', methods=['DELETE'])
@auto_rbac_required(override_permissions=[Permission.ADMIN_EDIT])
def delete_category(category_id):
    """Delete a product category"""
    try:
        with SessionLocal() as session:
            category = session.query(ProductCategory).filter(ProductCategory.id == category_id).first()
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            
            # Check if category has children
            children_count = session.query(ProductCategory).filter(ProductCategory.parent_id == category_id).count()
            if children_count > 0:
                return jsonify({'error': 'Cannot delete category with subcategories. Delete subcategories first.'}), 400
            
            # Check if category has products (when shop_products.category_id is implemented)
            # products_count = session.query(ShopProduct).filter(ShopProduct.category_id == category_id).count()
            # if products_count > 0:
            #     return jsonify({'error': 'Cannot delete category with products. Move products to another category first.'}), 400
            
            category_name = category.name
            session.delete(category)
            session.commit()
            
            # Log admin action
            log_admin_action(
                action="product_category.deleted",
                resource_type="product_category",
                resource_id=category_id,
                details={
                    'name': category_name,
                    'slug': category.slug
                }
            )
            
            return jsonify({
                'success': True,
                'message': f'Category "{category_name}" deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting product category: {e}")
        return jsonify({'error': 'Failed to delete category'}), 500
