# 🎮 Deckport Console Deployment Guide

**Version**: 1.0 Production  
**Date**: December 2024  
**Status**: ✅ **PRODUCTION READY**

---

## 📋 **Overview**

This guide covers the complete **automated console deployment system** for Deckport gaming consoles. The system transforms a fresh Ubuntu Server installation into a fully functional gaming kiosk with a single command.

### 🎯 **Deployment Goal**
```bash
Ubuntu Server + WiFi → curl command → Full Deckport Console
```

---

## 🏗️ **System Architecture**

### **Service Structure**
```
deckport.ai (Main Server)
├── frontend.service (port 8001) - Admin panel, deployment endpoints
├── api.service (port 8002) - API endpoints, console registration
├── nginx - SSL termination and routing
└── PostgreSQL - Database with console management
```

### **Domain Routing**
- **`deckport.ai`** → Frontend (admin panel, deployment)
- **`api.deckport.ai`** → API service (console registration, heartbeat)
- **`deckport.ai/v1/*`** → API service (alternative routing)

---

## 🎯 **One-Command Deployment**

### **Basic Deployment**
```bash
curl -sSL https://deckport.ai/deploy/console | bash
```

### **Custom Deployment**
```bash
curl -sSL "https://deckport.ai/deploy/console?id=lobby-console-01&location=Main%20Lobby&version=latest" | bash
```

### **Parameters**
- **`id`**: Custom console ID (default: auto-generated)
- **`location`**: Physical location name
- **`version`**: Game version to install (default: latest)

---

## 📦 **Deployment Components**

### **1. Core System Packages**
```bash
# Essential packages installed automatically
curl wget git python3-flask python3-requests openssh-server
network-manager jq bc openssl

# X11 and graphics (auto-detected based on hardware)
xorg xinit openbox unclutter
libgl1-mesa-dri libegl-mesa0 libgles2 xserver-xorg-video-intel

# Multimedia and camera
v4l-utils alsa-utils pulseaudio ffmpeg gstreamer1.0-*
cheese guvcview uvcdynctrl

# Hardware monitoring
acpi powertop upower lm-sensors
```

### **2. Deployment Assets**
```
https://deckport.ai/deploy/assets/
├── wifi-portal.tar.gz      - WiFi configuration interface
├── boot-theme.tar.gz       - Plymouth boot theme (black background)
├── godot-game-latest.tar.gz - Exported Deckport game (63.7 MB)
├── configs.tar.gz          - System configuration files
└── console-registration.py - Production registration system
```

### **3. System Configuration**
- **Auto-login**: Automatic kiosk user login
- **X11 setup**: Graphics and display configuration
- **GRUB**: Silent boot with black background
- **Services**: Systemd services for kiosk mode
- **Security**: Firewall, permissions, user groups

---

## 🔄 **Deployment Process**

### **Phase 1: System Preparation**
1. **Update packages** and repositories
2. **Install core packages** in logical groups
3. **Auto-detect hardware** (Intel/AMD/NVIDIA graphics)
4. **Install hardware-specific drivers**
5. **Remove unnecessary packages** (snapd, cloud-init)

### **Phase 2: Console Registration**
1. **Generate RSA key pair** (2048-bit) for authentication
2. **Gather system information** (MAC, IP, CPU, memory)
3. **Register with Deckport API** (`api.deckport.ai`)
4. **Create console configuration** file
5. **Handle registration failures** gracefully

### **Phase 3: Download Components**
1. **WiFi Portal**: Branded network configuration interface
2. **Boot Theme**: Plymouth theme with Deckport branding
3. **Godot Game**: Your exported console game (actual game, not placeholder)
4. **System Configs**: Services, scripts, X11, GRUB configurations

### **Phase 4: Install Components**
1. **Extract and install** WiFi portal to `/opt/wifi-portal`
2. **Install Plymouth theme** to system themes directory
3. **Install Godot game** to `/opt/godot-game`
4. **Install systemd services** and configuration files

### **Phase 5: System Configuration**
1. **Configure X11** for kiosk mode (disable TTY switching)
2. **Configure GRUB** for silent boot
3. **Setup camera permissions** and udev rules
4. **Configure user groups** (add kiosk to video group)
5. **Setup firewall** rules

