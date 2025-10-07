# 🎮 Deckport Console Installation Guide

**Version**: 1.0 Production  
**Date**: August 2025  
**Target**: Ubuntu Server 22.04 LTS

---

## 📋 **Pre-Installation Checklist**

### **Hardware Requirements**
- [ ] **CPU**: x86_64 processor (Intel/AMD)
- [ ] **RAM**: Minimum 4GB, Recommended 8GB
- [ ] **Storage**: Minimum 32GB, Recommended 64GB SSD
- [ ] **Graphics**: Intel UHD, AMD, or NVIDIA graphics
- [ ] **Network**: WiFi or Ethernet connectivity
- [ ] **USB Ports**: For NFC reader and peripherals
- [ ] **Display**: HDMI/DisplayPort output

### **Peripherals (Optional)**
- [ ] **NFC Reader**: ACR122U or PN532-based USB reader
- [ ] **Camera**: USB webcam for surveillance
- [ ] **Audio**: Speakers or headphones
- [ ] **Input**: Keyboard and mouse for setup

---

## 🖥️ **Ubuntu Server Installation**

### **Step 1: Download Ubuntu Server**
- **Download**: Ubuntu Server 22.04 LTS from https://ubuntu.com/download/server
- **Create**: Bootable USB drive using Rufus, Etcher, or dd
- **Boot**: From USB drive

### **Step 2: Ubuntu Installation Process**

#### **Language & Keyboard**
```
Language: English (or preferred)
Keyboard Layout: Swedish (se) - IMPORTANT for console use
```

#### **Network Configuration**
```
Network: Configure WiFi or Ethernet
- WiFi: Select network and enter password
- Ethernet: Should auto-configure
- Test: Ensure internet connectivity works
```

#### **Storage Configuration**
```
Storage: Use entire disk (default)
- Filesystem: ext4 (default)
- Swap: Enable (recommended)
- Encryption: Optional (not required for console)
```

#### **Profile Setup**
```
Your name: Console Administrator
Your server's name: kiosk001 (or custom name)
Pick a username: kiosk
Choose a password: [secure password - remember this]
```

#### **SSH Setup**
```
Install OpenSSH server: YES (recommended for remote management)
Import SSH identity: No (skip)
```

#### **Featured Server Snaps**
```
Skip all snaps (we'll install what we need later)
```

### **Step 3: Complete Installation**
- **Remove USB drive** when prompted
- **Reboot** into fresh Ubuntu Server
- **Login** with kiosk user credentials

---

## ⚙️ **Post-Installation Setup**

### **Step 1: System Updates**
```bash
# Update package lists and system
sudo apt update
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget openssh-server

# Reboot if kernel was updated
sudo reboot
```

### **Step 2: WiFi Configuration (If Not Done During Installation)**
```bash
# Find your WiFi interface name
ip link show | grep -E "wl|wlan"
# Look for: wlp1s0, wlan0, wlx123456789abc, etc.

# Edit netplan configuration
sudo nano /etc/netplan/00-installer-config.yaml

# Add WiFi configuration (replace interface name and WiFi details):
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s3:  # Ethernet interface (if present)
      dhcp4: true
  wifis:
    wlp1s0:  # Your WiFi interface name here
      dhcp4: true
      access-points:
        "YourWiFiName":
          password: "YourWiFiPassword"

# Apply netplan configuration
sudo netplan apply

# Wait for connection (may take 10-30 seconds)
sleep 10
```

### **Step 3: Network Verification**
```bash
# Test internet connectivity
ping -c 3 8.8.8.8
ping -c 3 google.com

# Check IP configuration
ip addr show

# Verify DNS resolution
nslookup deckport.ai

# Check WiFi connection status
ip route show | grep default
```

### **Step 3: Swedish Keyboard Configuration**
```bash
# Set Swedish keyboard layout
sudo localectl set-keymap se
sudo localectl set-x11-keymap se

# Verify configuration
localectl status

# Test Swedish characters: å ä ö
```

### **Step 4: SSH Access (Optional)**
```bash
# Enable SSH service
sudo systemctl enable ssh
sudo systemctl start ssh

# Check SSH status
sudo systemctl status ssh

# Get IP address for remote access
hostname -I
```

---

## 🚀 **Console Deployment**

### **Step 1: Run Deployment Command**
```bash
# Basic deployment (auto-generated console ID)
curl -sSL https://deckport.ai/deploy/console | bash

# Custom deployment with specific ID and location
curl -sSL "https://deckport.ai/deploy/console?id=arcade-main-01&location=Main%20Arcade%20Floor" | bash
```

### **Step 2: Monitor Deployment Progress**

