#!/bin/bash
# Development startup script for Deckport.ai (New Structure)

set -e

echo "🚀 Starting Deckport.ai Development Environment (New Structure)"

# Set environment variables
export API_BASE=http://127.0.0.1:8002
export LOG_LEVEL=INFO

# Check if API is running
if ! curl -s http://127.0.0.1:8002/health > /dev/null; then
    echo "⚠️  API is not running on port 8002. The systemd service should be running."
    echo "   Check with: systemctl status api"
    exit 1
fi

echo "✅ API is running on port 8002"

# Start frontend
echo "🌐 Starting Frontend on port 5000"
cd /home/jp/deckport.ai/services/frontend

# Activate venv and install requirements if needed
source venv/bin/activate

# Check if requests is installed
if ! python -c "import requests" 2>/dev/null; then
    echo "📦 Installing frontend requirements..."
    pip install -r requirements.txt
fi

# Start the frontend
echo "🎯 Frontend starting at http://127.0.0.1:5000"
echo "   API backend: $API_BASE"
echo "   Press Ctrl+C to stop"
echo ""
echo "🏗️  Note: Using new project structure!"
echo "   - API routes now organized in services/api/routes/"
echo "   - Shared models in shared/models/"
echo "   - Authentication with JWT tokens"
python app.py