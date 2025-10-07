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
from . import nfc_management
from . import shop_management
# Temporarily disabled - fixing import issues
# from . import card_generation_ai
# from . import card_set_generator_ai
from . import console_management
from . import arena_management
from . import game_operations
from . import player_management
from . import communications
from . import analytics
from . import system_admin
# Temporarily disabled - import error
# from . import security_monitoring
from . import cms
from . import console_logs
from . import asset_generation
# from . import card_batch_production  # Temporarily disabled - has shared import issues
# from . import card_database_production  # Temporarily disabled - has shared import issues