### **Phase 6: Deckport Integration**
1. **Create console configuration** with API endpoints
2. **Setup heartbeat monitoring** (every 30 seconds)
3. **Configure battery monitoring** system
4. **Setup camera surveillance** capabilities
5. **Create management scripts**

### **Phase 7: Enable Services**
1. **Enable systemd services**:
   - `deckport-kiosk.service` - Main game kiosk
   - `wifi-portal.service` - Network configuration
   - `network-check.service` - Connectivity monitoring
2. **Configure auto-login** for kiosk user
3. **Setup automatic kiosk startup**

### **Phase 8: Final Steps**
1. **Clean up** temporary files
2. **Send completion status** to Deckport API
3. **Display success message** with console information
4. **Automatic reboot** into kiosk mode

---

## 🎮 **Console Features After Deployment**

### **🔋 Battery Management**
- **Real-time monitoring**: Capacity, charging status, time remaining
- **Low battery alerts**: 20% warning, 10% critical
- **Power consumption tracking**: Watts usage monitoring
- **AC adapter detection**: Automatic power source detection
- **Godot integration**: Battery data available to game via JSON file

### **📹 Camera Surveillance**
- **Hardware detection**: Automatic camera discovery and testing
- **Admin control**: Start/stop surveillance from admin panel
- **Live streaming**: Real-time video monitoring with recording
- **Security integration**: Audit logs for all surveillance activities
- **Camera testing**: Verify camera functionality remotely

### **📊 Health Monitoring**
- **System metrics**: CPU, memory, disk, temperature
- **Network monitoring**: Latency and connectivity
- **Heartbeat system**: 30-second status updates to server
- **Health alerts**: Automatic warnings for critical issues
- **Performance tracking**: Historical data collection

### **🗺️ Location Tracking**
- **GPS coordinates**: Latitude/longitude support
- **Address information**: Human-readable location names
- **Location history**: Track console movements
- **Multiple sources**: Manual, GPS, IP-based location

### **🔄 Remote Management**
- **Game updates**: Remote game version deployment
- **System updates**: Software, firmware, hardware version tracking
- **Remote commands**: Restart, reboot, view logs
- **Configuration management**: Update settings remotely
- **Fleet operations**: Batch updates across multiple consoles

---

## 🖥️ **Server-Side Components**

### **1. Deployment Server**
```python
# Frontend Flask app (port 8001)
/deploy/console              - Main deployment script
/deploy/assets/*             - Downloadable components
/deploy/detect-hardware      - Hardware detection script
/deploy/status              - Deployment server status

# Admin panel integration
/admin/consoles             - Console fleet management
/admin/surveillance         - Camera control dashboard
```

### **2. API Service**
```python
# API Flask app (port 8002)
/v1/auth/device/register    - Console registration
/v1/console/heartbeat       - Health monitoring
/v1/admin/devices/*         - Console management APIs
/health                     - Service health check
```

### **3. Database Integration**
```sql
-- Console management tables
consoles                    - Main console registry
console_login_tokens        - QR login system
audit_logs                  - Activity and security logs

-- Enhanced features (via migration)
console_location_history    - Location tracking
console_version_history     - Version management
product_categories          - Shop category system
```

---

## 🔧 **Development Workflow**

### **1. Game Development**
```bash
# Edit Godot project
cd /home/jp/deckport.ai/console

# Build and package automatically
python3 console/build_and_deploy.py

# Deploy to consoles
curl -sSL https://deckport.ai/deploy/console | bash
```

### **2. Update Deployment Assets**
```bash
# Rebuild deployment packages
cd /home/jp/deckport.ai/console/kiosk
python3 build_deployment_assets.py

# Restart frontend service
sudo systemctl restart frontend.service
```

### **3. Fleet Management**
```bash
# View all consoles
https://deckport.ai/admin/consoles

# Update specific console
POST /v1/admin/devices/{id}/update-game
{"version": "v1.2.3"}

# Monitor console health
GET /v1/admin/devices/{id}/health
```

---

## 🚨 **Troubleshooting**

### **Common Issues & Solutions**

