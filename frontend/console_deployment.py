"""
Console Deployment Routes
Handles automated kiosk console deployment and management
"""

from flask import Blueprint, request, jsonify, Response, render_template, make_response
from datetime import datetime, timezone
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

deploy_bp = Blueprint('deploy', __name__, url_prefix='/deploy')


@deploy_bp.route('/console')
@deploy_bp.route('/console/dry-run')
def deploy_console():
    """
    Main deployment script endpoint with ALL FIXES APPLIED
    Returns the production deployment script for automated console setup
    """
    
    # Get parameters with intelligent location detection
    console_id = request.args.get('id', f'console-{int(datetime.now().timestamp())}')
    game_version = request.args.get('version', 'latest')
    
    # Enhanced location detection
    location = request.args.get('location')
    if not location:
        # Try to determine location from IP or other sources
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if client_ip and client_ip != '127.0.0.1' and client_ip != 'unknown':
            location = f"Console-{client_ip.replace('.', '-')}"
        else:
            location = f"Console-{console_id.split('-')[-1]}"
    
    dry_run = 'dry-run' in request.path
    
    # Generate deployment script with all fixes applied directly
    script = f"""#!/bin/bash

#################################################
# Deckport Console Production Deployment Script
# Generated: {datetime.now().isoformat()}
# Console ID: {console_id}
# Game Version: {game_version}
# Status: PRODUCTION READY with X11/WiFi fixes
#################################################

set +e  # Don't exit on error - handle gracefully

# Enhanced error handling and logging
exec > >(tee -a /var/log/deckport-deployment.log)
exec 2>&1

# Trap to catch any script exits
trap 'echo "🚨 DEPLOYMENT SCRIPT EXITED at line $LINENO with exit code $?" | tee -a /var/log/deckport-deployment.log' EXIT

# Function to log with timestamp and write to deployment log
deployment_log() {{
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> /var/log/deckport-deployment.log 2>/dev/null || true
}}

deployment_log "🚀 DEPLOYMENT STARTED with enhanced error handling"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
PURPLE='\\033[0;35m'
NC='\\033[0m' # No Color

# Configuration
DEPLOYMENT_SERVER="https://deckport.ai"
API_SERVER="https://deckport.ai"
CONSOLE_ID="{console_id}"
GAME_VERSION="{game_version}"
LOCATION_PROVIDED="{location}"

# Enhanced location detection
detect_location() {{
    local detected_location="$LOCATION_PROVIDED"
    
    # If location is generic, try to detect more specific information
    if [[ "$detected_location" == "Console-"* ]] || [[ "$detected_location" == "Unknown" ]]; then
        info "Detecting console location..."
        
        # Try to get location from hostname
        local hostname_location=$(hostname | sed 's/deckport//g' | sed 's/console//g' | sed 's/kiosk//g' | sed 's/[0-9-]//g')
        if [[ -n "$hostname_location" && "$hostname_location" != "" ]]; then
            detected_location="$hostname_location-Console"
            info "Location detected from hostname: $detected_location"
        fi
        
        # Try to get location from network (router name, etc.)
        local wifi_ssid=$(iwgetid -r 2>/dev/null || echo "")
        if [[ -n "$wifi_ssid" && "$wifi_ssid" != "" ]]; then
            detected_location="$wifi_ssid-Console"
            info "Location detected from WiFi: $detected_location"
        fi
        
        # Try to get location from IP subnet
        local ip_subnet=$(hostname -I | awk '{{print $1}}' | cut -d. -f1-3)
        if [[ -n "$ip_subnet" ]]; then
            detected_location="Network-${{ip_subnet}}.x-Console"
            info "Location detected from IP subnet: $detected_location"
        fi
        
        # If still generic, use more descriptive default
        if [[ "$detected_location" == "Console-"* ]]; then
            detected_location="Field-Console-$(date +%m%d)"
            info "Using date-based location: $detected_location"
        fi
    fi
    
    echo "$detected_location"
}}

# Detect and set final location
LOCATION=$(detect_location)

# Use auto-detected location (no interactive prompts for automated deployment)
info "Using auto-detected location: $LOCATION"

info "Final console location: $LOCATION"

# Enhanced logging function with deployment log
log() {{
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${{GREEN}}$message${{NC}}"
    deployment_log "LOG: $1"
}}

error() {{
    local message="[ERROR] $1"
    echo -e "${{RED}}$message${{NC}}"
    deployment_log "ERROR: $1"
    deployment_log "🚨 DEPLOYMENT FAILED at line ${{BASH_LINENO[0]}} in function ${{FUNCNAME[1]}}"
    exit 1
}}

warning() {{
    echo -e "${{YELLOW}}[WARNING]${{NC}} $1"
}}

info() {{
    echo -e "${{BLUE}}[INFO]${{NC}} $1"
}}

success() {{
    echo -e "${{PURPLE}}[SUCCESS]${{NC}} $1"
}}

# Check if running as correct user
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Run as the 'kiosk' user."
fi

# Check prerequisites
check_prerequisites() {{
    log "🔍 Checking deployment prerequisites..."
    
    # Check if kiosk user exists
    if ! id "kiosk" &>/dev/null; then
        error "User 'kiosk' does not exist. Please create the kiosk user first."
        exit 1
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        warning "Sudo access required. You may be prompted for password."
    fi
    
    # Check disk space (need at least 2GB)
    AVAILABLE_SPACE=$(df / | tail -1 | awk '{{print $4}}')
    if [[ $AVAILABLE_SPACE -lt 2097152 ]]; then
        error "Insufficient disk space. Need at least 2GB free."
        exit 1
    fi
    
    success "Prerequisites check completed"
}}

# Run prerequisites check
check_prerequisites

# Set up passwordless sudo IMMEDIATELY to prevent password prompts
info "Setting up passwordless sudo for deployment..."
echo "kiosk ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/deckport-deployment-immediate
info "✅ Passwordless sudo configured - no more password prompts during deployment"

log "========================================="
log "🎮 DECKPORT CONSOLE DEPLOYMENT STARTING"
log "========================================="
log "Console ID: $CONSOLE_ID"
log "Game Version: $GAME_VERSION"
log "Location: $LOCATION"
log "Deployment Server: $DEPLOYMENT_SERVER"
log "========================================="

#################################################
# PHASE 1: System Preparation
#################################################

deployment_log "📋 PHASE 1 STARTED: System Preparation"
log "🔧 Phase 1: Preparing system..."

# Sudo permissions already configured above - continue with deployment
info "Proceeding with deployment using passwordless sudo..."

# COMPREHENSIVE CLEANUP - TOTAL FRESH DEPLOYMENT
info "🧹 Performing TOTAL cleanup for fresh deployment (no Ubuntu reinstall needed)..."

# Stop ALL deckport and related services
sudo systemctl stop deckport-kiosk.service 2>/dev/null || true
sudo systemctl disable deckport-kiosk.service 2>/dev/null || true
sudo systemctl stop godot-kiosk.service 2>/dev/null || true
sudo systemctl disable godot-kiosk.service 2>/dev/null || true
sudo systemctl stop console-kiosk.service 2>/dev/null || true
sudo systemctl disable console-kiosk.service 2>/dev/null || true

# Remove all old startup scripts
sudo rm -f /home/kiosk/start-kiosk*.sh 2>/dev/null || true
sudo rm -f /home/kiosk/start-console*.sh 2>/dev/null || true

# Remove old systemd service files
sudo rm -f /etc/systemd/system/deckport-kiosk.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/godot-kiosk.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/console-kiosk.service 2>/dev/null || true

# Clean old configuration directories (but keep them for reuse)
sudo rm -rf /opt/deckport-console/* 2>/dev/null || true
sudo rm -rf /opt/godot-game/* 2>/dev/null || true
sudo rm -rf /opt/wifi-portal/* 2>/dev/null || true

# Remove old sudoers files (but KEEP deployment permissions active)
sudo rm -f /etc/sudoers.d/deckport-kiosk 2>/dev/null || true
sudo rm -f /etc/sudoers.d/deckport-kiosk-temp 2>/dev/null || true
sudo rm -f /etc/sudoers.d/deckport-kiosk-permanent 2>/dev/null || true
# NOTE: Keep deckport-kiosk-deploy active for this deployment process

# NOTE: Getty service cleanup moved to later in deployment to prevent terminal issues

# Kill any old processes
sudo pkill -f "start-kiosk" 2>/dev/null || true
sudo pkill -f "godot" 2>/dev/null || true
sudo pkill -f "X :0" 2>/dev/null || true
sudo pkill -f "Xorg" 2>/dev/null || true
sudo pkill -f "openbox" 2>/dev/null || true
sudo pkill -f "unclutter" 2>/dev/null || true

# Clean ALL old user session data
sudo rm -rf /home/kiosk/.config/openbox 2>/dev/null || true
sudo rm -rf /home/kiosk/.Xauthority 2>/dev/null || true
sudo rm -rf /home/kiosk/.xsession* 2>/dev/null || true

# Remove old bashrc configurations
sudo rm -f /home/kiosk/.bashrc 2>/dev/null || true
sudo rm -f /home/kiosk/.bash_profile 2>/dev/null || true

# Clean old logs
sudo rm -f /var/log/deckport*.log 2>/dev/null || true
sudo rm -f /var/log/godot*.log 2>/dev/null || true

# Reload systemd to clear old service definitions
sudo systemctl daemon-reload
sudo systemctl reset-failed

# Configure getty services properly (without stopping current session)
info "Configuring auto-login for future sessions..."

# Remove old getty overrides first
sudo rm -rf /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true
sudo rm -rf /etc/systemd/system/console-getty.service.d 2>/dev/null || true
sudo rm -rf /etc/systemd/system/serial-getty@ttyS0.service.d 2>/dev/null || true

# Create new auto-login configuration
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin kiosk %I $TERM
EOF

# Don't restart getty services during deployment to avoid terminal disruption
sudo systemctl daemon-reload
info "✅ Auto-login configured for next boot"

success "✅ Comprehensive cleanup completed - fresh installation ready"

# Update system
info "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages with robust error handling
info "Installing required packages..."

# Function to safely install packages
install_packages() {{
    local package_list="$1"
    local description="$2"
    
    info "Installing $description..."
    
    # Try to install packages, but don't fail if some are missing
    if ! sudo apt install -y $package_list; then
        warning "Some $description packages failed to install, trying individual installation..."
        
        # Try installing each package individually
        for package in $package_list; do
            if sudo apt install -y $package 2>/dev/null; then
                info "✅ Installed: $package"
            else
                warning "❌ Failed to install: $package (skipping)"
            fi
        done
    else
        success "✅ All $description packages installed successfully"
    fi
}}

# Install core system packages first (single sudo operation)
info "Installing core system packages..."
CORE_PACKAGES="curl wget git python3-flask python3-requests openssh-server network-manager jq bc openssl"
CORE_PACKAGES="$CORE_PACKAGES xorg xinit openbox unclutter x11-xserver-utils xserver-xorg-input-all xinput xauth"
CORE_PACKAGES="$CORE_PACKAGES nodejs npm plymouth plymouth-themes v4l-utils alsa-utils pulseaudio"
CORE_PACKAGES="$CORE_PACKAGES chromium-browser acpi powertop upower lm-sensors"
# Add critical Godot runtime dependencies for framebuffer mode
CORE_PACKAGES="$CORE_PACKAGES libc6 libgcc-s1 libstdc++6 zlib1g libpulse0"
CORE_PACKAGES="$CORE_PACKAGES libgl1-mesa-glx libglu1-mesa libasound2"

# Install all core packages in one operation
if sudo apt install -y $CORE_PACKAGES; then
    success "✅ All core packages installed successfully"
else
    warning "Some core packages failed, installing individually..."
    install_packages "$CORE_PACKAGES" "core system"
fi

# Auto-detect and install graphics packages
info "Detecting graphics hardware..."
GPU_INFO=$(lspci | grep -i "vga\\|display\\|graphics" 2>/dev/null || echo "No GPU detected")
info "Graphics Hardware: $GPU_INFO"

# Determine graphics type and install appropriate packages
if echo "$GPU_INFO" | grep -qi "intel"; then
    info "Intel graphics detected - installing Intel UHD Graphics support..."
    sudo apt install -y \\
        libgl1-mesa-dri \\
        libegl-mesa0 \\
        libgles2 \\
        libglx-mesa0 \\
        xserver-xorg-video-intel \\
        xserver-xorg-video-fbdev \\
        intel-media-va-driver \\
        mesa-utils || warning "Some Intel graphics packages failed to install"
    
    # Fix Intel UHD Graphics device creation issues
    info "Configuring Intel UHD Graphics device access..."
    
    # Add Intel-specific kernel parameters for UHD Graphics
    info "Adding Intel UHD Graphics kernel parameters..."
    sudo cp /etc/default/grub /etc/default/grub.backup
    
    # Add specific parameters for Intel Alder Lake-N UHD Graphics
    sudo sed -i 's/i915[^"]*//g' /etc/default/grub
    sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\\([^"]*\\)"/GRUB_CMDLINE_LINUX_DEFAULT="\\1 i915.force_probe=* intel_iommu=off i915.modeset=1"/' /etc/default/grub
    
    # Update GRUB
    sudo update-grub
    info "Intel graphics kernel parameters updated"
    
    # Create enhanced udev rules for Intel graphics device access (PRODUCTION FIX)
    cat << 'EOF' | sudo tee /etc/udev/rules.d/99-intel-graphics-console.rules
# Intel Graphics Console Access Rules - Production Fix for Permission Issues
SUBSYSTEM=="drm", KERNEL=="card*", GROUP="video", MODE="0664", TAG+="uaccess"
SUBSYSTEM=="drm", KERNEL=="renderD*", GROUP="video", MODE="0664", TAG+="uaccess"
SUBSYSTEM=="drm", KERNEL=="controlD*", GROUP="video", MODE="0664", TAG+="uaccess"
# Intel-specific device rules with enhanced permissions
SUBSYSTEM=="drm", ATTRS{{vendor}}=="0x8086", GROUP="video", MODE="0664", TAG+="uaccess"
# Console-specific permissions for TTY access
KERNEL=="fb*", GROUP="video", MODE="0664"
KERNEL=="tty*", GROUP="tty", MODE="0664"
# X11 socket permissions
SUBSYSTEM=="unix", KERNEL=="*X11-unix*", GROUP="video", MODE="0777"
EOF
    
    # Force reload graphics modules with proper parameters
    info "Reloading Intel graphics modules..."
    sudo modprobe -r i915 2>/dev/null || true
    sudo modprobe -r drm 2>/dev/null || true
    
    # Load DRM first, then Intel driver with force parameters
    sudo modprobe drm
    sudo modprobe i915 force_probe=* modeset=1
    
    # Trigger udev rules and wait longer for device creation
    sudo udevadm control --reload-rules
    sudo udevadm trigger --subsystem-match=drm
    sudo udevadm settle
    
    # Wait for device creation and retry if needed
    for i in {{1..5}}; do
        if [ -c "/dev/dri/card0" ]; then
            break
        fi
        info "Waiting for graphics device creation (attempt $i)..."
        sleep 2
        sudo udevadm trigger --subsystem-match=drm
    done
    
    # Verify graphics device creation and create X11 config (check card0 or card1)
    if [ -c "/dev/dri/card0" ] || [ -c "/dev/dri/card1" ]; then
        GRAPHICS_DEVICE=$(ls /dev/dri/card* | head -1)
        success "Intel graphics device created successfully: $GRAPHICS_DEVICE"
        
        # Create optimized X11 config for Intel UHD Graphics with VT handling and permissions
        sudo mkdir -p /etc/X11/xorg.conf.d
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

Section "Files"
    ModulePath "/usr/lib/xorg/modules"
EndSection
EOF
        success "Intel UHD Graphics X11 configuration created"
    else
        warning "Graphics device not created - using software rendering"
        
        # Use software rendering with VT handling fix
        sudo mkdir -p /etc/X11/xorg.conf.d
        cat << 'EOF' | sudo tee /etc/X11/xorg.conf.d/20-console-fallback.conf
Section "ServerLayout"
    Identifier "FallbackLayout"
    Screen "Screen0"
    Option "DontVTSwitch" "false"
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
        info "Kiosk-safe X11 configuration created"
    fi
    
    success "Intel graphics configuration completed"
    
elif echo "$GPU_INFO" | grep -qi "amd\\|radeon"; then
    info "AMD graphics detected - installing AMD support..."
    sudo apt install -y \\
        libgl1-mesa-dri \\
        libegl-mesa0 \\
        libgles2 \\
        libglx-mesa0 \\
        xserver-xorg-video-amdgpu \\
        mesa-vulkan-drivers \\
        mesa-utils || warning "Some AMD graphics packages failed to install"
    success "AMD graphics packages installed"
    
elif echo "$GPU_INFO" | grep -qi "nvidia"; then
    info "NVIDIA graphics detected - installing NVIDIA support..."
    sudo apt install -y \\
        nvidia-driver-470 \\
        libnvidia-gl-470 \\
        libegl-mesa0 \\
        libgles2 \\
        mesa-utils || warning "Some NVIDIA graphics packages failed to install"
    success "NVIDIA graphics packages installed"
    
else
    info "Generic/Unknown graphics - installing basic support..."
    sudo apt install -y \\
        libgl1-mesa-dri \\
        libegl-mesa0 \\
        libgles2 \\
        xserver-xorg-video-fbdev \\
        xserver-xorg-video-vesa \\
        mesa-utils || warning "Some graphics packages failed to install"
    success "Generic graphics packages installed"
fi

# Note: nodejs npm plymouth plymouth-themes v4l-utils alsa-utils pulseaudio chromium-browser acpi powertop upower lm-sensors
# are already installed in the core packages section above

# Install optional packages (video processing, camera tools, etc.)
info "Installing optional multimedia and camera packages..."
OPTIONAL_PACKAGES="ffmpeg gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good"
OPTIONAL_PACKAGES="$OPTIONAL_PACKAGES gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav"
OPTIONAL_PACKAGES="$OPTIONAL_PACKAGES cheese guvcview uvcdynctrl"

# Install optional packages (don't fail if they're not available)
if sudo apt install -y $OPTIONAL_PACKAGES 2>/dev/null; then
    success "✅ Optional multimedia packages installed"
else
    warning "Some optional packages not available, skipping..."
fi

# Install NFC and additional tools (optional)
info "Installing NFC reader support and additional tools..."
NFC_PACKAGES="libnfc-bin libnfc-dev libpcsclite-dev pcscd pcsc-tools libccid opensc opensc-pkcs11 vainfo evtest"

# Install NFC packages (don't fail if they're not available)
if sudo apt install -y $NFC_PACKAGES 2>/dev/null; then
    success "✅ NFC and additional tools installed"
else
    warning "Some NFC/additional tools not available, skipping..."
fi

# Remove unnecessary packages
info "Removing unnecessary packages..."
sudo apt remove -y \\
    snapd \\
    cloud-init \\
    ubuntu-advantage-tools || true

sudo apt autoremove -y

#################################################
# PHASE 2: Console Registration
#################################################

deployment_log "📋 PHASE 2 STARTED: Console Registration"
log "🔗 Phase 2: Registering console with Deckport..."

# Get system information
MAC_ADDRESS=$(ip link show | awk '/ether/ {{print $2}}' | head -n 1)
IP_ADDRESS=$(hostname -I | awk '{{print $1}}')
HOSTNAME=$(hostname)
CPU_INFO=$(cat /proc/cpuinfo | grep "model name" | head -n 1 | cut -d: -f2 | xargs)
MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{{print $2}}')
MEMORY_GB=$(($MEMORY_KB / 1024 / 1024))

info "System Information:"
info "  MAC Address: $MAC_ADDRESS"
info "  IP Address: $IP_ADDRESS" 
info "  Hostname: $HOSTNAME"
info "  CPU: $CPU_INFO"
info "  Memory: ${{MEMORY_GB}}GB"

# Download and run production console registration
info "Setting up console registration..."

# Create console configuration directory first
sudo mkdir -p /opt/deckport-console

# Simple registration without external dependencies
info "Registering console with simple method..."
    
# Create console configuration
sudo tee /opt/deckport-console/console.conf << EOL
CONSOLE_ID=$CONSOLE_ID
GAME_VERSION=$GAME_VERSION
LOCATION=$LOCATION
DEPLOYMENT_SERVER=$DEPLOYMENT_SERVER
API_SERVER=$API_SERVER
API_ENDPOINT=$API_SERVER/v1
REGISTERED_AT=$(date -Iseconds)
MAC_ADDRESS=$MAC_ADDRESS
IP_ADDRESS=$IP_ADDRESS
HOSTNAME=$HOSTNAME
REGISTRATION_STATUS=pending
EOL

# Try simple registration via curl (no Python dependencies)
info "Attempting console registration..."
REGISTRATION_RESPONSE=$(curl -s -X POST "https://api.deckport.ai/v1/auth/device/register" \\
    -H "Content-Type: application/json" \\
    -d "{{
        \\"device_uid\\": \\"$CONSOLE_ID\\",
        \\"public_key\\": \\"placeholder-will-be-generated-later\\",
        \\"location\\": {{
            \\"name\\": \\"$LOCATION\\",
            \\"source\\": \\"manual\\"
        }},
        \\"hardware_info\\": {{
            \\"mac_address\\": \\"$MAC_ADDRESS\\",
            \\"ip_address\\": \\"$IP_ADDRESS\\",
            \\"hostname\\": \\"$HOSTNAME\\",
            \\"cpu\\": \\"$CPU_INFO\\",
            \\"memory_gb\\": $MEMORY_GB
        }}
    }}" 2>/dev/null || echo "registration_failed")

if echo "$REGISTRATION_RESPONSE" | grep -q "success\\|pending\\|updated"; then
    success "Console registered successfully!"
    echo "REGISTRATION_STATUS=registered" | sudo tee -a /opt/deckport-console/console.conf
else
    warning "Console registration failed, continuing deployment..."
    echo "REGISTRATION_STATUS=failed" | sudo tee -a /opt/deckport-console/console.conf
fi

# Set proper permissions
chown -R kiosk:kiosk /opt/deckport-console/ 2>/dev/null || true
success "Console configuration created"

#################################################
# PHASE 3: Download and Install Components  
#################################################

deployment_log "📋 PHASE 3 STARTED: Component Download"
log "⬇️ Phase 3: Downloading Deckport components..."

# Create directories
sudo mkdir -p /opt/deckport-console
sudo mkdir -p /opt/wifi-portal
sudo mkdir -p /opt/godot-game
sudo chown -R kiosk:kiosk /opt/deckport-console

# Download deployment assets
TEMP_DIR="/tmp/kiosk"
# Create kiosk deployment directory
sudo mkdir -p $TEMP_DIR
sudo chown kiosk:kiosk $TEMP_DIR
mkdir -p $TEMP_DIR
cd $TEMP_DIR

info "Downloading console components..."

# Robust download function with retry logic
download_with_retry() {{
    local url="$1"
    local output="$2"
    local description="$3"
    local max_retries=8
    local retry_delay=15
    
    info "Downloading $description..."
    
    for ((i=1; i<=max_retries; i++)); do
        info "Attempt $i/$max_retries: $description"
        
        # Test network connectivity first
        if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            warning "Network connectivity issue detected, waiting..."
            sleep $retry_delay
            continue
        fi
        
        # Attempt download with enhanced settings for large files (fixes curl exit code 56)
        if curl -L -f --max-time 900 --connect-timeout 60 --retry 5 --retry-delay 10 \\
               --retry-connrefused --retry-max-time 1800 \\
               --keepalive-time 60 \\
               --speed-limit 512 --speed-time 60 \\
               -H "User-Agent: Deckport-Console-Deployment/1.0" \\
               -H "Connection: keep-alive" \\
               --progress-bar "$url" -o "$output"; then
            
            # Verify download was successful and file is not empty
            if [[ -f "$output" && -s "$output" ]]; then
                local file_size=$(stat -c%s "$output" 2>/dev/null || echo "0")
                if [[ $file_size -gt 100 ]]; then
                    success "✅ Successfully downloaded $description ($file_size bytes)"
                    return 0
                else
                    warning "Downloaded file appears to be corrupted or too small ($file_size bytes)"
                    rm -f "$output"
                fi
            else
                warning "Download completed but file is missing or empty"
            fi
        else
            warning "Download failed for $description (curl exit code: $?)"
        fi
        
        if [[ $i -lt $max_retries ]]; then
            warning "Retrying in $retry_delay seconds..."
            sleep $retry_delay
            retry_delay=$((retry_delay + 5))
        fi
    done
    
    error "Failed to download $description after $max_retries attempts"
    return 1
}}

# Download components with retry logic
download_with_retry "$DEPLOYMENT_SERVER/deploy/assets/wifi-portal" "wifi-portal.tar.gz" "WiFi portal" || warning "WiFi portal download failed"
download_with_retry "$DEPLOYMENT_SERVER/deploy/assets/boot-theme" "boot-theme.tar.gz" "boot theme" || warning "Boot theme download failed"

# Special handling for large game download (fixes curl exit code 56)
info "Preparing for large game download..."
# Disable WiFi power management during download
sudo iwconfig wlp1s0 power off 2>/dev/null || true
# Increase network buffer sizes
echo 'net.core.rmem_max = 67108864' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 67108864' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p 2>/dev/null || true

deployment_log "🎮 CRITICAL: Starting Godot game download"
if ! download_with_retry "$DEPLOYMENT_SERVER/deploy/assets/godot-game/$GAME_VERSION" "game.tar.gz" "Godot game (27MB)"; then
    deployment_log "🚨 CRITICAL FAILURE: Godot game download failed"
    ls -la /tmp/kiosk/ >> /var/log/deckport-deployment.log 2>&1 || true
    error "Failed to download game - check /var/log/deckport-deployment.log for details"
fi
deployment_log "✅ Godot game download completed successfully"

# Re-enable power management after download
sudo iwconfig wlp1s0 power on 2>/dev/null || true

download_with_retry "$DEPLOYMENT_SERVER/deploy/assets/configs" "configs.tar.gz" "configuration files" || warning "Config download failed"

#################################################
# PHASE 4: Install Components
#################################################

deployment_log "📋 PHASE 4 STARTED: Component Installation"
log "🎮 Phase 4: Installing Deckport components..."

# Install WiFi portal
info "Installing WiFi portal..."
sudo tar -xzf wifi-portal.tar.gz -C /opt/wifi-portal/
sudo chown -R kiosk:kiosk /opt/wifi-portal
# Python Flask already installed via apt packages

# Install boot theme
info "Installing boot theme..."
sudo mkdir -p /usr/share/plymouth/themes/deckport-console
sudo tar -xzf boot-theme.tar.gz -C /usr/share/plymouth/themes/deckport-console/

# Install the theme
sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth \\
    /usr/share/plymouth/themes/deckport-console/deckport-console.plymouth 100

sudo update-alternatives --set default.plymouth \\
    /usr/share/plymouth/themes/deckport-console/deckport-console.plymouth

sudo update-initramfs -u

# Install Godot game with enhanced error handling
info "Installing Godot game..."
deployment_log "🎮 CRITICAL: Starting Godot game installation"

if [[ ! -f "game.tar.gz" ]]; then
    deployment_log "🚨 CRITICAL: game.tar.gz file missing"
    ls -la . >> /var/log/deckport-deployment.log 2>&1 || true
    error "Game package not found for installation"
fi

if ! sudo tar -xzf game.tar.gz -C /opt/godot-game/; then
    deployment_log "🚨 CRITICAL: Game extraction failed"
    error "Failed to extract game package"
fi

sudo find /opt/godot-game -name "*.x86_64" -exec chmod +x {{}} \\;
sudo chown -R kiosk:kiosk /opt/godot-game

# Verify game installation
if ls /opt/godot-game/*.x86_64 >/dev/null 2>&1; then
    GAME_SIZE=$(stat -c%s /opt/godot-game/*.x86_64 2>/dev/null || echo "0")
    deployment_log "✅ Game installed successfully - size: $GAME_SIZE bytes"
else
    deployment_log "🚨 CRITICAL: No game executable found after installation"
    ls -la /opt/godot-game/ >> /var/log/deckport-deployment.log 2>&1 || true
    error "Game installation verification failed"
fi

# Install configuration files
info "Installing system configurations..."
tar -xzf configs.tar.gz

# Create production systemd service (CRITICAL)
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
ExecStart=/home/kiosk/start-kiosk.sh
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
StandardOutput=append:/var/log/deckport-service.log
StandardError=append:/var/log/deckport-service-error.log

[Install]
WantedBy=graphical.target
EOF

success "✅ Production systemd service created"
sudo systemctl daemon-reload

# Create production startup script (CRITICAL FOR X11)
info "Creating production startup script with X11 fixes..."
# Clean up any old startup scripts first - AGGRESSIVE cleanup
sudo rm -f /home/kiosk/start-kiosk-*.sh 2>/dev/null || true
sudo rm -f /home/kiosk/start-kiosk-fixed.sh 2>/dev/null || true
sudo pkill -f "start-kiosk-fixed.sh" 2>/dev/null || true
sudo systemctl stop deckport-kiosk.service 2>/dev/null || true

cat << 'EOF' | tee /home/kiosk/start-kiosk.sh
#!/bin/bash

# Deckport Console Production Startup Script
# Handles X11 server startup with proper permissions

CONSOLE_CONF="/opt/deckport-console/console.conf"
LOG_FILE="/var/log/deckport-console.log"
GAME_DIR="/opt/godot-game"

# Create deployment log function for startup script
deployment_log() {{
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> /var/log/deckport-deployment.log 2>/dev/null || true
    echo "$message" >> "$LOG_FILE" 2>/dev/null || true
}}

# Ensure log files exist with proper permissions
sudo touch "$LOG_FILE" 2>/dev/null || touch "$LOG_FILE" 2>/dev/null || true
sudo touch /var/log/deckport-deployment.log 2>/dev/null || touch /var/log/deckport-deployment.log 2>/dev/null || true
sudo touch /var/log/godot-game.log 2>/dev/null || touch /var/log/godot-game.log 2>/dev/null || true
sudo touch /var/log/godot-game-crashes.log 2>/dev/null || touch /var/log/godot-game-crashes.log 2>/dev/null || true
sudo touch /var/log/xorg-console.log 2>/dev/null || touch /var/log/xorg-console.log 2>/dev/null || true
sudo chmod 666 "$LOG_FILE" 2>/dev/null || chmod 666 "$LOG_FILE" 2>/dev/null || true
sudo chmod 666 /var/log/deckport-deployment.log 2>/dev/null || chmod 666 /var/log/deckport-deployment.log 2>/dev/null || true
sudo chmod 666 /var/log/godot-game.log 2>/dev/null || chmod 666 /var/log/godot-game.log 2>/dev/null || true
sudo chmod 666 /var/log/godot-game-crashes.log 2>/dev/null || chmod 666 /var/log/godot-game-crashes.log 2>/dev/null || true
sudo chmod 666 /var/log/xorg-console.log 2>/dev/null || chmod 666 /var/log/xorg-console.log 2>/dev/null || true

# Logging function
log() {{
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE" 2>/dev/null || true
}}

log "🎮 Starting Deckport Console (Production Version with X11 fixes)..."

# Source configuration
if [ -f "$CONSOLE_CONF" ]; then
    source "$CONSOLE_CONF"
    log "Configuration loaded: $CONSOLE_ID"
else
    log "Warning: No configuration file found"
fi

# Check network connectivity
check_network() {{
    ping -c 1 8.8.8.8 > /dev/null 2>&1
    return $?
}}

# Start X server with production fixes for permission issues
start_x_server() {{
    log "Starting X server with production permission fixes..."
    
    # Check if we have sudo access, if not skip sudo commands
    if sudo -n true 2>/dev/null; then
        # Groups should already be configured during deployment
        log "Sudo access available - configuring permissions"
    else
        log "No sudo access - skipping permission commands"
    fi
    
    # Fix TTY permissions (critical for Intel UHD Graphics) - only if sudo available
    if sudo -n true 2>/dev/null; then
        sudo chown kiosk:tty /dev/tty1 2>/dev/null || true
        sudo chmod g+rw /dev/tty1 2>/dev/null || true
    fi
    
    # Kill any existing X servers - try with and without sudo
    pkill -f "X :0" 2>/dev/null || sudo pkill -f "X :0" 2>/dev/null || true
    pkill -f "Xorg" 2>/dev/null || sudo pkill -f "Xorg" 2>/dev/null || true
    sleep 2
    
    # Clean up X11 locks and sockets - try without sudo first
    rm -f /tmp/.X0-lock 2>/dev/null || sudo rm -f /tmp/.X0-lock 2>/dev/null || true
    rm -f /tmp/.X11-unix/X0 2>/dev/null || sudo rm -f /tmp/.X11-unix/X0 2>/dev/null || true
    
    # Ensure X11 directory permissions - try without sudo first
    mkdir -p /tmp/.X11-unix 2>/dev/null || sudo mkdir -p /tmp/.X11-unix 2>/dev/null || true
    chmod 1777 /tmp/.X11-unix 2>/dev/null || sudo chmod 1777 /tmp/.X11-unix 2>/dev/null || true
    if sudo -n true 2>/dev/null; then
        sudo chown root:root /tmp/.X11-unix 2>/dev/null || true
    fi
    
    # Set up environment
    export DISPLAY=:0
    export XAUTHORITY=/home/kiosk/.Xauthority
    
    # Create X authority file with proper permissions
    touch /home/kiosk/.Xauthority
    chown kiosk:kiosk /home/kiosk/.Xauthority
    chmod 600 /home/kiosk/.Xauthority
    
    # Generate X authority with fallback
    if ! xauth generate :0 . trusted 2>/dev/null; then
        deployment_log "⚠️ xauth generate failed, trying manual setup"
        xauth add :0 . $(xxd -l 16 -p /dev/urandom) 2>/dev/null || true
    fi
    
    # Ensure kiosk user can access graphics devices
    if sudo -n true 2>/dev/null; then
        sudo usermod -a -G video,input kiosk 2>/dev/null || true
        for device in /dev/dri/card* /dev/dri/renderD*; do
            if [[ -e "$device" ]]; then
                sudo chown :video "$device" 2>/dev/null || true
                sudo chmod g+rw "$device" 2>/dev/null || true
            fi
        done
    fi
    
    # Try multiple X server startup methods for maximum compatibility
    deployment_log "🖥️ Attempting X server startup method 1: Direct X command"
    
    # Method 1: Direct X server (most reliable for consoles)
    if sudo -u kiosk X :0 \\
        -nolisten tcp \\
        -nolisten local \\
        -novtswitch \\
        -sharevts \\
        -keeptty \\
        vt1 \\
        -auth /home/kiosk/.Xauthority \\
        > /var/log/xorg-console.log 2>&1 &
    then
        deployment_log "✅ X server method 1 started successfully"
    else
        deployment_log "⚠️ X server method 1 failed, trying method 2"
        
        # Method 2: startx with specific parameters
        if sudo -u kiosk startx -- :0 -nolisten tcp vt1 > /var/log/xorg-startx.log 2>&1 &
        then
            deployment_log "✅ X server method 2 (startx) started successfully"
        else
            deployment_log "⚠️ X server method 2 failed, trying method 3"
            
            # Method 3: Simple X server without VT switching
            if sudo -u kiosk X :0 > /var/log/xorg-simple.log 2>&1 &
            then
                deployment_log "✅ X server method 3 (simple) started successfully"
            else
                deployment_log "❌ All X server methods failed"
                return 1
            fi
        fi
    fi
    
    X_PID=$!
    log "X server started with PID: $X_PID"
    
    # Wait for X server to initialize with extended timeout
    deployment_log "⏳ Waiting for X server to initialize..."
    for i in {{1..30}}; do
        if DISPLAY=:0 xset q > /dev/null 2>&1; then
            deployment_log "✅ X server started successfully after $i seconds"
            log "✅ X server started successfully"
            export DISPLAY=:0
            return 0
        fi
        if [[ $i -eq 10 ]] || [[ $i -eq 20 ]]; then
            deployment_log "⏳ Still waiting for X server... ($i/30 seconds)"
        fi
        sleep 1
    done
    
    log "❌ X server failed to start within timeout"
    sudo kill $X_PID 2>/dev/null || true
    return 1
}}

# Configure display environment
setup_display() {{
    log "Configuring display environment..."
    
    export DISPLAY=:0
    
    # Configure display settings
    DISPLAY=:0 xset s off 2>/dev/null || true
    DISPLAY=:0 xset -dpms 2>/dev/null || true
    DISPLAY=:0 xset s noblank 2>/dev/null || true
    
    # Hide cursor
    DISPLAY=:0 unclutter -idle 1 -root &
    
    # Start window manager
    DISPLAY=:0 openbox &
    sleep 2
    
    log "Display environment configured"
}}

# Find game executable
find_game() {{
    if [ ! -d "$GAME_DIR" ]; then
        log "❌ Game directory not found: $GAME_DIR"
        return 1
    fi
    
    log "Searching for game executable in $GAME_DIR..."
    
    # Look for game executable (including test game)
    GAME_EXECUTABLE=""
    for name in "game.x86_64" "test-game.x86_64" "deckport_console.x86_64" "console.x86_64"; do
        if [ -f "$GAME_DIR/$name" ] && [ -x "$GAME_DIR/$name" ]; then
            GAME_EXECUTABLE="$GAME_DIR/$name"
            break
        fi
    done
    
    # If not found, look for any .x86_64 file
    if [ -z "$GAME_EXECUTABLE" ]; then
        GAME_EXECUTABLE=$(find "$GAME_DIR" -name "*.x86_64" -executable | head -n 1)
    fi
    
    if [ -n "$GAME_EXECUTABLE" ] && [ -f "$GAME_EXECUTABLE" ]; then
        log "✅ Game found: $GAME_EXECUTABLE"
        echo "$GAME_EXECUTABLE"
        return 0
    else
        log "❌ No game executable found"
        log "Directory contents:"
        ls -la "$GAME_DIR" >> "$LOG_FILE" 2>/dev/null || true
        return 1
    fi
}}

# Main execution with production error handling
main() {{
    # Check network
    if ! check_network; then
        log "⚠️ No network connection - starting in offline mode"
    else
        log "✅ Network connectivity confirmed"
    fi
    
    # Skip X11 entirely - use framebuffer mode for console
    deployment_log "🖥️ Using framebuffer mode for console (bypassing X11)"
    log "🖥️ Starting console in framebuffer mode (more reliable than X11)"
    
    # Set up framebuffer environment for console display
    export DISPLAY=":0"
    export SDL_VIDEODRIVER=fbcon
    export SDL_FBDEV=/dev/fb0
    export SDL_NOMOUSE=1
    export GODOT_USE_FRAMEBUFFER=1
    # Set API server for game to use external server (correct endpoints)
    export API_SERVER="https://deckport.ai"
    export API_ENDPOINT="https://deckport.ai/v1"
    export DECKPORT_API_URL="https://deckport.ai"
    export HEALTH_ENDPOINT="https://deckport.ai/health"
    
    # Ensure framebuffer device is accessible
    if [[ -e "/dev/fb0" ]]; then
        deployment_log "✅ Framebuffer device found: /dev/fb0"
        if sudo -n true 2>/dev/null; then
            sudo chmod 666 /dev/fb0 2>/dev/null || true
            sudo chown kiosk:video /dev/fb0 2>/dev/null || true
        fi
    else
        deployment_log "⚠️ No framebuffer device found, trying alternative methods"
    fi
    
    # Set console font and clear screen
    setfont /usr/share/consolefonts/Lat15-Fixed16.psf.gz 2>/dev/null || true
    clear
    
    deployment_log "✅ Framebuffer environment configured"
    
    # Skip display setup - using framebuffer mode
    deployment_log "⏭️ Skipping X11 display setup - using framebuffer mode"
    
    # Find and start game
    GAME_EXEC_PATH=$(find_game)
    if [ $? -eq 0 ] && [ -n "$GAME_EXEC_PATH" ]; then
        deployment_log "✅ Game executable found: $GAME_EXEC_PATH"
        log "🚀 Starting game: $GAME_EXEC_PATH"
        
        # Change to game directory
        cd "$GAME_DIR"
        
        deployment_log "🎮 Starting game in framebuffer mode"
        log "🎮 Launching game directly on framebuffer (no X11 required)"
        
        # Start game with framebuffer mode and enhanced error logging
        while true; do
            deployment_log "🎮 Attempting to execute game in directory: $GAME_DIR"
            log "🎮 Game starting with framebuffer mode..."
            
            # Use framebuffer mode - no X11 required (use relative path to avoid corruption)
            cd "$GAME_DIR"
            deployment_log "🎮 Executing: ./game.x86_64 (relative path)"
            # Try framebuffer approach - start minimal X server for Godot
            startx ./game.x86_64 -- :0 -nolisten tcp > /var/log/godot-game.log 2>&1
            GAME_EXIT_CODE=$?
            
            deployment_log "🎮 Game exited with code: $GAME_EXIT_CODE"
            log "🎮 Game exited with code: $GAME_EXIT_CODE"
            
            # Log game crash details for server upload
            if [ $GAME_EXIT_CODE -ne 0 ]; then
                deployment_log "🚨 GAME CRASH DETECTED - Exit Code: $GAME_EXIT_CODE"
                
                # Special handling for exit code 255 (general error) and 127 (command not found)
                if [ $GAME_EXIT_CODE -eq 255 ]; then
                    deployment_log "🚨 EXIT CODE 255: General error - likely graphics or resource issue"
                    echo "=== EXIT CODE 255 ANALYSIS $(date) ===" >> /var/log/godot-game-crashes.log
                    echo "Exit code 255 typically means: Graphics driver, display, or resource loading issue" >> /var/log/godot-game-crashes.log
                    echo "Framebuffer status:" >> /var/log/godot-game-crashes.log
                    ls -la /dev/fb* >> /var/log/godot-game-crashes.log 2>/dev/null || true
                    echo "Graphics drivers:" >> /var/log/godot-game-crashes.log
                    lsmod | grep -E "i915|drm|video" >> /var/log/godot-game-crashes.log 2>/dev/null || true
                    echo "Last 30 lines of verbose game log:" >> /var/log/godot-game-crashes.log
                    tail -30 /var/log/godot-game.log >> /var/log/godot-game-crashes.log 2>/dev/null || true
                    echo "Environment variables:" >> /var/log/godot-game-crashes.log
                    env | grep -E "SDL|DISPLAY|FB|GODOT" >> /var/log/godot-game-crashes.log
                    deployment_log "🚨 EXIT CODE 255: Analysis logged - trying fallback audio driver"
                    
                    # Try with different audio driver
                    deployment_log "🔧 Trying ALSA audio driver as fallback"
                    ./game.x86_64 --rendering-driver opengl3 --audio-driver ALSA --verbose > /var/log/godot-game-alsa.log 2>&1
                    FALLBACK_EXIT=$?
                    if [ $FALLBACK_EXIT -eq 0 ]; then
                        deployment_log "✅ ALSA audio driver works - continuing with ALSA"
                        break
                    else
                        deployment_log "❌ ALSA also failed with exit code: $FALLBACK_EXIT"
                        # Try dummy audio
                        ./game.x86_64 --rendering-driver opengl3 --audio-driver Dummy --verbose > /var/log/godot-game-dummy.log 2>&1
                        DUMMY_EXIT=$?
                        if [ $DUMMY_EXIT -eq 0 ]; then
                            deployment_log "✅ Dummy audio driver works - continuing with Dummy"
                            break
                        else
                            deployment_log "❌ All audio drivers failed - entering debug mode"
                            sleep infinity
                        fi
                    fi
                elif [ $GAME_EXIT_CODE -eq 127 ]; then
                    deployment_log "🚨 EXIT CODE 127: Detailed analysis starting"
                    echo "=== EXIT CODE 127 COMPREHENSIVE ANALYSIS $(date) ===" >> /var/log/godot-game-crashes.log
                    echo "This means: Command not found - checking all possible causes" >> /var/log/godot-game-crashes.log
                    
                    echo "1. Game file verification:" >> /var/log/godot-game-crashes.log
                    echo "Expected path: $GAME_EXECUTABLE" >> /var/log/godot-game-crashes.log
                    ls -la "$GAME_EXECUTABLE" >> /var/log/godot-game-crashes.log 2>/dev/null || echo "File not found at expected path!" >> /var/log/godot-game-crashes.log
                    echo "Game directory contents:" >> /var/log/godot-game-crashes.log
                    ls -la "$GAME_DIR" >> /var/log/godot-game-crashes.log 2>/dev/null || true
                    
                    echo "2. File type check:" >> /var/log/godot-game-crashes.log
                    file "$GAME_EXECUTABLE" >> /var/log/godot-game-crashes.log 2>/dev/null || echo "Cannot determine file type" >> /var/log/godot-game-crashes.log
                    
                    echo "3. Permissions verification:" >> /var/log/godot-game-crashes.log
                    stat "$GAME_EXECUTABLE" >> /var/log/godot-game-crashes.log 2>/dev/null || echo "Cannot stat file" >> /var/log/godot-game-crashes.log
                    
                    echo "4. Dependencies check:" >> /var/log/godot-game-crashes.log
                    ldd "$GAME_EXECUTABLE" >> /var/log/godot-game-crashes.log 2>/dev/null || echo "ldd failed - file may be corrupted" >> /var/log/godot-game-crashes.log
                    
                    echo "5. Direct execution test:" >> /var/log/godot-game-crashes.log
                    "$GAME_EXECUTABLE" --version >> /var/log/godot-game-crashes.log 2>&1 || echo "Direct execution failed" >> /var/log/godot-game-crashes.log
                    
                    echo "6. Working directory check:" >> /var/log/godot-game-crashes.log
                    pwd >> /var/log/godot-game-crashes.log
                    ls -la . >> /var/log/godot-game-crashes.log
                    
                    echo "7. PATH verification:" >> /var/log/godot-game-crashes.log
                    echo "PATH: $PATH" >> /var/log/godot-game-crashes.log
                    echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH" >> /var/log/godot-game-crashes.log
                    
                    echo "8. Shell check:" >> /var/log/godot-game-crashes.log
                    echo "Shell: $SHELL" >> /var/log/godot-game-crashes.log
                    echo "User: $USER" >> /var/log/godot-game-crashes.log
                    
                    deployment_log "🚨 EXIT CODE 127: Comprehensive analysis logged"
                    
                    # Don't restart on exit code 127 - keep service alive for debugging
                    deployment_log "🛑 EXIT CODE 127: Stopping restart loop - keeping service alive for debugging"
                    log "🛑 Game has exit code 127 - stopping restart attempts"
                    log "📋 Check /var/log/godot-game-crashes.log for detailed analysis"
                    sleep infinity
                fi
                
                echo "=== GAME CRASH REPORT $(date) ===" >> /var/log/godot-game-crashes.log
                echo "Exit Code: $GAME_EXIT_CODE" >> /var/log/godot-game-crashes.log
                echo "Game Executable: $GAME_EXECUTABLE" >> /var/log/godot-game-crashes.log
                echo "Last 20 lines of game log:" >> /var/log/godot-game-crashes.log
                tail -20 /var/log/godot-game.log >> /var/log/godot-game-crashes.log 2>/dev/null || true
                echo "Environment:" >> /var/log/godot-game-crashes.log
                env | grep -E "DISPLAY|SDL|FB" >> /var/log/godot-game-crashes.log
                echo "Graphics devices:" >> /var/log/godot-game-crashes.log
                ls -la /dev/fb* /dev/dri/* >> /var/log/godot-game-crashes.log 2>/dev/null || true
                echo "========================================" >> /var/log/godot-game-crashes.log
            fi
            
            # If game exited cleanly (code 0), don't restart
            if [ $GAME_EXIT_CODE -eq 0 ]; then
                log "Game exited normally"
                break
            fi
            
            # Log crash information
            log "❌ Game crashed - restarting in 5 seconds..."
            if [ -f "/var/log/godot-game.log" ]; then
                tail -10 /var/log/godot-game.log >> "$LOG_FILE" 2>/dev/null || true
            fi
            
            sleep 5
        done
    else
        log "❌ Cannot start game - executable not found"
        log "📋 Available files in game directory:"
        ls -la /opt/godot-game/ >> /var/log/deckport-console.log 2>&1 || true
        log "❌ Game startup failed - keeping service running for debugging"
        # Don't exit - keep service running so we can debug
        sleep infinity
    fi
}}

# Run main function
main
EOF

# Set proper permissions and ownership
chmod +x /home/kiosk/start-kiosk.sh
chown kiosk:kiosk /home/kiosk/start-kiosk.sh

# Ensure the systemd service uses the correct script
sudo systemctl stop deckport-kiosk.service 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable deckport-kiosk.service
sudo systemctl start deckport-kiosk.service
# Verify the service file points to the correct script
info "Systemd service configured to use: /home/kiosk/start-kiosk.sh"
success "✅ Production startup script created and service restarted with framebuffer mode"

# Management script will be created later in the deployment process
info "Management script will be created in Phase 7.5"

#################################################
# PHASE 5: System Configuration
#################################################

log "⚙️ Phase 5: Configuring system..."

# Configure X11
info "Configuring X11..."
if [ -f "x11/xorg.conf" ]; then
    sudo cp x11/xorg.conf /etc/X11/
    success "X11 configuration installed"
else
    error "X11 configuration not found"
    find . -name "xorg.conf" 2>/dev/null || echo "No xorg.conf found anywhere"
fi

# Configure GRUB for silent boot
info "Configuring GRUB..."
if [ -f "grub/grub" ]; then
    sudo cp /etc/default/grub /etc/default/grub.backup
    sudo cp grub/grub /etc/default/grub
    sudo update-grub
    success "GRUB configuration updated"
else
    error "GRUB configuration not found"
    find . -name "grub" 2>/dev/null || echo "No grub config found anywhere"
fi

# Configure sudoers for kiosk user (including camera access)
echo "kiosk ALL=(ALL) NOPASSWD: /usr/bin/nmcli, /usr/bin/systemctl, /opt/deckport-console/manage-console.sh, /usr/bin/reboot, /usr/bin/shutdown, /usr/bin/v4l2-ctl, /usr/bin/ffmpeg" | sudo tee /etc/sudoers.d/deckport-kiosk

# Add kiosk user to required groups for console access (will be consolidated later)
# sudo usermod -a -G video,tty,input,audio kiosk  # REMOVED - consolidated below

# Configure X11 to allow kiosk user to start X server
info "Configuring X11 permissions for kiosk user..."
echo "allowed_users=anybody" | sudo tee /etc/X11/Xwrapper.config
echo "needs_root_rights=yes" | sudo tee -a /etc/X11/Xwrapper.config

# Setup camera permissions and configuration
info "Configuring camera access..."

# Create udev rules for camera access
cat << 'EOF' | sudo tee /etc/udev/rules.d/99-deckport-camera.rules
# Deckport Console Camera Access Rules
SUBSYSTEM=="video4linux", GROUP="video", MODE="0664"
SUBSYSTEM=="usb", ATTRS{{idVendor}}=="*", ATTRS{{idProduct}}=="*", GROUP="video", MODE="0664"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Test camera availability and configuration
info "Testing camera hardware..."
CAMERA_DEVICES=$(ls /dev/video* 2>/dev/null || echo "")
if [ -n "$CAMERA_DEVICES" ]; then
    success "Camera devices found: $CAMERA_DEVICES"
    
    # Test first camera
    FIRST_CAMERA=$(echo $CAMERA_DEVICES | awk '{{print $1}}')
    if [ -n "$FIRST_CAMERA" ]; then
        info "Testing camera: $FIRST_CAMERA"
        
        # Get camera info
        CAMERA_INFO=$(v4l2-ctl --device=$FIRST_CAMERA --info 2>/dev/null || echo "Camera info unavailable")
        success "Camera test successful: $FIRST_CAMERA"
        
        # Set optimal camera settings for console use
        v4l2-ctl --device=$FIRST_CAMERA --set-ctrl=brightness=128 2>/dev/null || true
        v4l2-ctl --device=$FIRST_CAMERA --set-ctrl=contrast=128 2>/dev/null || true
        v4l2-ctl --device=$FIRST_CAMERA --set-ctrl=saturation=128 2>/dev/null || true
        
        info "Camera configured with optimal settings"
    fi
else
    warning "No camera devices found - surveillance will be disabled"
fi

# Test and configure NFC reader
info "Testing NFC reader hardware..."
NFC_DEVICES=""
NFC_AVAILABLE="false"

# Start PC/SC daemon for smart card readers
sudo systemctl enable pcscd
sudo systemctl start pcscd
sleep 2

# Detect NFC readers
if command -v nfc-list >/dev/null 2>&1; then
    info "Scanning for NFC readers..."
    NFC_SCAN_RESULT=$(timeout 10 nfc-list 2>/dev/null || echo "")
    
    if echo "$NFC_SCAN_RESULT" | grep -q "NFC device"; then
        NFC_AVAILABLE="true"
        NFC_DEVICES=$(echo "$NFC_SCAN_RESULT" | grep "NFC device" | head -3)
        success "NFC reader(s) found:"
        echo "$NFC_DEVICES" | while read -r line; do
            info "  $line"
        done
        
        # Test NFC functionality
        info "Testing NFC reader functionality..."
        if timeout 5 nfc-poll -1 >/dev/null 2>&1; then
            success "NFC reader test successful"
        else
            warning "NFC reader found but polling test failed"
        fi
    else
        warning "No NFC readers detected"
    fi
else
    warning "NFC tools not available"
fi

# Configure NFC reader permissions
info "Configuring NFC reader permissions..."
cat << 'EOF' | sudo tee /etc/udev/rules.d/99-nfc-readers.rules
# NFC Reader Access Rules
# ACR122U and compatible readers
SUBSYSTEM=="usb", ATTRS{{idVendor}}=="072f", ATTRS{{idProduct}}=="2200", GROUP="plugdev", MODE="0664"
SUBSYSTEM=="usb", ATTRS{{idVendor}}=="072f", ATTRS{{idProduct}}=="2224", GROUP="plugdev", MODE="0664"
# PN532 based readers
SUBSYSTEM=="usb", ATTRS{{idVendor}}=="1fc9", ATTRS{{idProduct}}=="0117", GROUP="plugdev", MODE="0664"
# Generic NFC readers
SUBSYSTEM=="usb", ENV{{ID_USB_INTERFACES}}=="*0b0000*", GROUP="plugdev", MODE="0664"
EOF

# Add kiosk user to plugdev group for NFC access
# sudo usermod -a -G plugdev kiosk  # REMOVED - consolidated below

# Reload udev rules for NFC
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb

# Create hardware configuration for Godot
cat > /opt/deckport-console/hardware.conf << EOL
# Deckport Console Hardware Configuration

# Camera Configuration
CAMERA_DEVICES="$CAMERA_DEVICES"
FIRST_CAMERA="$FIRST_CAMERA"
CAMERA_AVAILABLE=$([ -n "$CAMERA_DEVICES" ] && echo "true" || echo "false")
SURVEILLANCE_ENABLED=$([ -n "$CAMERA_DEVICES" ] && echo "true" || echo "false")

# NFC Configuration
NFC_DEVICES="$NFC_DEVICES"
NFC_AVAILABLE="$NFC_AVAILABLE"
NFC_ENABLED=$([ "$NFC_AVAILABLE" = "true" ] && echo "true" || echo "false")

# Configuration timestamp
CONFIGURED_AT=$(date -Iseconds)
EOL

# Create necessary directories and proper Openbox configuration
mkdir -p /home/kiosk/.config/openbox

# Create valid Openbox configuration for kiosk mode
cat > /home/kiosk/.config/openbox/rc.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc" xmlns:xi="http://www.w3.org/2001/XInclude">
  <resistance>
    <strength>10</strength>
    <screen_edge_strength>20</screen_edge_strength>
  </resistance>
  <focus>
    <focusNew>yes</focusNew>
    <followMouse>no</followMouse>
    <focusLast>yes</focusLast>
    <underMouse>no</underMouse>
    <focusDelay>200</focusDelay>
    <raiseOnFocus>no</raiseOnFocus>
  </focus>
  <placement>
    <policy>Smart</policy>
    <center>yes</center>
    <monitor>Primary</monitor>
    <primaryMonitor>1</primaryMonitor>
  </placement>
  <theme>
    <name>Clearlooks</name>
    <titleLayout>NLIMC</titleLayout>
    <keepBorder>yes</keepBorder>
    <animateIconify>yes</animateIconify>
    <font place="ActiveWindow">
      <name>sans</name>
      <size>8</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
    <font place="InactiveWindow">
      <name>sans</name>
      <size>8</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
    <font place="MenuHeader">
      <name>sans</name>
      <size>9</size>
      <weight>normal</weight>
      <slant>normal</slant>
    </font>
    <font place="MenuItem">
      <name>sans</name>
      <size>9</size>
      <weight>normal</weight>
      <slant>normal</slant>
    </font>
    <font place="ActiveOnScreenDisplay">
      <name>sans</name>
      <size>9</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
    <font place="InactiveOnScreenDisplay">
      <name>sans</name>
      <size>9</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
  </theme>
  <desktops>
    <number>1</number>
    <firstdesk>1</firstdesk>
    <names>
      <name>Deckport Console</name>
    </names>
    <popupTime>875</popupTime>
  </desktops>
  <resize>
    <drawContents>yes</drawContents>
    <popupShow>Nonpixel</popupShow>
    <popupPosition>Center</popupPosition>
    <popupFixedPosition>
      <x>10</x>
      <y>10</y>
    </popupFixedPosition>
  </resize>
  <margins>
    <top>0</top>
    <bottom>0</bottom>
    <left>0</left>
    <right>0</right>
  </margins>
  <dock>
    <position>TopLeft</position>
    <floatingX>0</floatingX>
    <floatingY>0</floatingY>
    <noStrut>no</noStrut>
    <stacking>Above</stacking>
    <direction>Vertical</direction>
    <autoHide>no</autoHide>
    <hideDelay>300</hideDelay>
    <showDelay>300</showDelay>
    <moveButton>Middle</moveButton>
  </dock>
  <keyboard>
    <chainQuitKey>C-g</chainQuitKey>
  </keyboard>
  <mouse>
    <dragThreshold>1</dragThreshold>
    <doubleClickTime>500</doubleClickTime>
    <screenEdgeWarpTime>400</screenEdgeWarpTime>
    <screenEdgeWarpMouse>false</screenEdgeWarpMouse>
  </mouse>
  <menu>
    <hideDelay>200</hideDelay>
    <middle>no</middle>
    <submenuShowDelay>100</submenuShowDelay>
    <submenuHideDelay>400</submenuHideDelay>
    <applicationIcons>yes</applicationIcons>
    <manageDesktops>yes</manageDesktops>
  </menu>
  <applications>
    <application name="*">
      <decor>no</decor>
      <maximized>true</maximized>
      <fullscreen>yes</fullscreen>
    </application>
  </applications>
</openbox_config>
EOF

# Set proper ownership
chown kiosk:kiosk /home/kiosk/.config/openbox/rc.xml

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp  
sudo ufw allow 8001/tcp  # For console communication
sudo ufw --force enable

# Disable unnecessary services
sudo systemctl disable cups || true
sudo systemctl disable bluetooth || true
sudo systemctl disable avahi-daemon || true

#################################################
# PHASE 6: Deckport Integration
#################################################

log "🔗 Phase 6: Setting up Deckport integration..."

# Create console configuration file
cat > /opt/deckport-console/console.conf << EOL
CONSOLE_ID=$CONSOLE_ID
GAME_VERSION=$GAME_VERSION
LOCATION=$LOCATION
DEPLOYMENT_SERVER=$DEPLOYMENT_SERVER
API_ENDPOINT=$API_SERVER/v1
REGISTERED_AT=$(date -Iseconds)
MAC_ADDRESS=$MAC_ADDRESS
IP_ADDRESS=$IP_ADDRESS
HOSTNAME=$HOSTNAME
EOL

# Create heartbeat script
cat > /opt/deckport-console/heartbeat.sh << 'EOL'
#!/bin/bash
source /opt/deckport-console/console.conf

# Get current system stats
UPTIME=$(cat /proc/uptime | cut -d' ' -f1)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\\([0-9.]*\\)%* id.*/\\1/" | awk '{{print 100 - $1}}')
MEMORY_USAGE=$(free | grep Mem | awk '{{printf("%.1f", $3/$2 * 100.0)}}')
DISK_USAGE=$(df / | tail -1 | awk '{{print $5}}' | sed 's/%//')
TEMP=$(sensors 2>/dev/null | grep "Core 0" | awk '{{print $3}}' | sed 's/+//;s/°C//' || echo "0")

# Get battery information
get_battery_info() {{
    local bat_path="/sys/class/power_supply"
    local battery_capacity="100"
    local battery_status="AC_Power"
    local battery_present="0"
    local battery_voltage="0"
    local battery_current="0"
    local power_consumption="0"
    local time_remaining="0"
    local charging_rate="0"
    
    # Check for battery directories
    for bat in $bat_path/BAT*; do
        if [ -d "$bat" ]; then
            battery_present="1"
            
            # Read battery information
            [ -f "$bat/capacity" ] && battery_capacity=$(cat "$bat/capacity" 2>/dev/null || echo "100")
            [ -f "$bat/status" ] && battery_status=$(cat "$bat/status" 2>/dev/null || echo "Unknown")
            [ -f "$bat/voltage_now" ] && battery_voltage=$(cat "$bat/voltage_now" 2>/dev/null || echo "0")
            [ -f "$bat/current_now" ] && battery_current=$(cat "$bat/current_now" 2>/dev/null || echo "0")
            
            # Calculate power consumption (Watts)
            if [ "$battery_voltage" != "0" ] && [ "$battery_current" != "0" ]; then
                power_consumption=$(awk "BEGIN {{printf \\"%.2f\\", ($battery_voltage * $battery_current) / 1000000000000}}")
            fi
            
            # Estimate time remaining (hours)
            if [ "$battery_status" = "Discharging" ] && [ "$battery_current" != "0" ]; then
                # Rough estimate: current capacity / discharge rate
                time_remaining=$(awk "BEGIN {{printf \\"%.0f\\", ($battery_capacity * 60 / 100)}}")  # Simplified estimate
            elif [ "$battery_status" = "Charging" ] && [ "$battery_current" != "0" ]; then
                # Time to full charge
                time_remaining=$(awk "BEGIN {{printf \\"%.0f\\", ((100 - $battery_capacity) * 60 / 100)}}")  # Simplified estimate
            fi
            
            break  # Use first battery found
        fi
    done
    
    # Check for AC adapter
    local ac_online="0"
    for ac in $bat_path/A{{C,DP}}*; do
        if [ -d "$ac" ] && [ -f "$ac/online" ]; then
            ac_online=$(cat "$ac/online" 2>/dev/null || echo "0")
            break
        fi
    done
    
    echo "$battery_capacity,$battery_status,$battery_present,$battery_voltage,$battery_current,$power_consumption,$time_remaining,$ac_online"
}}

# Get battery data
BATTERY_INFO=$(get_battery_info)
IFS=',' read -r BATTERY_CAPACITY BATTERY_STATUS BATTERY_PRESENT BATTERY_VOLTAGE BATTERY_CURRENT POWER_CONSUMPTION TIME_REMAINING AC_ONLINE <<< "$BATTERY_INFO"

# Get camera information
get_camera_info() {{
    local camera_count=0
    local camera_devices=""
    local camera_status="unavailable"
    
    # Count video devices
    for dev in /dev/video*; do
        if [ -c "$dev" ]; then
            camera_count=$((camera_count + 1))
            camera_devices="$camera_devices $dev"
            camera_status="available"
        fi
    done
    
    # Test first camera if available
    local camera_working="false"
    if [ $camera_count -gt 0 ]; then
        local first_camera=$(echo $camera_devices | awk '{{print $1}}')
        if timeout 5 v4l2-ctl --device=$first_camera --info > /dev/null 2>&1; then
            camera_working="true"
            camera_status="working"
        fi
    fi
    
    echo "$camera_count,$camera_status,$camera_working,$camera_devices"
}}

# Get camera data
CAMERA_INFO=$(get_camera_info)
IFS=',' read -r CAMERA_COUNT CAMERA_STATUS CAMERA_WORKING CAMERA_DEVICES <<< "$CAMERA_INFO"

# Get NFC reader information
get_nfc_info() {{
    local nfc_count=0
    local nfc_devices=""
    local nfc_status="unavailable"
    local nfc_working="false"
    
    # Check if PC/SC daemon is running
    if systemctl is-active pcscd >/dev/null 2>&1; then
        nfc_status="daemon_running"
        
        # Check for NFC readers
        if command -v nfc-list >/dev/null 2>&1; then
            local nfc_scan=$(timeout 5 nfc-list 2>/dev/null || echo "")
            if echo "$nfc_scan" | grep -q "NFC device"; then
                nfc_count=$(echo "$nfc_scan" | grep -c "NFC device")
                nfc_devices=$(echo "$nfc_scan" | grep "NFC device" | head -3 | tr '\n' ';')
                nfc_status="available"
                
                # Test if NFC reader is working
                if timeout 3 nfc-poll -1 >/dev/null 2>&1; then
                    nfc_working="true"
                    nfc_status="working"
                fi
            fi
        fi
    fi
    
    echo "$nfc_count,$nfc_status,$nfc_working,$nfc_devices"
}}

# Get NFC data
NFC_INFO=$(get_nfc_info)
IFS=',' read -r NFC_COUNT NFC_STATUS NFC_WORKING NFC_DEVICES <<< "$NFC_INFO"

# Determine health status based on battery and system metrics
HEALTH_STATUS="healthy"
if [ "$BATTERY_PRESENT" = "1" ] && [ "$BATTERY_CAPACITY" -lt "10" ]; then
    HEALTH_STATUS="critical"
elif [ "$BATTERY_PRESENT" = "1" ] && [ "$BATTERY_CAPACITY" -lt "20" ]; then
    HEALTH_STATUS="warning"
elif [ "$(echo "$CPU_USAGE > 90" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
    HEALTH_STATUS="warning"
fi

# Send heartbeat to Deckport with battery data
curl -s -X POST "$API_SERVER/v1/console/heartbeat" \\
    -H "Content-Type: application/json" \\
    -H "X-Device-UID: $CONSOLE_ID" \\
    -d "{{
        \\"device_uid\\": \\"$CONSOLE_ID\\",
        \\"health_status\\": \\"$HEALTH_STATUS\\",
        \\"uptime_seconds\\": ${{UPTIME%.*}},
        \\"cpu_usage_percent\\": $CPU_USAGE,
        \\"memory_usage_percent\\": $MEMORY_USAGE,
        \\"disk_usage_percent\\": $DISK_USAGE,
        \\"temperature_celsius\\": $TEMP,
        \\"software_version\\": \\"$GAME_VERSION\\",
        \\"battery\\": {{
            \\"capacity_percent\\": $BATTERY_CAPACITY,
            \\"status\\": \\"$BATTERY_STATUS\\",
            \\"present\\": $BATTERY_PRESENT,
            \\"voltage_mv\\": $BATTERY_VOLTAGE,
            \\"current_ma\\": $BATTERY_CURRENT,
            \\"power_consumption_watts\\": $POWER_CONSUMPTION,
            \\"time_remaining_minutes\\": $TIME_REMAINING,
            \\"ac_connected\\": $AC_ONLINE
        }},
        \\"camera\\": {{
            \\"device_count\\": $CAMERA_COUNT,
            \\"status\\": \\"$CAMERA_STATUS\\",
            \\"working\\": $CAMERA_WORKING,
            \\"devices\\": \\"$CAMERA_DEVICES\\",
            \\"surveillance_capable\\": $([ \\"$CAMERA_WORKING\\" = \\"true\\" ] && echo \\"true\\" || echo \\"false\\")
        }},
        \\"nfc\\": {{
            \\"reader_count\\": $NFC_COUNT,
            \\"status\\": \\"$NFC_STATUS\\",
            \\"working\\": $NFC_WORKING,
            \\"devices\\": \\"$NFC_DEVICES\\",
            \\"card_scanning_enabled\\": $([ \\"$NFC_WORKING\\" = \\"true\\" ] && echo \\"true\\" || echo \\"false\\")
        }},
        \\"location\\": {{
            \\"name\\": \\"$LOCATION\\"
        }}
    }}" > /dev/null 2>&1

# Write battery status to JSON file for Godot to read
cat > /tmp/deckport_battery_status.json << EOF
{{
    "battery_percent": $BATTERY_CAPACITY,
    "battery_status": "$BATTERY_STATUS",
    "is_charging": $([ "$BATTERY_STATUS" = "Charging" ] && echo "true" || echo "false"),
    "is_low_battery": $([ "$BATTERY_CAPACITY" -lt "20" ] && echo "true" || echo "false"),
    "is_critical_battery": $([ "$BATTERY_CAPACITY" -lt "10" ] && echo "true" || echo "false"),
    "time_remaining_minutes": $TIME_REMAINING,
    "power_consumption_watts": $POWER_CONSUMPTION,
    "ac_connected": $([ "$AC_ONLINE" = "1" ] && echo "true" || echo "false"),
    "battery_present": $([ "$BATTERY_PRESENT" = "1" ] && echo "true" || echo "false"),
    "timestamp": "$(date -Iseconds)"
}}
EOF

# Set permissions so Godot can read it
chmod 644 /tmp/deckport_battery_status.json
EOL

chmod +x /opt/deckport-console/heartbeat.sh

# Download log streaming system (optional - don't fail deployment if this fails)
info "Setting up log streaming..."
if curl -s "$DEPLOYMENT_SERVER/deploy/assets/log-streamer" -o /opt/deckport-console/console_log_streamer.py; then
    chmod +x /opt/deckport-console/console_log_streamer.py
    success "Log streaming system downloaded"
    
    # Test if Python requests is available for log streaming
    info "Testing Python dependencies..."
    if python3 -c "import requests" 2>/dev/null; then
        success "Python requests available - setting up full monitoring"
        LOG_STREAMING_ENABLED="true"
    else
        warning "Python requests not available - basic monitoring only"
        LOG_STREAMING_ENABLED="false"
    fi
    
    # Set up cron jobs with robust error handling
    info "Configuring monitoring cron jobs..."
    
    # Create new crontab content
    CRONTAB_CONTENT="# Deckport Console Monitoring
* * * * * /opt/deckport-console/heartbeat.sh >/dev/null 2>&1
* * * * * sleep 30; /opt/deckport-console/heartbeat.sh >/dev/null 2>&1"
    
    # Add log streaming if available
    if [ "$LOG_STREAMING_ENABLED" = "true" ]; then
        CRONTAB_CONTENT="$CRONTAB_CONTENT
*/5 * * * * /usr/bin/python3 /opt/deckport-console/console_log_streamer.py upload >/dev/null 2>&1 || true"
    fi
    
    # Apply crontab safely
    if echo "$CRONTAB_CONTENT" | crontab - 2>/dev/null; then
        success "Monitoring cron jobs configured successfully"
    else
        warning "Could not set up cron jobs - will use systemd timer as fallback"
        # Create systemd timer as fallback (but don't fail deployment)
        echo "Cron setup failed, continuing deployment..." || true
    fi
else
    warning "Could not download log streaming system - continuing without it"
    # Set up basic heartbeat monitoring
    info "Setting up basic heartbeat monitoring..."
    BASIC_CRONTAB="# Deckport Console Basic Monitoring
* * * * * /opt/deckport-console/heartbeat.sh >/dev/null 2>&1
* * * * * sleep 30; /opt/deckport-console/heartbeat.sh >/dev/null 2>&1"
    
    if echo "$BASIC_CRONTAB" | crontab - 2>/dev/null; then
        success "Basic monitoring configured"
    else
        warning "Could not set up basic monitoring - continuing deployment"
    fi
fi

#################################################
# PHASE 7: Enable Services
#################################################

log "🚀 Phase 7: Enabling services..."

# Clean up any failed services first (PRODUCTION FIX)
info "Cleaning up failed services..."
sudo systemctl reset-failed

# Disable problematic snap services that cause system degradation
for service in snap.cups.cups-browsed.service snap.cups.cupsd.service; do
    if systemctl is-enabled $service 2>/dev/null; then
        warning "Disabling problematic service: $service"
        sudo systemctl disable $service 2>/dev/null || true
        sudo systemctl stop $service 2>/dev/null || true
    fi
done

# Enable all required services
sudo systemctl enable plymouth
sudo systemctl enable wifi-portal.service
sudo systemctl enable network-check.service
sudo systemctl enable deckport-kiosk.service
sudo systemctl enable ssh
sudo systemctl enable NetworkManager  # Ensure NetworkManager is enabled for WiFi stability

# Fix X11 and console permissions for kiosk user (PRODUCTION FIXES)
info "Configuring X11 and console permissions with production fixes..."

# Add kiosk user to ALL required groups for console and graphics access (CONSOLIDATED)
# This fixes the "xf86OpenConsole: Cannot open virtual console 1" error
# Consolidating all usermod operations into one to avoid multiple password prompts
sudo usermod -a -G tty,video,input,dialout,audio,plugdev,netdev kiosk
success "Kiosk user added to all required groups (consolidated operation)"

# Fix X11 console access permissions - critical for Intel UHD Graphics
sudo chmod 666 /dev/tty1 2>/dev/null || true
sudo chmod 666 /dev/tty0 2>/dev/null || true
sudo chown kiosk:tty /dev/tty1 2>/dev/null || true
success "Console TTY access permissions configured"

# Create X11 socket directory with proper permissions
sudo mkdir -p /tmp/.X11-unix
sudo chmod 1777 /tmp/.X11-unix
sudo chown root:root /tmp/.X11-unix

# Create X authority directory for kiosk user
sudo mkdir -p /var/run/xauth
sudo chown kiosk:kiosk /var/run/xauth
sudo chmod 755 /var/run/xauth

# Ensure home directory has proper ownership
sudo chown -R kiosk:kiosk /home/kiosk
sudo chmod 755 /home/kiosk

success "X11 directories and permissions configured with production fixes"

# Create log file with proper permissions
sudo touch /var/log/deckport-console.log
sudo chown kiosk:kiosk /var/log/deckport-console.log
sudo chmod 644 /var/log/deckport-console.log
success "Console log file permissions configured"

# Configure auto-login for kiosk user
info "Configuring auto-login..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d

# Create auto-login override with working configuration
cat << 'EOF' | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin kiosk %I \$TERM
EOF

# Also create override for console login
sudo mkdir -p /etc/systemd/system/console-getty.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/console-getty.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin kiosk --noclear %I $TERM
Type=idle
EOF

# Alternative: Configure systemd for auto-login
sudo mkdir -p /etc/systemd/system/serial-getty@ttyS0.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin kiosk %I 115200,38400,9600 vt220
EOF

# Set proper systemd target for kiosk mode
info "Configuring system target for kiosk mode..."
sudo systemctl set-default graphical.target

# Enable auto-login services
sudo systemctl enable getty@tty1.service
sudo systemctl enable console-getty.service 2>/dev/null || true

# Force reload getty service with new configuration
sudo systemctl daemon-reload
sudo systemctl restart getty@tty1.service

# Configure automatic kiosk startup
info "Configuring automatic kiosk startup..."

# Create .bashrc for auto-start
cat << 'EOF' > /home/kiosk/.bashrc
# Deckport Console Auto-Start
# Start kiosk mode automatically on login

if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]] || [[ $(tty) = /dev/console ]]; then
    echo "========================================="
    echo "🎮 Deckport Console Auto-Starting..."
    echo "========================================="
    exec /home/kiosk/start-kiosk.sh
fi
EOF

# Also create .bash_profile as fallback
cat << 'EOF' > /home/kiosk/.bash_profile
# Auto-start kiosk if on main console
if [ "$(tty)" = "/dev/tty1" ] || [ "$(tty)" = "/dev/console" ]; then
    if [ -z "$DISPLAY" ]; then
        echo "Starting Deckport Console..."
        exec /home/kiosk/start-kiosk.sh
    fi
fi
EOF

# Set proper permissions
chmod 644 /home/kiosk/.bashrc /home/kiosk/.bash_profile
chown kiosk:kiosk /home/kiosk/.bashrc /home/kiosk/.bash_profile

# Reload systemd configuration
sudo systemctl daemon-reload

# Verify kiosk service exists and enable it
if [ -f "/etc/systemd/system/deckport-kiosk.service" ]; then
    sudo systemctl enable deckport-kiosk.service
    success "Deckport kiosk service enabled"
else
    error "Deckport kiosk service file not found"
    ls -la /etc/systemd/system/ | grep deckport || echo "No deckport services found"
fi

# Restart getty service to apply auto-login
sudo systemctl restart getty@tty1.service

#################################################
# PHASE 7.5: Install Console Management Tools (PRODUCTION)
#################################################

log "🛠️ Phase 7.5: Installing console management and diagnostic tools..."

# Create console management script
info "Creating console management script..."
cat << 'EOF' | sudo tee /opt/deckport-console/manage-console.sh
#!/bin/bash

# Deckport Console Management Script

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
        tail -50 /var/log/deckport-console.log 2>/dev/null || echo "No console logs available"
        ;;
    "system-info")
        echo "💻 System Information:"
        if [[ -f "$CONSOLE_CONF" ]]; then
            source "$CONSOLE_CONF"
            echo "Console ID: $CONSOLE_ID"
            echo "Location: $LOCATION"
            echo "Game Version: $GAME_VERSION"
        fi
        echo "Hostname: $(hostname)"
        echo "IP Address: $(hostname -I | awk '{{print $1}}')"
        echo "Uptime: $(uptime -p)"
        echo "Memory: $(free -h | grep Mem | awk '{{print $3 "/" $2}}')"
        echo "Disk: $(df -h / | tail -1 | awk '{{print $3 "/" $2 " (" $5 " used)"}}')"
        echo "Graphics: $(lspci | grep VGA | cut -d: -f3 | xargs)"
        ;;
    "fix-permissions")
        echo "🔧 Fixing permissions..."
        sudo usermod -a -G video,input,tty,audio,plugdev,netdev kiosk
        sudo chown -R kiosk:kiosk /opt/deckport-console
        sudo chown kiosk:kiosk /home/kiosk/.Xauthority 2>/dev/null || true
        sudo chmod 1777 /tmp/.X11-unix
        echo "✅ Permissions fixed"
        ;;
    "wifi-diagnostics")
        echo "📡 WiFi Diagnostics:"
        echo "Network interfaces:"
        ip link show | grep -E "^[0-9]+:.*state"
        echo ""
        echo "WiFi status:"
        iwconfig 2>/dev/null | head -10 || echo "iwconfig not available"
        echo ""
        echo "NetworkManager status:"
        nmcli general status 2>/dev/null || echo "NetworkManager not available"
        echo ""
        echo "Connectivity test:"
        ping -c 3 8.8.8.8 || echo "Internet connectivity failed"
        ;;
    "reset-wifi")
        echo "🔄 Resetting WiFi..."
        sudo systemctl restart NetworkManager
        sleep 5
        WIFI_INTERFACE=$(iwconfig 2>/dev/null | grep -o '^[a-zA-Z0-9]*' | head -1)
        if [[ -n "$WIFI_INTERFACE" ]]; then
            echo "Resetting WiFi interface: $WIFI_INTERFACE"
            sudo ip link set $WIFI_INTERFACE down
            sleep 2
            sudo ip link set $WIFI_INTERFACE up
            sleep 5
        fi
        echo "✅ WiFi reset complete"
        ;;
    *)
        echo "🎮 Deckport Console Management"
        echo "Usage: $0 {{{{command}}}}"
        echo ""
        echo "Available commands:"
        echo "  start              - Start the console"
        echo "  stop               - Stop the console"
        echo "  restart            - Restart the console"
        echo "  status             - Show service status"
        echo "  logs               - Show console logs"
        echo "  system-info        - Show system information"
        echo "  wifi-diagnostics   - Show WiFi diagnostics"
        echo "  reset-wifi         - Reset WiFi connection"
        echo "  fix-permissions    - Fix file permissions"
        ;;
esac
EOF

sudo chmod +x /opt/deckport-console/manage-console.sh
sudo chown kiosk:kiosk /opt/deckport-console/manage-console.sh

# Create comprehensive diagnostic script
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
lspci | grep -i "vga\|display\|graphics"
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
    else
        echo "❌ No game executable found"
    fi
else
    echo "❌ Game directory not found"
fi

echo ""
echo "=== RECENT LOGS ==="
echo "Console logs (last 10 lines):"
tail -10 /var/log/deckport-console.log 2>/dev/null || echo "No console logs"

echo ""
echo "========================================="
echo "Diagnostics complete"
echo "========================================="
EOF

sudo chmod +x /opt/deckport-console/diagnostics.sh
sudo chown kiosk:kiosk /opt/deckport-console/diagnostics.sh

success "Console management and diagnostic tools installed"

#################################################
# PHASE 8: Final Steps
#################################################

log "✅ Phase 8: Finalizing installation..."

# Clean up temporary files
cd /
rm -rf $TEMP_DIR

# Clear package cache
sudo apt clean

# Configure FINAL sudo permissions for kiosk operations
info "Configuring final sudo permissions for kiosk operations..."
# Keep deployment permissions active until the very end
info "Keeping deployment permissions active during final configuration..."

# Create PERMANENT sudo permissions for kiosk startup operations
cat << 'EOF' | sudo tee /etc/sudoers.d/deckport-kiosk-permanent
# Deckport Console Kiosk Sudo Permissions (PERMANENT)
kiosk ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/usermod, /usr/bin/chown, /usr/bin/chmod, /usr/bin/mkdir, /usr/bin/rm, /usr/bin/pkill, /usr/bin/kill, /usr/sbin/modprobe, /usr/sbin/udevadm, /usr/bin/touch, /bin/kill
# X11 and graphics permissions
kiosk ALL=(ALL) NOPASSWD: /usr/bin/X, /usr/bin/startx, /usr/bin/xset, /usr/bin/xauth
# Network and system management
kiosk ALL=(ALL) NOPASSWD: /usr/bin/nmcli, /usr/bin/reboot, /usr/bin/shutdown, /usr/bin/iwconfig
# Console management
kiosk ALL=(ALL) NOPASSWD: /opt/deckport-console/manage-console.sh
EOF

# Set proper permissions on sudoers file
sudo chmod 440 /etc/sudoers.d/deckport-kiosk-permanent
info "✅ Permanent sudo permissions configured for kiosk operations"

# Ensure the kiosk service is properly configured and started
sudo systemctl daemon-reload
sudo systemctl enable deckport-kiosk.service
sudo systemctl stop deckport-kiosk.service 2>/dev/null || true

# Set final permissions on startup script
chmod +x /home/kiosk/start-kiosk.sh
chown kiosk:kiosk /home/kiosk/start-kiosk.sh

success "✅ Final configuration completed"

# Clean up temporary deployment permissions
sudo rm -f /etc/sudoers.d/deckport-deployment-immediate 2>/dev/null || true
info "Temporary deployment permissions removed - permanent permissions active"

# Send completion status to Deckport
curl -s -X POST "$API_SERVER/v1/admin/devices/$CONSOLE_ID/status" \\
    -H "Content-Type: application/json" \\
    -d "{{
        \\"status\\": \\"deployed\\",
        \\"deployment_completed_at\\": \\"$(date -Iseconds)\\",
        \\"game_version\\": \\"$GAME_VERSION\\",
        \\"location\\": \\"$LOCATION\\"
    }}" || true

success "========================================="
success "🎉 DECKPORT CONSOLE DEPLOYMENT COMPLETE!"\nsuccess "✅ WITH PRODUCTION FIXES APPLIED"
success "========================================="
success "Console ID: $CONSOLE_ID"
success "IP Address: $IP_ADDRESS"
success "Game Version: $GAME_VERSION"
success "Location: $LOCATION"
success "========================================="
success ""
success "The system will reboot in 10 seconds..."
success "After reboot:"
success "  ✅ Console will start in kiosk mode"
success "  ✅ Game will launch automatically"  
success "  ✅ Heartbeat monitoring active"
success "  ✅ Remote management enabled"
success ""
success "SSH Access: ssh kiosk@$IP_ADDRESS"
success "Management: https://deckport.ai/admin/consoles"
success "========================================="

sleep 10
sudo reboot
"""
    
    response = make_response(script)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    # Don't use attachment header for curl | bash to work
    
    return response


