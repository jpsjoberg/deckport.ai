#!/bin/bash

echo "🔍 Deckport Console Quick Diagnostics"
echo "====================================="

echo ""
echo "🖥️ GRAPHICS HARDWARE:"
lspci | grep -i 'vga\|display\|graphics'

echo ""
echo "📦 GRAPHICS DRIVERS:"
lsmod | grep -E 'i915|nouveau|radeon|amdgpu' || echo "No graphics drivers loaded"

echo ""
echo "🎮 GRAPHICS DEVICES:"
ls -la /dev/dri/ 2>/dev/null || echo "No DRM devices found"

echo ""
echo "👤 USER GROUPS:"
echo "Current user: $(whoami)"
echo "Groups: $(groups)"

echo ""
echo "🔐 AUTO-LOGIN CONFIG:"
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || echo "No auto-login config found"

echo ""
echo "📋 KIOSK SERVICE:"
systemctl status deckport-kiosk.service --no-pager 2>/dev/null || echo "Deckport kiosk service not found"

echo ""
echo "🖼️ X11 ERRORS (Last 10 lines):"
tail -10 /var/log/Xorg.0.log 2>/dev/null || echo "No X11 logs found"

echo ""
echo "🎯 GAME STATUS:"
ls -la /opt/godot-game/ 2>/dev/null || echo "No game directory found"

echo ""
echo "⚙️ SYSTEM TARGET:"
systemctl get-default

echo ""
echo "🔧 CONSOLE CONFIG:"
cat /opt/deckport-console/console.conf 2>/dev/null || echo "No console config found"

echo ""
echo "====================================="
echo "🎯 CRITICAL ISSUES CHECK:"

# Check for common problems
if ! lsmod | grep -q i915; then
    echo "❌ Intel graphics driver not loaded"
fi

if [ ! -c /dev/dri/card0 ]; then
    echo "❌ No graphics device (/dev/dri/card0)"
fi

if ! groups | grep -q video; then
    echo "❌ User not in video group"
fi

if [ ! -f /etc/systemd/system/getty@tty1.service.d/autologin.conf ]; then
    echo "❌ Auto-login not configured"
fi

if ! systemctl is-enabled deckport-kiosk.service >/dev/null 2>&1; then
    echo "❌ Kiosk service not enabled"
fi

echo "====================================="
