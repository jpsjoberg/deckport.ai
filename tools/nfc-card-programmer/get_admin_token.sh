#!/bin/bash

echo "🔑 Getting Admin Token for NFC Card Programmer"
echo "=============================================="

# Default credentials
EMAIL="admin@deckport.ai"
PASSWORD="admin123"
API_URL="https://api.deckport.ai"

# Allow custom credentials
if [ "$1" != "" ]; then
    EMAIL="$1"
fi

if [ "$2" != "" ]; then
    PASSWORD="$2"
fi

echo "📧 Email: $EMAIL"
echo "🌐 API URL: $API_URL"
echo ""

# Get admin token
echo "🔐 Requesting admin token..."

RESPONSE=$(curl -s -X POST "$API_URL/v1/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

# Check if response contains access_token
if echo "$RESPONSE" | grep -q "access_token"; then
    # Extract token from JSON response
    TOKEN=$(echo "$RESPONSE" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
    
    if [ "$TOKEN" != "" ]; then
        echo "✅ Admin token obtained successfully!"
        echo ""
        echo "📋 Copy and run this command:"
        echo "export ADMIN_TOKEN=\"$TOKEN\""
        echo ""
        echo "🎯 Then you can use the NFC card programmer:"
        echo "python nfc_card_programmer.py --list-cards"
        echo "python nfc_card_programmer.py --interactive"
        echo ""
        echo "💾 Save to file (optional):"
        echo "echo 'export ADMIN_TOKEN=\"$TOKEN\"' > ~/.deckport_token"
        echo "source ~/.deckport_token"
        
        # Optionally save to env file
        echo "ADMIN_TOKEN=\"$TOKEN\"" > config.env
        echo "API_URL=\"$API_URL\"" >> config.env
        echo ""
        echo "📁 Token saved to config.env"
        echo "   Use: source config.env"
    else
        echo "❌ Failed to extract token from response"
        echo "Response: $RESPONSE"
    fi
else
    echo "❌ Login failed"
    echo "Response: $RESPONSE"
    echo ""
    echo "💡 Check:"
    echo "   - API server is running: $API_URL"
    echo "   - Credentials are correct: $EMAIL / $PASSWORD"
    echo "   - Network connectivity to server"
fi
