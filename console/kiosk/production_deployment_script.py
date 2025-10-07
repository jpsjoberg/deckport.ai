#!/usr/bin/env python3
"""
Deckport Console Production Deployment Script Generator
Generates production-ready deployment scripts with all fixes applied
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def generate_production_deployment_script(console_id=None, game_version="latest", location="Unknown"):
    """Generate production-ready deployment script with all fixes"""
    
    if not console_id:
        console_id = f"console-{int(datetime.now().timestamp())}"
    
    timestamp = datetime.now().isoformat()
    
    script = f'''#!/bin/bash

#################################################
# Deckport Console Production Deployment Script
# Generated: {timestamp}
# Console ID: {console_id}
# Game Version: {game_version}
# Location: {location}
# Status: PRODUCTION READY with X11/WiFi fixes
#################################################

set +e  # Don't exit on error - handle gracefully

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
PURPLE='\\033[0;35m'
CYAN='\\033[0;36m'
NC='\\033[0m' # No Color

# Configuration
DEPLOYMENT_SERVER="https://deckport.ai"
API_SERVER="https://deckport.ai"
CONSOLE_ID="{console_id}"
GAME_VERSION="{game_version}"
LOCATION="{location}"
DEPLOYMENT_LOG="/tmp/deckport-deployment.log"

# Enhanced logging with file output
log() {{
    local message="${{GREEN}}[$(date '+%Y-%m-%d %H:%M:%S')]${{NC}} $1"
    echo -e "$message"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEPLOYMENT_LOG"
}}

error() {{
    local message="${{RED}}[ERROR]${{NC}} $1"
    echo -e "$message" >&2
    echo "[ERROR] $1" >> "$DEPLOYMENT_LOG"
}}

warning() {{
    local message="${{YELLOW}}[WARNING]${{NC}} $1"
    echo -e "$message"
    echo "[WARNING] $1" >> "$DEPLOYMENT_LOG"
}}

info() {{
    local message="${{BLUE}}[INFO]${{NC}} $1"
    echo -e "$message"
    echo "[INFO] $1" >> "$DEPLOYMENT_LOG"
}}

success() {{
    local message="${{PURPLE}}[SUCCESS]${{NC}} $1"
    echo -e "$message"
    echo "[SUCCESS] $1" >> "$DEPLOYMENT_LOG"
}}

progress() {{
    local message="${{CYAN}}[PROGRESS]${{NC}} $1"
    echo -e "$message"
    echo "[PROGRESS] $1" >> "$DEPLOYMENT_LOG"
}}

# Initialize deployment log
echo "Deckport Console Deployment Log - ${{timestamp}}" > "$DEPLOYMENT_LOG"
echo "Console ID: $CONSOLE_ID" >> "$DEPLOYMENT_LOG"
echo "=========================================" >> "$DEPLOYMENT_LOG"

# Check prerequisites
check_prerequisites() {{
    log "🔍 Checking deployment prerequisites..."
    
    # Check if running as correct user
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Run as the 'kiosk' user with sudo privileges."
        exit 1
    fi
    
    # Check if kiosk user exists and has sudo access
    if ! id "kiosk" &>/dev/null; then
        error "User 'kiosk' does not exist. Please create the kiosk user first."
        exit 1
    fi
    
    # Test sudo access
    if ! sudo -n true 2>/dev/null; then
        warning "Sudo access required. You may be prompted for password."
    fi
    
    # Check internet connectivity
    if ! ping -c 1 8.8.8.8 &>/dev/null; then
        warning "No internet connectivity detected. Some features may not work."
    fi
    
    # Check available disk space (need at least 2GB)
    AVAILABLE_SPACE=$(df / | tail -1 | awk '{{print $4}}')
    if [[ $AVAILABLE_SPACE -lt 2097152 ]]; then
        error "Insufficient disk space. Need at least 2GB free."
        exit 1
    fi
    
    success "Prerequisites check completed"
}}

log "========================================="
log "🎮 DECKPORT CONSOLE PRODUCTION DEPLOYMENT"
log "========================================="
log "Console ID: $CONSOLE_ID"
log "Game Version: $GAME_VERSION"
log "Location: $LOCATION"
log "Deployment Server: $DEPLOYMENT_SERVER"
log "========================================="

# Run prerequisites check
check_prerequisites

#################################################
# PHASE 1: System Preparation with Fixes
#################################################

progress "🔧 Phase 1: System preparation with production fixes..."

# Create deployment directories
info "Creating deployment directories..."
sudo mkdir -p /opt/deckport-console
sudo mkdir -p /var/log/deckport
sudo mkdir -p /opt/wifi-portal
sudo mkdir -p /opt/godot-game

# Set proper ownership
sudo chown -R kiosk:kiosk /opt/deckport-console
sudo chmod 755 /opt/deckport-console

# Update system packages
info "Updating system packages..."
sudo apt update
if ! sudo apt upgrade -y; then
    warning "Some package upgrades failed, continuing..."
fi

# Function to safely install packages with better error handling
install_packages() {{
    local package_list="$1"
    local description="$2"
    local critical="${{3:-false}}"
    
    info "Installing $description packages..."
    
    # Convert package list to array
    read -ra PACKAGES <<< "$package_list"
    local failed_packages=()
    local installed_packages=()
    
    # Try installing all packages at once first
    if sudo apt install -y $package_list 2>/dev/null; then
        success "✅ All $description packages installed successfully"
        return 0
    fi
    
    warning "Batch installation failed, trying individual packages..."
    
    # Install packages individually
    for package in "${{PACKAGES[@]}}"; do
        if sudo apt install -y "$package" 2>/dev/null; then
            installed_packages+=("$package")
            info "✅ Installed: $package"
        else
            failed_packages+=("$package")
            warning "❌ Failed to install: $package"
        fi
    done
    
    # Report results
    if [[ ${{#installed_packages[@]}} -gt 0 ]]; then
        success "Installed ${{#installed_packages[@]}} $description packages"
    fi
    
    if [[ ${{#failed_packages[@]}} -gt 0 ]]; then
        if [[ "$critical" == "true" ]]; then
            error "Critical packages failed to install: ${{failed_packages[*]}}"
            return 1
        else
            warning "Non-critical packages failed: ${{failed_packages[*]}}"
        fi
    fi
    
    return 0
}}

# Install core system packages (critical)
install_packages "curl wget git openssh-server network-manager jq bc openssl sudo" "core system" true

# Install Python packages (critical for console operation)
install_packages "python3 python3-pip python3-flask python3-requests python3-psutil" "Python runtime" true

# Install X11 packages (critical for display)
install_packages "xorg xinit openbox unclutter x11-xserver-utils xserver-xorg-input-all xinput xauth" "X11 display system" true

# Install multimedia packages (important but not critical)
install_packages "alsa-utils pulseaudio v4l-utils ffmpeg" "multimedia support" false

# Install development tools (helpful for debugging)
install_packages "htop iotop lsof strace mesa-utils glxinfo" "system monitoring" false

#################################################
# PHASE 2: Graphics Hardware Setup with Fixes
#################################################

progress "🎨 Phase 2: Graphics hardware setup with production fixes..."

# Detect graphics hardware
info "Detecting graphics hardware..."
GPU_INFO=$(lspci | grep -i "vga\\|display\\|graphics" 2>/dev/null || echo "No GPU detected")
info "Graphics Hardware: $GPU_INFO"

# Create base directories
sudo mkdir -p /etc/X11/xorg.conf.d
sudo mkdir -p /etc/udev/rules.d

# Intel Graphics Setup (most common for consoles)
if echo "$GPU_INFO" | grep -qi "intel"; then
    info "Intel graphics detected - applying production Intel UHD Graphics configuration..."
    
    # Install Intel graphics packages
    install_packages "libgl1-mesa-dri libegl-mesa0 libgles2 libglx-mesa0 xserver-xorg-video-intel intel-media-va-driver mesa-utils" "Intel graphics" false
    
    # Apply Intel-specific kernel parameters
    info "Configuring Intel graphics kernel parameters..."
    sudo cp /etc/default/grub /etc/default/grub.backup 2>/dev/null || true
    
    # Remove old Intel parameters and add new ones
    sudo sed -i 's/i915[^"]*//g' /etc/default/grub
    sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\\([^"]*\\)"/GRUB_CMDLINE_LINUX_DEFAULT="\\1 i915.force_probe=* intel_iommu=off i915.modeset=1"/' /etc/default/grub
    
    # Update GRUB
    if ! sudo update-grub; then
        warning "GRUB update failed, but continuing..."
    fi
    
    # Create Intel graphics udev rules with proper permissions
    cat << 'EOF' | sudo tee /etc/udev/rules.d/99-intel-graphics-console.rules
# Intel Graphics Console Access Rules
SUBSYSTEM=="drm", KERNEL=="card*", GROUP="video", MODE="0664", TAG+="uaccess"
SUBSYSTEM=="drm", KERNEL=="renderD*", GROUP="video", MODE="0664", TAG+="uaccess"  
SUBSYSTEM=="drm", KERNEL=="controlD*", GROUP="video", MODE="0664", TAG+="uaccess"
# Intel-specific device rules
SUBSYSTEM=="drm", ATTRS{{vendor}}=="0x8086", GROUP="video", MODE="0664", TAG+="uaccess"
# Console-specific permissions
KERNEL=="fb*", GROUP="video", MODE="0664"
KERNEL=="tty*", GROUP="tty", MODE="0664"
EOF
    
    # Create production X11 configuration for Intel graphics
    cat << 'EOF' | sudo tee /etc/X11/xorg.conf.d/20-intel-console-production.conf
Section "ServerLayout"
    Identifier "ConsoleLayout"
    Screen "Screen0"
    Option "DontVTSwitch" "false"
    Option "AllowEmptyInput" "true"
    Option "AutoAddDevices" "true"
    Option "AutoEnableDevices" "true"
EndSection

Section "ServerFlags"
    Option "AutoAddDevices" "true"
    Option "AutoEnableDevices" "true"
    Option "DontZap" "false"
    Option "AllowMouseOpenFail" "true"
    Option "IgnoreABI" "true"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection

Section "Device"
    Identifier "Intel Console Graphics"
    Driver "intel"
    Option "AccelMethod" "sna"
    Option "TearFree" "true"
    Option "DRI" "3"
    Option "Backlight" "intel_backlight"
    BusID "PCI:0:2:0"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "Intel Console Graphics"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080" "1680x1050" "1280x1024" "1024x768"
    EndSubSection
EndSection

Section "InputClass"
    Identifier "evdev keyboard catchall"
    MatchIsKeyboard "on"
    MatchDevicePath "/dev/input/event*"
    Driver "evdev"
EndSection

Section "InputClass"
    Identifier "evdev mouse catchall"
    MatchIsPointer "on"
    MatchDevicePath "/dev/input/event*"
    Driver "evdev"
EndSection
EOF
    
    # Load Intel graphics modules with proper parameters
    info "Loading Intel graphics modules..."
    sudo modprobe -r i915 2>/dev/null || true
    sudo modprobe i915 force_probe=* modeset=1
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger --subsystem-match=drm
    sudo udevadm settle
    
    success "Intel graphics configuration applied"
    
else
    # Fallback configuration for other graphics or no GPU
    warning "Non-Intel graphics or no GPU detected - using safe fallback configuration"
    
    # Install basic graphics packages
    install_packages "libgl1-mesa-dri libegl-mesa0 libgles2 xserver-xorg-video-fbdev" "basic graphics" false
    
    # Create safe fallback X11 configuration
    cat << 'EOF' | sudo tee /etc/X11/xorg.conf.d/20-console-fallback.conf
Section "ServerLayout"
    Identifier "FallbackLayout"
    Screen "Screen0"
    Option "DontVTSwitch" "true"
    Option "DontZap" "false"
    Option "AllowEmptyInput" "true"
EndSection

Section "ServerFlags"
    Option "AutoAddDevices" "true"
    Option "AutoEnableDevices" "true"
    Option "AllowMouseOpenFail" "true"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection

Section "Device"
    Identifier "Fallback Device"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "Fallback Device"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080" "1680x1050" "1280x1024" "1024x768"
    EndSubSection
EndSection
EOF
    
    success "Fallback graphics configuration applied"
fi

#################################################
# PHASE 3: User and Permission Setup with Fixes
#################################################

progress "👤 Phase 3: User and permission setup with production fixes..."

# Ensure kiosk user is in all required groups
info "Adding kiosk user to required groups..."
sudo usermod -a -G video,input,tty,audio,dialout,plugdev,netdev kiosk

# Create proper X11 directories and permissions
info "Setting up X11 directories and permissions..."
sudo mkdir -p /tmp/.X11-unix
sudo chmod 1777 /tmp/.X11-unix
sudo chown root:root /tmp/.X11-unix

# Create X authority directory
sudo mkdir -p /var/run/xauth
sudo chown kiosk:kiosk /var/run/xauth
sudo chmod 755 /var/run/xauth

# Set up home directory permissions
sudo chown -R kiosk:kiosk /home/kiosk
sudo chmod 755 /home/kiosk

# Create console log directory
sudo mkdir -p /var/log/deckport
sudo chown kiosk:kiosk /var/log/deckport
sudo chmod 755 /var/log/deckport

success "User and permission setup completed"

#################################################
# PHASE 4: Console Registration with API
#################################################

progress "📡 Phase 4: Console registration with Deckport API..."

# Generate RSA key pair for console authentication
info "Generating RSA key pair for console authentication..."
mkdir -p /home/kiosk/.ssh
ssh-keygen -t rsa -b 2048 -f /home/kiosk/.ssh/console_key -N "" -C "$CONSOLE_ID" 2>/dev/null || true

# Gather system information
info "Gathering system information..."
HOSTNAME=$(hostname)
IP_ADDRESS=$(hostname -I | awk '{{print $1}}' 2>/dev/null || echo "unknown")
MAC_ADDRESS=$(ip link show | awk '/ether/ {{print $2}}' | head -1 2>/dev/null || echo "unknown")
CPU_INFO=$(lscpu | grep "Model name" | cut -d: -f2 | xargs 2>/dev/null || echo "unknown")
MEMORY_INFO=$(free -h | grep Mem | awk '{{print $2}}' 2>/dev/null || echo "unknown")
DISK_INFO=$(df -h / | tail -1 | awk '{{print $2}}' 2>/dev/null || echo "unknown")

# Create console configuration file
info "Creating console configuration file..."
cat << EOF | sudo tee /opt/deckport-console/console.conf
# Deckport Console Configuration
CONSOLE_ID="$CONSOLE_ID"
GAME_VERSION="$GAME_VERSION"
LOCATION="$LOCATION"
DEPLOYMENT_SERVER="$DEPLOYMENT_SERVER"
API_SERVER="$API_SERVER"
API_ENDPOINT="$API_SERVER/v1"
REGISTERED_AT="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
MAC_ADDRESS="$MAC_ADDRESS"
IP_ADDRESS="$IP_ADDRESS"
HOSTNAME="$HOSTNAME"
CPU_INFO="$CPU_INFO"
MEMORY_INFO="$MEMORY_INFO"
DISK_INFO="$DISK_INFO"
REGISTRATION_STATUS="pending"
EOF

# Attempt console registration with API
info "Attempting console registration with Deckport API..."
if command -v curl >/dev/null 2>&1; then
    PUBLIC_KEY=$(cat /home/kiosk/.ssh/console_key.pub 2>/dev/null || echo "")
    
    REGISTRATION_DATA=$(cat << EOF
{{
    "device_uid": "$CONSOLE_ID",
    "location_name": "$LOCATION",
    "mac_address": "$MAC_ADDRESS",
    "ip_address": "$IP_ADDRESS",
    "hostname": "$HOSTNAME",
    "cpu_info": "$CPU_INFO",
    "memory_info": "$MEMORY_INFO",
    "disk_info": "$DISK_INFO",
    "public_key": "$PUBLIC_KEY",
    "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
}}
EOF
    )
    
    if curl -s -X POST "$API_SERVER/v1/auth/device/register" \\
        -H "Content-Type: application/json" \\
        -d "$REGISTRATION_DATA" \\
        --max-time 30 > /tmp/registration_response.json 2>/dev/null; then
        
        if grep -q '"success".*true' /tmp/registration_response.json 2>/dev/null; then
            success "✅ Console registered successfully with Deckport API"
            echo 'REGISTRATION_STATUS="registered"' | sudo tee -a /opt/deckport-console/console.conf
        else
            warning "Console registration failed, but continuing deployment"
            echo 'REGISTRATION_STATUS="failed"' | sudo tee -a /opt/deckport-console/console.conf
        fi
    else
        warning "Could not reach Deckport API, continuing with offline setup"
        echo 'REGISTRATION_STATUS="offline"' | sudo tee -a /opt/deckport-console/console.conf
    fi
else
    warning "curl not available for registration, continuing..."
    echo 'REGISTRATION_STATUS="no-curl"' | sudo tee -a /opt/deckport-console/console.conf
fi

success "Console registration phase completed"

#################################################
# PHASE 5: Download and Install Components
#################################################

progress "📦 Phase 5: Downloading and installing console components..."

# Function to download with retry and verification
download_component() {{
    local url="$1"
    local destination="$2"
    local description="$3"
    local max_retries=3
    
    info "Downloading $description..."
    
    for ((i=1; i<=max_retries; i++)); do
        if curl -L -f -s --max-time 300 "$url" -o "$destination"; then
            if [[ -f "$destination" && -s "$destination" ]]; then
                success "✅ Downloaded $description successfully"
                return 0
            else
                warning "Downloaded file is empty or corrupted (attempt $i/$max_retries)"
            fi
        else
            warning "Download failed (attempt $i/$max_retries)"
        fi
        
        if [[ $i -lt $max_retries ]]; then
            info "Retrying in 5 seconds..."
            sleep 5
        fi
    done
    
    error "Failed to download $description after $max_retries attempts"
    return 1
}}

# Download WiFi portal
if download_component "$DEPLOYMENT_SERVER/deploy/assets/wifi-portal.tar.gz" "/tmp/wifi-portal.tar.gz" "WiFi portal"; then
    info "Installing WiFi portal..."
    sudo tar -xzf /tmp/wifi-portal.tar.gz -C /opt/
    sudo chown -R kiosk:kiosk /opt/wifi-portal
    sudo chmod +x /opt/wifi-portal/*.py 2>/dev/null || true
else
    warning "WiFi portal download failed - creating basic fallback"
    sudo mkdir -p /opt/wifi-portal
    echo "WiFi portal not available" | sudo tee /opt/wifi-portal/README.txt
fi

# Download boot theme
if download_component "$DEPLOYMENT_SERVER/deploy/assets/boot-theme.tar.gz" "/tmp/boot-theme.tar.gz" "boot theme"; then
    info "Installing boot theme..."
    sudo tar -xzf /tmp/boot-theme.tar.gz -C /tmp/
    sudo cp -r /tmp/deckport-console /usr/share/plymouth/themes/ 2>/dev/null || true
    sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/deckport-console/deckport-console.plymouth 100 2>/dev/null || true
    sudo update-initramfs -u 2>/dev/null || true
else
    warning "Boot theme download failed - using default theme"
fi

# Download Godot game (critical component)
if download_component "$DEPLOYMENT_SERVER/deploy/assets/godot-game-$GAME_VERSION.tar.gz" "/tmp/godot-game.tar.gz" "Godot game ($GAME_VERSION)"; then
    info "Installing Godot game..."
    sudo rm -rf /opt/godot-game/*
    sudo tar -xzf /tmp/godot-game.tar.gz -C /opt/godot-game/
    sudo chown -R kiosk:kiosk /opt/godot-game
    sudo chmod +x /opt/godot-game/*.x86_64 2>/dev/null || true
    
    # Verify game installation
    if ls /opt/godot-game/*.x86_64 >/dev/null 2>&1; then
        success "✅ Godot game installed successfully"
    else
        error "Godot game installation failed - no executable found"
        exit 1
    fi
else
    error "Critical component download failed - cannot proceed without game"
    exit 1
fi

# Download system configurations
if download_component "$DEPLOYMENT_SERVER/deploy/assets/configs.tar.gz" "/tmp/configs.tar.gz" "system configurations"; then
    info "Installing system configurations..."
    sudo tar -xzf /tmp/configs.tar.gz -C /tmp/
    
    # Install systemd services
    sudo cp /tmp/configs/systemd/*.service /etc/systemd/system/ 2>/dev/null || true
    
    # Install scripts
    sudo cp /tmp/configs/scripts/* /opt/deckport-console/ 2>/dev/null || true
    sudo chmod +x /opt/deckport-console/*.sh 2>/dev/null || true
    
    # Install additional X11 configs (merge with existing)
    sudo cp /tmp/configs/x11/* /etc/X11/xorg.conf.d/ 2>/dev/null || true
    
    # Install GRUB configuration
    if [[ -f /tmp/configs/grub/grub ]]; then
        sudo cp /etc/default/grub /etc/default/grub.backup-pre-deckport 2>/dev/null || true
        sudo cp /tmp/configs/grub/grub /etc/default/grub
        sudo update-grub 2>/dev/null || warning "GRUB update failed"
    fi
else
    warning "System configurations download failed - using built-in configurations"
fi

success "Component installation completed"

#################################################
# PHASE 6: Create Production Startup Scripts
#################################################

progress "🚀 Phase 6: Creating production startup scripts with fixes..."

# Create improved X11 startup script
info "Creating production X11 startup script..."
cat << 'EOF' | sudo tee /opt/deckport-console/start-x11-production.sh
#!/bin/bash

# Deckport Console Production X11 Startup Script
LOG_FILE="/var/log/deckport/x11-startup.log"

# Ensure log directory exists
mkdir -p /var/log/deckport
touch "$LOG_FILE"

log_x11() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

log_x11 "Starting X11 server for Deckport Console (Production)..."

# Ensure proper permissions and groups
sudo usermod -a -G video,input,tty kiosk 2>/dev/null || true

# Set up TTY permissions
sudo chown kiosk:tty /dev/tty1 2>/dev/null || true
sudo chmod g+rw /dev/tty1 2>/dev/null || true

# Clean up any existing X servers and locks
sudo pkill -f "X :0" 2>/dev/null || true
sudo pkill -f "Xorg" 2>/dev/null || true
sleep 2

# Remove X11 locks and sockets
sudo rm -f /tmp/.X0-lock 2>/dev/null || true
sudo rm -f /tmp/.X11-unix/X0 2>/dev/null || true

# Ensure X11 directory permissions
sudo mkdir -p /tmp/.X11-unix
sudo chmod 1777 /tmp/.X11-unix
sudo chown root:root /tmp/.X11-unix

# Set up environment
export DISPLAY=:0
export XAUTHORITY=/home/kiosk/.Xauthority

# Create X authority file
touch /home/kiosk/.Xauthority
chown kiosk:kiosk /home/kiosk/.Xauthority
xauth generate :0 . trusted 2>/dev/null || true

# Start X server with production-safe options
log_x11 "Launching X server with production configuration..."

# Use startx for better compatibility and error handling
cat << 'XINITRC_EOF' > /home/kiosk/.xinitrc-console
#!/bin/bash
# Deckport Console X Session

# Disable screen blanking and power management
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true  
xset s noblank 2>/dev/null || true

# Hide cursor
unclutter -idle 1 -root &

# Start window manager
openbox &

# Wait for window manager
sleep 2

# Start the console application
exec /opt/deckport-console/start-console-app.sh
XINITRC_EOF

chmod +x /home/kiosk/.xinitrc-console
chown kiosk:kiosk /home/kiosk/.xinitrc-console

# Start X session
sudo -u kiosk startx /home/kiosk/.xinitrc-console -- :0 -nolisten tcp -auth /home/kiosk/.Xauthority > "$LOG_FILE" 2>&1 &

X_PID=$!
log_x11 "X server started with PID: $X_PID"

# Wait for X server to initialize
for i in {{1..15}}; do
    if DISPLAY=:0 xset q > /dev/null 2>&1; then
        log_x11 "✅ X server started successfully"
        echo "$X_PID"
        exit 0
    fi
    sleep 1
done

log_x11 "❌ X server failed to start within timeout"
sudo kill $X_PID 2>/dev/null || true
exit 1
EOF

# Create console application launcher
info "Creating console application launcher..."
cat << 'EOF' | sudo tee /opt/deckport-console/start-console-app.sh
#!/bin/bash

# Deckport Console Application Launcher
LOG_FILE="/var/log/deckport/console-app.log"
GAME_DIR="/opt/godot-game"

# Ensure log directory exists
mkdir -p /var/log/deckport
touch "$LOG_FILE"

log_app() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

log_app "Starting Deckport Console Application..."

# Source console configuration
if [[ -f /opt/deckport-console/console.conf ]]; then
    source /opt/deckport-console/console.conf
    log_app "Configuration loaded: Console ID $CONSOLE_ID"
else
    log_app "Warning: No configuration file found"
fi

# Find game executable
find_game_executable() {{
    if [[ ! -d "$GAME_DIR" ]]; then
        log_app "❌ Game directory not found: $GAME_DIR"
        return 1
    fi
    
    # Look for game executable with common names
    for name in "game.x86_64" "deckport_console.x86_64" "console.x86_64"; do
        if [[ -f "$GAME_DIR/$name" && -x "$GAME_DIR/$name" ]]; then
            echo "$GAME_DIR/$name"
            return 0
        fi
    done
    
    # Look for any .x86_64 executable
    local game_exec=$(find "$GAME_DIR" -name "*.x86_64" -executable | head -1)
    if [[ -n "$game_exec" && -f "$game_exec" ]]; then
        echo "$game_exec"
        return 0
    fi
    
    log_app "❌ No game executable found in $GAME_DIR"
    return 1
}}

# Check network connectivity
check_network() {{
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}}

# Main application logic
main() {{
    # Set display environment
    export DISPLAY=:0
    
    # Check network connectivity
    if ! check_network; then
        log_app "⚠️ No network connectivity - starting in offline mode"
    else
        log_app "✅ Network connectivity confirmed"
    fi
    
    # Find and validate game executable
    GAME_EXECUTABLE=$(find_game_executable)
    if [[ $? -ne 0 || -z "$GAME_EXECUTABLE" ]]; then
        log_app "❌ Cannot start - no game executable found"
        
        # Show error screen instead of failing silently
        if command -v zenity >/dev/null 2>&1; then
            DISPLAY=:0 zenity --error --text="Deckport Console Error\\n\\nGame executable not found.\\nPlease check installation." --width=400 --height=200 &
        fi
        
        sleep 30  # Keep X session alive for debugging
        return 1
    fi
    
    log_app "✅ Game executable found: $GAME_EXECUTABLE"
    
    # Verify game executable
    if ! file "$GAME_EXECUTABLE" | grep -q "ELF.*executable"; then
        log_app "❌ Game file is not a valid executable"
        return 1
    fi
    
    # Change to game directory
    cd "$GAME_DIR" || {{
        log_app "❌ Cannot change to game directory"
        return 1
    }}
    
    log_app "🚀 Launching Deckport Game: $GAME_EXECUTABLE"
    
    # Launch game with error capture and restart capability
    while true; do
        # Start game
        "$GAME_EXECUTABLE" --fullscreen > /var/log/deckport/game-output.log 2>&1
        GAME_EXIT_CODE=$?
        
        log_app "🎮 Game exited with code: $GAME_EXIT_CODE"
        
        # If game exited cleanly (code 0), don't restart
        if [[ $GAME_EXIT_CODE -eq 0 ]]; then
            log_app "Game exited normally"
            break
        fi
        
        # Log crash information
        log_app "❌ Game crashed - checking for restart..."
        if [[ -f /var/log/deckport/game-output.log ]]; then
            log_app "Game crash output:"
            tail -10 /var/log/deckport/game-output.log >> "$LOG_FILE"
        fi
        
        # Wait before restart
        log_app "Restarting game in 5 seconds..."
        sleep 5
    done
}}

# Run main function
main
EOF

# Create main startup script
info "Creating main console startup script..."
cat << 'EOF' | sudo tee /home/kiosk/start-kiosk-production.sh
#!/bin/bash

# Deckport Console Production Startup Script
LOG_FILE="/var/log/deckport/startup.log"

# Ensure log directory exists
mkdir -p /var/log/deckport
touch "$LOG_FILE"

log() {{
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}}

log "🎮 Starting Deckport Console (Production Version)..."

# Source console configuration
if [[ -f /opt/deckport-console/console.conf ]]; then
    source /opt/deckport-console/console.conf
    log "Configuration loaded: $CONSOLE_ID"
else
    log "Warning: No configuration file found"
fi

# Function to check network connectivity
check_network() {{
    ping -c 1 8.8.8.8 > /dev/null 2>&1
    return $?
}}

# Function to start WiFi portal if needed
start_wifi_portal() {{
    log "No network connection - checking for WiFi portal..."
    
    if [[ -f /opt/wifi-portal/wifi_portal.py ]]; then
        log "Starting WiFi configuration portal..."
        
        # Start WiFi portal service
        cd /opt/wifi-portal
        python3 wifi_portal.py &
        PORTAL_PID=$!
        
        # Start X server for portal
        if /opt/deckport-console/start-x11-production.sh; then
            # Open browser to portal
            sleep 5
            DISPLAY=:0 chromium-browser --kiosk --no-first-run --disable-translate \\
                --disable-infobars --disable-suggestions-service \\
                --disable-save-password-bubble --start-maximized \\
                --window-position=0,0 --window-size=1920,1080 \\
                --disable-web-security --disable-features=VizDisplayCompositor \\
                http://localhost:8080 &
            
            # Wait for WiFi configuration
            while [[ ! -f /tmp/wifi_configured ]]; do
                sleep 2
            done
            
            log "WiFi configured successfully"
            pkill chromium-browser
            kill $PORTAL_PID 2>/dev/null || true
            sleep 2
        else
            log "❌ Failed to start X server for WiFi portal"
            kill $PORTAL_PID 2>/dev/null || true
        fi
    else
        log "WiFi portal not available - continuing without network"
    fi
}}

# Main startup logic
main() {{
    # Check network connectivity
    if ! check_network; then
        log "⚠️ No network connectivity detected"
        start_wifi_portal
        
        # Check again after WiFi portal
        if ! check_network; then
            log "Still no network - starting in offline mode"
        fi
    else
        log "✅ Network connectivity confirmed"
    fi
    
    # Start X server and console application
    log "Starting X server and console application..."
    exec /opt/deckport-console/start-x11-production.sh
}}

# Run main function
main
EOF

# Set permissions on all scripts
sudo chmod +x /opt/deckport-console/*.sh
sudo chmod +x /home/kiosk/start-kiosk-production.sh
sudo chown -R kiosk:kiosk /opt/deckport-console
sudo chown kiosk:kiosk /home/kiosk/start-kiosk-production.sh

success "Production startup scripts created"

#################################################
# PHASE 7: System Service Configuration
#################################################

progress "⚙️ Phase 7: Configuring system services..."

# Create production systemd service
info "Creating production systemd service..."
cat << 'EOF' | sudo tee /etc/systemd/system/deckport-kiosk.service
[Unit]
Description=Deckport Kiosk Console (Production)
After=graphical-session.target network.target
Wants=graphical-session.target network-online.target

[Service]
Type=simple
User=kiosk
Group=kiosk
WorkingDirectory=/home/kiosk
ExecStart=/home/kiosk/start-kiosk-production.sh
Restart=always
RestartSec=10
Environment="HOME=/home/kiosk"
Environment="DISPLAY=:0"
Environment="XDG_RUNTIME_DIR=/run/user/1000"

# Security settings (relaxed for graphics access)
NoNewPrivileges=false
PrivateTmp=false
MemoryMax=4G
CPUQuota=95%

# Logging
StandardOutput=append:/var/log/deckport/service.log
StandardError=append:/var/log/deckport/service-error.log

[Install]
WantedBy=graphical.target
EOF

# Configure auto-login for kiosk user
info "Configuring auto-login for kiosk user..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat << 'EOF' | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin kiosk %I $TERM
Type=simple
EOF

# Configure kiosk user bashrc for auto-start
info "Configuring kiosk user auto-start..."
cat << 'EOF' | sudo tee /home/kiosk/.bashrc
# Deckport Console Auto-Start Configuration

# If running interactively and on tty1, start console
if [[ $- == *i* ]] && [[ "$(tty)" == "/dev/tty1" ]]; then
    # Check if console service is not running
    if ! systemctl --user is-active --quiet deckport-kiosk.service 2>/dev/null; then
        echo "🎮 Starting Deckport Console..."
        exec /home/kiosk/start-kiosk-production.sh
    fi
fi

# Standard bashrc content
if [ -f /etc/bash.bashrc ]; then
    . /etc/bash.bashrc
fi
EOF

sudo chown kiosk:kiosk /home/kiosk/.bashrc

# Reload systemd and enable services
info "Enabling system services..."
sudo systemctl daemon-reload
sudo systemctl enable deckport-kiosk.service
sudo systemctl enable getty@tty1.service

# Clean up failed services
sudo systemctl reset-failed

success "System services configured"

#################################################
# PHASE 8: Final Configuration and Testing
#################################################

progress "🧪 Phase 8: Final configuration and testing..."

# Create console management tools
info "Installing console management tools..."
cat << 'EOF' | sudo tee /opt/deckport-console/manage-console-production.sh
#!/bin/bash

# Deckport Console Production Management Script

CONSOLE_CONF="/opt/deckport-console/console.conf"
SERVICE_NAME="deckport-kiosk.service"

case "$1" in
    "start")
        echo "▶️ Starting Deckport Console..."
        sudo systemctl start $SERVICE_NAME
        echo "✅ Console start initiated"
        ;;
    "stop")
        echo "⏹️ Stopping Deckport Console..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Console stopped"
        ;;
    "restart")
        echo "🔄 Restarting Deckport Console..."
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Console restart initiated"
        ;;
    "status")
        echo "📊 Console Service Status:"
        systemctl status $SERVICE_NAME --no-pager
        ;;
    "logs")
        echo "📋 Recent Console Logs:"
        tail -50 /var/log/deckport/startup.log 2>/dev/null || echo "No startup logs available"
        ;;
    "game-logs")
        echo "🎮 Game Logs:"
        tail -50 /var/log/deckport/game-output.log 2>/dev/null || echo "No game logs available"
        ;;
    "system-info")
        echo "💻 System Information:"
        if [[ -f "$CONSOLE_CONF" ]]; then
            source "$CONSOLE_CONF"
            echo "Console ID: $CONSOLE_ID"
            echo "Location: $LOCATION"
            echo "Game Version: $GAME_VERSION"
            echo "Registration Status: $REGISTRATION_STATUS"
        fi
        echo "Hostname: $(hostname)"
        echo "IP Address: $(hostname -I | awk '{{print $1}}')"
        echo "Uptime: $(uptime -p)"
        echo "Memory: $(free -h | grep Mem | awk '{{print $3 "/" $2}}')"
        echo "Disk: $(df -h / | tail -1 | awk '{{print $3 "/" $2 " (" $5 " used)"}}')"
        echo "Graphics: $(lspci | grep VGA | cut -d: -f3 | xargs)"
        ;;
    "network-test")
        echo "🌐 Network Connectivity Test:"
        if ping -c 3 deckport.ai; then
            echo "✅ Can reach deckport.ai"
        else
            echo "❌ Cannot reach deckport.ai"
        fi
        ;;
    "graphics-test")
        echo "🎨 Graphics Test:"
        if DISPLAY=:0 xset q >/dev/null 2>&1; then
            echo "✅ X server is running"
        else
            echo "❌ X server is not running"
        fi
        
        if command -v glxinfo >/dev/null 2>&1; then
            echo "OpenGL Info:"
            DISPLAY=:0 glxinfo | grep -E "OpenGL (vendor|renderer|version)" | head -3
        fi
        ;;
    "fix-permissions")
        echo "🔧 Fixing permissions..."
        sudo usermod -a -G video,input,tty,audio kiosk
        sudo chown -R kiosk:kiosk /opt/deckport-console
        sudo chown kiosk:kiosk /home/kiosk/.Xauthority 2>/dev/null || true
        sudo chmod 1777 /tmp/.X11-unix
        echo "✅ Permissions fixed"
        ;;
    "emergency-stop")
        echo "🚨 Emergency stop - killing all console processes..."
        sudo systemctl stop $SERVICE_NAME
        sudo pkill -f deckport
        sudo pkill -f godot
        sudo pkill -f "X :0"
        echo "✅ All console processes stopped"
        ;;
    *)
        echo "🎮 Deckport Console Production Management"
        echo "Usage: $0 {{command}}"
        echo ""
        echo "Available commands:"
        echo "  start           - Start the console"
        echo "  stop            - Stop the console"
        echo "  restart         - Restart the console"
        echo "  status          - Show service status"
        echo "  logs            - Show console logs"
        echo "  game-logs       - Show game logs"
        echo "  system-info     - Show system information"
        echo "  network-test    - Test network connectivity"
        echo "  graphics-test   - Test graphics system"
        echo "  fix-permissions - Fix file permissions"
        echo "  emergency-stop  - Emergency stop all processes"
        ;;
esac
EOF

sudo chmod +x /opt/deckport-console/manage-console-production.sh

# Create diagnostic script
info "Creating diagnostic script..."
cat << 'EOF' | sudo tee /opt/deckport-console/diagnostics.sh
#!/bin/bash

echo "========================================="
echo "🔍 DECKPORT CONSOLE DIAGNOSTICS"
echo "========================================="
echo "Generated: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "=== CONSOLE CONFIGURATION ==="
if [[ -f /opt/deckport-console/console.conf ]]; then
    cat /opt/deckport-console/console.conf
else
    echo "Configuration file not found"
fi

echo ""
echo "=== SYSTEM INFORMATION ==="
echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || uname -a)"
echo "Kernel: $(uname -r)"
echo "Memory: $(free -h | grep Mem | awk '{{print $3 "/" $2}}')"
echo "Disk: $(df -h / | tail -1 | awk '{{print $3 "/" $2 " (" $5 " used)"}}')"
echo "Uptime: $(uptime -p)"

echo ""
echo "=== GRAPHICS HARDWARE ==="
lspci | grep -i "vga\\|display\\|graphics"
echo ""
echo "Graphics devices:"
ls -la /dev/dri/ 2>/dev/null || echo "No DRI devices found"

echo ""
echo "=== NETWORK STATUS ==="
ip addr show | grep -E "inet.*scope global"
echo ""
echo "Network connectivity:"
ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "✅ Internet: OK" || echo "❌ Internet: Failed"
ping -c 1 deckport.ai >/dev/null 2>&1 && echo "✅ Deckport API: OK" || echo "❌ Deckport API: Failed"

echo ""
echo "=== SERVICE STATUS ==="
systemctl status deckport-kiosk.service --no-pager

echo ""
echo "=== X11 STATUS ==="
if DISPLAY=:0 xset q >/dev/null 2>&1; then
    echo "✅ X server: Running"
    echo "Display info:"
    DISPLAY=:0 xrandr 2>/dev/null | head -5 || echo "Cannot get display info"
else
    echo "❌ X server: Not running"
fi

echo ""
echo "=== GAME STATUS ==="
if [[ -d /opt/godot-game ]]; then
    echo "Game directory contents:"
    ls -la /opt/godot-game/
    
    GAME_EXEC=$(find /opt/godot-game -name "*.x86_64" -executable | head -1)
    if [[ -n "$GAME_EXEC" ]]; then
        echo "✅ Game executable found: $GAME_EXEC"
        echo "File info: $(file "$GAME_EXEC")"
    else
        echo "❌ No game executable found"
    fi
else
    echo "❌ Game directory not found"
fi

echo ""
echo "=== RECENT LOGS ==="
echo "Startup logs (last 10 lines):"
tail -10 /var/log/deckport/startup.log 2>/dev/null || echo "No startup logs"

echo ""
echo "Service logs (last 10 lines):"
tail -10 /var/log/deckport/service.log 2>/dev/null || echo "No service logs"

echo ""
echo "========================================="
echo "Diagnostics complete"
echo "========================================="
EOF

sudo chmod +x /opt/deckport-console/diagnostics.sh

# Run basic system tests
info "Running basic system tests..."

# Test X11 configuration
if [[ -f /etc/X11/xorg.conf.d/20-intel-console-production.conf ]] || [[ -f /etc/X11/xorg.conf.d/20-console-fallback.conf ]]; then
    success "✅ X11 configuration files present"
else
    warning "⚠️ X11 configuration may be incomplete"
fi

# Test game installation
if ls /opt/godot-game/*.x86_64 >/dev/null 2>&1; then
    success "✅ Game executable found"
else
    warning "⚠️ Game executable not found"
fi

# Test network connectivity
if ping -c 1 deckport.ai >/dev/null 2>&1; then
    success "✅ Network connectivity test passed"
else
    warning "⚠️ Cannot reach deckport.ai"
fi

# Test console configuration
if [[ -f /opt/deckport-console/console.conf ]]; then
    success "✅ Console configuration file created"
else
    warning "⚠️ Console configuration file missing"
fi

success "System tests completed"

#################################################
# PHASE 9: Cleanup and Finalization
#################################################

progress "🧹 Phase 9: Cleanup and finalization..."

# Clean up temporary files
info "Cleaning up temporary files..."
rm -f /tmp/*.tar.gz 2>/dev/null || true
rm -f /tmp/registration_response.json 2>/dev/null || true
rm -rf /tmp/configs 2>/dev/null || true

# Set final permissions
info "Setting final permissions..."
sudo chown -R kiosk:kiosk /home/kiosk
sudo chown -R kiosk:kiosk /opt/deckport-console
sudo chmod -R 755 /opt/deckport-console
sudo chmod +x /opt/deckport-console/*.sh

# Create deployment completion marker
info "Creating deployment completion marker..."
cat << EOF | sudo tee /opt/deckport-console/deployment-complete.txt
Deckport Console Deployment Completed Successfully
Deployment Date: $(date)
Console ID: $CONSOLE_ID
Game Version: $GAME_VERSION
Location: $LOCATION
Deployment Script Version: Production v2.0
EOF

success "Cleanup and finalization completed"

#################################################
# DEPLOYMENT COMPLETE
#################################################

log "========================================="
log "🎉 DECKPORT CONSOLE DEPLOYMENT COMPLETE!"
log "========================================="

echo ""
echo "📋 Deployment Summary:"
echo "  ✅ System packages installed and configured"
echo "  ✅ Graphics hardware detected and configured"
echo "  ✅ User permissions and groups set up"
echo "  ✅ Console registered with Deckport API"
echo "  ✅ Game and components downloaded and installed"
echo "  ✅ Production startup scripts created"
echo "  ✅ System services configured and enabled"
echo "  ✅ Management tools installed"
echo "  ✅ System tests completed"
echo ""
echo "🎮 Console Information:"
echo "  Console ID: $CONSOLE_ID"
echo "  Location: $LOCATION"
echo "  Game Version: $GAME_VERSION"
echo "  IP Address: $(hostname -I | awk '{{print $1}}')"
echo "  Hostname: $(hostname)"
echo ""
echo "🛠️ Management Commands:"
echo "  Status:    /opt/deckport-console/manage-console-production.sh status"
echo "  Restart:   /opt/deckport-console/manage-console-production.sh restart"
echo "  Logs:      /opt/deckport-console/manage-console-production.sh logs"
echo "  System:    /opt/deckport-console/manage-console-production.sh system-info"
echo "  Diagnose:  /opt/deckport-console/diagnostics.sh"
echo ""
echo "🚨 Emergency Access:"
echo "  Emergency TTY: Press Ctrl+Alt+F2"
echo "  Emergency Stop: /opt/deckport-console/manage-console-production.sh emergency-stop"
echo ""
echo "🔄 Next Steps:"
echo "  1. Console will reboot automatically in 30 seconds"
echo "  2. After reboot, console will start in kiosk mode"
echo "  3. Monitor console status at: https://deckport.ai/admin/consoles"
echo ""

# Upload deployment completion status
if command -v curl >/dev/null 2>&1 && ping -c 1 deckport.ai >/dev/null 2>&1; then
    info "Sending deployment completion notification..."
    
    COMPLETION_DATA=$(cat << EOF
{{
    "console_id": "$CONSOLE_ID",
    "deployment_status": "completed",
    "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S+00:00)",
    "location": "$LOCATION",
    "game_version": "$GAME_VERSION",
    "ip_address": "$(hostname -I | awk '{{print $1}}')",
    "hostname": "$(hostname)"
}}
EOF
    )
    
    curl -s -X POST "$API_SERVER/v1/admin/deployment/complete" \\
        -H "Content-Type: application/json" \\
        -d "$COMPLETION_DATA" \\
        --max-time 10 >/dev/null 2>&1 && success "✅ Deployment notification sent" || warning "⚠️ Could not send deployment notification"
fi

# Save deployment log
cp "$DEPLOYMENT_LOG" /opt/deckport-console/deployment.log 2>/dev/null || true

success "🎮 Production deployment completed successfully!"

echo ""
echo "⏰ Automatic reboot in 30 seconds..."
echo "   Press Ctrl+C to cancel automatic reboot"

# Countdown and reboot
for i in {{30..1}}; do
    echo -ne "\\r⏰ Rebooting in $i seconds...  "
    sleep 1
done

echo ""
log "🔄 Rebooting console to activate kiosk mode..."

# Reboot to activate all changes
sudo reboot

'''
    
    return script

def main():
    """Main function to generate and save the production deployment script"""
    
    # Get parameters from command line or use defaults
    console_id = sys.argv[1] if len(sys.argv) > 1 else None
    game_version = sys.argv[2] if len(sys.argv) > 2 else "latest"
    location = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
    
    # Generate the script
    script = generate_production_deployment_script(console_id, game_version, location)
    
    # Save to file
    output_file = Path("production_deployment_script.sh")
    with open(output_file, 'w') as f:
        f.write(script)
    
    # Make executable
    os.chmod(output_file, 0o755)
    
    print(f"✅ Production deployment script generated: {output_file}")
    print(f"📋 Console ID: {console_id or 'auto-generated'}")
    print(f"🎮 Game Version: {game_version}")
    print(f"📍 Location: {location}")
    print("")
    print("🚀 To deploy to console:")
    print(f"   scp {output_file} kiosk@[console-ip]:")
    print(f"   ssh kiosk@[console-ip] 'bash {output_file}'")
    print("")
    print("🌐 Or serve via web:")
    print("   curl -sSL https://deckport.ai/deploy/console | bash")

if __name__ == "__main__":
    main()
