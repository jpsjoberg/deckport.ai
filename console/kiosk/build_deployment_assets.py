#!/usr/bin/env python3
"""
Build Deployment Assets for Console Kiosk System
Creates all the packages needed for automated console deployment
"""

import os
import tarfile
import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
ASSETS_DIR = Path(__file__).parent / "deployment_assets"
STATIC_DIR = Path("/home/jp/deckport.ai/static/deploy")

def create_directories():
    """Create necessary directories"""
    ASSETS_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    
    print("📁 Created deployment directories")

def build_wifi_portal_package():
    """Build WiFi portal package"""
    print("🌐 Building WiFi portal package...")
    
    portal_dir = ASSETS_DIR / "wifi-portal"
    portal_dir.mkdir(exist_ok=True)
    
    templates_dir = portal_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create WiFi portal Python app
    wifi_portal_py = '''#!/usr/bin/env python3
import os
import subprocess
import json
from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__)

def get_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        result = subprocess.run(
            ['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi'],
            capture_output=True, text=True
        )
        networks = []
        seen = set()
        for line in result.stdout.strip().split('\\n'):
            if line:
                parts = line.split(':')
                if len(parts) >= 3 and parts[0] and parts[0] not in seen:
                    seen.add(parts[0])
                    networks.append({
                        'ssid': parts[0],
                        'signal': int(parts[1]) if parts[1] else 0,
                        'security': parts[2] if len(parts) > 2 else 'Open'
                    })
        return sorted(networks, key=lambda x: x['signal'], reverse=True)
    except Exception as e:
        print(f"Error scanning WiFi: {e}")
        return []

def connect_to_wifi(ssid, password):
    """Connect to WiFi network"""
    try:
        # Remove existing connection if it exists
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], 
                      capture_output=True)
        
        # Create new connection
        if password:
            result = subprocess.run(
                ['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password],
                capture_output=True, text=True
            )
        else:
            result = subprocess.run(
                ['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid],
                capture_output=True, text=True
            )
        
        if result.returncode == 0:
            # Test internet connectivity
            time.sleep(3)
            test = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                capture_output=True)
            if test.returncode == 0:
                # Create flag file to indicate successful connection
                open('/tmp/wifi_configured', 'w').close()
                return True
        return False
    except Exception as e:
        print(f"Error connecting to WiFi: {e}")
        return False

@app.route('/')
def index():
    networks = get_wifi_networks()
    return render_template('index.html', networks=networks)

@app.route('/scan')
def scan():
    networks = get_wifi_networks()
    return jsonify(networks)

@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password', '')
    
    if connect_to_wifi(ssid, password):
        # Continue with kiosk setup
        subprocess.run(['sudo', 'systemctl', 'start', 'deckport-kiosk.service'])
        return jsonify({'status': 'success', 'message': 'Connected successfully!'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to connect'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
'''
    
    # Create WiFi portal HTML template
    wifi_portal_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deckport Console Setup</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
            text-align: center;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .logo::before {
            content: "🎮";
            font-size: 48px;
            display: block;
            margin-bottom: 10px;
        }
        
        .network-list {
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .network-item {
            padding: 15px;
            border: 2px solid #f0f0f0;
            border-radius: 12px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .network-item:hover {
            border-color: #667eea;
            background: #f8f9ff;
            transform: translateY(-2px);
        }
        
        .network-item.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #f0f3ff 0%, #e8ecff 100%);
        }
        
        .network-name {
            font-weight: 600;
            color: #333;
        }
        
        .signal-strength {
            display: flex;
            gap: 2px;
        }
        
        .signal-bar {
            width: 3px;
            background: #ddd;
            border-radius: 1px;
        }
        
        .signal-bar.active {
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        }
        
        .password-section {
            display: none;
            margin-top: 20px;
        }
        
        .password-section.show {
            display: block;
        }
        
        input[type="password"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #f0f0f0;
            border-radius: 12px;
            font-size: 16px;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }
        
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
            color: #333;
            margin-top: 10px;
        }
        
        .status {
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
            text-align: center;
            display: none;
        }
        
        .status.show {
            display: block;
        }
        
        .status.success {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        
        .status.error {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24;
            border: 2px solid #f5c6cb;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo"></div>
        <h1>Deckport Console</h1>
        <p class="subtitle">Select your WiFi network to continue setup</p>
        
        <div class="network-list" id="networkList">
            {% for network in networks %}
            <div class="network-item" onclick="selectNetwork('{{ network.ssid }}', '{{ network.security }}')">
                <div class="network-name">{{ network.ssid }}</div>
                <div class="signal-strength">
                    <div class="signal-bar" style="height: 8px; {{ 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' if network.signal > 20 else '' }}"></div>
                    <div class="signal-bar" style="height: 12px; {{ 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' if network.signal > 40 else '' }}"></div>
                    <div class="signal-bar" style="height: 16px; {{ 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' if network.signal > 60 else '' }}"></div>
                    <div class="signal-bar" style="height: 20px; {{ 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' if network.signal > 80 else '' }}"></div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="password-section" id="passwordSection">
            <input type="password" id="password" placeholder="Enter WiFi password" onkeypress="if(event.key==='Enter') connect()">
        </div>
        
        <button class="btn" id="connectBtn" onclick="connect()" disabled>Connect to Network</button>
        <button class="btn btn-secondary" onclick="scanNetworks()">🔄 Refresh Networks</button>
        
        <div class="status" id="status"></div>
    </div>
    
    <script>
        let selectedNetwork = null;
        let selectedSecurity = null;
        
        function selectNetwork(ssid, security) {
            selectedNetwork = ssid;
            selectedSecurity = security;
            
            // Update UI
            document.querySelectorAll('.network-item').forEach(item => {
                item.classList.remove('selected');
            });
            event.currentTarget.classList.add('selected');
            
            // Show password field if network is secured
            const passwordSection = document.getElementById('passwordSection');
            if (security !== 'Open' && security !== '') {
                passwordSection.classList.add('show');
                document.getElementById('password').focus();
            } else {
                passwordSection.classList.remove('show');
            }
            
            document.getElementById('connectBtn').disabled = false;
        }
        
        async function connect() {
            if (!selectedNetwork) return;
            
            const password = document.getElementById('password').value;
            const connectBtn = document.getElementById('connectBtn');
            const status = document.getElementById('status');
            
            // Show loading state
            connectBtn.disabled = true;
            connectBtn.innerHTML = '<div class="spinner"></div>';
            status.className = 'status';
            
            try {
                const response = await fetch('/connect', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        ssid: selectedNetwork,
                        password: password
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    status.className = 'status show success';
                    status.innerHTML = '🎉 Connected! Starting Deckport console...<br><small>This may take a few minutes</small>';
                } else {
                    status.className = 'status show error';
                    status.textContent = data.message || 'Connection failed. Please try again.';
                    connectBtn.disabled = false;
                    connectBtn.textContent = 'Connect to Network';
                }
            } catch (error) {
                status.className = 'status show error';
                status.textContent = 'An error occurred. Please try again.';
                connectBtn.disabled = false;
                connectBtn.textContent = 'Connect to Network';
            }
        }
        
        async function scanNetworks() {
            const networkList = document.getElementById('networkList');
            networkList.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="spinner"></div><p style="margin-top: 10px;">Scanning...</p></div>';
            
            try {
                const response = await fetch('/scan');
                const networks = await response.json();
                
                let html = '';
                networks.forEach(network => {
                    html += `
                        <div class="network-item" onclick="selectNetwork('${network.ssid}', '${network.security}')">
                            <div class="network-name">${network.ssid}</div>
                            <div class="signal-strength">
                                <div class="signal-bar" style="height: 8px; ${network.signal > 20 ? 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' : ''}"></div>
                                <div class="signal-bar" style="height: 12px; ${network.signal > 40 ? 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' : ''}"></div>
                                <div class="signal-bar" style="height: 16px; ${network.signal > 60 ? 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' : ''}"></div>
                                <div class="signal-bar" style="height: 20px; ${network.signal > 80 ? 'background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);' : ''}"></div>
                            </div>
                        </div>
                    `;
                });
                networkList.innerHTML = html;
            } catch (error) {
                networkList.innerHTML = '<p style="text-align: center; color: #666;">Failed to scan networks</p>';
            }
        }
    </script>
</body>
</html>'''
    
    # Write files
    with open(portal_dir / "wifi_portal.py", "w") as f:
        f.write(wifi_portal_py)
    
    with open(templates_dir / "index.html", "w") as f:
        f.write(wifi_portal_html)
    
    # Create package
    with tarfile.open(STATIC_DIR / "wifi-portal.tar.gz", "w:gz") as tar:
        tar.add(portal_dir, arcname=".")
    
    print("✅ WiFi portal package created")

def build_boot_theme_package():
    """Build Plymouth boot theme package"""
    print("🎨 Building boot theme package...")
    
    theme_dir = ASSETS_DIR / "boot-theme"
    theme_dir.mkdir(exist_ok=True)
    
    # Plymouth theme configuration
    plymouth_theme = '''[Plymouth Theme]
Name=Deckport Console
Description=Deckport gaming console boot theme
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/deckport-console
ScriptFile=/usr/share/plymouth/themes/deckport-console/deckport-console.script
'''
    
    # Plymouth script
    plymouth_script = '''# Deckport Console Plymouth Boot Script
Window.SetBackgroundTopColor(0.0, 0.0, 0.0);    # Pure black background top
Window.SetBackgroundBottomColor(0.0, 0.0, 0.0);  # Pure black background bottom

# Load Deckport logo
logo.image = Image("logo.png");
logo.sprite = Sprite(logo.image);

# Center the logo
logo.sprite.SetX(Window.GetX() + (Window.GetWidth() - logo.image.GetWidth()) / 2);
logo.sprite.SetY(Window.GetY() + (Window.GetHeight() - logo.image.GetHeight()) / 2 - 50);

# Loading text with better styling
loading_text = "Starting Deckport Console...";
loading.image = Image.Text(loading_text, 0.8, 0.8, 0.8, 1, "Ubuntu 18");  # Light gray text, larger font
loading.sprite = Sprite(loading.image);
loading.sprite.SetX(Window.GetX() + (Window.GetWidth() - loading.image.GetWidth()) / 2);
loading.sprite.SetY(logo.sprite.GetY() + logo.image.GetHeight() + 50);

# Add version text
version_text = "Console OS v1.0";
version.image = Image.Text(version_text, 0.5, 0.5, 0.5, 1, "Ubuntu 12");  # Smaller gray text
version.sprite = Sprite(version.image);
version.sprite.SetX(Window.GetX() + (Window.GetWidth() - version.image.GetWidth()) / 2);
version.sprite.SetY(Window.GetY() + Window.GetHeight() - 50);  # Bottom of screen

# Loading animation
progress = 0;
fun refresh_callback() {
    progress++;
    
    # Pulse logo
    opacity = Math.Sin(progress / 30) * 0.3 + 0.7;
    logo.sprite.SetOpacity(opacity);
    
    # Animate loading text
    if ((progress / 20) % 2 < 1) {
        loading.sprite.SetOpacity(1);
    } else {
        loading.sprite.SetOpacity(0.5);
    }
}

Plymouth.SetRefreshFunction(refresh_callback);

# Handle boot progress
fun boot_progress_callback(duration, progress) {
    if (progress >= 1.0) {
        loading_text = "Ready!";
        loading.image = Image.Text(loading_text, 0.4, 1, 0.4, 1, "Ubuntu 16");
        loading.sprite = Sprite(loading.image);
        loading.sprite.SetX(Window.GetX() + (Window.GetWidth() - loading.image.GetWidth()) / 2);
        loading.sprite.SetY(logo.sprite.GetY() + logo.image.GetHeight() + 30);
    }
}

Plymouth.SetBootProgressFunction(boot_progress_callback);
'''
    
    # Create a simple logo placeholder (you can replace with actual logo)
    logo_placeholder = '''# This would be your actual logo.png file
# For now, we'll create a text-based placeholder in the script
'''
    
    # Write files
    with open(theme_dir / "deckport-console.plymouth", "w") as f:
        f.write(plymouth_theme)
    
    with open(theme_dir / "deckport-console.script", "w") as f:
        f.write(plymouth_script)
    
    # Create placeholder for logo (you'll need to add your actual logo.png)
    with open(theme_dir / "logo-placeholder.txt", "w") as f:
        f.write("Add your logo.png file here")
    
    # Create package
    with tarfile.open(STATIC_DIR / "boot-theme.tar.gz", "w:gz") as tar:
        tar.add(theme_dir, arcname=".")
    
    print("✅ Boot theme package created")

def build_configs_package():
    """Build system configuration package"""
    print("⚙️ Building configuration package...")
    
    configs_dir = ASSETS_DIR / "configs"
    configs_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (configs_dir / "systemd").mkdir(exist_ok=True)
    (configs_dir / "scripts").mkdir(exist_ok=True)
    (configs_dir / "x11").mkdir(exist_ok=True)
    (configs_dir / "grub").mkdir(exist_ok=True)
    
    # Systemd services
    kiosk_service = '''[Unit]
Description=Deckport Kiosk Console
After=graphical-session.target network.target
Wants=graphical-session.target network-online.target

[Service]
Type=simple
User=kiosk
Group=kiosk
WorkingDirectory=/home/kiosk
ExecStart=/home/kiosk/start-kiosk.sh
Restart=always
RestartSec=5
Environment="HOME=/home/kiosk"
Environment="DISPLAY=:0"
Environment="XDG_RUNTIME_DIR=/run/user/1000"

# Security and resource settings
NoNewPrivileges=true
PrivateTmp=true
MemoryMax=2G
CPUQuota=90%

[Install]
WantedBy=graphical.target
'''
    
    wifi_portal_service = '''[Unit]
Description=Deckport WiFi Configuration Portal
After=network.target
Before=deckport-kiosk.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wifi-portal
ExecStart=/usr/bin/python3 /opt/wifi-portal/wifi_portal.py
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
    
    network_check_service = '''[Unit]
Description=Deckport Network Connectivity Check
Before=deckport-kiosk.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then systemctl start wifi-portal.service; fi'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
'''
    
    # Startup script with VT switching fix
    start_kiosk_script = '''#!/bin/bash

# Deckport Console Startup Script
CONSOLE_CONF="/opt/deckport-console/console.conf"
LOG_FILE="/var/log/deckport-console.log"
GAME_DIR="/opt/godot-game"

# Logging function
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE" 2>/dev/null || true
}

log "🎮 Starting Deckport Console..."

# Source configuration
if [ -f "$CONSOLE_CONF" ]; then
    source "$CONSOLE_CONF"
    log "Configuration loaded"
else
    log "Warning: No configuration file found"
fi

# Check network connectivity
check_network() {
    ping -c 1 8.8.8.8 > /dev/null 2>&1
    return $?
}

# Start X server without VT switching
start_x_server() {
    log "Starting X server without VT switching..."
    
    # Kill any existing X servers
    pkill -f "X :0" 2>/dev/null || true
    sleep 1
    
    # Start X server with no VT switching and emergency exit capability
    X :0 -nolisten tcp -novtswitch -sharevts vt1 &
    X_PID=$!
    sleep 3
    
    # Set up emergency exit - Ctrl+Alt+Backspace to kill X
    DISPLAY=:0 setxkbmap -option terminate:ctrl_alt_bksp 2>/dev/null || true
    
    # Set display environment
    export DISPLAY=:0
    
    # Test if X server is responding
    if DISPLAY=:0 xset q > /dev/null 2>&1; then
        log "✅ X server started successfully"
        return 0
    else
        log "❌ X server failed to start"
        return 1
    fi
}

# Configure display and window manager
setup_display() {
    log "Configuring display environment..."
    
    export DISPLAY=:0
    
    # Disable screen blanking
    DISPLAY=:0 xset s off 2>/dev/null || true
    DISPLAY=:0 xset -dpms 2>/dev/null || true
    DISPLAY=:0 xset s noblank 2>/dev/null || true
    
    # Hide cursor
    DISPLAY=:0 unclutter -idle 1 -root &
    
    # Start minimal window manager
    DISPLAY=:0 openbox &
    sleep 2
    
    log "Display environment configured"
}

# Find game executable
find_game() {
    if [ ! -d "$GAME_DIR" ]; then
        log "❌ Game directory not found: $GAME_DIR"
        return 1
    fi
    
    # Look for game executable
    GAME_EXECUTABLE=""
    for name in "game.x86_64" "deckport_console.x86_64" "console.x86_64"; do
        if [ -f "$GAME_DIR/$name" ] && [ -x "$GAME_DIR/$name" ]; then
            GAME_EXECUTABLE="$GAME_DIR/$name"
            break
        fi
    done
    
    if [ -n "$GAME_EXECUTABLE" ]; then
        log "✅ Game found: $GAME_EXECUTABLE"
        echo "$GAME_EXECUTABLE"
        return 0
    else
        log "❌ No game executable found"
        return 1
    fi
}

# Main execution
log "Checking network..."
if ! check_network; then
    log "No network - starting WiFi portal..."
    
    if start_x_server; then
        setup_display
        
        # Start WiFi portal
        DISPLAY=:0 chromium-browser --kiosk --no-first-run --disable-translate \\
            --disable-infobars --disable-suggestions-service \\
            --disable-save-password-bubble --start-maximized \\
            --window-position=0,0 --window-size=1920,1080 \\
            --disable-web-security --disable-features=VizDisplayCompositor \\
            http://localhost:8080 &
        
        # Wait for WiFi configuration
        while [ ! -f /tmp/wifi_configured ]; do
            sleep 2
        done
        
        log "WiFi configured"
        pkill chromium-browser
        sleep 2
    fi
fi

# Start X server for game
if ! DISPLAY=:0 xset q > /dev/null 2>&1; then
    if ! start_x_server; then
        log "❌ Failed to start X server"
        exit 1
    fi
fi

setup_display

# Find and start game with detailed error logging
GAME_EXECUTABLE=$(find_game)
if [ $? -eq 0 ] && [ -n "$GAME_EXECUTABLE" ]; then
    log "🚀 Starting game: $GAME_EXECUTABLE"
    
    # Log game details before starting
    log "Game file size: $(stat -c%s "$GAME_EXECUTABLE" 2>/dev/null || echo 'Unknown') bytes"
    log "Game permissions: $(ls -la "$GAME_EXECUTABLE" 2>/dev/null || echo 'Cannot check')"
    
    # Test if game executable is valid
    if ! file "$GAME_EXECUTABLE" | grep -q "ELF.*executable"; then
        log "❌ Game file is not a valid executable"
        exit 1
    fi
    
    # Change to game directory
    cd "$GAME_DIR"
    log "Changed to game directory: $(pwd)"
    
    # Start game with error capture
    log "Launching Godot game..."
    
    # Capture both stdout and stderr from game
    "$GAME_EXECUTABLE" --fullscreen > /var/log/godot-game.log 2>&1 &
    GAME_PID=$!
    
    # Wait a moment to see if game starts successfully
    sleep 3
    
    # Check if game process is still running
    if kill -0 "$GAME_PID" 2>/dev/null; then
        log "✅ Game started successfully (PID: $GAME_PID)"
        
        # Wait for game to finish (this should run indefinitely)
        wait "$GAME_PID"
        GAME_EXIT_CODE=$?
        
        log "🎮 Game exited with code: $GAME_EXIT_CODE"
        
        # Log game output if it crashed
        if [ $GAME_EXIT_CODE -ne 0 ]; then
            log "❌ Game crashed - checking game logs..."
            if [ -f "/var/log/godot-game.log" ]; then
                log "Game error output:"
                tail -20 /var/log/godot-game.log >> "$LOG_FILE" 2>/dev/null || true
            fi
        fi
        
        exit $GAME_EXIT_CODE
    else
        log "❌ Game failed to start or crashed immediately"
        
        # Capture any error output
        if [ -f "/var/log/godot-game.log" ]; then
            log "Game startup errors:"
            cat /var/log/godot-game.log >> "$LOG_FILE" 2>/dev/null || true
        fi
        
        # Also check for common Godot issues
        log "Checking for common Godot startup issues..."
        log "Display environment: DISPLAY=$DISPLAY"
        log "OpenGL test: $(DISPLAY=:0 glxinfo | head -5 2>/dev/null || echo 'glxinfo not available')"
        log "Audio devices: $(aplay -l 2>/dev/null || echo 'No audio devices')"
        
        exit 1
    fi
else
    log "❌ Cannot find game executable"
    log "Game directory contents:"
    ls -la "$GAME_DIR" >> "$LOG_FILE" 2>/dev/null || true
    exit 1
fi
'''
    
    # Management script
    manage_console_script = '''#!/bin/bash

# Deckport Console Management Script
source /opt/deckport-console/console.conf

case "$1" in
    restart-game)
        echo "Restarting Deckport game..."
        sudo systemctl restart deckport-kiosk.service
        ;;
    update-game)
        echo "Updating Deckport game to version: $2"
        # Download new game version
        wget -O /tmp/game-update.tar.gz "$DEPLOYMENT_SERVER/deploy/assets/godot-game/$2"
        # Extract to game directory
        sudo tar -xzf /tmp/game-update.tar.gz -C /opt/godot-game/
        # Update version in config
        sed -i "s/GAME_VERSION=.*/GAME_VERSION=$2/" /opt/deckport-console/console.conf
        # Restart game
        sudo systemctl restart deckport-kiosk.service
        echo "Game updated successfully!"
        ;;
    view-logs)
        echo "=== Deckport Console Logs ==="
        sudo journalctl -u deckport-kiosk.service -n 50
        echo ""
        echo "=== Application Logs ==="
        tail -50 /var/log/deckport-console.log 2>/dev/null || echo "No application logs found"
        ;;
    reset-wifi)
        echo "Resetting WiFi configuration..."
        sudo rm -f /tmp/wifi_configured
        sudo nmcli con delete --all
        sudo systemctl restart network-check.service
        echo "WiFi reset complete"
        ;;
    system-info)
        echo "=== Deckport Console System Information ==="
        echo "Console ID: $CONSOLE_ID"
        echo "Game Version: $GAME_VERSION"
        echo "Location: $LOCATION"
        echo "IP Address: $(hostname -I | awk '{print $1}')"
        echo "Uptime: $(uptime -p)"
        echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5}')"
        echo "Memory Usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
        ;;
    send-heartbeat)
        echo "Sending heartbeat to Deckport..."
        /opt/deckport-console/heartbeat.sh
        echo "Heartbeat sent"
        ;;
    *)
        echo "Deckport Console Management"
        echo "Usage: $0 {restart-game|update-game <version>|view-logs|reset-wifi|system-info|send-heartbeat}"
        echo ""
        echo "Examples:"
        echo "  $0 restart-game"
        echo "  $0 update-game v1.2.3"
        echo "  $0 view-logs"
        echo "  $0 system-info"
        ;;
esac
'''
    
    # X11 configuration
    xorg_conf = '''Section "ServerFlags"
    Option "DontVTSwitch" "true"
    Option "DontZap" "true"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection

Section "InputClass"
    Identifier "touchscreen catchall"
    MatchIsTouchscreen "on"
    Driver "evdev"
    Option "EmulateThirdButton" "false"
    Option "EmulateThirdButtonTimeout" "0"
    Option "EmulateThirdButtonMoveThreshold" "0"
EndSection
'''
    
    # GRUB configuration
    grub_config = '''GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=0 rd.systemd.show_status=0 rd.udev.log_level=0 vt.global_cursor_default=0"
GRUB_CMDLINE_LINUX=""
'''
    
    # Write all config files
    with open(configs_dir / "systemd" / "deckport-kiosk.service", "w") as f:
        f.write(kiosk_service)
    
    with open(configs_dir / "systemd" / "wifi-portal.service", "w") as f:
        f.write(wifi_portal_service)
    
    with open(configs_dir / "systemd" / "network-check.service", "w") as f:
        f.write(network_check_service)
    
    with open(configs_dir / "scripts" / "start-kiosk.sh", "w") as f:
        f.write(start_kiosk_script)
    
    with open(configs_dir / "scripts" / "manage-console.sh", "w") as f:
        f.write(manage_console_script)
    
    with open(configs_dir / "x11" / "xorg.conf", "w") as f:
        f.write(xorg_conf)
    
    with open(configs_dir / "grub" / "grub", "w") as f:
        f.write(grub_config)
    
    # Create package
    with tarfile.open(STATIC_DIR / "configs.tar.gz", "w:gz") as tar:
        tar.add(configs_dir, arcname=".")
    
    print("✅ Configuration package created")

def build_game_package():
    """Build game package (placeholder)"""
    print("🎮 Building game package...")
    
    game_dir = ASSETS_DIR / "godot-game"
    game_dir.mkdir(exist_ok=True)
    
    # Create placeholder game files
    with open(game_dir / "README.txt", "w") as f:
        f.write("""Deckport Game Package
        
This package should contain:
- game.x86_64 (Godot executable)
- game.pck (Game data, if separate)
- Any additional game assets

To add your game:
1. Export your Godot project for Linux
2. Copy the exported files to this directory
3. Run this script again to rebuild the package
""")
    
    # Create package
    with tarfile.open(STATIC_DIR / "godot-game-latest.tar.gz", "w:gz") as tar:
        tar.add(game_dir, arcname=".")
    
    print("✅ Game package created (placeholder)")

def create_deployment_info():
    """Create deployment information file"""
    info = {
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "wifi_portal": "WiFi configuration portal",
            "boot_theme": "Plymouth boot theme with Deckport branding", 
            "configs": "System configuration files and scripts",
            "game": "Godot game executable and assets"
        },
        "deployment_url": "https://deckport.ai/deploy/console",
        "usage": "curl -sSL https://deckport.ai/deploy/console | bash"
    }
    
    with open(STATIC_DIR / "deployment-info.json", "w") as f:
        json.dump(info, f, indent=2)
    
    print("✅ Deployment info created")

def main():
    """Build all deployment assets"""
    print("🚀 Building Deckport Console Deployment Assets")
    print("=" * 50)
    
    create_directories()
    build_wifi_portal_package()
    build_boot_theme_package() 
    build_configs_package()
    build_game_package()
    create_deployment_info()
    
    print("=" * 50)
    print("✅ All deployment assets built successfully!")
    print(f"📁 Assets location: {STATIC_DIR}")
    print("🔗 Deployment URL: https://deckport.ai/deploy/console")
    print("")
    print("Next steps:")
    print("1. Add your Godot game files to replace the placeholder")
    print("2. Add your logo.png to the boot theme")
    print("3. Test deployment on a console")
    print("=" * 50)

if __name__ == "__main__":
    main()
