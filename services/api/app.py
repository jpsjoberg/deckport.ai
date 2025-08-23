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
from routes.admin_devices import admin_devices_bp
from routes.admin_game_operations import admin_game_ops_bp
from routes.admin_player_management import admin_player_mgmt_bp
from routes.gameplay import gameplay_bp

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
app.register_blueprint(admin_devices_bp)
app.register_blueprint(admin_game_ops_bp)
app.register_blueprint(admin_player_mgmt_bp)
app.register_blueprint(gameplay_bp)

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
