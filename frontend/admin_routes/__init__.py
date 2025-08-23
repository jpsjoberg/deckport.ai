"""
Admin routes package for Deckport Admin Panel
Provides comprehensive management interface for the entire ecosystem
"""

from flask import Blueprint

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import all route modules to register them
from . import dashboard
from . import card_management
from . import console_management
from . import game_operations
from . import player_management
from . import communications
from . import analytics
from . import system_admin
