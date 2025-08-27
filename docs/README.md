# 📚 Deckport.ai Documentation

**Last Updated**: August 25, 2025  
**Status**: Production Ready ✅

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
- Card system redesign and implementation
- Console integration and gameplay
- Technical architecture documentation
- **Status**: Active Development 🔄

### 🔧 [System](system/)
Infrastructure, deployment, and system administration
- Authentication and security systems
- Service management and monitoring
- Payment integration (Stripe)
- **Status**: Production Ready ✅

## 🏗️ System Architecture

### Core Services
- **API Service** (Port 8002): Backend API with comprehensive endpoints
- **Frontend Service** (Port 8001): Web interface and user portal
- **Database**: PostgreSQL with full schema and migrations
- **NFC Integration**: NTAG 424 DNA card system

### Key Features
- **Authentication**: JWT-based player and admin authentication
- **Shop System**: E-commerce with Stripe payment processing
- **Admin Panel**: Comprehensive administrative interface
- **NFC Cards**: Secure physical-digital card integration
- **Real-time Data**: Live analytics and monitoring

## 🔗 External Resources

- **Main README**: [../README.md](../README.md) - Project overview and setup
- **API Health**: http://localhost:8002/health
- **Frontend**: http://localhost:8001/
- **Admin Panel**: Accessible through main application

## 📊 Current Status

| Component | Status | Last Updated |
|-----------|--------|--------------|
| Admin Panel | ✅ Production Ready | Aug 25, 2025 |
| NFC System | ✅ Production Ready | Aug 25, 2025 |
| Shop System | ✅ Production Ready | Aug 25, 2025 |
| Authentication | ✅ Production Ready | Aug 25, 2025 |
| Game Engine | 🔄 In Development | Aug 25, 2025 |

## 🎯 Getting Help

1. **Technical Issues**: Check the relevant section documentation
2. **System Status**: Review service health endpoints
3. **Development**: See development documentation and testing guides
4. **Production Issues**: Consult admin panel and system monitoring

---

*This documentation is automatically maintained and reflects the current production state of the Deckport.ai platform.*
