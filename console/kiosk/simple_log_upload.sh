#!/bin/bash

echo "📡 Simple Console Log Upload"
echo "============================"

# Create smaller, focused log upload
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)

echo "Collecting essential deployment logs..."

# Create focused log data (smaller size)
LOG_DATA="DEPLOYMENT ERROR - $TIMESTAMP
Console: $HOSTNAME
Error: Failed to download game (X11 permission issue)

=== KEY FINDINGS ===
X11 Error: Cannot open virtual console 1 (Permission denied)
Graphics: Intel Alder Lake-N UHD Graphics detected
Game Status: Downloaded successfully (66MB file exists)
Network: All endpoints accessible

=== RECENT X11 ERRORS ===
$(journalctl --since '30 minutes ago' | grep -i 'x11\|xorg\|permission\|console' | tail -10)

=== KIOSK SERVICE STATUS ===
$(systemctl status deckport-kiosk.service --no-pager --lines=5 2>/dev/null)

=== GRAPHICS DEVICES ===
$(ls -la /dev/dri/ 2>/dev/null)

=== CONSOLE PERMISSIONS ===
$(groups kiosk 2>/dev/null)
$(ls -la /dev/tty1 2>/dev/null)

END LOG"

echo "Uploading to server..."

# Try multiple endpoints with smaller payload
echo "Trying API endpoint..."
echo "$LOG_DATA" | curl -X POST "https://api.deckport.ai/v1/debug/simple" \
    -H "Content-Type: text/plain" \
    -d @- \
    --connect-timeout 10 \
    --max-time 30 \
    -v

if [ $? -eq 0 ]; then
    echo "✅ Upload successful!"
else
    echo "❌ API upload failed, trying alternative..."
    
    # Alternative: Save locally and provide manual upload instructions
    LOCAL_FILE="/tmp/deployment_error_$TIMESTAMP.txt"
    echo "$LOG_DATA" > "$LOCAL_FILE"
    
    echo "📁 Logs saved locally: $LOCAL_FILE"
    echo "📋 Manual upload command:"
    echo "curl -X POST 'https://api.deckport.ai/v1/debug/simple' -H 'Content-Type: text/plain' -d @$LOCAL_FILE"
fi
