#!/bin/bash

echo "📡 Uploading Deployment Logs to Deckport Server"
echo "==============================================="

# Collect deployment error information
TIMESTAMP=$(date -Iseconds)
HOSTNAME=$(hostname)

# Comprehensive deployment error log
LOG_DATA="DEPLOYMENT ERROR LOG - $TIMESTAMP
HOSTNAME: $HOSTNAME
===============================================

=== DEPLOYMENT ERROR DETAILS ===
Error: Failed to download game
Time: $TIMESTAMP
Console: $HOSTNAME

=== SYSTEM INFORMATION ===
$(uname -a)
Memory: $(free -h | grep Mem)
Disk: $(df -h / | tail -1)
Network: $(ip route get 8.8.8.8 2>/dev/null | head -1)

=== RECENT DEPLOYMENT LOGS ===
$(journalctl --since '30 minutes ago' | grep -i 'deploy\|download\|error\|fail' | tail -20)

=== CURL TEST RESULTS ===
API Health: $(curl -s -w 'HTTP_%{http_code}' https://api.deckport.ai/health 2>/dev/null || echo 'FAILED')
Game Download: $(curl -s -I https://deckport.ai/deploy/assets/godot-game/latest 2>/dev/null | head -1 || echo 'FAILED')
Deployment Script: $(curl -s -I https://deckport.ai/deploy/console 2>/dev/null | head -1 || echo 'FAILED')

=== NETWORK CONNECTIVITY ===
DNS Resolution: $(nslookup deckport.ai 2>/dev/null | grep -A1 'Name:' || echo 'DNS FAILED')
Internet: $(ping -c 3 8.8.8.8 2>/dev/null | tail -1 || echo 'PING FAILED')

=== SYSTEM SERVICES ===
$(systemctl status --no-pager 2>/dev/null | head -10)

===============================================
END DEPLOYMENT ERROR LOG"

echo "Sending deployment error logs to server..."

# Upload to debug endpoint
curl -X POST "https://api.deckport.ai/v1/debug/simple" \
     -H "Content-Type: text/plain" \
     -d "$LOG_DATA" \
     --connect-timeout 30 \
     --max-time 60

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment logs uploaded successfully!"
    echo "📊 Debug file created on server with timestamp: $TIMESTAMP"
    echo "🔍 Logs are now available for analysis"
else
    echo ""
    echo "❌ Upload failed - trying alternative method..."
    
    # Fallback: Save to local file for manual review
    echo "$LOG_DATA" > "/tmp/deployment_error_$TIMESTAMP.log"
    echo "📁 Logs saved locally to: /tmp/deployment_error_$TIMESTAMP.log"
    echo "📋 You can manually share this file for analysis"
fi

echo "==============================================="
