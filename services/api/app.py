import os
import sys

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

from flask import Flask, jsonify
from dotenv import load_dotenv
from shared.utils.logging import setup_logging
from routes.health import health_bp
from routes.auth import auth_bp
from routes.cards import cards_bp
from routes.device_auth import device_auth_bp
from routes.console_login import console_login_bp
from routes.console_logs import console_logs_bp
from routes.arenas import arenas_bp
from routes.video_streaming import video_streaming_bp
from routes.nfc_cards import nfc_cards_bp
from routes.admin_analytics import admin_analytics_bp
from routes.admin_alerts import admin_alerts_bp
from routes.admin_communications import admin_communications_bp
from routes.admin_players import admin_players_bp
from routes.admin_devices import admin_devices_bp
from routes.admin_arenas import admin_arenas_bp
from routes.admin_game_operations import admin_game_ops_bp
from routes.admin_player_management import admin_player_mgmt_bp
from routes.admin_dashboard_stats import admin_dashboard_stats_bp
from routes.admin_tournaments import admin_tournaments_bp
from routes.admin_security_monitoring import admin_security_bp
from routes.player_wallet import player_wallet_bp
from routes.gameplay import gameplay_bp
from routes.card_pack import card_pack_bp
from routes.shop_admin import shop_admin_bp
from routes.shop import shop_bp
from routes.user_profile import user_profile_bp
from routes.nfc_admin import nfc_admin_bp
from routes.admin_profiles import admin_profiles_bp
from routes.admin_cms import admin_cms_bp
from routes.cms_public import cms_public_bp
from routes.product_categories import product_categories_bp
from routes.console_heartbeat import console_heartbeat_bp
from routes.console_logs_streaming import console_logs_streaming_bp
from routes.debug_upload import debug_upload_bp
from routes.admin_card_sets import admin_card_sets_bp
from routes.admin_cards_stats import admin_cards_stats_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Set up logging
logger = setup_logging("api", os.getenv("LOG_LEVEL", "INFO"))

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(cards_bp)
app.register_blueprint(device_auth_bp)
app.register_blueprint(console_login_bp)
app.register_blueprint(console_logs_bp)
app.register_blueprint(arenas_bp)
app.register_blueprint(video_streaming_bp)
app.register_blueprint(nfc_cards_bp)
app.register_blueprint(admin_analytics_bp)
app.register_blueprint(admin_alerts_bp)
app.register_blueprint(admin_communications_bp)
app.register_blueprint(admin_players_bp)
app.register_blueprint(admin_devices_bp)
app.register_blueprint(admin_arenas_bp)
app.register_blueprint(admin_game_ops_bp)
app.register_blueprint(admin_player_mgmt_bp)
app.register_blueprint(admin_dashboard_stats_bp)
app.register_blueprint(admin_tournaments_bp)
app.register_blueprint(admin_security_bp)
app.register_blueprint(player_wallet_bp)
app.register_blueprint(gameplay_bp)
app.register_blueprint(card_pack_bp)
app.register_blueprint(shop_admin_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(user_profile_bp)
app.register_blueprint(nfc_admin_bp)
app.register_blueprint(admin_profiles_bp)
app.register_blueprint(admin_cms_bp)
app.register_blueprint(cms_public_bp)
# app.register_blueprint(product_categories_bp)  # Temporarily disabled
app.register_blueprint(console_heartbeat_bp)
app.register_blueprint(console_logs_streaming_bp)
app.register_blueprint(debug_upload_bp)
app.register_blueprint(admin_card_sets_bp)
app.register_blueprint(admin_cards_stats_bp)

# Legacy endpoints for backward compatibility
@app.get("/v1/hello")
def hello():
    return jsonify(message="Hello from API - new structure active!")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# WSGI entrypoint
if __name__ == "__main__":
    app.run(debug=True)
