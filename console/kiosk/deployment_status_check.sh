#!/bin/bash

# Deckport Console Deployment Status Check
# Run this on the console during/after deployment to see what's happening

echo "🔍 DECKPORT CONSOLE DEPLOYMENT STATUS CHECK"
echo "============================================"
echo "Time: $(date)"
echo "Console: $(hostname)"
echo ""

# Check deployment progress
echo "📊 DEPLOYMENT PROGRESS:"
if pgrep -f "deploy.*console" >/dev/null; then
    echo "✅ Deployment script is running"
    echo "   PID: $(pgrep -f 'deploy.*console')"
else
    echo "❌ No deployment script running"
fi

# Check network connectivity
echo ""
echo "🌐 NETWORK CONNECTIVITY:"
if ping -c 1 deckport.ai >/dev/null 2>&1; then
    echo "✅ Can reach deckport.ai"
else
    echo "❌ Cannot reach deckport.ai"
fi

# Check download progress
echo ""
echo "📥 DOWNLOAD STATUS:"
if pgrep -f "curl.*deckport" >/dev/null; then
    echo "✅ Downloads in progress"
    echo "   Curl processes: $(pgrep -c -f curl)"
else
    echo "ℹ️ No active downloads"
fi

# Check disk space
echo ""
echo "💾 DISK SPACE:"
df -h / | tail -1 | awk '{print "   Used: " $3 "/" $2 " (" $5 ")"}'
AVAILABLE=$(df / | tail -1 | awk '{print $4}')
if [[ $AVAILABLE -lt 1048576 ]]; then  # Less than 1GB
    echo "⚠️  Low disk space!"
else
    echo "✅ Sufficient disk space"
fi

# Check for deployment assets
echo ""
echo "📦 DEPLOYMENT ASSETS:"
TEMP_DIRS=("/tmp/deckport-deploy-*" "/tmp/*godot*" "/tmp/*wifi*")
for dir in "${TEMP_DIRS[@]}"; do
    if ls $dir >/dev/null 2>&1; then
        echo "✅ Found: $dir"
        ls -la $dir 2>/dev/null | head -5
    fi
done

# Check system resources
echo ""
echo "⚡ SYSTEM RESOURCES:"
echo "   CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "   Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"

# Check for errors in recent logs
echo ""
echo "📋 RECENT ERRORS:"
journalctl --since "10 minutes ago" | grep -i "error\|fail\|denied" | tail -5 || echo "   No recent errors"

# Check X11 status
echo ""
echo "🖥️  X11 STATUS:"
if pgrep -f "X.*:0" >/dev/null; then
    echo "✅ X server is running"
    echo "   Display: $DISPLAY"
else
    echo "❌ X server not running"
fi

# Check for kiosk user and permissions
echo ""
echo "👤 USER PERMISSIONS:"
if id kiosk >/dev/null 2>&1; then
    echo "✅ Kiosk user exists"
    echo "   Groups: $(groups kiosk 2>/dev/null | cut -d: -f2)"
else
    echo "❌ Kiosk user not found"
fi

# Check TTY permissions
if [[ -c /dev/tty1 ]]; then
    echo "✅ TTY1 device exists"
    ls -la /dev/tty1 | awk '{print "   Permissions: " $1 " " $3 ":" $4}'
else
    echo "❌ TTY1 device not found"
fi

# Check deployment logs
echo ""
echo "📝 DEPLOYMENT LOGS:"
if [[ -f /var/log/deckport-console.log ]]; then
    echo "✅ Console log exists"
    echo "   Last 3 lines:"
    tail -3 /var/log/deckport-console.log
else
    echo "ℹ️ No console log yet"
fi

# Check service status
echo ""
echo "⚙️  SERVICES:"
if systemctl list-units | grep -q deckport; then
    echo "✅ Deckport services found:"
    systemctl list-units | grep deckport | awk '{print "   " $1 " - " $3}'
else
    echo "ℹ️ No Deckport services yet"
fi

echo ""
echo "============================================"
echo "Status check complete: $(date)"
echo ""
echo "💡 TIPS:"
echo "   • Run this script again to monitor progress"
echo "   • Check 'journalctl -f' for real-time logs"
echo "   • Press Ctrl+Alt+F2 for emergency terminal access"
echo "============================================"
