#!/bin/bash
# NFC Card Programmer Dependencies Installation Script

echo "🔧 Installing NFC Card Programmer Dependencies"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run this script as root/sudo"
   echo "💡 Run as regular user, script will ask for sudo when needed"
   exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    libnfc-bin \
    libnfc-dev \
    libusb-1.0-0-dev \
    pkg-config \
    python3-dev \
    python3-pip

# Add user to dialout group (needed for USB NFC readers)
echo "👤 Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user nfcpy cryptography requests

# Test NFC setup
echo ""
echo "🧪 Testing NFC setup..."
echo "========================================"

# Check if nfcpy is installed
python3 -c "import nfc; print('✅ nfcpy library installed')" 2>/dev/null || echo "❌ nfcpy installation failed"

# Check if NFC reader is detected
echo "🔍 Checking for NFC readers..."
if command -v nfc-list &> /dev/null; then
    nfc-list || echo "⚠️  No NFC readers detected (this is normal if none are connected)"
else
    echo "⚠️  nfc-list command not available"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Connect your NFC reader via USB"
echo "2. Log out and log back in (or restart) to apply group changes"
echo "3. Test with: python3 scripts/nfc_card_programmer.py --check-hardware"
echo ""
echo "🔧 Supported NFC readers:"
echo "   - ACR122U (USB, ~$40)"
echo "   - PN532 (Arduino/Pi, ~$15)" 
echo "   - ACR1252U (USB contactless, ~$60)"
echo "   - Most libnfc-compatible readers"
echo ""
echo "❓ Troubleshooting:"
echo "   - If reader not detected: sudo systemctl restart pcscd"
echo "   - Check permissions: ls -la /dev/ttyUSB* /dev/ttyACM*"
echo "   - Test manually: nfc-list"
