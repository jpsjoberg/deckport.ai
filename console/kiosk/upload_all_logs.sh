#!/bin/bash

echo "📡 Deckport Console - Complete Log Upload"
echo "========================================"
echo "🔍 Collecting all system logs..."
echo "📤 Will upload to server for analysis"
echo "========================================"

# Configuration
API_ENDPOINT="https://api.deckport.ai/v1/debug/simple"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/deckport_complete_logs_${TIMESTAMP}.txt"
HOSTNAME=$(hostname)

echo "📁 Creating log file: $LOG_FILE"

# Collect comprehensive log data
{
echo "DECKPORT CONSOLE COMPLETE LOG UPLOAD"
echo "Generated: $(date -Iseconds)"
echo "Hostname: $HOSTNAME"
echo "Timestamp: $TIMESTAMP"
echo "=============================================="

echo ""
echo "=== DEPLOYMENT ERROR DETAILS ==="
echo "Error: Failed to download game"
echo "Console: $HOSTNAME"
echo "Time: $(date)"

echo ""
echo "=== SYSTEM INFORMATION ==="
echo "OS: $(uname -a)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo "Uptime: $(uptime)"
echo "Load: $(cat /proc/loadavg)"

echo ""
echo "=== NETWORK CONNECTIVITY TESTS ==="
echo "DNS Test: $(nslookup deckport.ai 2>/dev/null | grep -A1 'Name:' || echo 'DNS_FAILED')"
echo "Internet: $(ping -c 2 8.8.8.8 2>/dev/null | tail -1 || echo 'PING_FAILED')"
echo "API Health: $(curl -s -w 'HTTP_%{http_code}' https://api.deckport.ai/health 2>/dev/null || echo 'API_FAILED')"
echo "Deployment Script: $(curl -s -I https://deckport.ai/deploy/console 2>/dev/null | head -1 || echo 'DEPLOY_SCRIPT_FAILED')"
echo "Game Download: $(curl -s -I https://deckport.ai/deploy/assets/godot-game/latest 2>/dev/null | head -1 || echo 'GAME_DOWNLOAD_FAILED')"

echo ""
echo "=== RECENT DEPLOYMENT LOGS (CRITICAL) ==="
journalctl --since '1 hour ago' | grep -i 'deploy\|download\|curl\|error\|fail' | tail -30

echo ""
echo "=== SYSTEM SERVICES STATUS ==="
systemctl status --no-pager | head -10
echo ""
echo "Failed services:"
systemctl --failed --no-pager

echo ""
echo "=== GRAPHICS HARDWARE ==="
lspci | grep -i 'vga\|display\|graphics'
echo ""
echo "Graphics drivers:"
lsmod | grep -E 'i915|drm|video|nouveau|amdgpu'

echo ""
echo "=== GRAPHICS DEVICES ==="
ls -la /dev/dri/ 2>/dev/null || echo "No DRI devices found"
ls -la /dev/fb* 2>/dev/null || echo "No framebuffer devices found"

echo ""
echo "=== X11 LOGS (DISPLAY ISSUES) ==="
tail -30 /var/log/Xorg.0.log 2>/dev/null || echo "No X11 logs found"

echo ""
echo "=== GAME CRASH LOGS (CRITICAL) ==="
cat /var/log/godot-game-crashes.log 2>/dev/null || echo "No game crash logs found"

echo ""
echo "=== GAME RUNTIME LOGS ==="
tail -50 /var/log/godot-game.log 2>/dev/null || echo "No game runtime logs found"

echo ""
echo "=== DEPLOYMENT LOGS ==="
tail -100 /var/log/deckport-deployment.log 2>/dev/null || echo "No deployment logs found"

echo ""
echo "=== SYSTEMD LOGS (RECENT ERRORS) ==="
journalctl --since '30 minutes ago' --priority=err --no-pager | tail -20

echo ""
echo "=== NETWORK INTERFACES ==="
ip addr show | grep -E 'inet|state|mtu'

echo ""
echo "=== DISK SPACE ==="
df -h

echo ""
echo "=== MEMORY USAGE ==="
free -h

echo ""
echo "=== RUNNING PROCESSES ==="
ps aux | grep -E 'godot|game|kiosk|X|systemd' | head -15

echo ""
echo "=== ENVIRONMENT VARIABLES ==="
env | grep -E 'DISPLAY|HOME|USER|PATH' | head -10

echo ""
echo "=== CONSOLE CONFIGURATION ==="
cat /opt/deckport-console/console.conf 2>/dev/null || echo "No console config found"

echo ""
echo "=== GAME STATUS ==="
if [ -f "/opt/godot-game/game.x86_64" ]; then
    echo "✅ Game executable exists:"
    ls -la /opt/godot-game/game.x86_64
else
    echo "❌ Game executable missing"
    echo "Checking alternative locations:"
    find /opt -name "*game*" -type f 2>/dev/null | head -5
fi

echo ""
echo "=== KIOSK SERVICE STATUS ==="
systemctl status deckport-kiosk.service --no-pager 2>/dev/null || echo "Kiosk service not found"

echo ""
echo "=== AUTO-LOGIN CONFIGURATION ==="
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || echo "No auto-login config"

echo ""
echo "=== GRUB CONFIGURATION ==="
cat /etc/default/grub | grep -E 'CMDLINE|GRUB_'

echo ""
echo "=== RECENT BOOT LOGS ==="
journalctl -b --no-pager | tail -20

echo ""
echo "=============================================="
echo "END COMPLETE LOG DATA"
echo "=============================================="

} > "$LOG_FILE"

