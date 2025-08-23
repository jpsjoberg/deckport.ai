"""
Communications Routes for Deckport Admin Panel
Handles multi-channel community engagement and marketing
"""

from flask import render_template, jsonify
from . import admin_bp


@admin_bp.route('/communications')
def communications():
    """Communications hub dashboard"""
    return render_template('admin/communications/index.html')