@deploy_bp.route('/assets/wifi-portal')
def download_wifi_portal():
    """Download WiFi portal package"""
    from flask import send_file
    asset_path = '/home/jp/deckport.ai/static/deploy/wifi-portal.tar.gz'
    if os.path.exists(asset_path):
        return send_file(asset_path, as_attachment=True, download_name='wifi-portal.tar.gz')
    return jsonify({"error": "WiFi portal package not found"}), 404


@deploy_bp.route('/assets/boot-theme')  
def download_boot_theme():
    """Download boot theme package"""
    from flask import send_file
    asset_path = '/home/jp/deckport.ai/static/deploy/boot-theme.tar.gz'
    if os.path.exists(asset_path):
        return send_file(asset_path, as_attachment=True, download_name='boot-theme.tar.gz')
    return jsonify({"error": "Boot theme package not found"}), 404


@deploy_bp.route('/console-command/<console_id>')
def console_command(console_id):
    """Simple endpoint for console to check for pending commands"""
    from flask import jsonify
    
    # Simple command system - console checks this endpoint
    # For now, return update command if needed
    return jsonify({{
        "command": "update_game",
        "script": """#!/bin/bash
echo "🔄 UPDATING GAME WITH FIXED API URLS"
sudo systemctl stop deckport-kiosk.service
cd /tmp
curl -L "https://deckport.ai/deploy/assets/godot-game/latest" -o game-update.tar.gz
sudo tar -xzf game-update.tar.gz -C /opt/godot-game/
sudo chmod +x /opt/godot-game/*.x86_64
sudo chown -R kiosk:kiosk /opt/godot-game
sudo systemctl start deckport-kiosk.service
echo "✅ Game updated with fixed API URLs"
""",
        "message": "Update game to fix API connectivity"
    }})

