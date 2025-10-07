#!/bin/bash

#################################################
# Emergency Console Diagnostics Script
# Collects all system information and sends to server for debugging
#################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log "🚨 Deckport Emergency Console Diagnostics"
log "=========================================="

# Configuration
SERVER_URL="https://api.deckport.ai"
CONSOLE_ID="emergency-$(date +%s)"
DIAGNOSTIC_DATA=""

# Function to add data to diagnostic report
add_data() {
    local section="$1"
    local data="$2"
    DIAGNOSTIC_DATA="$DIAGNOSTIC_DATA

========== $section ==========
$data
"
}

log "📊 Collecting system information..."

# System Information
info "Collecting basic system info..."
add_data "SYSTEM_INFO" "$(
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Kernel: $(uname -a)"
echo "Distribution: $(cat /etc/os-release 2>/dev/null || echo 'Unknown')"
echo "Architecture: $(arch)"
echo "CPU Info: $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2)"
echo "Memory: $(free -h)"
echo "Disk: $(df -h)"
)"

# Graphics Hardware
info "Collecting graphics information..."
add_data "GRAPHICS_HARDWARE" "$(
echo "=== PCI Graphics ==="
lspci | grep -i 'vga\|display\|graphics'
echo ""
echo "=== Graphics Modules ==="
lsmod | grep -E 'i915|nouveau|radeon|amdgpu'
echo ""
echo "=== Graphics Packages ==="
dpkg -l | grep -E 'mesa|intel|graphics|xorg' | head -10
echo ""
echo "=== DRM Devices ==="
ls -la /dev/dri/ 2>/dev/null || echo 'No DRM devices'
)"

# X11 Configuration and Logs
info "Collecting X11 information..."
add_data "X11_STATUS" "$(
echo "=== X11 Configuration ==="
cat /etc/X11/xorg.conf 2>/dev/null || echo 'No xorg.conf found'
echo ""
echo "=== X11 Logs ==="
cat /var/log/Xorg.0.log 2>/dev/null | tail -50 || echo 'No X11 logs found'
echo ""
echo "=== Display Environment ==="
echo "DISPLAY: $DISPLAY"
echo "XDG_SESSION_TYPE: $XDG_SESSION_TYPE"
echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo ""
echo "=== X Server Test ==="
ps aux | grep -E '[Xx]org|[Xx] :0' || echo 'No X server running'
)"

# Auto-Login Configuration
info "Collecting auto-login configuration..."
add_data "AUTO_LOGIN_CONFIG" "$(
echo "=== Getty Service Override ==="
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || echo 'No auto-login config found'
echo ""
echo "=== User Profile Scripts ==="
cat /home/kiosk/.bashrc 2>/dev/null || echo 'No .bashrc found'
echo ""
cat /home/kiosk/.bash_profile 2>/dev/null || echo 'No .bash_profile found'
echo ""
echo "=== Current TTY ==="
tty
echo "Current User: $(whoami)"
echo "Groups: $(groups)"
)"

# Service Status
info "Collecting service status..."
add_data "SERVICES_STATUS" "$(
echo "=== Deckport Services ==="
systemctl status deckport-kiosk.service --no-pager 2>/dev/null || echo 'Deckport kiosk service not found'
echo ""
systemctl status wifi-portal.service --no-pager 2>/dev/null || echo 'WiFi portal service not found'
echo ""
echo "=== System Target ==="
systemctl get-default
echo ""
echo "=== Active Services ==="
systemctl list-units --state=active --type=service | grep -E 'deckport|kiosk|getty' || echo 'No deckport services found'
)"

# Console Logs
info "Collecting console logs..."
add_data "CONSOLE_LOGS" "$(
echo "=== Deckport Console Logs ==="
cat /var/log/deckport-console.log 2>/dev/null | tail -50 || echo 'No console logs found'
echo ""
echo "=== System Logs (Recent) ==="
journalctl --since '10 minutes ago' --no-pager | tail -30 || echo 'No recent system logs'
echo ""
echo "=== Auth Logs ==="
cat /var/log/auth.log 2>/dev/null | tail -20 || echo 'No auth logs found'
)"

# Network and Configuration
info "Collecting network and configuration..."
add_data "NETWORK_CONFIG" "$(
echo "=== Network Status ==="
ip addr show
echo ""
echo "=== DNS Configuration ==="
cat /etc/resolv.conf 2>/dev/null || echo 'No DNS config'
echo ""
echo "=== Console Configuration ==="
cat /opt/deckport-console/console.conf 2>/dev/null || echo 'No console config found'
echo ""
echo "=== Game Directory ==="
ls -la /opt/godot-game/ 2>/dev/null || echo 'No game directory found'
)"

# Processes and Environment
info "Collecting process information..."
add_data "PROCESS_INFO" "$(
echo "=== Running Processes ==="
ps aux | head -20
echo ""
echo "=== Environment Variables ==="
env | grep -E 'DISPLAY|XDG|HOME|USER' | sort
echo ""
echo "=== Cron Jobs ==="
crontab -l 2>/dev/null || echo 'No cron jobs found'
)"

log "📤 Sending diagnostic data to server..."

# Create diagnostic payload
TIMESTAMP=$(date -Iseconds)
HOSTNAME=$(hostname)
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Send diagnostic data to server
PAYLOAD=$(cat << EOF
{
    "console_id": "$CONSOLE_ID",
    "device_uid": "$HOSTNAME",
    "diagnostic_type": "emergency_debug",
    "timestamp": "$TIMESTAMP",
    "ip_address": "$IP_ADDRESS",
    "diagnostic_data": $(echo "$DIAGNOSTIC_DATA" | jq -R -s .)
}
EOF
)

# Try to send to server
if command -v curl >/dev/null 2>&1; then
    RESPONSE=$(curl -s -X POST "$SERVER_URL/v1/console-logs/crash-report" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        log "✅ Diagnostic data sent to server successfully"
        echo "Response: $RESPONSE"
    else
        error "❌ Failed to send diagnostic data to server"
        warning "Saving diagnostic data locally..."
        echo "$DIAGNOSTIC_DATA" > /tmp/deckport_diagnostics_$(date +%s).txt
        log "📁 Diagnostic data saved to /tmp/deckport_diagnostics_$(date +%s).txt"
    fi
else
    error "❌ curl not available - saving diagnostic data locally"
    echo "$DIAGNOSTIC_DATA" > /tmp/deckport_diagnostics_$(date +%s).txt
    log "📁 Diagnostic data saved to /tmp/deckport_diagnostics_$(date +%s).txt"
fi

log "=========================================="
log "🏁 Emergency diagnostics complete"
log "=========================================="

# Also display critical info locally for immediate debugging
echo ""
log "🔍 CRITICAL ISSUES SUMMARY:"

# Check for common X11 issues
if ! lsmod | grep -q i915; then
    error "❌ Intel graphics driver (i915) not loaded"
fi

if [ ! -c /dev/dri/card0 ]; then
    error "❌ No graphics device found (/dev/dri/card0 missing)"
fi

if ! groups | grep -q video; then
    error "❌ User not in video group"
fi

if [ ! -f /etc/systemd/system/getty@tty1.service.d/autologin.conf ]; then
    error "❌ Auto-login configuration missing"
fi

if ! systemctl is-enabled deckport-kiosk.service >/dev/null 2>&1; then
    error "❌ Deckport kiosk service not enabled"
fi

log "Run this script as: ./emergency_diagnostics.sh"
log "Data will be available in admin panel for review"
