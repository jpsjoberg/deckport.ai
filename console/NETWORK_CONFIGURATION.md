# 🌐 Deckport Console Network Configuration

## 📋 Overview

This document outlines the complete network configuration for the Deckport Console, ensuring all connections are properly set up for real-time gameplay and API data updates.

## 🔧 Network Architecture

### Service Endpoints
- **API Service (HTTP)**: `http://127.0.0.1:8002`
- **Real-time Service (WebSocket)**: `ws://127.0.0.1:8003`
- **Frontend Service**: `http://127.0.0.1:8001` (for admin/web interface)

### Console Configuration Files
- `scripts/NetworkClient.gd`: Main network client with all endpoints
- `nfc_manager.gd`: NFC card authentication endpoints
- `server_logger.gd`: Real-time logging endpoints
- `game_state_manager.gd`: Game state synchronization

## ✅ Verified API Endpoints

### Core API (Port 8002)
| Endpoint | Method | Purpose | Status |
|----------|--------|---------|---------|
| `/health` | GET | Service health check | ✅ Working |
| `/v1/console/logs` | POST | Real-time console logging | ✅ Working |
| `/v1/gameplay/queue/status` | GET | Matchmaking queue status | ✅ Working |
| `/v1/gameplay/queue/join` | POST | Join matchmaking queue | ✅ Working |
| `/v1/gameplay/queue/leave` | POST | Leave matchmaking queue | ✅ Working |
| `/v1/gameplay/matches/{id}/start` | POST | Start match | ✅ Working |
| `/v1/gameplay/matches/{id}/state` | GET | Get match state | ✅ Working |
| `/v1/nfc-cards/authenticate` | POST | NFC card authentication | ✅ Working* |

*Requires proper authentication headers

### WebSocket Real-time (Port 8003)
| Message Type | Direction | Purpose | Status |
|--------------|-----------|---------|---------|
| `ping/pong` | Bidirectional | Connection keepalive | ✅ Working |
| `queue.join` | Console → Server | Join matchmaking | ✅ Working |
| `match.found` | Server → Console | Match found notification | ✅ Working |
| `match.start` | Server → Console | Match start signal | ✅ Working |
| `state.update` | Bidirectional | Game state sync | ✅ Working |
| `card.play` | Console → Server | Card play action | ✅ Working |
| `timer.tick` | Server → Console | Turn timer updates | ✅ Working |

## 🔐 Authentication Flow

### Device Authentication
1. Console registers with unique device UID
2. Server validates device and issues JWT token
3. Token used for all subsequent API calls
4. WebSocket connection authenticated via token

### Player Authentication
1. Player scans QR code or uses NFC card
2. Console sends authentication request to server
3. Server validates and returns player session data
4. Session maintained throughout gameplay

## 🎮 Real-time Gameplay Flow

### Matchmaking Process
```
Console → API: Join queue (/v1/gameplay/queue/join)
Console ← WebSocket: Queue confirmation (queue.ack)
Console ← WebSocket: Match found (match.found)
Console → WebSocket: Ready signal (match.ready)
Console ← WebSocket: Match start (match.start)
```

### Battle Synchronization
```
Console → WebSocket: Card play (card.play)
Console ← WebSocket: State update (state.update)
Console ← WebSocket: Timer tick (timer.tick)
Console → API: Get match state (/v1/gameplay/matches/{id}/state)
```

### NFC Card Integration
```
Console → NFC Reader: Scan card
Console → API: Authenticate card (/v1/nfc-cards/authenticate)
Console ← API: Card validation result
Console → WebSocket: Card play action (card.play)
```

## 📊 Connection Monitoring

### Health Checks
- **API Health**: Automated health checks every 30 seconds
- **WebSocket Keepalive**: Ping/pong every 10 seconds
- **Connection Recovery**: Automatic reconnection on failure
- **Timeout Handling**: 5-second timeouts with 3 retry attempts

### Logging & Monitoring
- **Real-time Logging**: All events sent to server via `/v1/console/logs`
- **Performance Metrics**: Network latency and response times tracked
- **Error Reporting**: Network errors automatically logged and reported
- **Connection Status**: Real-time connection status monitoring

## 🔧 Configuration Files

### NetworkClient.gd Configuration
```gdscript
# Server endpoints
var server_url: String = "http://127.0.0.1:8002"
var websocket_url: String = "ws://127.0.0.1:8003"

# Connection settings
var max_reconnect_attempts: int = 5
var reconnect_delay: float = 2.0
var request_timeout: float = 5.0
```

### NFC Manager Configuration
```gdscript
# API configuration
var api_base_url: String = "http://127.0.0.1:8002"
var nfc_auth_endpoint: String = "/v1/nfc-cards/authenticate"
```

### Server Logger Configuration
```gdscript
# Logging configuration
var server_url = "http://127.0.0.1:8002"
var log_endpoint = "/v1/console/logs"
var batch_size = 10
var send_interval = 5.0
```

## 🚀 Production Deployment

### Network Requirements
- **Bandwidth**: Minimum 1 Mbps for real-time gameplay
- **Latency**: < 100ms to server for optimal experience
- **Stability**: Stable internet connection required
- **Ports**: Outbound access to ports 8002 (HTTP) and 8003 (WebSocket)

### Security Considerations
- **HTTPS/WSS**: Use encrypted connections in production
- **Authentication**: JWT tokens with expiration
- **Rate Limiting**: Server-side rate limiting implemented
- **Input Validation**: All inputs validated on server side

### Monitoring & Alerts
- **Connection Status**: Real-time monitoring dashboard
- **Performance Metrics**: Latency and throughput tracking
- **Error Alerts**: Automatic alerts for connection failures
- **Health Checks**: Continuous service health monitoring

## 🔍 Troubleshooting

### Common Issues

#### API Connection Failures
- **Symptom**: HTTP requests failing or timing out
- **Solution**: Check service status, network connectivity
- **Command**: `curl http://127.0.0.1:8002/health`

#### WebSocket Connection Issues
- **Symptom**: Real-time features not working
- **Solution**: Verify WebSocket service, check authentication
- **Command**: `systemctl status realtime.service`

#### NFC Authentication Errors
- **Symptom**: Card scanning fails or returns errors
- **Solution**: Check NFC endpoint configuration, verify card data
- **Endpoint**: `/v1/nfc-cards/authenticate`

### Diagnostic Commands
```bash
# Check service status
sudo systemctl status api.service realtime.service

# Test API connectivity
curl http://127.0.0.1:8002/health

# Test WebSocket service
curl http://127.0.0.1:8003/health

# Run connection verification
python3 /home/jp/deckport.ai/console/verify_connections.py
```

## 📞 Support

### Development Team
- **Network Issues**: Check service logs and connection status
- **API Problems**: Verify endpoint configuration and authentication
- **Real-time Issues**: Check WebSocket service and message handling
- **Performance**: Monitor network metrics and optimize as needed

---

**Last Updated**: December 28, 2024  
**Status**: ✅ Production Ready - All Core Connections Verified  
**Next Review**: Monitor performance metrics and connection stability
