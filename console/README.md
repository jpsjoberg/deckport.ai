# Deckport Console

[![Godot Engine](https://img.shields.io/badge/Godot-4.2+-blue.svg)](https://godotengine.org/)
[![Linux](https://img.shields.io/badge/Platform-Linux-green.svg)](https://www.linux.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

**Deckport Console** is a dedicated gaming device client for the Deckport physical-digital trading card game. Built with Godot Engine, it provides a complete kiosk-mode experience that boots directly into the game, completely hiding the underlying Ubuntu operating system.

## 🎮 Features

- **🖥️ Kiosk Mode**: Complete branded experience from power-on
- **🚀 Zero Desktop**: Ubuntu completely hidden from users  
- **🔄 Auto-Recovery**: Automatic restart on crashes
- **📡 Server Integration**: Real-time communication with game servers
- **💳 NFC Support**: Physical card scanning and verification
- **🎵 Audio System**: Game sounds and voice chat
- **📱 Touch Interface**: Optimized for touchscreen consoles
- **🔒 Secure Updates**: Over-the-air updates with verification

## 🏗️ Architecture

The console uses a **kiosk architecture** that transforms a standard Ubuntu system into a dedicated gaming device:

```
Power On → Custom Boot Logo → Ubuntu (Hidden) → X11 Minimal → Godot Game → Deckport Interface
```

**Users never see Ubuntu - only your branded game experience!**

## 📋 Prerequisites

- **Operating System**: Ubuntu 20.04+ (will be hidden in kiosk mode)
- **Hardware**: 
  - 2GB RAM minimum (4GB recommended)
  - 8GB storage minimum  
  - OpenGL 3.3 compatible graphics
  - Network connectivity (Ethernet/WiFi)
  - Optional: NFC reader (USB/Serial)
  - Optional: Touchscreen display
- **Software**: 
  - Godot Engine 4.2+
  - Build tools (`build-essential`, `git`, `curl`)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/deckport-console.git
cd deckport-console
```

### 2. Install Godot Engine
```bash
# Download and install Godot 4.2+
wget https://downloads.tuxfamily.org/godotengine/4.2.1/Godot_v4.2.1-stable_linux.x86_64.zip
unzip Godot_v4.2.1-stable_linux.x86_64.zip
sudo mv Godot_v4.2.1-stable_linux.x86_64 /usr/local/bin/godot
sudo chmod +x /usr/local/bin/godot
```

### 2. Open Project in Godot
```bash
cd /home/jp/deckport.ai/console
godot project.godot
```

### 3. Build Console
```bash
# Export for Linux
godot --headless --export-release "Linux/X11" build/linux_x86_64/deckport_console

# Test the build
./build/linux_x86_64/deckport_console
```

### 4. Set Up Kiosk Mode (Optional)
```bash
# Configure console to boot directly into game
sudo ./kiosk/setup_kiosk.sh

# Reboot to activate kiosk mode
sudo reboot
```

## Project Structure

```
console/
├── project.godot          # Godot project configuration
├── export_presets.cfg     # Export settings for builds
├── scenes/                # Game scenes (.tscn files)
├── scripts/               # GDScript files (.gd files)
├── assets/                # Game assets (images, sounds, etc.)
├── autoload/              # Global scripts (auto-loaded)
├── build/                 # Build outputs
├── kiosk/                 # Kiosk mode configuration
└── README.md             # This file
```

## Key Features

### Kiosk Mode
- **Zero Desktop Exposure**: Ubuntu completely hidden from users
- **Auto-Start**: Game launches immediately on power-on
- **Crash Recovery**: Auto-restart if game crashes
- **Branded Boot**: Custom Deckport logo throughout boot sequence

### Hardware Integration
- **NFC Reader**: USB/Serial NFC card scanning
- **Network**: Ethernet/WiFi for server communication
- **Audio**: Game sounds and voice chat support
- **Display**: Full HD (1920x1080) fullscreen experience

### Server Communication
- **Authentication**: ✅ **Complete two-tier system implemented**
  - **Device Auth**: RSA keypair registration and authentication
  - **Player Auth**: QR code login via phone confirmation
  - **JWT Tokens**: Device and player tokens for API access
- **Real-time**: WebSocket connection for live matches (Phase 2)
- **Updates**: Over-the-air (OTA) update system (Phase 4)
- **Card Verification**: NFC card validation with server (Phase 3)

## Authentication System

### Two-Tier Authentication
The console uses a secure two-tier authentication system:

#### 1. Device Authentication (Hardware Level)
- **RSA Keypairs**: Each console generates a unique 2048-bit RSA keypair
- **Device Registration**: Admin approves new consoles via server admin panel
- **Signed Authentication**: Console signs nonces with private key for login
- **Device JWT**: 24-hour tokens for API access

#### 2. Player Authentication (User Level)  
- **QR Code Flow**: Console displays QR code for player login
- **Phone Confirmation**: Player scans QR, logs in on phone, confirms console
- **Player JWT**: Scoped tokens for console game sessions
- **Secure Handoff**: No passwords typed on console hardware

### Authentication Flow
```
Console Boot → Device Auth (RSA) → Device JWT → Ready for Players
Player Arrives → QR Code → Phone Login → Player JWT → Game Session
```

### Security Features
- **Private keys never leave console** hardware
- **Admin approval required** for new devices
- **Token expiration** prevents long-term compromise
- **Audit logging** of all authentication events
- **No console passwords** - all auth via secure phone flow

### Implementation Files
- `scripts/AuthManager.gd` - Complete authentication logic
- `scripts/Bootloader.gd` - Integration with boot sequence  
- `autoload/Global.gd` - Token storage and device management

## Development Workflow

### Local Development
1. **Edit in Godot**: Open `project.godot` in Godot editor
2. **Test Scenes**: Use F6 to test individual scenes
3. **Run Project**: Use F5 to run full project
4. **Build**: Export to `build/linux_x86_64/` for testing

### Console Deployment
1. **Build Release**: Export optimized release build
2. **Copy to Console**: Transfer build to console hardware
3. **Configure Kiosk**: Run kiosk setup script
4. **Test Boot**: Verify console boots directly to game

## Scene Architecture

### Bootloader.tscn
- **Purpose**: First scene loaded on console start
- **Features**: Logo display, update checking, server connection
- **Duration**: ~8 seconds from power-on to main menu

### MainMenu.tscn (Planned)
- **Purpose**: Main console interface
- **Features**: Player login, matchmaking, settings
- **Navigation**: Touch or gamepad controls

### AuthQR.tscn (Planned)
- **Purpose**: QR code login for players
- **Features**: Display QR code, poll for confirmation
- **Flow**: Generate QR → Display → Wait for phone confirmation

### GameBoard.tscn (Planned)
- **Purpose**: Main game interface
- **Features**: Card play area, NFC scanning, real-time updates
- **Integration**: WebSocket for real-time, NFC for cards

## Configuration

### Global Settings
- **Server URL**: Configurable for dev/production
- **Device ID**: Unique console identifier
- **Debug Mode**: Additional logging and shortcuts

### Console Settings
- **Display**: Resolution, fullscreen, VSync
- **Audio**: Volume levels for different channels
- **Network**: Connection timeouts, retry attempts
- **NFC**: Scan settings and timeouts

### Kiosk Settings
- **Auto-start**: Game launches on boot
- **Crash Recovery**: Automatic restart on failure
- **Idle Timeout**: Screensaver after inactivity
- **Security**: Restricted system access

## Build Configuration

### Export Presets
- **Target**: Linux/X11 64-bit
- **Features**: Optimized for console hardware
- **Packaging**: Embedded PCK for single executable
- **Graphics**: OpenGL compatibility mode

### System Requirements
- **OS**: Ubuntu 20.04+ (hidden in kiosk mode)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 8GB minimum for OS + game
- **Graphics**: OpenGL 3.3 compatible
- **Network**: Ethernet or WiFi for server connection

## Troubleshooting

### Console Won't Start
1. Check if build exists: `ls build/linux_x86_64/deckport_console`
2. Test build manually: `./build/linux_x86_64/deckport_console`
3. Check systemd logs: `sudo journalctl -u deckport-console.service`

### Kiosk Mode Issues
1. Verify auto-login: `sudo systemctl status getty@tty1.service`
2. Check X11 startup: `sudo journalctl -u deckport-console.service`
3. Access recovery terminal: `Ctrl+Alt+F2`

### Network Connection
1. Test server connectivity: `curl http://127.0.0.1:8002/health`
2. Check console logs in Godot debug output
3. Verify network settings in Global.gd

### NFC Reader (When Implemented)
1. Check USB connection: `lsusb | grep -i nfc`
2. Verify permissions: User in `dialout` group
3. Test with NFC tools: `nfc-list` (if available)

## Development Notes

### Phase 3 Implementation Status
- ✅ **Project Structure**: Complete Godot project setup
- ✅ **Kiosk Mode**: Full kiosk configuration system
- ✅ **Boot Sequence**: Bootloader with logo and progress
- ✅ **Global Systems**: Settings, logging, state management
- ✅ **Authentication System**: Complete device + player authentication
  - ✅ **Device Authentication**: RSA keypair-based hardware auth
  - ✅ **Player Login**: QR code + phone confirmation flow
  - ✅ **JWT Integration**: Token management and API communication
  - ✅ **Security**: Cryptographic signatures and token expiration
- 📋 **NFC Integration**: Card scanning (Phase 3)
- 📋 **Real-time**: WebSocket game communication (Phase 2)
- 📋 **Game Scenes**: Main menu, game board, etc. (Phase 3)

### Next Steps
1. **Complete Phase 2**: Real-time WebSocket integration
2. **Build Game Scenes**: Main menu, game board interfaces
3. **NFC Integration**: Physical card scanning system
4. **Server Communication**: Device authentication and registration
5. **OTA Updates**: Automatic update system

## Security Considerations

### Kiosk Mode Security
- **Limited User Access**: Console runs as restricted `deckport` user
- **No Desktop Access**: Ubuntu desktop completely hidden
- **System Protection**: Limited file system access
- **Network Isolation**: Only game server communication allowed

### Update Security
- **Signed Updates**: All updates cryptographically signed
- **Rollback Protection**: Previous version kept as backup
- **Verification**: SHA256 checksums for all downloads
- **Secure Channel**: HTTPS for all update communications

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style
- Follow GDScript style guide
- Use clear, descriptive variable names
- Comment complex logic
- Keep functions focused and small

### Testing
- Test all changes on actual console hardware
- Verify kiosk mode functionality
- Check server communication
- Validate NFC integration (if applicable)

## 📄 License

This project is proprietary software. All rights reserved.

See [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues
- **Console won't start**: Check build exists and is executable
- **Kiosk mode problems**: Verify systemd services and auto-login
- **Network issues**: Test server connectivity and API endpoints
- **NFC problems**: Check hardware connection and permissions

### Getting Help
- 📧 Email: support@deckport.ai
- 📖 Documentation: [docs.deckport.ai](https://docs.deckport.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/deckport-console/issues)

## 🏷️ Versioning

We use [Semantic Versioning](http://semver.org/) for version numbers.

- **Major**: Breaking changes to console interface or server protocol
- **Minor**: New features that are backwards compatible
- **Patch**: Bug fixes and minor improvements

## 🔄 Changelog

### v1.0.0 (Planned - Phase 3)
- ✅ Complete kiosk mode system
- ✅ Bootloader with branded experience  
- ✅ Global state and settings management
- ✅ Structured logging system
- 📋 Main game interface
- 📋 NFC card integration
- 📋 Server authentication
- 📋 Real-time match communication

### v0.1.0 (Current - Phase 1)
- ✅ Project structure and Godot setup
- ✅ Kiosk mode configuration
- ✅ Boot sequence implementation
- ✅ Development tooling

## 🔗 Related Projects

- **[Deckport API](https://github.com/your-org/deckport-api)**: Game server backend
- **[Deckport Frontend](https://github.com/your-org/deckport-frontend)**: Web interface
- **[Deckport Realtime](https://github.com/your-org/deckport-realtime)**: WebSocket service

## 📊 Project Status

- **Phase 1**: ✅ User Management & Core Game Logic (Complete)
- **Phase 2**: 🔄 Real-time Features & Matchmaking (In Progress)  
- **Phase 3**: 📋 Hardware Integration (Console, NFC) (Planned)
- **Phase 4**: 📋 Advanced Features (Video, OTA) (Planned)

---

**Built with ❤️ for the Deckport trading card game community** 🎮✨