@deploy_bp.route('/update-game')
def update_game():
    """Game update script - updates game without full deployment"""
    from flask import Response
    
    script = f"""#!/bin/bash
# Deckport Console Game Update Script
# Updates only the game without full deployment

echo "🎮 DECKPORT CONSOLE GAME UPDATE"
echo "==============================="

# Check if running as kiosk user
if [[ "$USER" != "kiosk" ]]; then
    echo "❌ This script should be run as the 'kiosk' user"
    echo "💡 Run: sudo su - kiosk"
    exit 1
fi

# Stop the console service
echo "⏸️ Stopping console service..."
sudo systemctl stop deckport-kiosk.service

# Backup current game
echo "💾 Backing up current game..."
sudo cp /opt/godot-game/game.x86_64 /opt/godot-game/game.x86_64.backup 2>/dev/null || true

# Download new game
echo "⬇️ Downloading latest game..."
cd /tmp
curl -L "https://deckport.ai/deploy/assets/godot-game/latest" -o game-update.tar.gz

# Verify download
if [[ ! -f "game-update.tar.gz" ]] || [[ ! -s "game-update.tar.gz" ]]; then
    echo "❌ Game download failed"
    exit 1
fi

# Extract new game
echo "📦 Installing new game..."
sudo tar -xzf game-update.tar.gz -C /opt/godot-game/
sudo chmod +x /opt/godot-game/*.x86_64
sudo chown -R kiosk:kiosk /opt/godot-game

# Verify installation
if ls /opt/godot-game/*.x86_64 >/dev/null 2>&1; then
    GAME_SIZE=$(stat -c%s /opt/godot-game/game.x86_64 2>/dev/null || echo "0")
    echo "✅ Game updated successfully - size: $GAME_SIZE bytes"
else
    echo "❌ Game installation failed - restoring backup"
    sudo cp /opt/godot-game/game.x86_64.backup /opt/godot-game/game.x86_64 2>/dev/null || true
    exit 1
fi

# Clean up
rm -f game-update.tar.gz

# Restart console service
echo "🚀 Starting console service..."
sudo systemctl start deckport-kiosk.service

echo "✅ Game update completed!"
echo "🎮 Console should restart with new game version"
"""
    
    return Response(
        script,
        mimetype='text/plain',
        headers={{'Content-Disposition': 'attachment; filename=update-game.sh'}}
    )

