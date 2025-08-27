"""
NFC Card Management Routes for Deckport Admin Panel
Handles physical NFC card production, tracking, and lifecycle management
"""

import requests
from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime, timezone
from functools import wraps
from . import admin_bp
from services.api_service import APIService

# Initialize API service
api_service = APIService()

def require_admin_auth(f):
    """Decorator to require admin authentication for frontend routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/nfc-cards')
@require_admin_auth
def nfc_management_dashboard():
    """NFC Card Management Dashboard"""
    try:
        # Get NFC card statistics
        stats_response = api_service.get('/v1/nfc-cards/admin/stats')
        stats = stats_response if stats_response else {
            'total_cards': 0,
            'programmed_cards': 0,
            'activated_cards': 0,
            'traded_cards': 0,
            'revoked_cards': 0,
            'by_status': {
                'programmed': 0,
                'activated': 0,
                'traded': 0,
                'revoked': 0,
                'damaged': 0
            },
            'by_product': {},
            'recent_activations': 0,
            'pending_trades': 0
        }
        
        # Get recent card batches
        batches_response = api_service.get('/v1/nfc-cards/admin/batches?limit=5')
        recent_batches = batches_response.get('batches', []) if batches_response else []
        
        # Get recent card activities
        activities_response = api_service.get('/v1/nfc-cards/admin/activities?limit=10')
        recent_activities = activities_response.get('activities', []) if activities_response else []
        
        return render_template('admin/nfc_management/dashboard.html',
                             stats=stats,
                             recent_batches=recent_batches,
                             recent_activities=recent_activities)
                             
    except Exception as e:
        flash(f'Error loading NFC dashboard: {str(e)}', 'error')
        # Return with empty data as fallback
        stats = {
            'total_cards': 0, 'programmed_cards': 0, 'activated_cards': 0,
            'traded_cards': 0, 'revoked_cards': 0,
            'by_status': {'programmed': 0, 'activated': 0, 'traded': 0, 'revoked': 0, 'damaged': 0},
            'by_product': {}, 'recent_activations': 0, 'pending_trades': 0
        }
        return render_template('admin/nfc_management/dashboard.html',
                             stats=stats, recent_batches=[], recent_activities=[])

@admin_bp.route('/nfc-cards/cards')
@require_admin_auth
def nfc_cards_list():
    """List all NFC cards with filtering and search"""
    try:
        # Get filter parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status = request.args.get('status', '')
        product_sku = request.args.get('product_sku', '')
        owner_search = request.args.get('owner_search', '')
        batch_code = request.args.get('batch_code', '')
        
        # Build query parameters
        params = {
            'page': page,
            'per_page': per_page
        }
        if status:
            params['status'] = status
        if product_sku:
            params['product_sku'] = product_sku
        if owner_search:
            params['owner_search'] = owner_search
        if batch_code:
            params['batch_code'] = batch_code
        
        # Get cards from API
        cards_response = api_service.get('/v1/nfc-cards/admin/cards', params=params)
        
        if cards_response:
            cards = cards_response.get('cards', [])
            pagination = cards_response.get('pagination', {})
        else:
            cards = []
            pagination = {'page': 1, 'pages': 1, 'total': 0, 'per_page': per_page}
        
        # Get available product SKUs for filter dropdown
        products_response = api_service.get('/v1/catalog/cards')
        available_products = []
        if products_response:
            available_products = [{'product_sku': p['product_sku'], 'name': p['name']} 
                                for p in products_response.get('items', [])]
        
        # Get available batches for filter dropdown
        batches_response = api_service.get('/v1/nfc-cards/admin/batches')
        available_batches = []
        if batches_response:
            available_batches = [{'batch_code': b['batch_code']} 
                               for b in batches_response.get('batches', [])]
        
        return render_template('admin/nfc_management/cards_list.html',
                             cards=cards,
                             pagination=pagination,
                             filters={
                                 'status': status,
                                 'product_sku': product_sku,
                                 'owner_search': owner_search,
                                 'batch_code': batch_code
                             },
                             available_products=available_products,
                             available_batches=available_batches)
                             
    except Exception as e:
        flash(f'Error loading NFC cards: {str(e)}', 'error')
        return render_template('admin/nfc_management/cards_list.html',
                             cards=[], pagination={'page': 1, 'pages': 1, 'total': 0},
                             filters={}, available_products=[], available_batches=[])

@admin_bp.route('/nfc-cards/cards/<int:card_id>')
@require_admin_auth
def nfc_card_detail(card_id):
    """Individual NFC card detail and management"""
    try:
        # Get card details
        card_response = api_service.get(f'/v1/nfc-cards/admin/cards/{card_id}')
        
        if not card_response:
            flash('NFC card not found', 'error')
            return redirect(url_for('admin.nfc_cards_list'))
        
        card = card_response
        
        # Get card history/logs
        history_response = api_service.get(f'/v1/nfc-cards/admin/cards/{card_id}/history')
        card_history = history_response.get('history', []) if history_response else []
        
        # Get security logs
        security_response = api_service.get(f'/v1/nfc-cards/admin/cards/{card_id}/security-logs')
        security_logs = security_response.get('logs', []) if security_response else []
        
        # Get trade history if applicable
        trades_response = api_service.get(f'/v1/nfc-cards/admin/cards/{card_id}/trades')
        trade_history = trades_response.get('trades', []) if trades_response else []
        
        return render_template('admin/nfc_management/card_detail.html',
                             card=card,
                             card_history=card_history,
                             security_logs=security_logs,
                             trade_history=trade_history)
                             
    except Exception as e:
        flash(f'Error loading card details: {str(e)}', 'error')
        return redirect(url_for('admin.nfc_cards_list'))

@admin_bp.route('/nfc-cards/batches')
@require_admin_auth
def nfc_batches_list():
    """List all card production batches"""
    try:
        # Get filter parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        product_sku = request.args.get('product_sku', '')
        status = request.args.get('status', '')
        
        # Build query parameters
        params = {
            'page': page,
            'per_page': per_page
        }
        if product_sku:
            params['product_sku'] = product_sku
        if status:
            params['status'] = status
        
        # Get batches from API
        batches_response = api_service.get('/v1/nfc-cards/admin/batches', params=params)
        
        if batches_response:
            batches = batches_response.get('batches', [])
            pagination = batches_response.get('pagination', {})
        else:
            batches = []
            pagination = {'page': 1, 'pages': 1, 'total': 0, 'per_page': per_page}
        
        # Get available product SKUs for filter dropdown
        products_response = api_service.get('/v1/catalog/cards')
        available_products = []
        if products_response:
            available_products = [{'product_sku': p['product_sku'], 'name': p['name']} 
                                for p in products_response.get('items', [])]
        
        return render_template('admin/nfc_management/batches_list.html',
                             batches=batches,
                             pagination=pagination,
                             filters={
                                 'product_sku': product_sku,
                                 'status': status
                             },
                             available_products=available_products)
                             
    except Exception as e:
        flash(f'Error loading batches: {str(e)}', 'error')
        return render_template('admin/nfc_management/batches_list.html',
                             batches=[], pagination={'page': 1, 'pages': 1, 'total': 0},
                             filters={}, available_products=[])

@admin_bp.route('/nfc-cards/batches/<int:batch_id>')
@require_admin_auth
def nfc_batch_detail(batch_id):
    """Individual batch detail and management"""
    try:
        # Get batch details
        batch_response = api_service.get(f'/v1/nfc-cards/admin/batches/{batch_id}')
        
        if not batch_response:
            flash('Batch not found', 'error')
            return redirect(url_for('admin.nfc_batches_list'))
        
        batch = batch_response
        
        # Get cards in this batch
        cards_response = api_service.get(f'/v1/nfc-cards/admin/batches/{batch_id}/cards')
        batch_cards = cards_response.get('cards', []) if cards_response else []
        
        # Calculate batch statistics
        total_cards = len(batch_cards)
        activated_cards = len([c for c in batch_cards if c.get('status') == 'activated'])
        traded_cards = len([c for c in batch_cards if c.get('status') == 'traded'])
        revoked_cards = len([c for c in batch_cards if c.get('status') == 'revoked'])
        
        batch_stats = {
            'total_cards': total_cards,
            'activated_cards': activated_cards,
            'traded_cards': traded_cards,
            'revoked_cards': revoked_cards,
            'activation_rate': (activated_cards / total_cards * 100) if total_cards > 0 else 0
        }
        
        return render_template('admin/nfc_management/batch_detail.html',
                             batch=batch,
                             batch_cards=batch_cards,
                             batch_stats=batch_stats)
                             
    except Exception as e:
        flash(f'Error loading batch details: {str(e)}', 'error')
        return redirect(url_for('admin.nfc_batches_list'))

@admin_bp.route('/nfc-cards/production')
@require_admin_auth
def nfc_production_dashboard():
    """NFC card production planning and management"""
    try:
        # Get published card templates available for production
        templates_response = api_service.get('/v1/catalog/cards?published=true')
        available_templates = templates_response.get('items', []) if templates_response else []
        
        # Get production statistics
        production_stats_response = api_service.get('/v1/nfc-cards/admin/production-stats')
        production_stats = production_stats_response if production_stats_response else {
            'cards_programmed_today': 0,
            'cards_programmed_this_week': 0,
            'cards_programmed_this_month': 0,
            'active_batches': 0,
            'pending_programming': 0,
            'programming_stations': []
        }
        
        return render_template('admin/nfc_management/production.html',
                             available_templates=available_templates,
                             production_stats=production_stats)
                             
    except Exception as e:
        flash(f'Error loading production dashboard: {str(e)}', 'error')
        return render_template('admin/nfc_management/production.html',
                             available_templates=[], production_stats={})

@admin_bp.route('/nfc-cards/trades')
@require_admin_auth
def nfc_trades_list():
    """List and manage card trades"""
    try:
        # Get filter parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '')
        
        # Build query parameters
        params = {
            'page': page,
            'per_page': per_page
        }
        if status:
            params['status'] = status
        
        # Get trades from API
        trades_response = api_service.get('/v1/nfc-cards/admin/trades', params=params)
        
        if trades_response:
            trades = trades_response.get('trades', [])
            pagination = trades_response.get('pagination', {})
        else:
            trades = []
            pagination = {'page': 1, 'pages': 1, 'total': 0, 'per_page': per_page}
        
        return render_template('admin/nfc_management/trades_list.html',
                             trades=trades,
                             pagination=pagination,
                             filters={'status': status})
                             
    except Exception as e:
        flash(f'Error loading trades: {str(e)}', 'error')
        return render_template('admin/nfc_management/trades_list.html',
                             trades=[], pagination={'page': 1, 'pages': 1, 'total': 0},
                             filters={})

# API Routes for AJAX operations

@admin_bp.route('/api/nfc-cards/<int:card_id>/revoke', methods=['POST'])
@require_admin_auth
def revoke_nfc_card(card_id):
    """Revoke an NFC card (security action)"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Admin revocation')
        
        response = api_service.post(f'/v1/nfc-cards/admin/cards/{card_id}/revoke', {
            'reason': reason
        })
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Card {card_id} revoked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to revoke card'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error revoking card: {str(e)}'
        }), 500

