# 📚 Deckport.ai Documentation

**Last Updated**: September 13, 2025  
**Status**: 🚀 **85% Complete - Production Ready Core Systems** ✅

## 🎯 Quick Start

Welcome to the Deckport.ai documentation! This is your central hub for all technical documentation, guides, and system information.

### 🚀 For New Developers
1. Read the [Project Structure](PROJECT_STRUCTURE.md) for system architecture
2. Set up your [Local Development Environment](system/LOCAL_TESTING.md)
3. Review the [Authentication System](system/AUTHENTICATION_SYSTEM.md)
4. Explore the [API Documentation](../README.md#api-endpoints)

### 🛡️ For Administrators
1. Access the [Admin Panel Documentation](admin/README.md)
2. Review [System Services](system/SYSTEMD_SERVICES.md)
3. Check [Testing Procedures](system/TESTING_GUIDE.md)

## 📋 Documentation Sections

### 🛡️ [Admin Panel](admin/)
Complete administrative interface documentation
- Production-ready admin dashboard
- User and content management
- System monitoring and analytics
- **Status**: Production Ready ✅

### 🃏 [NFC Card System](nfc/)
Physical-digital card integration with NTAG 424 DNA
- Secure card programming and authentication
- Trading and marketplace functionality
- Production deployment guides
- **Status**: Production Ready ✅

### 🎮 [Development](development/)
Game development and card system architecture
- Card system redesign and implementation (COMPLETE)
- Console integration and gameplay (85% COMPLETE)
- Battle system and multiplayer (COMPLETE)
- Technical architecture documentation
- **Status**: Near Production Ready 🚀

### 🔧 [System](system/)
Infrastructure, deployment, and system administration
- Authentication and security systems
- Service management and monitoring
- Payment integration (Stripe)
- **Status**: Production Ready ✅

## 🏗️ System Architecture

### Core Services (Production Ready)
- **API Service** (Port 8002): Backend API with comprehensive endpoints ✅
- **Frontend Service** (Port 8001): Web interface and admin portal ✅
- **Realtime Service**: WebSocket service for multiplayer gameplay ✅
- **Database**: PostgreSQL with full schema and migrations ✅
- **Console System**: Godot-based kiosk mode gaming consoles ✅

### Key Features (Current Implementation)
- **Authentication**: JWT-based player and admin authentication ✅
- **Battle System**: Real-time multiplayer card battles ✅
- **Admin Panel**: Comprehensive administrative interface (85% complete) ✅
- **Card Catalog**: 1,793 cards with AI generation system ✅
- **Console Integration**: Kiosk mode with QR login ✅
- **Security**: RBAC, audit logging, and monitoring ✅

## 🔗 External Resources

- **Main README**: [../README.md](../README.md) - Project overview and setup
- **API Health**: http://localhost:8002/health
- **Frontend**: http://localhost:8001/
- **Admin Panel**: Accessible through main application

## 📊 Current Status

| Component | Status | Last Updated |
|-----------|--------|--------------|
| Admin Panel | ✅ 85% Production Ready | Sep 13, 2025 |
| Authentication | ✅ Production Ready | Sep 13, 2025 |
| Battle System | ✅ Production Ready | Sep 13, 2025 |
| Multiplayer | ✅ Production Ready | Sep 13, 2025 |
| Console System | ✅ Production Ready | Sep 13, 2025 |
| NFC Hardware | 🔄 Hardware Pending | Sep 13, 2025 |

## 🎯 Getting Help

1. **Technical Issues**: Check the relevant section documentation
2. **System Status**: Review service health endpoints
3. **Development**: See development documentation and testing guides
4. **Production Issues**: Consult admin panel and system monitoring

---

*This documentation is automatically maintained and reflects the current production state of the Deckport.ai platform.*