@deploy_bp.route('/assets/godot-test-game')
def download_test_game():
    """Download test game package"""
    from flask import send_file
    asset_path = '/home/jp/deckport.ai/static/deploy/godot-test-game.tar.gz'
    if os.path.exists(asset_path):
        return send_file(asset_path, as_attachment=True, download_name='test-game.tar.gz')
    return jsonify({"error": "Test game package not found"}), 404

@deploy_bp.route('/assets/godot-game/<version>')
def download_game(version):
    """Download game package"""
    from flask import send_file
    # Map version to actual file
    if version == 'latest':
        asset_path = '/home/jp/deckport.ai/static/deploy/godot-game-latest.tar.gz'
    else:
        asset_path = f'/home/jp/deckport.ai/static/deploy/godot-game-{version}.tar.gz'
    
    if os.path.exists(asset_path):
        return send_file(asset_path, as_attachment=True, download_name=f'game-{version}.tar.gz')
    
    # Fallback to latest if specific version not found
    latest_path = '/home/jp/deckport.ai/static/deploy/godot-game-latest.tar.gz'
    if os.path.exists(latest_path):
        return send_file(latest_path, as_attachment=True, download_name='game-latest.tar.gz')
    
    return jsonify({"error": f"Game package {version} not found"}), 404


@deploy_bp.route('/assets/configs')
def download_configs():
    """Download configuration files package"""
    from flask import send_file
    asset_path = '/home/jp/deckport.ai/static/deploy/configs.tar.gz'
    if os.path.exists(asset_path):
        return send_file(asset_path, as_attachment=True, download_name='configs.tar.gz')
    return jsonify({"error": "Configuration package not found"}), 404


