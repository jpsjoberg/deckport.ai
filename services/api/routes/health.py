"""
Health check routes
"""

from flask import Blueprint, jsonify
from sqlalchemy import text
from shared.database.connection import SessionLocal

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with database connectivity test"""
    try:
        # Test database connection
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return jsonify({
            "status": "ok",
            "database": "connected",
            "service": "api"
        })
    except Exception as e:
        return jsonify({
            "status": "ok", 
            "database": "disconnected",
            "error": str(e),
            "service": "api"
        }), 500