@admin_bp.route('/api/nfc-cards/<int:card_id>/restore', methods=['POST'])
@require_admin_auth
def restore_nfc_card(card_id):
    """Restore a revoked NFC card"""
    try:
        response = api_service.post(f'/v1/nfc-cards/admin/cards/{card_id}/restore')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Card {card_id} restored successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to restore card'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error restoring card: {str(e)}'
        }), 500

@admin_bp.route('/api/nfc-cards/batch/<int:batch_id>/export', methods=['GET'])
@require_admin_auth
def export_batch_data(batch_id):
    """Export batch data as CSV"""
    try:
        response = api_service.get(f'/v1/nfc-cards/admin/batches/{batch_id}/export')
        
        if response:
            return jsonify(response)
        else:
            return jsonify({
                'error': 'Failed to export batch data'
            }), 400
            
    except Exception as e:
        return jsonify({
            'error': f'Error exporting batch: {str(e)}'
        }), 500

@admin_bp.route('/api/nfc-cards/stats/real-time', methods=['GET'])
@require_admin_auth
def get_nfc_realtime_stats():
    """Get real-time NFC card statistics"""
    try:
        stats_response = api_service.get('/v1/nfc-cards/admin/stats/real-time')
        
        if stats_response:
            return jsonify(stats_response)
        else:
            return jsonify({
                'error': 'Failed to get real-time stats'
            }), 400
            
    except Exception as e:
        return jsonify({
            'error': f'Error getting stats: {str(e)}'
        }), 500
