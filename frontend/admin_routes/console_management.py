"""
Console Management Routes for Deckport Admin Panel
Handles console fleet management, diagnostics, and deployment
"""

import requests
from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime, timezone
from . import admin_bp
from ..services.api_service import APIService

# Initialize API service
api_service = APIService()

@admin_bp.route('/consoles')
def console_management():
    """Console fleet management dashboard"""
    try:
        # Get console fleet data from API
        consoles_response = api_service.get('/v1/admin/devices')
        pending_response = api_service.get('/v1/admin/devices?status=pending')
        
        consoles = consoles_response.get('devices', []) if consoles_response else []
        pending_consoles = pending_response.get('devices', []) if pending_response else []
        
        # Calculate fleet statistics
        total_consoles = len(consoles)
        online_count = len([c for c in consoles if c.get('status') == 'active' and c.get('last_seen_minutes', 999) < 5])
        offline_count = len([c for c in consoles if c.get('status') == 'active' and c.get('last_seen_minutes', 0) >= 5])
        maintenance_count = len([c for c in consoles if c.get('status') == 'maintenance'])
        pending_count = len(pending_consoles)
        
        fleet_stats = {
            'total': total_consoles,
            'online': online_count,
            'offline': offline_count,
            'maintenance': maintenance_count,
            'pending': pending_count
        }
        
        return render_template('admin/console_management/index.html', 
                             consoles=consoles, 
                             pending_consoles=pending_consoles[:3],  # Show first 3 in sidebar
                             fleet_stats=fleet_stats)
                             
    except Exception as e:
        flash(f'Error loading console data: {str(e)}', 'error')
        # Return with mock data as fallback
        fleet_stats = {'total': 0, 'online': 0, 'offline': 0, 'maintenance': 0, 'pending': 0}
        return render_template('admin/console_management/index.html', 
                             consoles=[], 
                             pending_consoles=[],
                             fleet_stats=fleet_stats)

@admin_bp.route('/consoles/<device_uid>')
def console_detail(device_uid):
    """Individual console detail and management"""
    try:
        # Get specific console data
        console_response = api_service.get(f'/v1/admin/devices/{device_uid}')
        
        if not console_response:
            flash('Console not found', 'error')
            return redirect(url_for('admin.console_management'))
            
        console = console_response
        
        # Get console logs and diagnostics
        logs_response = api_service.get(f'/v1/admin/devices/{device_uid}/logs')
        diagnostics_response = api_service.get(f'/v1/admin/devices/{device_uid}/diagnostics')
        
        console['logs'] = logs_response.get('logs', []) if logs_response else []
        console['diagnostics'] = diagnostics_response.get('diagnostics', {}) if diagnostics_response else {}
        
        return render_template('admin/console_management/console_detail.html', console=console)
        
    except Exception as e:
        flash(f'Error loading console details: {str(e)}', 'error')
        return redirect(url_for('admin.console_management'))

@admin_bp.route('/consoles/registration')
def console_registration():
    """Console registration approval interface"""
    try:
        # Get all pending registrations
        pending_response = api_service.get('/v1/admin/devices?status=pending')
        pending_consoles = pending_response.get('devices', []) if pending_response else []
        
        return render_template('admin/console_management/registration.html', 
                             pending_consoles=pending_consoles)
                             
    except Exception as e:
        flash(f'Error loading pending registrations: {str(e)}', 'error')
        return render_template('admin/console_management/registration.html', 
                             pending_consoles=[])

# API Routes for AJAX calls
@admin_bp.route('/api/console/<device_uid>/approve', methods=['POST'])
def approve_console(device_uid):
    """Approve a pending console registration"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/approve', 
                                  {'approved': True})
        
        if response and response.get('status') == 'approved':
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} approved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to approve console'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error approving console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/reject', methods=['POST'])
def reject_console(device_uid):
    """Reject a pending console registration"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/reject', 
                                  {'approved': False})
        
        if response:
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} rejected'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reject console'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error rejecting console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/reboot', methods=['POST'])
def reboot_console(device_uid):
    """Send reboot command to console"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/reboot')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Reboot command sent to {device_uid}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send reboot command'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error rebooting console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/shutdown', methods=['POST'])
def shutdown_console(device_uid):
    """Send shutdown command to console"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/shutdown')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Shutdown command sent to {device_uid}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send shutdown command'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error shutting down console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/ping', methods=['POST'])
def ping_console(device_uid):
    """Send ping to offline console"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/ping')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Ping sent to {device_uid}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Console did not respond to ping'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pinging console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/status', methods=['GET'])
def get_console_status(device_uid):
    """Get real-time console status"""
    try:
        response = api_service.get(f'/v1/admin/devices/{device_uid}/status')
        
        if response:
            return jsonify(response)
        else:
            return jsonify({
                'error': 'Console not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': f'Error getting console status: {str(e)}'
        }), 500

@admin_bp.route('/api/consoles/fleet-status', methods=['GET'])
def get_fleet_status():
    """Get real-time fleet status for dashboard updates"""
    try:
        consoles_response = api_service.get('/v1/admin/devices')
        consoles = consoles_response.get('devices', []) if consoles_response else []
        
        # Calculate real-time statistics
        total_consoles = len(consoles)
        online_count = len([c for c in consoles if c.get('status') == 'active' and c.get('last_seen_minutes', 999) < 5])
        offline_count = len([c for c in consoles if c.get('status') == 'active' and c.get('last_seen_minutes', 0) >= 5])
        maintenance_count = len([c for c in consoles if c.get('status') == 'maintenance'])
        
        return jsonify({
            'total': total_consoles,
            'online': online_count,
            'offline': offline_count,
            'maintenance': maintenance_count,
            'consoles': consoles
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting fleet status: {str(e)}'
        }), 500