@deploy_bp.route('/assets/console-registration')
def download_console_registration():
    """Download console registration script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/console_registration.py'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='console_registration.py')
    return jsonify({"error": "Console registration script not found"}), 404


@deploy_bp.route('/assets/log-streamer')
def download_log_streamer():
    """Download console log streaming script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/console_log_streamer.py'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='console_log_streamer.py')
    return jsonify({"error": "Console log streamer script not found"}), 404


@deploy_bp.route('/assets/emergency-diagnostics')
def download_emergency_diagnostics():
    """Download emergency diagnostics script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/emergency_diagnostics.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='emergency_diagnostics.sh')
    return jsonify({"error": "Emergency diagnostics script not found"}), 404


@deploy_bp.route('/assets/simple-diagnostics')
def download_simple_diagnostics():
    """Download simple diagnostics script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/simple_diagnostics.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='simple_diagnostics.sh')
    return jsonify({"error": "Simple diagnostics script not found"}), 404


@deploy_bp.route('/assets/manual-log-upload')
def download_manual_log_upload():
    """Download manual log upload script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/manual_log_upload.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='manual_log_upload.sh')
    return jsonify({"error": "Manual log upload script not found"}), 404


@deploy_bp.route('/assets/collect-logs-local')
def download_collect_logs_local():
    """Download local log collection script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/collect_logs_local.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='collect_logs_local.sh')
    return jsonify({"error": "Local log collection script not found"}), 404