#### **Problem: Package Installation Fails**
```bash
# Graphics packages not found
→ Script auto-detects hardware and installs correct drivers
→ Falls back to software rendering if hardware packages unavailable

# Python environment issues  
→ Uses system packages (python3-flask) instead of pip
→ Handles externally-managed-environment errors
```

#### **Problem: Console Registration Fails**
```bash
# API service not responding
→ Deployment continues with basic configuration
→ Console can be registered later via admin panel

# Invalid RSA keys
→ Script generates proper 2048-bit RSA key pairs
→ Validates key format before registration
```

#### **Problem: Auto-Login Not Working**
```bash
# Console boots to login prompt
→ Check: sudo systemctl status getty@tty1.service
→ Fix: Reconfigure auto-login via deployment script

# Kiosk mode doesn't start
→ Check: /home/kiosk/.bashrc for auto-start script
→ Fix: Redeploy with enhanced auto-login configuration
```

#### **Problem: Game Doesn't Launch**
```bash
# Game executable not found
→ Check: ls -la /opt/godot-game/
→ Fix: Rebuild game package with python3 console/build_and_deploy.py

# X11 display issues
→ Check: DISPLAY=:0 xset q
→ Fix: X server startup in start-kiosk.sh script
```

### **Emergency Console Access**
```bash
# If console gets stuck in kiosk mode
1. Press Ctrl+Alt+F2 (switch to TTY2)
2. Login as kiosk user
3. sudo systemctl stop deckport-kiosk.service
4. sudo systemctl set-default multi-user.target
5. sudo reboot
```

---

## 📊 **Monitoring & Management**

### **Admin Panel Features**
- **Fleet Overview**: https://deckport.ai/admin/consoles
- **Console Details**: Location, battery, camera, health status
- **Real-time Monitoring**: Live health metrics and alerts
- **Remote Control**: Game updates, surveillance, system commands
- **Deployment History**: Track all console deployments

### **Console Heartbeat Data**
```json
{
  "device_uid": "console-123456",
  "health_status": "healthy",
  "uptime_seconds": 86400,
  "cpu_usage_percent": 25.5,
  "memory_usage_percent": 45.2,
  "disk_usage_percent": 30.1,
  "temperature_celsius": 45.0,
  "battery": {
    "capacity_percent": 85,
    "status": "Discharging",
    "time_remaining_minutes": 180,
    "power_consumption_watts": 15.5
  },
  "camera": {
    "device_count": 1,
    "status": "working",
    "surveillance_capable": true
  },
  "location": {
    "name": "Main Lobby"
  }
}
```

---

## 🔐 **Security Features**

### **Console Authentication**
- **RSA key pairs**: 2048-bit keys for secure authentication
- **Device registration**: Consoles must be approved by admin
- **JWT tokens**: Secure API communication
- **Audit logging**: All console activities logged

### **Network Security**
- **Firewall configuration**: Only necessary ports open
- **SSH access**: Secure remote management
- **SSL/TLS**: All communication encrypted
- **Permission controls**: Minimal privilege principle

### **Surveillance Security**
- **Admin authorization**: Only authorized admins can start surveillance
- **Audit trails**: All surveillance activities logged
- **Recording management**: Automatic recording with retention policies
- **Privacy controls**: Clear indicators when surveillance is active

---

## 🚀 **Production Deployment Checklist**

### **Pre-Deployment**
- [ ] **Server Setup**: Ensure frontend.service and api.service running
- [ ] **Game Build**: Run `python3 console/build_and_deploy.py`
- [ ] **Asset Check**: Verify all deployment assets built successfully
- [ ] **Network**: Confirm api.deckport.ai is accessible

### **Console Preparation**
- [ ] **Ubuntu Server**: Install Ubuntu Server 22.04 LTS
- [ ] **User Account**: Create `kiosk` user with sudo privileges
- [ ] **SSH Access**: Enable SSH for remote management
- [ ] **Network**: Connect to WiFi or ethernet

### **Deployment Execution**
- [ ] **Run Command**: `curl -sSL https://deckport.ai/deploy/console | bash`
- [ ] **Monitor Progress**: Watch deployment phases complete
- [ ] **Verify Registration**: Console appears in admin panel
- [ ] **Test Auto-Boot**: Console reboots into kiosk mode

