"""
Analytics Routes for Deckport Admin Panel
Handles business intelligence, reporting, and data analysis
"""

from flask import render_template, jsonify
from . import admin_bp


@admin_bp.route('/analytics')
def analytics():
    """Analytics dashboard"""
    return render_template('admin/analytics/index.html')
