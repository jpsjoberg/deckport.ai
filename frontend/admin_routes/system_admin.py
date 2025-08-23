"""
System Administration Routes for Deckport Admin Panel
Handles infrastructure management, security, and maintenance
"""

from flask import render_template, jsonify
from . import admin_bp


@admin_bp.route('/system')
def system_admin():
    """System administration dashboard"""
    return render_template('admin/system_admin/index.html')
