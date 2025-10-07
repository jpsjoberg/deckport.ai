# Deckport.ai Project Structure & Current Status

**Last Updated**: September 13, 2025  
**Status**: 🚀 **85% Complete - Production Ready Core Systems**

## Overview
This document reflects the current project structure for Deckport.ai after successful cleanup and organization. The system is now production-ready with comprehensive authentication, admin panels, and core gameplay systems implemented.

## Core Architecture Principles

### 1. **Modular Services**
- Each service has a single responsibility
- Services communicate via well-defined APIs
- Easy to develop, test, and deploy independently

### 2. **Current Implementation Status**
- **✅ Phase 1**: User Management & Core Game Logic (COMPLETE)
- **✅ Phase 2**: Real-time Features & Matchmaking (COMPLETE)
- **🔄 Phase 3**: Hardware Integration (NFC, Consoles) - In Progress
- **📋 Phase 4**: Advanced Features (Video, OTA) - Planned

### 3. **Production Ready**
- Proper configuration management
- Database migrations
- Testing framework
- CI/CD pipeline
- Monitoring and logging

---

## Current Project Structure

```
/home/jp/deckport.ai/
├── README.md                     # Main project documentation
├── TODO.md                       # Active development tasks
├── card_generation_queue.db      # Card generation system database
├── Godot_v4.3-stable_linux.x86_64.zip  # Current Godot engine
├── godot-headless               # Headless Godot binary
│
│   └── DB_pass                  # Database credentials
│
├── api/                         # Legacy API service (Flask)
│   ├── app.py                   # Main API application
│   ├── models.py                # Legacy models
│   └── wsgi.py                  # WSGI entry point
│
├── frontend/                    # Web frontend service (Flask)
│   ├── app.py                   # Frontend application
│   ├── templates/               # HTML templates
│   ├── static/                  # CSS, JS, images
│   ├── services/                # Card management services
│   ├── admin_routes/            # Admin route handlers
│   └── requirements.txt         # Python dependencies
│
├── services/                    # Backend microservices
│   ├── api/                     # Main API service
│   ├── realtime/                # WebSocket service (IMPLEMENTED)
│   └── frontend/                # Frontend service
│
├── console/                     # Godot console client (IMPLEMENTED)
│   ├── project.godot            # Godot project file
│   ├── scenes/                  # Game scenes (.tscn)
│   ├── scripts/                 # Game scripts (.gd)
│   ├── assets/                  # Game assets
│   ├── build/                   # Console builds
│   └── kiosk/                   # Kiosk mode deployment
│
├── shared/                      # Shared libraries and models
│   ├── models/                  # SQLAlchemy database models
│   ├── auth/                    # Authentication utilities
│   ├── database/                # Database connection & migrations
│   ├── security/                # Security utilities
│   └── services/                # Shared business logic
│
├── cardmaker.ai/                # AI card generation system
│   ├── deckport.sqlite3         # Card database
│   ├── cards_output/            # Generated card images
│   ├── card_elements/           # Card composition assets
│   └── art-generation.json      # ComfyUI workflow
│
├── scripts/                     # Utility scripts
│   ├── init-database.py         # Database initialization
│   ├── dev-start.sh             # Development startup
│   ├── check_db.py              # Database verification
│   ├── reset_admin_password.py  # Admin password reset
│   └── [various utility scripts]
│
├── tests/                       # Test suites
│   ├── integration/             # Integration tests
│   ├── setup/                   # Test setup utilities
│   ├── unit/                    # Unit tests
│   └── test_*.py                # Moved test files
│
├── docs/                        # Documentation (ORGANIZED)
│   ├── admin/                   # Admin system documentation
│   ├── api/                     # API documentation
│   ├── deployment/              # Deployment guides
│   ├── development/             # Development documentation
│   ├── nfc/                     # NFC system documentation
│   ├── security/                # Security reports and guides
│   ├── system/                  # System documentation
│   ├── reports/                 # Test results and reports
│   └── PROJECT_STRUCTURE.md     # This file
│
├── tools/                       # Development tools
│   └── nfc-card-programmer/     # NFC programming tools
│
├── deployment/                  # Infrastructure as code
│   ├── docker/                  # Docker configurations
│   ├── kubernetes/              # Kubernetes manifests
│   └── terraform/               # Terraform configurations
│
├── requirements/                # Requirements files
│   ├── requirements-arena-creation.txt
│   └── requirements-stripe.txt
│
├── migrations/                  # Database migrations
│   └── [various migration files]
│
├── workflows/                   # ComfyUI workflows
│   └── arena-generation.json
│
└── static/                      # Static assets
    ├── cards/
    ├── images/
    └── videos/
│
├── shared/                       # Shared code between services
│   ├── __init__.py
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── console.py
│   │   ├── card.py
│   │   ├── match.py
│   │   └── nfc.py
│   ├── auth/                    # Authentication utilities
│   │   ├── __init__.py
│   │   ├── jwt_handler.py
│   │   └── device_auth.py
│   ├── database/                # Database utilities
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── migrations/
│   └── utils/                   # Common utilities
│       ├── __init__.py
│       ├── logging.py
│       ├── validation.py
│       └── crypto.py
│
├── services/                     # Microservices
│   ├── api/                     # REST API Service
│   │   ├── app.py
│   │   ├── wsgi.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── cards.py
│   │   │   ├── matches.py
│   │   │   ├── admin.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   ├── card_service.py
│   │   │   ├── match_service.py
│   │   │   └── nfc_service.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── rate_limit.py
│   │
│   ├── frontend/                # Web Frontend Service
│   │   ├── app.py
│   │   ├── wsgi.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── static/
│   │   │   ├── css/
│   │   │   ├── js/
│   │   │   └── images/
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── auth/
│   │   │   ├── game/
│   │   │   ├── admin/
│   │   │   └── components/
│   │   └── utils/
│   │       └── api_client.py
│   │
│   ├── realtime/               # WebSocket Service (Phase 2)
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── matchmaking.py
│   │   │   ├── game_state.py
│   │   │   └── notifications.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── queue_manager.py
│   │   │   └── match_manager.py
│   │   └── protocols/
│   │       ├── __init__.py
│   │       └── game_protocol.py
│   │
│   └── console-bridge/         # Console Communication Service (Phase 3)
│       ├── app.py
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── device_auth.py
│       │   ├── qr_login.py
│       │   └── ota_updates.py
│       └── services/
│           ├── __init__.py
│           ├── device_manager.py
│           └── update_service.py
│
├── console/                     # Godot Console Client (Phase 3)
│   ├── project.godot
│   ├── export_presets.cfg
│   ├── scenes/
│   │   ├── Bootloader.tscn
│   │   ├── AuthQR.tscn
│   │   ├── MainMenu.tscn
│   │   └── Game.tscn
│   ├── scripts/
│   │   ├── Bootloader.gd
│   │   ├── AuthQR.gd
│   │   ├── RealtimeClient.gd
│   │   └── GameManager.gd
│   └── assets/
│       ├── cards/
│       ├── ui/
│       └── audio/
│
└── deployment/                  # Deployment configurations
    ├── docker/
    │   └── docker-compose.prod.yml
    ├── kubernetes/
    │   ├── namespace.yaml
    │   ├── api-deployment.yaml
    │   ├── frontend-deployment.yaml
    │   └── realtime-deployment.yaml
    └── terraform/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## Current Development Status

### ✅ Phase 1: User Management & Core Game Logic (COMPLETE)
**Status**: Production Ready ✅

**Implemented Features**:
- ✅ User registration/login with JWT authentication
- ✅ Password hashing and validation with secure storage
- ✅ User profiles and comprehensive player management
- ✅ Card catalog with database integration (1,793 cards)
- ✅ Advanced admin panel with 85% feature completion
- ✅ Match history and statistics tracking
- ✅ Role-based access control (RBAC) system
- ✅ Security audit logging and monitoring

**Active Services**:
- `services/api/` - REST API with comprehensive endpoints
- `frontend/` - Web interface with admin panel
- PostgreSQL database with full schema
- Authentication system with JWT tokens

**Production Status**:
- ✅ Working authentication system
- ✅ Card catalog with 1,793 cards
- ✅ Comprehensive admin dashboard
- ✅ Security and monitoring systems

### ✅ Phase 2: Real-time Features & Multiplayer (COMPLETE)
**Status**: Production Ready ✅

**Implemented Features**:
- ✅ WebSocket service for real-time communication (573 lines)
- ✅ Matchmaking system with ELO-based pairing (279 lines)
- ✅ Real-time game state synchronization (453 lines)
- ✅ Battle system logic with turn management
- ✅ Console-to-console communication
- ✅ Connection recovery and error handling

**Active Services**:
- `services/api/` - Enhanced with game engine endpoints
- `services/realtime/` - WebSocket service (IMPLEMENTED)
- `console/` - Godot client with battle system (1,291 lines)
- PostgreSQL with game state management

**Production Status**:
- ✅ Live multiplayer battles implemented
- ✅ Real-time game state synchronization
- ✅ Turn-based gameplay with resource management
- ✅ Battle interface with card scanning simulation

### 🔄 Phase 3: Hardware Integration (IN PROGRESS)
**Status**: 75% Complete - Console Ready, NFC Hardware Pending

**Implemented Features**:
- ✅ Console device registration and authentication
- ✅ QR code login flow for consoles
- ✅ Console kiosk mode with fullscreen experience
- ✅ Card scanning simulation (Q/W/E keys)
- ✅ Console-to-server communication via WebSocket
- ✅ Device management admin tools
- ✅ Video background support for arenas
- ❌ Physical NFC card verification (hardware pending)

**Active Services**:
- All previous services fully integrated
- `console/` - Godot client application (COMPLETE)
- Console kiosk deployment system (COMPLETE)

**Current Status**:
- ✅ Console application fully functional
- ✅ Kiosk mode deployment ready
- ✅ Card scanning simulation working
- ❌ Physical NFC hardware integration pending

### 📋 Phase 4: Advanced Features (PLANNED)
**Status**: 20% Complete - Basic Features Implemented

**Planned Features**:
- 📋 Video calls during matches (LiveKit integration)
- 📋 TURN server for NAT traversal
- 📋 Over-the-air update system for consoles
- 📋 Signed update packages
- 📋 Advanced tournament management
- ✅ Advanced admin monitoring (85% complete)

**Future Services**:
- LiveKit integration for video calls
- TURN server for connectivity
- Update distribution system
- Tournament management system

**Development Priority**:
- 🔥 Complete Phase 3 NFC integration first
- 📋 Tournament system implementation
- 📋 Video call integration
- 📋 Advanced analytics and reporting

---

## Service Communication

### API Gateway Pattern
```
Internet → NGINX → {
  api.deckport.ai → API Service
  app.deckport.ai → Frontend Service  
  ws.deckport.ai → Realtime Service
}
```

### Internal Communication
- **HTTP REST**: API ↔ Frontend, API ↔ Console-Bridge
- **WebSocket**: Frontend ↔ Realtime, Console ↔ Realtime
- **Database**: All services → PostgreSQL
- **Cache**: Realtime → Redis (Phase 2+)
- **Message Queue**: Services → Redis/PostgreSQL (Phase 2+)

---

## Development Workflow

### Phase 1 Setup (Current Priority)
```bash
# 1. Set up shared models and database
cd /home/jp/deckport.ai
mkdir -p shared/{models,auth,database,utils}
mkdir -p services/{api,frontend,realtime,console-bridge}

