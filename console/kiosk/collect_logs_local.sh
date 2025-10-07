#!/bin/bash

echo "🔍 Collecting Console Logs Locally"
echo "=================================="

LOG_FILE="/tmp/console_debug_$(date +%s).txt"

echo "Saving logs to: $LOG_FILE"

{
echo "DECKPORT CONSOLE DEBUG LOG"
echo "Generated: $(date)"
echo "Hostname: $(hostname)"
echo "=================================="

echo ""
echo "=== GRAPHICS HARDWARE ==="
lspci | grep -i 'vga\|display\|graphics'

echo ""
echo "=== GRAPHICS DRIVERS ==="
lsmod | grep -E 'i915|drm|video'

echo ""
echo "=== GRAPHICS DEVICES ==="
ls -la /dev/dri/ 2>/dev/null || echo "No DRI devices"
ls -la /dev/fb* 2>/dev/null || echo "No framebuffer devices"

echo ""
echo "=== X11 ERRORS (CRITICAL) ==="
tail -20 /var/log/Xorg.0.log 2>/dev/null || echo "No X11 logs"

echo ""
echo "=== KIOSK SERVICE STATUS ==="
systemctl status deckport-kiosk.service --no-pager 2>/dev/null || echo "Service not found"

echo ""
echo "=== AUTO-LOGIN CONFIG ==="
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || echo "No config"

echo ""
echo "=== GRUB KERNEL PARAMETERS ==="
cat /etc/default/grub | grep CMDLINE

echo ""
echo "=== RECENT SYSTEM LOGS ==="
journalctl --since '5 minutes ago' --no-pager | tail -15

} > "$LOG_FILE"

echo ""
echo "✅ Logs collected in: $LOG_FILE"
echo ""
echo "🔍 CRITICAL X11 ERRORS:"
echo "======================"
tail -10 /var/log/Xorg.0.log 2>/dev/null | grep -E "(EE)|(WW)|(error)" || echo "No X11 errors found"

echo ""
echo "📊 GRAPHICS DEVICE STATUS:"
echo "========================="
if [ -c "/dev/dri/card0" ]; then
    echo "✅ Graphics device exists: /dev/dri/card0"
else
    echo "❌ Graphics device missing: /dev/dri/card0"
fi

echo ""
echo "🎮 GAME STATUS:"
echo "=============="
if [ -f "/opt/godot-game/game.x86_64" ]; then
    echo "✅ Game executable exists"
    ls -la /opt/godot-game/game.x86_64
else
    echo "❌ Game executable missing"
fi

echo ""
echo "📁 Full log saved to: $LOG_FILE"
echo "You can view it with: cat $LOG_FILE"
