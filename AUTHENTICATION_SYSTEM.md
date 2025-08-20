# Deckport.ai Authentication System

## Overview

The Deckport.ai platform uses a sophisticated **two-tier authentication system** designed for secure console hardware and seamless player experience.

## 🏗️ Architecture

### Two Authentication Tiers

#### 1. **Device Authentication** (Hardware Level)
- **Purpose**: Authenticate console hardware with server
- **Method**: RSA 2048-bit keypair + signed nonce
- **Token**: Device JWT (24-hour expiry)
- **Security**: Private keys never leave console hardware

#### 2. **Player Authentication** (User Level)
- **Purpose**: Authenticate players on console
- **Method**: QR code + phone confirmation
- **Token**: Player JWT (console-scoped)
- **UX**: No typing on console - all via phone

## 🔄 Complete Authentication Flow

### Phase 1: Device Registration (One-time Setup)
```
1. Console generates RSA keypair on first boot
2. Console → Server: Register device with public key
3. Admin → Server: Approve device via admin panel
4. Device status: "pending" → "active"
```

### Phase 2: Device Authentication (Every Boot)
```
1. Console → Console: Generate random nonce
2. Console → Console: Sign nonce with private key
3. Console → Server: Send device_uid + nonce + signature
4. Server → Server: Verify signature with stored public key
5. Server → Console: Device JWT token (24h)
```

### Phase 3: Player Login (When Player Approaches)
```
1. Console → Server: Request login token (with Device JWT)
2. Server → Console: Login token + QR URL
3. Console: Display QR code
4. Player: Scan QR → Opens login page on phone
5. Player → Server: Login with email/password
6. Player → Server: Confirm console login
7. Console → Server: Poll for confirmation
8. Server → Console: Player JWT + player info
```

## 🛡️ Security Features

### Device Security
- **RSA 2048-bit keypairs** - Industry standard encryption
- **Private keys secured** - Never transmitted or stored on server
- **Nonce-based auth** - Prevents replay attacks
- **Admin approval** - Manual device verification
- **Token expiration** - Automatic security refresh

### Player Security
- **Phone-based auth** - Familiar and secure for users
- **No console passwords** - Eliminates typing security risks
- **Short-lived tokens** - QR codes expire in 5 minutes
- **Scoped permissions** - Player tokens limited to console use
- **Audit trail** - All authentication events logged

### Network Security
- **HTTPS everywhere** - Encrypted communication
- **JWT tokens** - Stateless and verifiable
- **Rate limiting** - Prevents brute force attacks
- **Token validation** - Server-side verification

## 💻 Implementation

### Server Components

#### API Endpoints
- `POST /v1/auth/device/register` - Device registration
- `POST /v1/auth/device/login` - Device authentication
- `POST /v1/console-login/start` - Start player QR login
- `POST /v1/console-login/confirm` - Confirm from phone
- `GET /v1/console-login/poll` - Poll for confirmation

#### Files
- `services/api/routes/device_auth.py` - Device authentication
- `services/api/routes/console_login.py` - QR login flow
- `shared/auth/jwt_handler.py` - JWT token management
- `shared/models/base.py` - Database models

### Console Components

#### Godot Scripts
- `scripts/AuthManager.gd` - Complete authentication logic
- `scripts/Bootloader.gd` - Boot sequence integration
- `autoload/Global.gd` - Global state and token storage

#### Key Features
- **Automatic keypair generation** on first boot
- **Secure key storage** in user:// directory
- **Token caching** with expiration checking
- **Error handling** and retry logic
- **Development mode** support

## 🧪 Testing

### Device Authentication Test
```bash
# 1. Register device (requires admin approval)
curl -X POST http://127.0.0.1:8002/v1/auth/device/register \
  -H "Content-Type: application/json" \
  -d '{"device_uid": "TEST_DEVICE", "public_key": "..."}'

# 2. Authenticate device (after approval)
curl -X POST http://127.0.0.1:8002/v1/auth/device/login \
  -H "Content-Type: application/json" \
  -d '{"device_uid": "TEST_DEVICE", "nonce": "...", "signature": "..."}'
```

### QR Login Test
```bash
# 1. Start login (requires device JWT)
curl -X POST http://127.0.0.1:8002/v1/console-login/start \
  -H "Authorization: Bearer DEVICE_JWT"

# 2. Confirm login (requires player JWT)
curl -X POST http://127.0.0.1:8002/v1/console-login/confirm \
  -H "Authorization: Bearer PLAYER_JWT" \
  -H "Content-Type: application/json" \
  -d '{"login_token": "LOGIN_TOKEN"}'

# 3. Poll for confirmation (device)
curl http://127.0.0.1:8002/v1/console-login/poll?login_token=LOGIN_TOKEN \
  -H "Authorization: Bearer DEVICE_JWT"
```

## 📊 Database Schema

### Tables Used
- `consoles` - Device registration and public keys
- `console_login_tokens` - QR login flow tokens
- `players` - User accounts and authentication
- `audit_logs` - Authentication event logging

### Key Fields
- `consoles.device_uid` - Unique device identifier
- `consoles.public_key_pem` - RSA public key for verification
- `consoles.status` - pending/active/revoked
- `console_login_tokens.token_hash` - Hashed login tokens
- `console_login_tokens.expires_at` - Token expiration

## 🔧 Configuration

### Environment Variables
```bash
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
DATABASE_URL=postgresql://...
```

### Console Settings
```gdscript
# In Global.gd
var device_uid: String = "DECK_1642534567_1234"
var server_url: String = "https://api.deckport.ai"
var device_token: String = ""
var player_token: String = ""
```

## 🚀 Deployment

### Console Deployment
1. **Build console** with authentication system
2. **Deploy to hardware** with kiosk mode
3. **Register device** via admin panel
4. **Test authentication** flow end-to-end

### Server Deployment
1. **Deploy API** with new authentication routes
2. **Run database migrations** for auth tables
3. **Configure JWT secrets** and encryption keys
4. **Test device registration** and approval flow

## 📈 Monitoring

### Key Metrics
- Device registration requests
- Authentication success/failure rates
- Token expiration and refresh patterns
- QR login completion rates
- Security events and anomalies

### Logs
- All authentication events logged with structured data
- Device registration and approval audit trail
- Player login patterns and usage analytics
- Security events and potential threats

---

**The authentication system provides enterprise-grade security with consumer-friendly UX!** 🔐✨

## Status: ✅ Complete and Ready for Phase 3 Development
