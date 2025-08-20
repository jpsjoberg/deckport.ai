#!/usr/bin/env python3
"""
WSGI entry point for Deckport API service
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, '/home/jp/deckport.ai')

# Import the Flask app from the new structure
from app import app

# The app is imported from app.py with all routes and blueprints

# WSGI entrypoint
if __name__ == "__main__":
    app.run(debug=True)
