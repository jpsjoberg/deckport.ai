#!/bin/bash

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
        DISPLAY=:0 chromium-browser --kiosk --no-first-run --disable-translate \
            --disable-infobars --disable-suggestions-service \
            --disable-save-password-bubble --start-maximized \
            --window-position=0,0 --window-size=1920,1080 \
            --disable-web-security --disable-features=VizDisplayCompositor \
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
