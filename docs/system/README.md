# 🔧 System Documentation

**Last Updated**: September 13, 2025  
**Status**: Production Ready with Advanced Features ✅

## 📋 System Overview

This section contains infrastructure, deployment, and system administration documentation for the Deckport.ai platform.

## 🚀 Production Systems

### Core Services (Production Ready)
- **API Service**: Backend API running on port 8002 ✅
- **Frontend Service**: Web interface running on port 8001 ✅
- **Realtime Service**: WebSocket multiplayer service ✅
- **Database**: PostgreSQL with comprehensive schema ✅
- **Authentication**: JWT-based authentication system ✅
- **Console System**: Godot kiosk mode consoles ✅

### Infrastructure
- **Systemd Services**: Service management and monitoring
- **Environment Configuration**: Production environment setup
- **SSL/TLS**: Secure communication protocols
- **Monitoring**: Health checks and system metrics

## 🔐 Authentication & Security

### Authentication System
- **Player Authentication**: JWT tokens for user sessions
- **Admin Authentication**: Elevated permissions for admin users
- **NFC Security**: NTAG 424 DNA cryptographic security
- **API Security**: Rate limiting and input validation

### Security Features
- **Password Hashing**: Secure password storage
- **Session Management**: Secure session handling
- **CSRF Protection**: Cross-site request forgery prevention
- **Input Validation**: Comprehensive data validation

## 💳 Payment Integration

### Stripe Integration
- **Payment Processing**: Secure payment handling
- **Webhook Management**: Real-time payment notifications
- **Subscription Support**: Recurring payment capabilities
- **Refund Processing**: Automated refund handling

## 🧪 Testing & Development

### Local Development
- **Development Setup**: Local environment configuration
- **Testing Framework**: Comprehensive test suite
- **Database Migrations**: Schema management and updates
- **API Testing**: Endpoint validation and testing

## 📚 Documentation Files

- [Authentication System](AUTHENTICATION_SYSTEM.md) - JWT and security implementation
- [Systemd Services](SYSTEMD_SERVICES.md) - Service configuration and management
- [Local Testing](LOCAL_TESTING.md) - Development environment setup
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing procedures

## 🔗 Related Documentation

- [Admin Panel](../admin/README.md) - Administrative interface
- [NFC System](../nfc/README.md) - NFC card integration
- [Development](../development/README.md) - Development documentation

## 🎯 Quick Reference

### Service Management
```bash
# Check service status
sudo systemctl status api.service
sudo systemctl status frontend.service

# Restart services
sudo systemctl restart api.service
sudo systemctl restart frontend.service

# View logs
sudo journalctl -u api.service -f
```

### Database Operations
```bash
# Connect to database
psql -h localhost -U deckport_user -d deckport_db

# Run migrations
python3 run_migration.py migrations/filename.sql
```

### Health Checks
- **API Health**: `http://localhost:8002/health`
- **Frontend**: `http://localhost:8001/`
- **Database**: Connection status via API health endpoint
