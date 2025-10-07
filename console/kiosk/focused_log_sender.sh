#!/bin/bash

echo "📡 Focused Console Log Sender"
echo "============================="

API_URL="https://api.deckport.ai/v1/debug/simple"
CONSOLE_ID="$(hostname)-$(date +%s)"

send_log() {
    local log_name="$1"
    local log_data="$2"
    
    echo "Sending $log_name..."
    
    echo "LOG: $log_name
CONSOLE: $CONSOLE_ID
TIME: $(date)
DATA:
$log_data" | curl -X POST "$API_URL" -d @- -H "Content-Type: text/plain" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ $log_name sent"
    else
        echo "❌ $log_name failed"
    fi
    sleep 1
}

echo "Sending critical logs one by one..."

# 1. Graphics Hardware
send_log "GRAPHICS_HARDWARE" "$(lspci | grep -i 'vga\|display\|graphics')"

# 2. Graphics Drivers
send_log "GRAPHICS_DRIVERS" "$(lsmod | grep -E 'i915|drm|video')"

# 3. Graphics Devices
send_log "GRAPHICS_DEVICES" "$(ls -la /dev/dri/ 2>/dev/null || echo 'No DRI devices found')"

# 4. X11 Errors (most critical)
send_log "X11_ERRORS" "$(tail -100 /var/log/Xorg.0.log 2>/dev/null || echo 'No X11 logs found')"

# 5. Kiosk Service Status
send_log "KIOSK_SERVICE" "$(systemctl status deckport-kiosk.service --no-pager 2>/dev/null || echo 'Service not found')"

# 6. Auto-login Config
send_log "AUTO_LOGIN" "$(cat /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || echo 'No auto-login config')"

# 7. Recent System Logs
send_log "SYSTEM_LOGS" "$(journalctl --since '5 minutes ago' --no-pager | tail -100)"

# 8. X11 Configuration
send_log "X11_CONFIG" "$(cat /etc/X11/xorg.conf.d/*.conf 2>/dev/null || echo 'No X11 config files')"

# 9. GRUB Parameters
send_log "GRUB_PARAMS" "$(cat /etc/default/grub | grep CMDLINE)"

# 10. Process Status
send_log "PROCESSES" "$(ps aux | grep -E 'X|kiosk|godot|game' | head -20)"

# 11. Godot Game Logs (if they exist)
send_log "GODOT_GAME_LOGS" "$(tail -100 /var/log/godot-game.log 2>/dev/null || echo 'No Godot game logs found')"

# 12. Console Startup Logs
send_log "CONSOLE_STARTUP" "$(tail -100 /var/log/deckport-console.log 2>/dev/null || echo 'No console startup logs found')"

# 13. NFC Reader Status
send_log "NFC_READERS" "$(timeout 5 nfc-list 2>/dev/null || echo 'No NFC readers or nfc-list not available')"

# 14. USB Devices (for NFC reader detection)
send_log "USB_DEVICES" "$(lsusb | grep -E 'NFC|072f|1fc9|Smart|Card' || echo 'No NFC-related USB devices found')"

echo ""
echo "✅ All logs sent individually (enhanced with 100-line capture)!"
echo "Check server for received data."