# 2. Move existing code to new structure
mv api/* services/api/
mv frontend/* services/frontend/

# 3. Create shared database models
# 4. Implement user authentication
# 5. Build card catalog with real data
# 6. Create basic game mechanics
```

### Development Commands
```bash
# Start development environment
make dev-start

# Run tests
make test

# Database migrations
make db-migrate
make db-upgrade

# Deploy to staging
make deploy-staging
```

---

## Configuration Management

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Authentication
JWT_SECRET_KEY=...
JWT_ALGORITHM=RS256

# External Services
LIVEKIT_API_KEY=...
LIVEKIT_SECRET=...

# NFC Configuration
NFC_ISSUER_KEYS=...

# Service URLs
API_BASE_URL=https://api.deckport.ai
REALTIME_URL=wss://ws.deckport.ai
```

### Service Configuration
- Each service has its own `requirements.txt`
- Shared dependencies in root `requirements.txt`
- Environment-specific configs in `config/`
- Secrets managed via environment variables

---

## Database Schema

### Core Tables (Phase 1)
- `users` - User accounts and profiles
- `card_catalog` - Card definitions
- `user_cards` - Card ownership
- `matches` - Game matches
- `match_participants` - Match players
- `decks` - User deck configurations

### Extended Tables (Phase 2+)
- `consoles` - Registered devices
- `nfc_cards` - Physical card instances
- `card_batches` - Provisioning batches
- `console_login_tokens` - QR login flow
- `console_updates` - OTA update management

---

## Testing Strategy

### Unit Tests
- Each service has comprehensive unit tests
- Shared code has dedicated test suites
- Mock external dependencies

### Integration Tests
- API endpoint testing
- Database integration tests
- Service-to-service communication

### End-to-End Tests
- Full user workflows
- Multi-service scenarios
- Console integration tests

---

## Deployment Strategy

### Development
- Local development with `docker-compose`
- Hot reloading for rapid iteration
- Local database and Redis

### Staging
- Kubernetes cluster
- Automated deployment from `main` branch
- Production-like environment

### Production
- Kubernetes with proper scaling
- Database backups and monitoring
- Blue-green deployments
- Comprehensive logging and metrics

---

## Security Considerations

### Authentication
- JWT tokens with RS256 signing
- Device certificates for consoles
- Rate limiting on auth endpoints

### Data Protection
- Encrypted database connections
- Secrets management
- HTTPS/WSS everywhere

### NFC Security
- NTAG 424 DNA verification
- Server-side key management
- Secure provisioning workflow

---

## Monitoring & Observability

### Logging
- Structured JSON logging
- Centralized log aggregation
- Request tracing across services

### Metrics
- Prometheus metrics collection
- Grafana dashboards
- Service health monitoring

### Alerting
- Critical system alerts
- Performance degradation warnings
- Security incident notifications

---

## Next Actions

### Immediate (This Week)
1. **Restructure Project**: Move files to new structure
2. **Shared Models**: Create database models in `shared/models/`
3. **User Authentication**: Implement JWT-based auth in API
4. **Database Integration**: Replace mock data with real queries
5. **Basic Game Logic**: Implement turn-based gameplay

### Phase 1 Completion Criteria
- [ ] Users can register, login, and manage profiles
- [ ] Card catalog loads from database with filtering
- [ ] Basic deck building interface works
- [ ] Turn-based matches can be played in browser
- [ ] Admin panel for user and card management
- [ ] All endpoints properly authenticated and tested

**Ready to start Phase 1 implementation!** 🚀
