#!/bin/bash

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