The deployment will show these phases:
```
Phase 1: System Preparation (5-10 minutes)
├── Package updates and installation
├── Graphics driver detection and setup
├── Hardware configuration (camera, NFC)
└── System cleanup

Phase 2: Console Registration (1-2 minutes)
├── System information gathering
├── Console registration with Deckport API
└── Configuration file creation

Phase 3: Component Download (2-5 minutes)
├── WiFi portal package
├── Boot theme package  
├── Godot game package
└── System configuration files

Phase 4: Component Installation (3-5 minutes)
├── WiFi portal setup
├── Plymouth boot theme
├── Godot game installation
└── System configurations

Phase 5: System Configuration (2-3 minutes)
├── X11 configuration for graphics
├── GRUB configuration for silent boot
├── User permissions and groups
└── Security settings

Phase 6: Deckport Integration (1-2 minutes)
├── Heartbeat monitoring setup
├── Battery monitoring configuration
├── Camera surveillance setup
└── NFC reader configuration

Phase 7: Service Configuration (1-2 minutes)
├── Systemd service installation
├── Auto-login configuration
├── Service enablement
└── Cron job setup

Phase 8: Final Steps (1 minute)
├── System cleanup
├── Configuration verification
├── Completion notification
└── Automatic reboot
```

### **Step 3: Deployment Completion**
```
Expected Output:
========================================
🎉 DECKPORT CONSOLE DEPLOYMENT COMPLETE!
========================================
Console ID: [your-console-id]
IP Address: [console-ip]
Game Version: latest
Location: [your-location]
========================================

The system will reboot in 10 seconds...
After reboot:
  ✅ Console will start in kiosk mode
  ✅ Game will launch automatically
  ✅ Heartbeat monitoring active
  ✅ Remote management enabled

SSH Access: ssh kiosk@[console-ip]
Management: https://deckport.ai/admin/consoles
========================================
```

---

## 🔧 **Troubleshooting Common Issues**

### **Issue 1: Deployment Stops at Package Installation**
```bash
# Symptoms: "Unable to locate package" errors
# Solution: Check internet connectivity and repository access

# Fix:
sudo apt update
sudo apt install -f  # Fix broken packages
curl -sSL https://deckport.ai/deploy/console | bash  # Retry deployment
```

### **Issue 2: Graphics Driver Issues**
```bash
# Symptoms: Black screen or X11 errors after reboot
# Solution: Check graphics hardware and drivers

# Diagnosis:
lspci | grep -i graphics  # Check graphics hardware
lsmod | grep i915         # Check Intel driver loaded
ls -la /dev/dri/          # Check graphics devices

# Fix: Run hardware detection
curl -sSL https://deckport.ai/deploy/detect-hardware | bash
```

### **Issue 3: Console Registration Failed**
```bash
# Symptoms: "Console registration failed" during deployment
# Solution: Check API connectivity

# Diagnosis:
curl -s https://api.deckport.ai/health  # Test API access
ping api.deckport.ai                   # Test DNS resolution

# Fix: Deployment continues without registration - can register later via admin panel
```

### **Issue 4: Console Prompts for Password**
```bash
# Symptoms: Login prompt instead of automatic kiosk mode
# Solution: Auto-login configuration issue

# Fix:
sudo systemctl status getty@tty1.service
sudo systemctl restart getty@tty1.service
sudo systemctl set-default graphical.target
sudo reboot
```

### **Issue 5: Game Doesn't Start**
```bash
# Symptoms: Black screen or X11 starts but no game
# Solution: Check game installation and X11 permissions

# Diagnosis:
ls -la /opt/godot-game/                    # Check game files
systemctl status deckport-kiosk.service   # Check kiosk service
journalctl -u deckport-kiosk.service      # Check service logs

# Fix:
sudo systemctl restart deckport-kiosk.service
```

---

## 🚨 **Emergency Recovery**

### **Get Console Access**
If console gets stuck in kiosk mode:
```bash
# Method 1: Kill X11 Session (Black Screen Overlay)
Ctrl + Alt + Backspace  # Kill X server and return to TTY

# Method 2: Switch TTY
Ctrl + Alt + F2  # Switch to TTY2
Ctrl + Alt + F3  # Try different TTYs (F1, F3, F4, F5, F6)

# Method 3: Magic SysRq Keys (Print Screen Key)
Alt + Print Screen + R  # Take keyboard control
Alt + Print Screen + K  # Kill all processes on current console
Alt + Print Screen + E  # Terminate all processes

# Method 4: SSH access
ssh kiosk@[console-ip]

# Method 5: Recovery mode
# During boot: Press Shift → Advanced Options → Recovery Mode
```

### **Black Screen Issues**

If console shows black screen on all TTYs:
```bash
# If black overlay covering TTY:
Ctrl + Alt + Backspace  # Kill X server overlay

# If complete display failure:
# 1. Hard reset: Hold power button 10 seconds
# 2. Boot to GRUB: Press Shift during boot
# 3. Add kernel parameter: nomodeset
# 4. Boot in safe graphics mode

# Display troubleshooting:
# - Try different HDMI/DisplayPort
# - Check monitor input source
# - Try different monitor if available
```

