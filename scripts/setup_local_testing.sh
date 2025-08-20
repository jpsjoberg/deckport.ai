#!/bin/bash
# Setup script for local testing environment
# Run this on your local development machine

echo "🛠️  Setting up Deckport.ai Local Testing Environment"

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python: $python_version"

# Create virtual environment for testing
echo "📦 Creating test environment..."
python3 -m venv deckport-test-env
source deckport-test-env/bin/activate

# Install test dependencies
echo "📥 Installing test dependencies..."
pip install websockets requests asyncio

echo ""
echo "✅ Local testing environment ready!"
echo ""
echo "📋 Usage Examples:"
echo ""
echo "# Test your remote server (replace with your server IP/domain):"
echo "python local_test_client.py --server YOUR_SERVER_IP"
echo ""
echo "# Test specific components:"
echo "python local_test_client.py --server YOUR_SERVER_IP --test-only api"
echo "python local_test_client.py --server YOUR_SERVER_IP --test-only websocket"
echo "python local_test_client.py --server YOUR_SERVER_IP --test-only frontend"
echo ""
echo "# Interactive WebSocket testing:"
echo "python local_test_client.py --server YOUR_SERVER_IP --interactive"
echo ""
echo "# Test production server with HTTPS:"
echo "python local_test_client.py --server deckport.ai --https"
echo ""
echo "🔧 Configuration:"
echo "   - API will be tested on port 8002 (or api.domain.com)"
echo "   - WebSocket will be tested on port 8003 (or ws.domain.com)"
echo "   - Frontend will be tested on port 5000 (or domain.com)"
echo ""
echo "🎯 To test now:"
echo "   source deckport-test-env/bin/activate"
echo "   python local_test_client.py --server YOUR_SERVER_IP"
