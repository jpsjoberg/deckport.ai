# Deckport AI - Physical-Digital Trading Card Game

[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Godot](https://img.shields.io/badge/Godot-4.4+-blue.svg)](https://godotengine.org)

**Deckport AI** is a competitive physical-digital trading card game that bridges the gap between physical cards and digital gameplay through innovative console technology.

## 🎮 **Project Overview**

Deckport combines the tactile experience of physical trading cards with the dynamic possibilities of digital gaming. Players use real cards scanned by specialized console hardware to engage in strategic battles in digital arenas.

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │      API        │    │    Console      │
│   (Flask)       │    │   (Flask)       │    │   (Godot)       │
│   Port: 8001    │◄──►│   Port: 8002    │◄──►│   Kiosk Mode    │
│                 │    │                 │    │                 │
│ • Web Interface │    │ • Game Logic    │    │ • Card Scanning │
│ • User Auth     │    │ • Authentication│    │ • QR Login      │
│ • Admin Panel   │    │ • Real-time API │    │ • Touch UI      │
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
│   ├── static/            # CSS, JS, images
│   ├── venv/              # Python virtual environment
│   └── requirements.txt   # Python dependencies
├── console/               # Game console (Godot)
│   ├── project.godot      # Godot project file
│   ├── scenes/            # Game scenes (.tscn)
│   ├── scripts/           # Game scripts (.gd)
│   ├── assets/            # Game assets
│   └── build/             # Console builds
└── README.md              # This file
```

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.9+
- PostgreSQL 13+
- Godot Engine 4.4+
- Git

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

python app.py
```

### **5. Set Up Console**
```bash
cd ../console
godot project.godot  # Open in Godot Editor
# Press F5 to run the console
```

## 🌐 **Services**

### **API Service** (`http://127.0.0.1:8002`)
- **Authentication**: Device and player authentication
- **Game Logic**: Card validation, match management
- **Real-time**: WebSocket support for live gameplay
- **Admin**: Console management and monitoring

### **Frontend** (`http://127.0.0.1:8001`)
- **Player Portal**: Account management, collection viewing
- **Admin Dashboard**: System monitoring, user management
- **Authentication**: Email/password and social login
- **Mobile Optimized**: Responsive design for phone access

### **Console** (Kiosk Mode)
- **QR Authentication**: Phone-based login system
- **Card Scanning**: NFC and camera-based card recognition
- **Touch Interface**: Fullscreen game experience
- **Real-time Gameplay**: Live match participation

## 🔐 **Authentication Flow**

```
Phone App → QR Code → Console Login → Game Session
     ↑         ↓         ↑         ↓
Web Portal ← API ← Device Auth → Real-time Match
```

1. **Device Registration**: Consoles register with unique IDs
2. **QR Code Generation**: Console displays QR for player login
3. **Phone Authentication**: Player scans QR, logs in on phone
4. **Session Creation**: Console receives player session token
5. **Game Access**: Full game functionality unlocked

## 🎯 **Development Phases**

- ✅ **Phase 1**: User Management & Core Game Logic
- ✅ **Phase 2**: Real-time Features & Matchmaking  
- 🔄 **Phase 3**: Hardware Integration (Console, NFC) - **In Progress**
- 📋 **Phase 4**: Advanced Features (Video, OTA Updates)

## 🛠️ **Development**

### **Running Services**
```bash
# Start API (Terminal 1)
cd api && source venv/bin/activate && python app.py

# Start Frontend (Terminal 2)
cd frontend && source venv/bin/activate && python app.py

# Start Console (Terminal 3)
cd console && godot --headless --main-pack project.godot
```

### **Testing**
```bash
# Test API health
curl http://127.0.0.1:8002/health

# Test Frontend
curl http://127.0.0.1:8001/

# Test Console connectivity
# Open Godot project and run with F5
```

## 📋 **Features**

### **Completed Features**
- ✅ **Complete Authentication System**: Device + player two-tier auth
- ✅ **QR Code Login**: Phone-based console authentication
- ✅ **Console Kiosk Mode**: Fullscreen gaming experience
- ✅ **Real-time Logging**: Security and activity monitoring
- ✅ **Card Scanning Simulation**: Q/W/E key card scanning
- ✅ **Touch Interface**: Console touch and keyboard controls
- ✅ **Video Backgrounds**: Support for MP4/OGV backgrounds

### **In Development**
- 🔄 **Hardware NFC Integration**: Real card scanning
- 🔄 **WebSocket Real-time**: Live multiplayer matches
- 🔄 **Advanced Game Scenes**: Hero selection, arena battles
- 🔄 **Match Statistics**: Performance tracking and analytics

### **Planned Features**
- 📋 **Over-the-Air Updates**: Automatic console updates
- 📋 **Advanced Security**: Enhanced device authentication
- 📋 **Tournament Mode**: Competitive play features
- 📋 **Card Marketplace**: Trading and collection management

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

# Console
CONSOLE_API_URL=http://127.0.0.1:8002
PUBLIC_API_URL=https://api.deckport.ai  # For QR codes
DEVICE_ID=DECK_DEV_CONSOLE_01
```

## 🐛 **Troubleshooting**

### **Common Issues**
- **API won't start**: Check Python version and virtual environment
- **Console connection failed**: Verify API service is running on port 8002
- **QR code not working**: Check network connectivity and public URL
- **Cards not scanning**: Verify Q/W/E key bindings in Godot

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
```

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