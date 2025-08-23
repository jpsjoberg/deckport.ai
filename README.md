# Deckport AI - Physical-Digital Trading Card Game

[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Godot](https://img.shields.io/badge/Godot-4.4+-blue.svg)](https://godotengine.org)

**Deckport AI** is a competitive physical-digital trading card game that bridges the gap between physical cards and digital gameplay through innovative console technology and AI-powered card generation.

## 🎮 **Project Overview**

Deckport combines the tactile experience of physical trading cards with the dynamic possibilities of digital gaming. Players use real NFC-enabled cards scanned by specialized console hardware to engage in strategic battles in digital arenas, with AI-generated artwork and evolving card mechanics.

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │      API        │    │    Console      │
│   (Flask)       │    │   (Flask)       │    │   (Godot)       │
│   Port: 8001    │◄──►│   Port: 8002    │◄──►│   Kiosk Mode    │
│                 │    │                 │    │                 │
│ • Web Interface │    │ • Game Logic    │    │ • Card Scanning │
│ • User Auth     │    │ • Authentication│    │ • QR Login      │
│ • Admin Panel   │    │ • Real-time API │    │ • Touch UI      │
│ • Card Gen      │    │ • Card System   │    │ • Video BG      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 **Project Structure**

```
deckport.ai/
├── api/                    # Game API service (Flask)
│   ├── app.py             # Main API application
│   ├── models/            # Database models
│   ├── routes/            # API endpoints
│   ├── venv/              # Python virtual environment
│   └── requirements.txt   # Python dependencies
├── frontend/              # Web frontend (Flask)
│   ├── app.py             # Frontend application
│   ├── templates/         # HTML templates
│   │   └── admin/         # Admin panel templates
│   ├── static/            # CSS, JS, images
│   ├── services/          # Card management services
│   ├── venv/              # Python virtual environment
│   └── requirements.txt   # Python dependencies
├── console/               # Game console (Godot)
│   ├── project.godot      # Godot project file
│   ├── scenes/            # Game scenes (.tscn)
│   ├── scripts/           # Game scripts (.gd)
│   ├── assets/            # Game assets
│   └── build/             # Console builds
├── cardmaker.ai/          # AI card generation system
│   ├── deckport.sqlite3   # Card database
│   ├── cards_output/      # Generated card images
│   ├── card_elements/     # Card composition assets
│   └── art-generation.json # ComfyUI workflow
└── shared/                # Shared utilities and models
    ├── models/            # Database models
    ├── auth/              # Authentication utilities
    ├── database/          # Database connection
    └── utils/             # Common utilities
```

## 🎯 **Current Status: Phase 3 Ready**

### **✅ Phase 1: User Management & Core Game Logic (Complete)**
- ✅ **Complete Authentication System**: Device + player two-tier auth
- ✅ **Database-driven System**: PostgreSQL with real data
- ✅ **Card Catalog**: Working with database integration
- ✅ **Admin System**: Comprehensive management interface
- ✅ **User Management**: Registration, login, profiles
- ✅ **Modular Architecture**: Services-based structure

### **✅ Phase 2: Real-time Features & Matchmaking (Complete)**
- ✅ **Console Authentication**: QR code login flow
- ✅ **Console Kiosk Mode**: Fullscreen gaming experience
- ✅ **Real-time Logging**: Security and activity monitoring
- ✅ **Card Scanning Simulation**: Q/W/E key card scanning
- ✅ **Touch Interface**: Console touch and keyboard controls
- ✅ **Video Backgrounds**: Support for MP4/OGV backgrounds

### **🔄 Phase 3: Hardware Integration (In Progress)**
- 🔄 **Hardware NFC Integration**: Real card scanning
- 🔄 **WebSocket Real-time**: Live multiplayer matches
- 🔄 **Advanced Game Scenes**: Hero selection, arena battles
- 🔄 **Match Statistics**: Performance tracking and analytics

### **📋 Phase 4: Advanced Features (Planned)**
- 📋 **Over-the-Air Updates**: Automatic console updates
- 📋 **Advanced Security**: Enhanced device authentication
- 📋 **Tournament Mode**: Competitive play features
- 📋 **Card Marketplace**: Trading and collection management

## 🎴 **Two-Tier Card System**

Deckport uses a sophisticated **two-tier card architecture** that separates card design from physical instances:

### **Tier 1: Card Templates (Raw Designs)**
- **Purpose**: Master card designs and specifications created by admins
- **AI Generated**: Artwork created via ComfyUI integration
- **Reusable**: One template can create many NFC card instances
- **Lifecycle**: Created → Reviewed → Published → Available for NFC production

### **Tier 2: NFC Card Instances (Unique Physical Cards)**
- **Purpose**: Unique physical cards owned by players
- **Evolutionary**: Can gain experience and evolve beyond base template
- **Trackable**: Complete history of matches, evolutions, and ownership
- **Tradeable**: Can change owners while maintaining history

### **Database Architecture**
```sql
-- Tier 1: Templates (Admin-Managed)
card_sets                    # Card collections/expansions
card_templates              # Master card designs
card_template_stats         # Base statistics
card_template_mana_costs    # Mana requirements
card_template_art_generation # AI art metadata

-- Tier 2: Instances (Player-Owned)
nfc_card_instances          # Physical NFC cards
card_evolutions             # Evolution history
card_match_participation    # Match usage tracking
```

## 🎨 **AI-Powered Card Generation**

### **ComfyUI Integration**
- **External Server**: ComfyUI running on dedicated AI generation server
- **FLUX Model**: High-quality diffusion model for card artwork
- **Painterly Style**: Oil painting aesthetic matching game theme
- **Custom Prompts**: Dynamic text injection for each card
- **Consistent Sizing**: 1200x2048 resolution optimized for card composition

### **Generation Process**
1. **Prompt Creation**: Admin enters descriptive text for card artwork
2. **Workflow Injection**: System updates ComfyUI workflow with prompt
3. **Queue Submission**: Workflow submitted to external ComfyUI server
4. **Progress Monitoring**: Real-time status tracking and queue management
5. **Image Retrieval**: Generated artwork downloaded and processed
6. **Card Composition**: Final card assembled with frames, icons, and text

### **Card Composition Pipeline**
1. **Base Artwork**: AI-generated art scaled and positioned
2. **Frame Overlay**: Rarity-specific frames (legendary gets special treatment)
3. **Glow Effects**: Screen blend mode for magical appearance
4. **Mana Icons**: Color-specific mana symbols
5. **Text Elements**: Card name and category with custom fonts
6. **Rarity Indicators**: Visual rarity gems and effects
7. **Set Symbols**: Game set identification icons

## 🔐 **Authentication System**

### **Two-Tier Authentication Architecture**

#### **1. Device Authentication (Hardware Level)**
- **RSA Keypairs**: Each console generates unique 2048-bit RSA keypair
- **Device Registration**: Admin approves new consoles via server admin panel
- **Signed Authentication**: Console signs nonces with private key for login
- **Device JWT**: 24-hour tokens for API access

#### **2. Player Authentication (User Level)**
- **QR Code Flow**: Console displays QR code for player login
- **Phone Confirmation**: Player scans QR, logs in on phone, confirms console
- **Player JWT**: Scoped tokens for console game sessions
- **Secure Handoff**: No passwords typed on console hardware

### **Complete Authentication Flow**
```
Console Boot → Device Auth (RSA) → Device JWT → Ready for Players
Player Arrives → QR Code → Phone Login → Player JWT → Game Session
```

## 🎮 **Console System**

### **Kiosk Mode Architecture**
```
Power On → Custom Boot Logo → Ubuntu (Hidden) → X11 Minimal → Godot Game → Deckport Interface
```

**Users never see Ubuntu - only the branded game experience!**

### **Console Features**
- **🖥️ Kiosk Mode**: Complete branded experience from power-on
- **🚀 Zero Desktop**: Ubuntu completely hidden from users
- **🔄 Auto-Recovery**: Automatic restart on crashes
- **📡 Server Integration**: Real-time communication with game servers
- **💳 NFC Support**: Physical card scanning and verification
- **🎵 Audio System**: Game sounds and voice chat
- **📱 Touch Interface**: Optimized for touchscreen consoles
- **🔒 Secure Updates**: Over-the-air updates with verification

### **Console Scenes**
- **simple_boot.tscn**: Boot screen with logo and progress
- **simple_menu.tscn**: Main menu with QR login option
- **qr_login_scene.tscn**: QR authentication display
- **player_menu.tscn**: Post-login player interface

## 🎯 **Game Design**

### **Core Game Identity**
- **One Hero System**: One Creature or Structure in play at a time
- **Arsenal System**: No deck building - scan any owned cards during match
- **Fast-Paced**: 10-second play windows with quickdraw bonuses
- **Arena Advantages**: Mana color matching provides bonuses

### **Canonical Mana Colors**
- **CRIMSON**: Aggressive damage and direct effects
- **AZURE**: Control and card manipulation
- **VERDANT**: Healing and growth mechanics
- **OBSIDIAN**: Dark magic and life drain
- **RADIANT**: Light magic and protection
- **AETHER**: Artifacts and colorless flexibility

### **Turn Structure**
1. **Start Phase** (10 seconds): Mana/energy generation, arena effects
2. **Main Phase** (40 seconds): Hero summoning, actions, equipment
3. **Attack Phase** (15 seconds): Combat and reactions
4. **End Phase** (5 seconds): End effects, focus banking

## 🛠️ **Admin Panel**

### **Comprehensive Management System**
- **🎨 Card Management**: AI-powered card generation and template system
- **🖥️ Console Fleet Management**: Monitor and control all hardware devices
- **🎮 Game Operations**: Balance cards, manage tournaments, monitor matches
- **👥 Player Management**: User accounts, support, moderation
- **📡 Communications Hub**: Multi-channel community engagement
- **📊 Analytics & BI**: Business intelligence and performance metrics
- **💰 Economy Management**: Marketplace, pricing, monetization
- **⚙️ System Administration**: Infrastructure, security, maintenance

### **Key Admin Features**
- **Real-time Monitoring**: Live console status and player activity
- **AI Art Generation**: ComfyUI integration for card artwork
- **Card Template System**: Create and manage reusable card designs
- **NFC Production**: Convert templates to physical NFC cards
- **Evolution Tracking**: Monitor card growth and changes
- **Batch Operations**: Mass production and management tools

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.9+
- PostgreSQL 13+
- Godot Engine 4.4+
- Git
- ComfyUI server (for card generation)

### **1. Clone Repository**
```bash
git clone https://github.com/jpsjoberg/deckport.ai.git
cd deckport.ai
```

### **2. Set Up PostgreSQL Database**
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update && sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE deckport;
CREATE USER deckport_app WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE deckport TO deckport_app;
\q
```

### **3. Set Up API Service**
```bash
cd api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
echo "DATABASE_URL=postgresql+psycopg://deckport_app:your_password@127.0.0.1:5432/deckport" > .env
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env

python app.py
```

### **4. Set Up Frontend**
```bash
cd ../frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
echo "API_URL=http://127.0.0.1:8002" > .env
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env
echo "COMFYUI_HOST=http://your-comfyui-server:8188" >> .env
echo "CARDMAKER_DB_PATH=/path/to/cardmaker.ai/deckport.sqlite3" >> .env

python app.py
```

### **5. Set Up Console**
```bash
cd ../console
godot project.godot  # Open in Godot Editor
# Press F5 to run the console
```

### **6. Initialize Database**
```bash
cd ../
python scripts/init-database.py
```

## 🌐 **Services**

### **API Service** (`http://127.0.0.1:8002`)
- **Authentication**: Device and player authentication
- **Game Logic**: Card validation, match management
- **Real-time**: WebSocket support for live gameplay
- **Admin**: Console management and monitoring
- **Card System**: Template and instance management

### **Frontend** (`http://127.0.0.1:8001`)
- **Player Portal**: Account management, collection viewing
- **Admin Dashboard**: System monitoring, user management
- **Card Management**: AI-powered card generation interface
- **Authentication**: Email/password and social login
- **Mobile Optimized**: Responsive design for phone access

### **Console** (Kiosk Mode)
- **QR Authentication**: Phone-based login system
- **Card Scanning**: NFC and camera-based card recognition
- **Touch Interface**: Fullscreen game experience
- **Real-time Gameplay**: Live match participation
- **Video Backgrounds**: Rich atmospheric experiences

## 🔧 **Configuration**

### **Environment Variables**
```bash
# API Service
DATABASE_URL=postgresql+psycopg://deckport_app:your_password@127.0.0.1:5432/deckport
SECRET_KEY=your-secret-key-here
DEBUG=True

# Frontend
API_URL=http://127.0.0.1:8002
SECRET_KEY=your-secret-key-here
DEBUG=True
COMFYUI_HOST=http://your-comfyui-server:8188
CARDMAKER_DB_PATH=/path/to/cardmaker.ai/deckport.sqlite3
CARDMAKER_OUTPUT_DIR=/path/to/cardmaker.ai/cards_output
CARDMAKER_ELEMENTS_DIR=/path/to/cardmaker.ai/card_elements

# Console
CONSOLE_API_URL=http://127.0.0.1:8002
PUBLIC_API_URL=https://api.deckport.ai  # For QR codes
DEVICE_ID=DECK_DEV_CONSOLE_01
```

## 🧪 **Testing**

### **API Testing**
```bash
# Health check
curl http://127.0.0.1:8002/health

# Card catalog
curl "http://127.0.0.1:8002/v1/catalog/cards"

# User registration
curl -X POST -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' \
  http://127.0.0.1:8002/v1/auth/player/register
```

### **Console Testing**
```bash
# Build console
cd console
godot --headless --export-release "Linux/X11" build/linux_x86_64/deckport_console

# Test build
./build/linux_x86_64/deckport_console
```

### **Card Generation Testing**
1. Navigate to `/admin/cards` in the admin panel
2. Check ComfyUI server status (green dot = online)
3. Click "Generate New Card" to create your first card
4. Enter card details and artwork prompt
5. Submit and monitor generation progress

## 🐛 **Troubleshooting**

### **Common Issues**
- **API won't start**: Check Python version and virtual environment
- **Console connection failed**: Verify API service is running on port 8002
- **QR code not working**: Check network connectivity and public URL
- **Cards not scanning**: Verify Q/W/E key bindings in Godot
- **ComfyUI not connecting**: Check server status and network configuration

### **Debug Commands**
```bash
# Check service status
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8001/

# View logs
tail -f api/logs/app.log
tail -f frontend/logs/app.log

# Test console build
cd console && ./build/linux_x86_64/deckport_console

# Test ComfyUI connection
curl http://your-comfyui-server:8188/system_stats
```

## 📊 **Game Balance**

### **Current Card Statistics**
- **Total Cards**: 1,793 (ACTION: 600, CREATURE: 599, STRUCTURE: 594)
- **Efficiency Range**: 0.33 - 1.93 (power/cost ratio)
- **Energy Economy**: 33.3% of actions playable with 1 energy
- **Mana Economy**: Average hero cost 4.46 mana
- **Color Distribution**: Balanced across all 6 mana colors

### **Balance Features**
- **Automatic Rarity Assignment**: Based on efficiency percentiles
- **Arena Advantages**: Mana color matching provides strategic depth
- **Evolution System**: Cards can grow beyond base templates
- **Dynamic Balancing**: Real-time card stat adjustments

## 📄 **License**

This project is proprietary software. All rights reserved.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📞 **Support**

- 📧 **Email**: support@deckport.ai
- 📖 **Documentation**: [docs.deckport.ai](https://docs.deckport.ai)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/deckport-ai/issues)

---

**Built with ❤️ for the trading card game community** 🎮✨

*Last updated: December 2024 - Now with AI-powered card generation and comprehensive admin system!*