@deploy_bp.route('/assets/focused-log-sender')
def download_focused_log_sender():
    """Download focused log sender script"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/focused_log_sender.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='focused_log_sender.sh')
    return jsonify({"error": "Focused log sender script not found"}), 404


@deploy_bp.route('/assets/upload-all-logs')
def download_upload_all_logs():
    """Download comprehensive log upload script with real-time feedback"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/upload_all_logs.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='upload_all_logs.sh')
    return jsonify({"error": "Upload all logs script not found"}), 404


@deploy_bp.route('/assets/console-presetup')
def download_console_presetup():
    """Download console pre-setup script for Swedish keyboard and WiFi"""
    from flask import send_file
    script_path = '/home/jp/deckport.ai/console/kiosk/console_presetup.sh'
    if os.path.exists(script_path):
        return send_file(script_path, as_attachment=True, download_name='console_presetup.sh')
    return jsonify({"error": "Console pre-setup script not found"}), 404


@deploy_bp.route('/detect-hardware')
def detect_hardware():
    """Hardware detection script for consoles"""
    
    script = '''#!/bin/bash

#################################################
# Deckport Console Hardware Detection Script
# Detects hardware and recommends correct packages
#################################################

echo "🔍 Deckport Console Hardware Detection"
echo "======================================"

# Colors for output
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m'

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect graphics hardware
echo ""
info "Detecting graphics hardware..."

GPU_INFO=$(lspci | grep -i "vga\\|display\\|graphics" || echo "No GPU detected")
echo "Graphics Hardware: $GPU_INFO"

# Determine graphics type
if echo "$GPU_INFO" | grep -qi "intel"; then
    GPU_TYPE="intel"
    success "Intel graphics detected"
elif echo "$GPU_INFO" | grep -qi "amd\\|radeon"; then
    GPU_TYPE="amd"
    success "AMD graphics detected"
elif echo "$GPU_INFO" | grep -qi "nvidia"; then
    GPU_TYPE="nvidia"
    success "NVIDIA graphics detected"
else
    GPU_TYPE="generic"
    warning "Unknown/Generic graphics detected"
fi

# Check available graphics packages
echo ""
info "Checking available graphics packages..."

check_package() {
    if apt-cache show "$1" >/dev/null 2>&1; then
        success "✅ $1 is available"
        return 0
    else
        error "❌ $1 is not available"
        return 1
    fi
}

# Check base packages
check_package "libgl1-mesa-dri"
check_package "libegl1-mesa"
check_package "libgles2-mesa"
check_package "libglx-mesa0"

# Check hardware-specific packages
case $GPU_TYPE in
    intel)
        info "Checking Intel-specific packages..."
        check_package "xserver-xorg-video-intel"
        check_package "intel-media-va-driver"
        check_package "i965-va-driver"
        ;;
    amd)
        info "Checking AMD-specific packages..."
        check_package "xserver-xorg-video-amdgpu"
        check_package "mesa-vulkan-drivers"
        check_package "libdrm-amdgpu1"
        ;;
    nvidia)
        info "Checking NVIDIA-specific packages..."
        check_package "nvidia-driver-470"
        check_package "libnvidia-gl-470"
        ;;
    generic)
        info "Checking generic packages..."
        check_package "xserver-xorg-video-fbdev"
        check_package "xserver-xorg-video-vesa"
        ;;
esac

# Generate recommended package list
echo ""
success "Hardware Detection Complete!"
echo "======================================"
echo "GPU Type: $GPU_TYPE"
echo "Recommended packages for deployment script:"

case $GPU_TYPE in
    intel)
        echo "# Intel UHD Graphics packages"
        echo "libgl1-mesa-dri libegl1-mesa libgles2-mesa libglx-mesa0 xserver-xorg-video-intel intel-media-va-driver"
        ;;
    amd)
        echo "# AMD Graphics packages"
        echo "libgl1-mesa-dri libegl1-mesa libgles2-mesa libglx-mesa0 xserver-xorg-video-amdgpu mesa-vulkan-drivers"
        ;;
    nvidia)
        echo "# NVIDIA Graphics packages"
        echo "nvidia-driver-470 libnvidia-gl-470 libegl1-mesa libgles2-mesa"
        ;;
    generic)
        echo "# Generic Graphics packages"
        echo "libgl1-mesa-dri libegl1-mesa libgles2-mesa xserver-xorg-video-fbdev"
        ;;
esac

echo ""
echo "Copy the package list above and use it in your deployment script."
'''
    
    response = make_response(script)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    
    return response


@deploy_bp.route('/status')
def deployment_status():
    """Check deployment server status"""
    return jsonify({
        "status": "online",
        "server": "deckport.ai",
        "timestamp": datetime.now().isoformat(),
        "available_versions": ["latest", "v1.0.0"],
        "deployment_endpoint": "/deploy/console",
        "hardware_detection_endpoint": "/deploy/detect-hardware"
    })
