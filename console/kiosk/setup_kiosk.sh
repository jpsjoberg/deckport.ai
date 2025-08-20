#!/bin/bash
# Deckport Console Kiosk Setup Script
# This script configures Ubuntu to boot directly into the Deckport game

set -e

echo "🎮 Setting up Deckport Console Kiosk Mode..."
echo "⚠️  This will modify system settings to hide Ubuntu desktop"
echo "Press Enter to continue or Ctrl+C to cancel"
read

# 1. Disable Ubuntu desktop and login manager
echo "🖥️  Disabling desktop environment..."
sudo systemctl set-default multi-user.target
sudo systemctl disable gdm3 2>/dev/null || sudo systemctl disable lightdm 2>/dev/null || true

# 2. Create deckport user for console if it doesn't exist
echo "👤 Setting up deckport user..."
sudo useradd -m -s /bin/bash deckport 2>/dev/null || echo "User deckport already exists"
sudo usermod -a -G audio,video,input,dialout deckport

# 3. Configure auto-login for deckport user
echo "🔐 Configuring auto-login..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat << 'EOF' | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin deckport --noclear %I $TERM
EOF

# 4. Install X11 if not present
echo "📦 Installing required packages..."
sudo apt update
sudo apt install -y xinit xserver-xorg-core xserver-xorg-input-all xserver-xorg-video-all

# 5. Set custom boot splash (if image exists)
if [ -f "/home/jp/deckport.ai/console/assets/logos/boot_splash.png" ]; then
    echo "🖼️  Setting custom boot splash..."
    sudo cp /home/jp/deckport.ai/console/assets/logos/boot_splash.png /usr/share/pixmaps/deckport_splash.png
fi

# 6. Install systemd services
echo "⚙️  Installing systemd services..."
sudo cp /home/jp/deckport.ai/console/kiosk/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable deckport-console.service

# 7. Configure .bashrc for deckport user to start X11 with game
echo "🚀 Configuring auto-start..."
cat << 'EOF' | sudo tee /home/deckport/.bashrc
# Auto-start Deckport console on login
if [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]]; then
    # Set up minimal X11 environment
    export DISPLAY=:0
    
    # Start X11 with the Deckport game
    exec startx /home/jp/deckport.ai/console/build/linux_x86_64/deckport_console -- -nocursor
fi
EOF

# 8. Create .xinitrc for deckport user
cat << 'EOF' | sudo tee /home/deckport/.xinitrc
#!/bin/bash
# Deckport Console X11 startup

# Disable screen blanking and power management
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 1 &

# Set black background
xsetroot -solid black

# Start the Deckport console game
exec /home/jp/deckport.ai/console/build/linux_x86_64/deckport_console
EOF

sudo chmod +x /home/deckport/.xinitrc

# 9. Set ownership for deckport user files
sudo chown deckport:deckport /home/deckport/.bashrc /home/deckport/.xinitrc

# 10. Create desktop entry
sudo mkdir -p /usr/share/applications
cat << 'EOF' | sudo tee /usr/share/applications/deckport-console.desktop
[Desktop Entry]
Name=Deckport Console
Comment=Deckport Trading Card Game Console
Exec=/home/jp/deckport.ai/console/build/linux_x86_64/deckport_console
Icon=/home/jp/deckport.ai/console/assets/logos/deckport_logo.png
Terminal=false
Type=Application
Categories=Game;
StartupNotify=true
EOF

# 11. Install unclutter to hide mouse cursor
sudo apt install -y unclutter

# 12. Create console management script
cat << 'EOF' | sudo tee /home/jp/deckport.ai/console/scripts/kiosk_manager.sh
#!/bin/bash
# Deckport Kiosk Manager
# Monitors and manages the console in kiosk mode

CONSOLE_PATH="/home/jp/deckport.ai/console/build/linux_x86_64/deckport_console"
LOG_FILE="/var/log/deckport-kiosk.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_message "Deckport Kiosk Manager started"

while true; do
    # Check if console is running
    if ! pgrep -f "deckport_console" > /dev/null; then
        log_message "Console not running, checking if it should be..."
        
        # Check if deckport user is logged in
        if who | grep -q "deckport"; then
            log_message "Deckport user logged in but console not running - this is expected during startup"
        fi
    fi
    
    # Check for updates (placeholder)
    # TODO: Implement update checking logic
    
    sleep 30
done
EOF

sudo chmod +x /home/jp/deckport.ai/console/scripts/kiosk_manager.sh

echo ""
echo "✅ Kiosk mode setup complete!"
echo ""
echo "📋 Summary of changes:"
echo "  • Disabled desktop environment (multi-user.target)"
echo "  • Created deckport user with auto-login"
echo "  • Configured X11 to start Deckport game directly"
echo "  • Installed systemd services for console management"
echo "  • Set up crash recovery and monitoring"
echo ""
echo "🔄 Next steps:"
echo "  1. Build your Godot game: cd console && godot --headless --export-release 'Linux/X11'"
echo "  2. Test the build: ./build/linux_x86_64/deckport_console"
echo "  3. Reboot to activate kiosk mode: sudo reboot"
echo ""
echo "⚠️  After reboot, Ubuntu desktop will be hidden and only your game will show!"
echo "   To access terminal: Ctrl+Alt+F2 (login as your regular user)"
echo "   To disable kiosk mode: sudo systemctl set-default graphical.target && sudo reboot"