### **Disable Kiosk Mode**
```bash
# Stop kiosk service
sudo systemctl stop deckport-kiosk.service
sudo systemctl disable deckport-kiosk.service

# Remove auto-start scripts
rm -f /home/kiosk/.bashrc /home/kiosk/.bash_profile

# Set normal boot mode
sudo systemctl set-default multi-user.target

# Reboot to normal mode
sudo reboot
```

### **Reset Console**
```bash
# Complete reset (if needed)
sudo systemctl stop deckport-kiosk.service wifi-portal.service
sudo systemctl disable deckport-kiosk.service wifi-portal.service
sudo systemctl set-default multi-user.target
sudo rm -rf /opt/deckport-console /opt/wifi-portal /opt/godot-game
sudo reboot
```

---

## 🔍 **Diagnostic Tools**

### **Manual Log Collection**
```bash
# Collect system information for debugging
curl -sSL https://deckport.ai/deploy/assets/focused-log-sender | bash

# Simple diagnostics (local output)
curl -sSL https://deckport.ai/deploy/assets/simple-diagnostics | bash
```

### **Hardware Detection**
```bash
# Check hardware compatibility
curl -sSL https://deckport.ai/deploy/detect-hardware | bash
```

### **Service Status Check**
```bash
# Check all Deckport services
systemctl status deckport-kiosk.service
systemctl status wifi-portal.service
systemctl status network-check.service

# Check system logs
journalctl --since '10 minutes ago' --no-pager
```

---

## 📱 **Admin Panel Management**

### **After Successful Deployment**
1. **Login**: https://deckport.ai/admin/login
   - Email: `admin@deckport.ai`
   - Password: `admin123`

2. **Console Fleet**: Navigate to Console Management
3. **Find Console**: Look for your console in the list
4. **Monitor Status**: Real-time health monitoring
5. **Remote Control**: Game updates, surveillance, location management

### **Console Features in Admin Panel**
- ✅ **Real-time monitoring**: Battery, camera, health metrics
- ✅ **Remote game updates**: Deploy new game versions
- ✅ **Camera surveillance**: Live video monitoring
- ✅ **Location tracking**: GPS and manual location management
- ✅ **Log viewer**: Debug console issues remotely
- ✅ **System control**: Restart, reboot, view logs

---

## 🎯 **Installation Checklist**

### **Pre-Deployment**
- [ ] Fresh Ubuntu Server 22.04 LTS installed
- [ ] Swedish keyboard configured
- [ ] Network connectivity verified
- [ ] System fully updated
- [ ] SSH access configured (optional)

### **During Deployment**
- [ ] Monitor deployment progress
- [ ] Watch for error messages
- [ ] Ensure network stays connected
- [ ] Note console ID and IP address

### **Post-Deployment**
- [ ] Console reboots automatically
- [ ] Auto-login to kiosk mode works
- [ ] Game launches in fullscreen
- [ ] Console appears in admin panel
- [ ] Heartbeat monitoring active

### **Verification**
- [ ] Game responds to input
- [ ] Network connectivity maintained
- [ ] NFC reader detected (if connected)
- [ ] Camera functional (if connected)
- [ ] Battery monitoring working (if portable)

---

## 📞 **Support Information**

### **Deployment Issues**
- **Log collection**: Use diagnostic tools to gather system information
- **Admin panel**: Check console status in fleet management
- **SSH access**: Remote debugging via SSH connection

### **Hardware Issues**
- **Graphics problems**: Run hardware detection script
- **NFC reader**: Check USB device detection
- **Camera issues**: Verify camera permissions and drivers

### **Service Issues**
- **Kiosk mode**: Check systemd service status
- **Auto-login**: Verify getty service configuration
- **Game startup**: Check game executable and logs

---

## 🎮 **Quick Reference Commands**

### **Essential Commands**
```bash
# Deploy console
curl -sSL https://deckport.ai/deploy/console | bash

# Check console status
systemctl status deckport-kiosk.service

# View console logs
journalctl -u deckport-kiosk.service -f

# Test hardware
curl -sSL https://deckport.ai/deploy/detect-hardware | bash

# Emergency access
Ctrl + Alt + F2  # Switch to TTY2
```

### **Console Management**
```bash
# Restart game
sudo systemctl restart deckport-kiosk.service

# Update game version (manual)
# Use admin panel for remote updates

# Check network
ping 8.8.8.8

# View system info
htop  # or top for system monitoring
```

---

**🎯 This guide covers the complete console installation process from fresh Ubuntu to fully functional Deckport gaming console with remote management capabilities.**

*Keep this guide handy for all console installations - it includes troubleshooting for common issues and complete configuration instructions.*
