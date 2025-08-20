# Contributing to Deckport Console

Thank you for your interest in contributing to the Deckport Console project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Development Environment
1. **Ubuntu 20.04+** with desktop environment (for development)
2. **Godot Engine 4.2+** installed and accessible via command line
3. **Git** for version control
4. **Console hardware** for testing (or VM for basic testing)

### First Time Setup
```bash
# Clone the repository
git clone https://github.com/your-org/deckport-console.git
cd deckport-console

# Open in Godot
godot project.godot
```

## 🔄 Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 2. Make Changes
- Follow the project structure and naming conventions
- Test your changes thoroughly
- Update documentation if needed

### 3. Test Your Changes
```bash
# Build the console
godot --headless --export-release "Linux/X11" build/linux_x86_64/deckport_console

# Test the build
./build/linux_x86_64/deckport_console

# Test kiosk mode (if applicable)
sudo ./kiosk/setup_kiosk.sh
```

### 4. Commit and Push
```bash
git add .
git commit -m "feat: add amazing new feature"
git push origin feature/your-feature-name
```

### 5. Create Pull Request
- Use the PR template
- Provide clear description of changes
- Include screenshots/videos if UI changes
- Reference any related issues

## 📝 Code Style Guidelines

### GDScript Style
- **Indentation**: Use tabs (Godot default)
- **Naming**: 
  - Variables: `snake_case`
  - Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Signals: `snake_case`

### Example:
```gdscript
extends Control

# Constants
const MAX_PLAYERS = 4
const DEFAULT_TIMEOUT = 30.0

# Signals
signal player_joined(player_name)
signal game_started()

# Variables
var current_player_count: int = 0
var is_game_active: bool = false

func _ready():
    connect_to_server()
    setup_ui()

func connect_to_server():
    Logger.log_info("NetworkClient", "Connecting to server")
    # Implementation here
```

### Documentation
- **Functions**: Document public functions with docstrings
- **Complex Logic**: Add inline comments for complex algorithms
- **TODO Comments**: Use `# TODO:` for future improvements
- **FIXME Comments**: Use `# FIXME:` for known issues

```gdscript
func calculate_card_damage(base_damage: int, modifiers: Array) -> int:
    """Calculate final card damage with all modifiers applied.
    
    Args:
        base_damage: The base damage value of the card
        modifiers: Array of damage modifier dictionaries
        
    Returns:
        Final calculated damage value
    """
    var final_damage = base_damage
    
    # Apply each modifier in sequence
    for modifier in modifiers:
        match modifier.type:
            "multiply":
                final_damage *= modifier.value
            "add":
                final_damage += modifier.value
            # TODO: Add support for conditional modifiers
    
    return max(0, final_damage)  # Damage can't be negative
```

## 🧪 Testing Guidelines

### Manual Testing Checklist
- [ ] Console builds without errors
- [ ] Boot sequence works correctly
- [ ] Kiosk mode functions properly
- [ ] Server connection established
- [ ] UI responds to input correctly
- [ ] NFC scanning works (if implemented)
- [ ] Audio plays correctly
- [ ] Performance is acceptable

### Hardware Testing
- Test on actual console hardware when possible
- Verify touchscreen functionality
- Test NFC reader integration
- Check network connectivity
- Validate audio output

### Performance Testing
- Monitor memory usage during gameplay
- Check frame rate stability
- Test with multiple concurrent operations
- Verify boot time is acceptable

## 📋 Commit Message Guidelines

Use conventional commit format:

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat: add NFC card scanning functionality
fix: resolve boot sequence crash on startup
docs: update kiosk setup instructions
style: format Bootloader.gd according to style guide
refactor: extract server communication to separate class
test: add unit tests for card validation
chore: update Godot version to 4.2.1
```

## 🐛 Bug Reports

### Before Reporting
1. Check existing issues to avoid duplicates
2. Test on latest version
3. Try to reproduce the issue consistently

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- Console hardware: [e.g. Custom build, Raspberry Pi 4]
- OS: [e.g. Ubuntu 20.04]
- Godot version: [e.g. 4.2.1]
- Console version: [e.g. v1.0.0]

**Additional context**
Any other context about the problem.
```

## 🚀 Feature Requests

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## 🔒 Security Issues

For security vulnerabilities:
1. **DO NOT** create a public issue
2. Email security@deckport.ai with details
3. Include steps to reproduce
4. Allow time for assessment and fix before disclosure

## 📞 Getting Help

- 💬 **Discord**: [Deckport Community](https://discord.gg/deckport)
- 📧 **Email**: dev-support@deckport.ai
- 📖 **Documentation**: [docs.deckport.ai](https://docs.deckport.ai)

## 🏆 Recognition

Contributors will be recognized in:
- Project README.md
- Release notes
- Console credits screen (for significant contributions)

Thank you for contributing to Deckport Console! 🎮✨
