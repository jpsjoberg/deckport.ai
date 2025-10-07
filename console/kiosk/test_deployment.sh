#!/bin/bash

# Test deployment script to identify issues
echo "🧪 Testing Deckport Console Deployment System"
echo "=============================================="

# Test 1: Check deployment server connectivity
echo "1️⃣ Testing deployment server connectivity..."
if curl -s https://deckport.ai/deploy/status > /dev/null; then
    echo "✅ Deployment server is accessible"
    curl -s https://deckport.ai/deploy/status
else
    echo "❌ Cannot reach deployment server"
    exit 1
fi

echo ""

# Test 2: Check asset availability
echo "2️⃣ Testing asset downloads..."
assets=("wifi-portal" "boot-theme" "configs" "godot-game/latest")

for asset in "${assets[@]}"; do
    echo "Testing: $asset"
    if curl -I https://deckport.ai/deploy/assets/$asset 2>/dev/null | grep -q "200 OK"; then
        echo "✅ $asset is available"
    else
        echo "❌ $asset is not available"
    fi
done

echo ""

# Test 3: Download and check deployment script
echo "3️⃣ Testing deployment script download..."
SCRIPT_SIZE=$(curl -s https://deckport.ai/deploy/console | wc -c)
if [ $SCRIPT_SIZE -gt 1000 ]; then
    echo "✅ Deployment script downloaded ($SCRIPT_SIZE bytes)"
    echo "Script preview:"
    curl -s https://deckport.ai/deploy/console | head -20
else
    echo "❌ Deployment script seems too small or empty"
fi

echo ""

# Test 4: Check if we're on a kiosk system
echo "4️⃣ Checking system environment..."
if [ "$USER" = "kiosk" ]; then
    echo "✅ Running as kiosk user"
elif [ "$USER" = "root" ]; then
    echo "⚠️ Running as root - script should be run as kiosk user"
else
    echo "ℹ️ Running as user: $USER"
fi

if which sudo > /dev/null; then
    echo "✅ sudo is available"
else
    echo "❌ sudo is not available"
fi

echo ""

# Test 5: Check network connectivity
echo "5️⃣ Testing network connectivity..."
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ Internet connectivity working"
else
    echo "❌ No internet connectivity"
fi

echo ""
echo "=============================================="
echo "Test completed. If all tests pass, the deployment should work."
echo ""
echo "To run actual deployment:"
echo "curl -sSL https://deckport.ai/deploy/console | bash"
echo ""
echo "With custom parameters:"
echo "curl -sSL \"https://deckport.ai/deploy/console?id=test-console&location=Test%20Lab\" | bash"
