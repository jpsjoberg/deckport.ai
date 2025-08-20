# Deckport.ai Project Structure & Development Plan

## Overview
This document defines the improved project structure for Deckport.ai, designed for phased development starting with user handling and building up to the full MVP with real-time features, NFC verification, video calls, and console support.

## Core Architecture Principles

### 1. **Modular Services**
- Each service has a single responsibility
- Services communicate via well-defined APIs
- Easy to develop, test, and deploy independently

### 2. **Phased Development**
- **Phase 1**: User Management & Core Game Logic
- **Phase 2**: Real-time Features & Matchmaking
- **Phase 3**: Hardware Integration (NFC, Consoles)
- **Phase 4**: Advanced Features (Video, OTA)

### 3. **Production Ready**
- Proper configuration management
- Database migrations
- Testing framework
- CI/CD pipeline
- Monitoring and logging

---

## Project Structure

```
/home/jp/deckport.ai/
├── README.md
├── PROJECT_STRUCTURE.md          # This file
├── MVP_STATUS.md                 # Current status
├── docker-compose.yml            # Development environment
├── Makefile                      # Development commands
├── .env.example                  # Environment template
├── requirements.txt              # Shared Python requirements
│
├── config/                       # Configuration files
│   ├── nginx/
│   │   ├── api.conf
│   │   ├── frontend.conf
│   │   └── realtime.conf
│   ├── livekit/
│   │   └── livekit.yaml
│   └── systemd/
│       ├── api.service
│       ├── frontend.service
│       └── realtime.service
│
├── scripts/                      # Utility scripts
│   ├── dev-start.sh             # Development startup
│   ├── deploy.sh                # Deployment script
│   ├── migrate.sh               # Database migrations
│   ├── seed-data.py             # Sample data
│   └── nfc-provision.py         # NFC card provisioning
│
├── tests/                        # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                         # Documentation
│   ├── api/
│   ├── deployment/
│   └── development/
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

## Development Phases

### Phase 1: User Management & Core Game Logic (Week 1-2)
**Goal**: Solid foundation with user accounts and basic gameplay

**Features**:
- ✅ User registration/login with JWT
- ✅ Password hashing and validation
- ✅ User profiles and preferences
- ✅ Card catalog with database integration
- ✅ Basic deck building interface
- ✅ Turn-based game mechanics (web-based)
- ✅ Match history and statistics
- ✅ Admin panel for user/card management

**Services Active**:
- `api/` - REST API with user auth
- `frontend/` - Web interface
- PostgreSQL database

**Key Deliverables**:
- Working user authentication
- Card catalog with real database
- Basic game that can be played in browser
- Admin tools for content management

### Phase 2: Real-time Features & Matchmaking (Week 3-4)
**Goal**: Add real-time gameplay and matchmaking

**Features**:
- ✅ WebSocket service for real-time communication
- ✅ Matchmaking queue with ELO-based pairing
- ✅ Real-time game state synchronization
- ✅ Live match spectating
- ✅ In-game chat
- ✅ Push notifications

**Services Active**:
- `api/` - Enhanced with matchmaking endpoints
- `frontend/` - Real-time game interface
- `realtime/` - WebSocket service
- PostgreSQL + Redis for queues

**Key Deliverables**:
- Players can find matches automatically
- Real-time gameplay with state sync
- Live spectating capabilities
- Robust matchmaking system

### Phase 3: Hardware Integration (Week 5-6)
**Goal**: Console support and NFC card verification

**Features**:
- ✅ Console device registration and authentication
- ✅ QR code login flow for consoles
- ✅ NFC card verification (NTAG 424 DNA)
- ✅ Card provisioning and activation system
- ✅ Console-to-server communication
- ✅ Device management admin tools

**Services Active**:
- All previous services
- `console-bridge/` - Console communication service
- `console/` - Godot client application

**Key Deliverables**:
- Working console application
- Physical card scanning and verification
- Secure device authentication
- Card provisioning workflow

### Phase 4: Advanced Features (Week 7-8)
**Goal**: Video calls and over-the-air updates

**Features**:
- ✅ Video calls during matches (LiveKit)
- ✅ TURN server for NAT traversal
- ✅ OTA update system for consoles
- ✅ Signed update packages
- ✅ Console update management
- ✅ Advanced admin monitoring

**Services Active**:
- All services fully integrated
- LiveKit for video
- TURN server for connectivity
- Update distribution system

**Key Deliverables**:
- Video calls working in matches
- Automatic console updates
- Complete admin dashboard
- Production monitoring

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
