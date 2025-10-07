# Ubuntu Godot Kiosk Console - Complete Setup Guide

## Part 1: Initial Ubuntu Installation

### Step 1: Install Ubuntu Server
1. Download Ubuntu Server 22.04 LTS (not Desktop edition)
2. During installation:
   - Create user: `kiosk` (remember this password for initial setup)
   - Enable OpenSSH server when prompted
   - Don't install any additional snaps

### Step 2: Initial System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    xorg \
    xinit \
    openbox \
    unclutter \
    nodejs \
    npm \
    network-manager \
    python3-pip \
    python3-flask \
    git \
    curl \
    plymouth \
    plymouth-themes \
    v4l-utils \
    alsa-utils \
    pulseaudio

# Remove unnecessary packages
sudo apt remove -y \
    snapd \
    cloud-init \
    ubuntu-advantage-tools

# Clean up
sudo apt autoremove -y
```

## Part 2: WiFi Setup Portal

### Step 3: Create WiFi Configuration Web App

Create the directory structure:
```bash
sudo mkdir -p /opt/wifi-portal
sudo chown kiosk:kiosk /opt/wifi-portal
cd /opt/wifi-portal
```

Create `/opt/wifi-portal/wifi_portal.py`:
```python
#!/usr/bin/env python3
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
        for line in result.stdout.strip().split('\n'):
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
        # Trigger system to continue booting
        subprocess.run(['sudo', 'systemctl', 'start', 'godot-kiosk.service'])
        return jsonify({'status': 'success', 'message': 'Connected successfully!'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to connect'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
```

Create `/opt/wifi-portal/templates/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Console WiFi Setup</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
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
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .network-list {
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .network-item {
            padding: 15px;
            border: 2px solid #f0f0f0;
            border-radius: 10px;
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
        }
        
        .network-item.selected {
            border-color: #667eea;
            background: #f0f3ff;
        }
        
        .network-name {
            font-weight: 500;
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
            background: #4caf50;
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
            padding: 12px;
            border: 2px solid #f0f0f0;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            margin-top: 10px;
        }
        
        .status {
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            text-align: center;
            display: none;
        }
        
        .status.show {
            display: block;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Console Setup</h1>
        <p class="subtitle">Select your WiFi network to continue</p>
        
        <div class="network-list" id="networkList">
            {% for network in networks %}
            <div class="network-item" onclick="selectNetwork('{{ network.ssid }}', '{{ network.security }}')">
                <div class="network-name">{{ network.ssid }}</div>
                <div class="signal-strength">
                    <div class="signal-bar" style="height: 8px; {{ 'background: #4caf50;' if network.signal > 20 else '' }}"></div>
                    <div class="signal-bar" style="height: 12px; {{ 'background: #4caf50;' if network.signal > 40 else '' }}"></div>
                    <div class="signal-bar" style="height: 16px; {{ 'background: #4caf50;' if network.signal > 60 else '' }}"></div>
                    <div class="signal-bar" style="height: 20px; {{ 'background: #4caf50;' if network.signal > 80 else '' }}"></div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="password-section" id="passwordSection">
            <input type="password" id="password" placeholder="Enter WiFi password" onkeypress="if(event.key==='Enter') connect()">
        </div>
        
        <button class="btn" id="connectBtn" onclick="connect()" disabled>Connect</button>
        <button class="btn btn-secondary" onclick="scanNetworks()">Refresh Networks</button>
        
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
                    status.textContent = 'Connected! Starting console...';
                    setTimeout(() => {
                        status.textContent = 'Console is now running!';
                    }, 3000);
                } else {
                    status.className = 'status show error';
                    status.textContent = data.message || 'Connection failed. Please try again.';
                    connectBtn.disabled = false;
                    connectBtn.textContent = 'Connect';
                }
            } catch (error) {
                status.className = 'status show error';
                status.textContent = 'An error occurred. Please try again.';
                connectBtn.disabled = false;
                connectBtn.textContent = 'Connect';
            }
        }
        
        async function scanNetworks() {
            const networkList = document.getElementById('networkList');
            networkList.innerHTML = '<div class="spinner"></div>';
            
            try {
                const response = await fetch('/scan');
                const networks = await response.json();
                
                let html = '';
                networks.forEach(network => {
                    html += `
                        <div class="network-item" onclick="selectNetwork('${network.ssid}', '${network.security}')">
                            <div class="network-name">${network.ssid}</div>
                            <div class="signal-strength">
                                <div class="signal-bar" style="height: 8px; ${network.signal > 20 ? 'background: #4caf50;' : ''}"></div>
                                <div class="signal-bar" style="height: 12px; ${network.signal > 40 ? 'background: #4caf50;' : ''}"></div>
                                <div class="signal-bar" style="height: 16px; ${network.signal > 60 ? 'background: #4caf50;' : ''}"></div>
                                <div class="signal-bar" style="height: 20px; ${network.signal > 80 ? 'background: #4caf50;' : ''}"></div>
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
</html>
```

### Step 4: Create WiFi Portal Service

Create `/etc/systemd/system/wifi-portal.service`:
```bash
sudo nano /etc/systemd/system/wifi-portal.service
```

Add:
```ini
[Unit]
Description=WiFi Configuration Portal
After=network.target

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
```

## Part 3: Boot Logo Configuration

### Step 5: Create Custom Plymouth Theme

Create theme directory:
```bash
sudo mkdir -p /usr/share/plymouth/themes/game-console
cd /usr/share/plymouth/themes/game-console
```

Create `/usr/share/plymouth/themes/game-console/game-console.plymouth`:
```ini
[Plymouth Theme]
Name=Game Console
Description=Custom boot theme for game console
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/game-console
ScriptFile=/usr/share/plymouth/themes/game-console/game-console.script
```

Create `/usr/share/plymouth/themes/game-console/game-console.script`:
```
# Plymouth boot script
Window.SetBackgroundTopColor(0.16, 0.16, 0.16);
Window.SetBackgroundBottomColor(0.16, 0.16, 0.16);

# Load your logo
logo.image = Image("logo.png");
logo.sprite = Sprite(logo.image);

# Center the logo
logo.sprite.SetX(Window.GetX() + (Window.GetWidth() - logo.image.GetWidth()) / 2);
logo.sprite.SetY(Window.GetY() + (Window.GetHeight() - logo.image.GetHeight()) / 2);

# Optional: Add loading animation
progress = 0;
fun refresh_callback() {
    progress++;
    logo.sprite.SetOpacity(Math.Sin(progress / 20) * 0.3 + 0.7);
}
Plymouth.SetRefreshFunction(refresh_callback);
```

Add your logo:
```bash
# Copy your logo.png to the theme directory
sudo cp /path/to/your/logo.png /usr/share/plymouth/themes/game-console/logo.png

# Install the theme
sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth \
    /usr/share/plymouth/themes/game-console/game-console.plymouth 100

# Select the theme
sudo update-alternatives --set default.plymouth \
    /usr/share/plymouth/themes/game-console/game-console.plymouth

# Update initramfs
sudo update-initramfs -u
```

## Part 4: Godot Game Setup

### Step 6: Install Godot Game

```bash
# Create directory for the game
sudo mkdir -p /opt/godot-game
sudo chown kiosk:kiosk /opt/godot-game

# Copy your exported Godot game (Linux build)
# Assuming you have exported your game as 'game.x86_64'
sudo cp /path/to/your/game.x86_64 /opt/godot-game/
sudo cp /path/to/your/game.pck /opt/godot-game/  # if separate
sudo chmod +x /opt/godot-game/game.x86_64
```

### Step 7: Create Kiosk Startup Script

Create `/home/kiosk/start-kiosk.sh`:
```bash
#!/bin/bash

# Check for network connectivity
check_network() {
    ping -c 1 8.8.8.8 > /dev/null 2>&1
    return $?
}

# Start X server
startx -- -nocursor &
XPID=$!
sleep 2

# Set display
export DISPLAY=:0

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 0 &

# Check if WiFi is configured
if ! check_network; then
    # Start WiFi portal
    echo "No network connection. Starting WiFi portal..."
    
    # Start openbox window manager
    openbox &
    
    # Start WiFi configuration portal
    chromium-browser --kiosk --no-first-run --disable-translate \
        --disable-infobars --disable-suggestions-service \
        --disable-save-password-bubble --start-maximized \
        --window-position=0,0 --window-size=1920,1080 \
        http://localhost:8080 &
    
    # Wait for WiFi to be configured
    while [ ! -f /tmp/wifi_configured ]; do
        sleep 2
    done
    
    # Kill browser
    pkill chromium-browser
fi

# Start the Godot game
exec /opt/godot-game/game.x86_64 --fullscreen
```

Make it executable:
```bash
chmod +x /home/kiosk/start-kiosk.sh
```

### Step 8: Create Systemd Services

Create `/etc/systemd/system/godot-kiosk.service`:
```bash
sudo nano /etc/systemd/system/godot-kiosk.service
```

Add:
```ini
[Unit]
Description=Godot Game Kiosk
After=multi-user.target network.target
Wants=network-online.target

[Service]
Type=simple
User=kiosk
Group=kiosk
PAMName=login
TTYPath=/dev/tty7
StandardInput=tty
StandardOutput=tty
ExecStart=/home/kiosk/start-kiosk.sh
Restart=always
RestartSec=10
Environment="HOME=/home/kiosk"

[Install]
WantedBy=graphical.target
```

Create network check service `/etc/systemd/system/network-check.service`:
```bash
sudo nano /etc/systemd/system/network-check.service
```

Add:
```ini
[Unit]
Description=Network Connectivity Check
Before=godot-kiosk.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then systemctl start wifi-portal.service; fi'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

## Part 5: System Lockdown

### Step 9: Disable TTY Switching and Boot Menu

Disable TTY switching:
```bash
sudo nano /etc/X11/xorg.conf
```

Add:
```
Section "ServerFlags"
    Option "DontVTSwitch" "true"
    Option "DontZap" "true"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection
```

Configure GRUB for silent boot:
```bash
sudo nano /etc/default/grub
```

Set:
```bash
GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=0 rd.systemd.show_status=0 rd.udev.log_level=0 vt.global_cursor_default=0"
GRUB_CMDLINE_LINUX=""
```

Update GRUB:
```bash
sudo update-grub
```

### Step 10: Install Additional Dependencies

```bash
# Install Chromium for WiFi portal
sudo apt install -y chromium-browser

# Configure auto-login for kiosk user
sudo systemctl set-default multi-user.target

# Disable unnecessary services
sudo systemctl disable cups
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

## Part 6: Remote Management

### Step 11: Setup SSH for Remote Access

```bash
# Configure SSH
sudo nano /etc/ssh/sshd_config
```

Add/modify:
```
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication yes  # Change to 'no' after setting up keys
```

Create management script `/opt/manage-console.sh`:
```bash
#!/bin/bash

case "$1" in
    restart-game)
        sudo systemctl restart godot-kiosk.service
        ;;
    update-game)
        # Download new game version
        wget -O /tmp/game-update.tar.gz "$2"
        # Extract to game directory
        sudo tar -xzf /tmp/game-update.tar.gz -C /opt/godot-game/
        # Restart game
        sudo systemctl restart godot-kiosk.service
        ;;
    view-logs)
        sudo journalctl -u godot-kiosk.service -n 100
        ;;
    reset-wifi)
        sudo rm /tmp/wifi_configured
        sudo nmcli con delete --all
        sudo systemctl restart network-check.service
        ;;
    *)
        echo "Usage: $0 {restart-game|update-game|view-logs|reset-wifi}"
        ;;
esac
```

Make it executable:
```bash
sudo chmod +x /opt/manage-console.sh
```

## Part 7: Final Setup

### Step 12: Enable Services and Test

```bash
# Enable services
sudo systemctl enable plymouth
sudo systemctl enable wifi-portal.service
sudo systemctl enable network-check.service
sudo systemctl enable godot-kiosk.service

# Set permissions
sudo chown -R kiosk:kiosk /opt/godot-game
sudo chown -R kiosk:kiosk /opt/wifi-portal

# Allow kiosk user to run network commands without password
sudo visudo
# Add this line:
# kiosk ALL=(ALL) NOPASSWD: /usr/bin/nmcli, /usr/bin/systemctl

# Create necessary directories
mkdir -p /home/kiosk/.config/openbox
echo "" > /home/kiosk/.config/openbox/rc.xml

# Test WiFi portal
sudo systemctl start wifi-portal.service
# Visit http://console-ip:8080 to test

# Reboot to test everything
sudo reboot
```

## Boot Sequence

When the console boots, it will:

1. Show your custom boot logo via Plymouth
2. Check for network connectivity
3. If no network: Launch WiFi configuration portal
4. Once connected: Start Godot game in fullscreen
5. If network exists: Boot directly to Godot game

## Remote Management Commands

From any computer on the network:
```bash
# SSH into console
ssh kiosk@console-ip

# Restart game
/opt/manage-console.sh restart-game

# Update game
/opt/manage-console.sh update-game http://your-server/game-update.tar.gz

# View logs
/opt/manage-console.sh view-logs

# Reset WiFi (force portal to appear)
/opt/manage-console.sh reset-wifi
```

## Troubleshooting

### If WiFi portal doesn't appear:
```bash
# Check service status
sudo systemctl status wifi-portal.service
sudo journalctl -u wifi-portal.service

# Manually start portal
sudo python3 /opt/wifi-portal/wifi_portal.py
```

### If game doesn't start:
```bash
# Check service status
sudo systemctl status godot-kiosk.service
sudo journalctl -u godot-kiosk.service

# Test game manually
DISPLAY=:0 /opt/godot-game/game.x86_64
```

### To access system locally (emergency):
1. Press Ctrl+Alt+F2 during boot (if not disabled)
2. Login as kiosk user
3. Run: `sudo systemctl stop godot-kiosk.service`

## Security Notes

1. Change default passwords immediately
2. Set up SSH keys and disable password authentication
3. Configure firewall: `sudo ufw allow 22/tcp && sudo ufw allow 8080/tcp && sudo ufw enable`
4. Consider VPN for remote management
5. Regular security updates: Create cron job for unattended upgrades

## Optional Enhancements

- Add watchdog to auto-restart game if it crashes
- Implement automatic updates from your server
- Add VPN client for secure remote access
- Set up monitoring with Prometheus/Grafana
- Create backup/restore functional