### **Post-Deployment Verification**
- [ ] **Game Launch**: Deckport game starts automatically
- [ ] **Admin Panel**: Console visible at https://deckport.ai/admin/consoles
- [ ] **Heartbeat**: Real-time monitoring data appearing
- [ ] **Remote Control**: Test game update, surveillance, location update

---

## 🎛️ **Administrative Operations**

### **Fleet Management**
```bash
# View all consoles
https://deckport.ai/admin/consoles

# Individual console management
https://deckport.ai/admin/consoles/{console_id}

# Surveillance dashboard
https://deckport.ai/admin/surveillance
```

### **Console Operations**
```bash
# Update game version
POST /v1/admin/devices/{id}/update-game
{"version": "v1.2.3", "force": false}

# Update location
PUT /v1/admin/devices/{id}/location
{"location_name": "Arcade Floor 2", "latitude": 40.7128, "longitude": -74.0060}

# Start surveillance
POST /v1/admin/devices/{id}/camera/start-surveillance
{"reason": "Security check", "enable_audio": true}

# Get health history
GET /v1/admin/devices/{id}/health
```

### **SSH Management**
```bash
# Connect to console
ssh kiosk@[console-ip]

# Console management commands
/opt/deckport-console/manage-console.sh {command}

# Available commands:
restart-game        - Restart the Deckport game
update-game {ver}   - Update to specific game version
view-logs          - View console and game logs
reset-wifi         - Reset WiFi configuration
system-info        - Show console system information
send-heartbeat     - Send immediate heartbeat to server
```

---

## 🔧 **Component Details**

### **WiFi Portal**
- **Purpose**: Network configuration for consoles without ethernet
- **Technology**: Flask web app with responsive UI
- **Features**: Network scanning, password input, connection testing
- **Branding**: Deckport-styled interface with gradients
- **Location**: `/opt/wifi-portal/` on deployed consoles

### **Boot Theme**
- **Purpose**: Professional boot appearance with Deckport branding
- **Technology**: Plymouth theme with custom script
- **Features**: Black background, logo display, loading animation
- **Location**: `/usr/share/plymouth/themes/deckport-console/`

### **Godot Game Package**
- **Purpose**: The actual Deckport console game
- **Technology**: Exported Godot 4.2+ Linux executable
- **Features**: Full game with all assets embedded
- **Size**: ~63 MB executable, ~25 MB compressed
- **Location**: `/opt/godot-game/` on deployed consoles

### **System Configurations**
```
configs/
├── systemd/
│   ├── deckport-kiosk.service     - Main kiosk service
│   ├── wifi-portal.service        - WiFi configuration service
│   └── network-check.service      - Network connectivity check
├── scripts/
│   ├── start-kiosk.sh            - Kiosk startup script
│   └── manage-console.sh          - Console management commands
├── x11/
│   └── xorg.conf                  - X11 configuration (disable TTY switching)
└── grub/
    └── grub                       - GRUB configuration (silent boot)
```

---

## 📱 **Console Monitoring**

### **Real-Time Data**
Consoles send heartbeat every 30 seconds with:
- **System Health**: CPU, memory, disk usage, temperature
- **Battery Status**: Charge level, charging state, time remaining
- **Camera Status**: Available cameras, surveillance capability
- **Network Status**: Connectivity, latency
- **Game Status**: Version, uptime, performance

### **Admin Dashboard**
- **Fleet Overview**: All consoles with status indicators
- **Individual Management**: Detailed console control interface
- **Health Monitoring**: Real-time metrics and historical data
- **Alert System**: Notifications for critical issues
- **Batch Operations**: Update multiple consoles simultaneously

---

## 🔄 **Update System**

### **Game Updates**
```bash
# Server-side: Build new game version
python3 console/build_and_deploy.py

# Admin panel: Deploy to consoles
1. Go to console detail page
2. Select target version
3. Click "Update Game"
4. Console downloads and installs automatically

# Console receives update via heartbeat
1. Server responds with update_available: true
2. Console downloads new game package
3. Game restarts with new version
4. Console reports success back to server
```

