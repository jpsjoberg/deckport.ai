#!/bin/bash

echo "📡 Manual Console Log Upload to Server"
echo "======================================"

# Collect all critical logs and system info
TIMESTAMP=$(date -Iseconds)
HOSTNAME=$(hostname)

echo "Collecting system logs..."

# Create comprehensive log data
LOG_DATA="CONSOLE LOG UPLOAD - $TIMESTAMP
HOSTNAME: $HOSTNAME
========================================

=== SYSTEM INFO ===
$(uname -a)
$(free -h)
$(df -h)
$(lsmod | grep -E 'i915|drm|video')

=== GRAPHICS HARDWARE ===
$(lspci | grep -i 'vga\|display\|graphics')

=== GRAPHICS DEVICES ===
$(ls -la /dev/dri/ 2>/dev/null || echo 'No DRI devices')
$(ls -la /dev/fb* 2>/dev/null || echo 'No framebuffer devices')

=== X11 LOGS (CRITICAL) ===
$(tail -50 /var/log/Xorg.0.log 2>/dev/null || echo 'No X11 logs')

=== CONSOLE LOGS ===
$(cat /var/log/deckport-console.log 2>/dev/null || echo 'No console logs')

=== SYSTEMD SERVICES ===
$(systemctl status deckport-kiosk.service --no-pager 2>/dev/null || echo 'Kiosk service not found')
$(systemctl status getty@tty1.service --no-pager 2>/dev/null || echo 'Getty service not found')

=== AUTO-LOGIN CONFIG ===
$(cat /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || echo 'No auto-login config')

=== RECENT SYSTEM LOGS ===
$(journalctl --since '10 minutes ago' --no-pager | tail -30)

=== KIOSK STARTUP LOGS ===
$(journalctl -u deckport-kiosk.service --no-pager 2>/dev/null || echo 'No kiosk service logs')

=== X11 CONFIGURATION ===
$(cat /etc/X11/xorg.conf 2>/dev/null || echo 'No main xorg.conf')
$(ls -la /etc/X11/xorg.conf.d/ 2>/dev/null || echo 'No xorg.conf.d')
$(cat /etc/X11/xorg.conf.d/*.conf 2>/dev/null || echo 'No X11 config files')

=== GRUB CONFIGURATION ===
$(cat /etc/default/grub | grep -E 'CMDLINE|i915')

=== PROCESSES ===
$(ps aux | grep -E 'X|kiosk|godot|game' | head -10)

=== NETWORK ===
$(ip addr show | grep -E 'inet|state')

========================================
END LOG DATA"

echo "Sending logs to server..."

# Send to API endpoint
curl -X POST "https://api.deckport.ai/v1/console-logs/crash-report" \
    -H "Content-Type: application/json" \
    -d "{
        \"console_id\": \"manual-upload-$(date +%s)\",
        \"device_uid\": \"$HOSTNAME\",
        \"crash_type\": \"manual_debug\",
        \"error_message\": \"Manual log upload for debugging\",
        \"system_state\": {},
        \"log_files\": {
            \"all_logs\": {
                \"content\": $(echo "$LOG_DATA" | jq -R -s .),
                \"compressed\": false
            }
        }
    }" 2>&1

echo ""
echo "✅ Log upload complete!"
echo "Check admin panel or database for logs."
