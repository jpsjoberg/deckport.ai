# Changelog

All notable changes to the Deckport Console project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete project structure for Godot 4.2+
- Kiosk mode configuration system
- Boot sequence with branded loading
- Global state management system
- Structured logging framework
- Console settings management
- Systemd service integration
- Auto-recovery and crash protection

### Changed
- N/A (Initial release)

### Deprecated
- N/A (Initial release)

### Removed
- N/A (Initial release)

### Fixed
- N/A (Initial release)

### Security
- Kiosk mode security restrictions
- Limited user access permissions
- Secure update verification system

## [0.1.0] - 2025-01-18

### Added
- Initial project setup
- Godot 4.2 project configuration
- Export presets for Linux builds
- Basic directory structure
- Kiosk mode setup scripts
- Global autoload scripts (Global.gd, Settings.gd, Logger.gd)
- Bootloader scene with progress tracking
- Systemd service files for console management
- Comprehensive documentation

### Technical Details
- **Godot Version**: 4.2.1
- **Target Platform**: Linux/X11 64-bit
- **Rendering**: OpenGL Compatibility mode
- **Resolution**: 1920x1080 fullscreen
- **Boot Time**: ~8 seconds from power-on to main menu

### Kiosk Mode Features
- Ubuntu desktop completely hidden
- Auto-login for dedicated console user
- X11 minimal environment
- Automatic game startup
- Crash recovery system
- System resource monitoring

### Development Tools
- Complete build system
- Development and production configurations
- Logging and debugging framework
- Settings management system
- Hardware integration framework

---

## Version History

- **v0.1.0**: Initial project setup and kiosk mode foundation
- **v1.0.0**: Planned for Phase 3 completion with full game functionality

## Release Notes Format

Each release includes:
- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

## Development Phases

- **Phase 1** (✅ Complete): User Management & Core Game Logic
- **Phase 2** (🔄 In Progress): Real-time Features & Matchmaking  
- **Phase 3** (📋 Planned): Hardware Integration (Console, NFC)
- **Phase 4** (📋 Planned): Advanced Features (Video, OTA Updates)