echo ""
echo "✅ Log collection complete!"
echo "📊 Log file size: $(du -h $LOG_FILE | cut -f1)"
echo "📁 Local file: $LOG_FILE"

echo ""
echo "📤 Uploading logs to server..."
echo "🌐 Endpoint: $API_ENDPOINT"

# Check file size and handle appropriately
FILE_SIZE=$(wc -c < "$LOG_FILE")
echo "📊 Log file size: $FILE_SIZE bytes"

if [ $FILE_SIZE -gt 50000 ]; then
    echo "⚠️ Large log file detected, splitting upload..."
    
    # Split large file and upload in chunks
    split -b 40000 "$LOG_FILE" "${LOG_FILE}_chunk_"
    
    CHUNK_COUNT=0
    for chunk_file in "${LOG_FILE}_chunk_"*; do
        CHUNK_COUNT=$((CHUNK_COUNT + 1))
        echo "📤 Uploading chunk $CHUNK_COUNT..."
        
        CHUNK_RESPONSE=$(curl -X POST "$API_ENDPOINT" \
            -H "Content-Type: text/plain" \
            -d "CHUNK $CHUNK_COUNT - $(basename $chunk_file)
$(cat $chunk_file)" \
            --connect-timeout 30 \
            --max-time 60 \
            -w "HTTP_CODE:%{http_code}" \
            -s 2>&1)
        
        CHUNK_CODE=$(echo "$CHUNK_RESPONSE" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)
        if [ "$CHUNK_CODE" = "200" ]; then
            echo "✅ Chunk $CHUNK_COUNT uploaded successfully"
        else
            echo "❌ Chunk $CHUNK_COUNT failed: $CHUNK_CODE"
        fi
        
        # Clean up chunk file
        rm -f "$chunk_file"
    done
    
    UPLOAD_RESPONSE="Chunked upload completed with $CHUNK_COUNT chunks"
    HTTP_CODE="200"
    
else
    # Upload single file for smaller logs
    echo "📤 Uploading single file..."
    UPLOAD_RESPONSE=$(curl -X POST "$API_ENDPOINT" \
        -H "Content-Type: text/plain" \
        -d @"$LOG_FILE" \
        -w "HTTP_CODE:%{http_code}|TIME:%{time_total}|SIZE:%{size_upload}" \
        --connect-timeout 30 \
        --max-time 60 \
        -s 2>&1)
fi

# Parse response
HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)
UPLOAD_TIME=$(echo "$UPLOAD_RESPONSE" | grep -o 'TIME:[0-9.]*' | cut -d: -f2)
UPLOAD_SIZE=$(echo "$UPLOAD_RESPONSE" | grep -o 'SIZE:[0-9]*' | cut -d: -f2)

echo ""
echo "📊 Upload Results:"
echo "=================="

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Upload successful!"
    echo "📡 HTTP Code: $HTTP_CODE"
    echo "⏱️  Upload time: ${UPLOAD_TIME}s"
    echo "📦 Upload size: $UPLOAD_SIZE bytes"
    echo ""
    echo "🔍 Server debug file created with timestamp: $TIMESTAMP"
    echo "📋 Logs are now available for analysis"
    echo "🎯 Debug identifier: deckport_complete_logs_${TIMESTAMP}"
else
    echo "❌ Upload failed!"
    echo "📡 HTTP Code: $HTTP_CODE"
    echo "📄 Response: $UPLOAD_RESPONSE"
    echo ""
    echo "💾 Logs saved locally for manual review:"
    echo "📁 File: $LOG_FILE"
    echo "📊 Size: $(du -h $LOG_FILE | cut -f1)"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- Check internet connectivity"
    echo "- Verify API server is running"
    echo "- Try manual upload later"
fi

echo ""
echo "========================================"
echo "🎮 Deckport Log Upload Complete"
echo "========================================"

# Keep local copy for backup
echo "💾 Local backup: $LOG_FILE"
echo "🔍 View with: cat $LOG_FILE"
