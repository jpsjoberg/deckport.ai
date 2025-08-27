"""
Card Production Workflow Admin Interface
Manages the 3-tier card system: Templates → Products → NFC Cards
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from shared.auth.decorators import admin_required
from shared.database.connection import SessionLocal
import json
import logging
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)

workflow_bp = Blueprint('card_workflow', __name__, url_prefix='/admin/workflow')

@workflow_bp.route('/', methods=['GET'])
@admin_required
def workflow_dashboard():
    """Main workflow dashboard showing all stages"""
    
    with SessionLocal() as session:
        # Get counts for each stage
        stats = {
            'templates_in_design': session.execute(
                "SELECT COUNT(*) FROM card_templates WHERE is_design_complete = FALSE"
            ).scalar(),
            'templates_ready_for_balance': session.execute(
                "SELECT COUNT(*) FROM card_templates WHERE is_design_complete = TRUE AND is_balanced = FALSE"
            ).scalar(),
            'templates_ready_for_production': session.execute(
                "SELECT COUNT(*) FROM card_templates WHERE is_balanced = TRUE AND is_ready_for_production = FALSE"
            ).scalar(),
            'ready_for_image_generation': session.execute(
                "SELECT COUNT(*) FROM cards_ready_for_generation"
            ).scalar(),
            'products_awaiting_publication': session.execute(
                "SELECT COUNT(*) FROM card_products WHERE is_published = FALSE"
            ).scalar(),
            'published_products': session.execute(
                "SELECT COUNT(*) FROM card_products WHERE is_published = TRUE"
            ).scalar(),
            'nfc_cards_active': session.execute(
                "SELECT COUNT(*) FROM nfc_cards WHERE status = 'activated'"
            ).scalar()
        }
        
        # Get recent activity
        recent_templates = session.execute("""
            SELECT name, created_at, is_design_complete, is_balanced, is_ready_for_production
            FROM card_templates 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
        
        recent_products = session.execute("""
            SELECT name, product_sku, created_at, is_published
            FROM card_products 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
    
    return render_template('admin/workflow/dashboard.html', 
                         stats=stats,
                         recent_templates=recent_templates,
                         recent_products=recent_products)

@workflow_bp.route('/templates', methods=['GET'])
@admin_required
def manage_templates():
    """Manage card templates (Tier 1)"""
    
    stage = request.args.get('stage', 'all')
    
    with SessionLocal() as session:
        query = "SELECT * FROM card_templates"
        params = {}
        
        if stage == 'design':
            query += " WHERE is_design_complete = FALSE"
        elif stage == 'balance':
            query += " WHERE is_design_complete = TRUE AND is_balanced = FALSE"
        elif stage == 'ready':
            query += " WHERE is_balanced = TRUE AND is_ready_for_production = FALSE"
        elif stage == 'production':
            query += " WHERE is_ready_for_production = TRUE"
        
        query += " ORDER BY created_at DESC"
        
        templates = session.execute(query, params).fetchall()
    
    return render_template('admin/workflow/templates.html', 
                         templates=templates, 
                         current_stage=stage)

@workflow_bp.route('/templates/<int:template_id>/review', methods=['GET', 'POST'])
@admin_required
def review_template(template_id):
    """Review and approve a template for next stage"""
    
    with SessionLocal() as session:
        template = session.execute(
            "SELECT * FROM card_templates WHERE id = :id",
            {"id": template_id}
        ).fetchone()
        
        if not template:
            flash('Template not found', 'error')
            return redirect(url_for('card_workflow.manage_templates'))
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'approve_design':
                session.execute(
                    "UPDATE card_templates SET is_design_complete = TRUE WHERE id = :id",
                    {"id": template_id}
                )
                flash('Template design approved!', 'success')
                
            elif action == 'approve_balance':
                # Update stats if provided
                new_stats = request.form.get('base_stats')
                if new_stats:
                    try:
                        stats_json = json.loads(new_stats)
                        session.execute(
                            "UPDATE card_templates SET base_stats = :stats, is_balanced = TRUE WHERE id = :id",
                            {"stats": json.dumps(stats_json), "id": template_id}
                        )
                    except json.JSONDecodeError:
                        flash('Invalid stats JSON', 'error')
                        return redirect(request.url)
                else:
                    session.execute(
                        "UPDATE card_templates SET is_balanced = TRUE WHERE id = :id",
                        {"id": template_id}
                    )
                flash('Template balance approved!', 'success')
                
            elif action == 'approve_production':
                session.execute(
                    "UPDATE card_templates SET is_ready_for_production = TRUE WHERE id = :id",
                    {"id": template_id}
                )
                flash('Template approved for production!', 'success')
            
            session.commit()
            return redirect(url_for('card_workflow.manage_templates'))
    
    return render_template('admin/workflow/review_template.html', template=template)

@workflow_bp.route('/generate-images', methods=['GET', 'POST'])
@admin_required
def generate_images():
    """Generate images for templates ready for production"""
    
    if request.method == 'GET':
        # Show templates ready for image generation
        with SessionLocal() as session:
            ready_templates = session.execute(
                "SELECT * FROM cards_ready_for_generation ORDER BY created_at"
            ).fetchall()
        
        return render_template('admin/workflow/generate_images.html', 
                             templates=ready_templates)
    
    # POST: Generate images for selected templates
    template_ids = request.form.getlist('template_ids')
    
    if not template_ids:
        flash('No templates selected', 'error')
        return redirect(url_for('card_workflow.generate_images'))
    
    generated_count = 0
    
    with SessionLocal() as session:
        for template_id in template_ids:
            try:
                # Get template data
                template = session.execute(
                    "SELECT * FROM card_templates WHERE id = :id",
                    {"id": template_id}
                ).fetchone()
                
                if not template:
                    continue
                
                # Generate image (mock implementation)
                image_url = generate_card_image(template)
                
                # Create product record
                product_sku = generate_product_sku(template.card_set_id, template.color_code)
                
                session.execute("""
                    INSERT INTO card_products (
                        template_id, card_set_id, product_sku, name, description, 
                        flavor_text, rarity, category, color_code, base_stats,
                        attachment_rules, duration, token_spec, reveal_trigger,
                        image_url, display_label, is_published
                    ) VALUES (
                        :template_id, :card_set_id, :product_sku, :name, :description,
                        :flavor_text, :rarity, :category, :color_code, :base_stats,
                        :attachment_rules, :duration, :token_spec, :reveal_trigger,
                        :image_url, :display_label, FALSE
                    )
                """, {
                    "template_id": template.id,
                    "card_set_id": template.card_set_id,
                    "product_sku": product_sku,
                    "name": template.name,
                    "description": template.description,
                    "flavor_text": template.flavor_text,
                    "rarity": template.rarity,
                    "category": template.category,
                    "color_code": template.color_code,
                    "base_stats": json.dumps(template.base_stats) if template.base_stats else None,
                    "attachment_rules": json.dumps(template.attachment_rules) if template.attachment_rules else None,
                    "duration": json.dumps(template.duration) if template.duration else None,
                    "token_spec": json.dumps(template.token_spec) if template.token_spec else None,
                    "reveal_trigger": json.dumps(template.reveal_trigger) if template.reveal_trigger else None,
                    "image_url": image_url,
                    "display_label": f"{template.rarity.title()} {template.category.title()}"
                })
                
                generated_count += 1
                logger.info(f"Generated product for template {template.name} -> {product_sku}")
                
            except Exception as e:
                logger.error(f"Error generating product for template {template_id}: {e}")
                continue
        
        session.commit()
    
    flash(f'Generated {generated_count} card products!', 'success')
    return redirect(url_for('card_workflow.manage_products'))

@workflow_bp.route('/products', methods=['GET'])
@admin_required
def manage_products():
    """Manage card products (Tier 2 - The Card Catalog)"""
    
    status = request.args.get('status', 'all')
    
    with SessionLocal() as session:
        query = """
            SELECT p.*, t.art_prompt, cs.name as set_name
            FROM card_products p
            LEFT JOIN card_templates t ON p.template_id = t.id
            LEFT JOIN card_sets cs ON p.card_set_id = cs.id
        """
        
        if status == 'unpublished':
            query += " WHERE p.is_published = FALSE"
        elif status == 'published':
            query += " WHERE p.is_published = TRUE"
        elif status == 'printable':
            query += " WHERE p.is_printable = TRUE"
        
        query += " ORDER BY p.created_at DESC"
        
        products = session.execute(query).fetchall()
    
    return render_template('admin/workflow/products.html', 
                         products=products, 
                         current_status=status)

@workflow_bp.route('/products/<int:product_id>/publish', methods=['POST'])
@admin_required
def publish_product(product_id):
    """Publish a product to the game catalog"""
    
    with SessionLocal() as session:
        session.execute(
            "UPDATE card_products SET is_published = TRUE, release_date = CURRENT_DATE WHERE id = :id",
            {"id": product_id}
        )
        session.commit()
    
    flash('Product published to game catalog!', 'success')
    return redirect(url_for('card_workflow.manage_products'))

@workflow_bp.route('/products/<int:product_id>/mark-printable', methods=['POST'])
@admin_required
def mark_printable(product_id):
    """Mark a product as ready for physical production"""
    
    with SessionLocal() as session:
        session.execute(
            "UPDATE card_products SET is_printable = TRUE WHERE id = :id",
            {"id": product_id}
        )
        session.commit()
    
    flash('Product marked as printable!', 'success')
    return redirect(url_for('card_workflow.manage_products'))

def generate_card_image(template):
    """Generate card image from template (mock implementation)"""
    
    # In production, this would:
    # 1. Call ComfyUI or other image generation service
    # 2. Use template.art_prompt to generate the image
    # 3. Composite the image with card frame, stats, etc.
    # 4. Save to static/cards/ directory
    # 5. Return the URL
    
    # For now, return a mock URL
    safe_name = template.name.lower().replace(' ', '-').replace("'", "")
    return f"/static/cards/{template.color_code.lower()}-{safe_name}.png"

def generate_product_sku(card_set_id, color_code):
    """Generate unique product SKU"""
    
    with SessionLocal() as session:
        # Get set code
        set_code = session.execute(
            "SELECT code FROM card_sets WHERE id = :id",
            {"id": card_set_id}
        ).scalar()
        
        if not set_code:
            set_code = "UNK"
        
        # Find next number for this color
        max_num = session.execute("""
            SELECT COALESCE(MAX(
                CAST(SUBSTRING(product_sku FROM '[0-9]+$') AS INTEGER)
            ), 0)
            FROM card_products 
            WHERE product_sku LIKE :pattern
        """, {"pattern": f"{color_code}-%"}).scalar()
        
        next_num = (max_num or 0) + 1
        
        return f"{color_code}-{next_num:03d}"