### **System Updates**
- **Software versions**: Track and update console software
- **Configuration updates**: Push new settings to consoles
- **Security patches**: Deploy security updates fleet-wide
- **Feature rollouts**: Gradual deployment of new features

---

## 🎯 **Deployment Examples**

### **Single Console Deployment**
```bash
# Basic deployment
curl -sSL https://deckport.ai/deploy/console | bash

# Custom console for specific location
curl -sSL "https://deckport.ai/deploy/console?id=arcade-main-01&location=Main%20Arcade%20Floor" | bash
```

### **Fleet Deployment**
```bash
# Deploy multiple consoles with different IDs
for i in {01..10}; do
    ssh kiosk@console-${i} "curl -sSL 'https://deckport.ai/deploy/console?id=lobby-console-${i}&location=Lobby%20Section%20${i}' | bash"
done
```

### **Development Console**
```bash
# Deploy with development version
curl -sSL "https://deckport.ai/deploy/console?id=dev-console&location=Development%20Lab&version=dev" | bash
```

---

## 📋 **Prerequisites**

### **Server Requirements**
- **Ubuntu Server 22.04 LTS** (fresh installation)
- **Network connectivity** (WiFi or ethernet)
- **User account**: `kiosk` user with sudo privileges
- **SSH access**: For remote management (optional)
- **Hardware**: Intel/AMD/NVIDIA graphics support

### **Server Infrastructure**
- **Deckport server**: Running frontend.service and api.service
- **Domain access**: deckport.ai and api.deckport.ai
- **SSL certificates**: Valid certificates for HTTPS
- **Database**: PostgreSQL with console management tables

---

## 🎉 **Success Indicators**

### **Deployment Success**
- ✅ **Console registration**: Appears in admin panel
- ✅ **Auto-reboot**: Console reboots automatically after deployment
- ✅ **Kiosk mode**: Boots directly to game without login prompt
- ✅ **Game launch**: Deckport game starts in fullscreen
- ✅ **Heartbeat**: Real-time data appears in admin panel

### **Feature Verification**
- ✅ **Battery monitoring**: Battery data visible in admin panel
- ✅ **Camera control**: Can start surveillance from admin
- ✅ **Location tracking**: Console location shown correctly
- ✅ **Remote updates**: Can update game version remotely
- ✅ **Health monitoring**: System metrics updating in real-time

---

## 🔮 **Advanced Features**

### **Development Integration**
- **Real-time sync**: Update consoles during development
- **A/B testing**: Deploy different versions to different consoles
- **Performance monitoring**: Track game performance across fleet
- **Remote debugging**: Access console logs and diagnostics

### **Enterprise Features**
- **Batch operations**: Update entire fleet simultaneously
- **Staged rollouts**: Deploy to subset first, then full fleet
- **Geographic management**: Organize consoles by location
- **Analytics**: Usage patterns, performance metrics, uptime statistics

---

## 📞 **Support & Maintenance**

### **Log Files**
- **Console logs**: `/var/log/deckport-console.log`
- **System logs**: `journalctl -u deckport-kiosk.service`
- **API logs**: Server-side audit logs
- **Deployment logs**: Real-time during deployment

### **Common Commands**
```bash
# Console management
/opt/deckport-console/manage-console.sh system-info
/opt/deckport-console/manage-console.sh view-logs
/opt/deckport-console/manage-console.sh restart-game

# Service management
sudo systemctl status deckport-kiosk.service
sudo systemctl restart deckport-kiosk.service
sudo journalctl -u deckport-kiosk.service -f
```

---

## 🎯 **Quick Reference**

### **Deployment Command**
```bash
curl -sSL https://deckport.ai/deploy/console | bash
```

### **Admin Panel**
```
https://deckport.ai/admin/consoles
```

### **Emergency Access**
```bash
Ctrl+Alt+F2  # Switch to TTY2 for emergency access
```

### **Console Management**
```bash
ssh kiosk@[console-ip]
/opt/deckport-console/manage-console.sh
```

---

**🎮 Your production-ready console deployment system is complete and fully documented! 🚀**

*This guide covers the complete automated deployment system with all enhanced features including battery monitoring, camera surveillance, location tracking, and remote management capabilities.*
