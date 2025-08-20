# Local Testing Guide for Deckport.ai

This guide explains how to test your Deckport.ai server from your local development machine.

## 🛠️ Setup (One-time)

### 1. Download Test Scripts
```bash
# Download the test client from your server
scp user@your-server:/home/jp/deckport.ai/scripts/local_test_client.py .
scp user@your-server:/home/jp/deckport.ai/scripts/setup_local_testing.sh .
scp user@your-server:/home/jp/deckport.ai/scripts/requirements-test-client.txt .

# Or clone if you have a git repository
git clone your-repo-url
cd deckport-console  # or deckport-server
```

### 2. Setup Local Environment
```bash
# Run setup script
chmod +x setup_local_testing.sh
./setup_local_testing.sh

# Activate test environment
source deckport-test-env/bin/activate
```

## 🧪 Testing Your Server

### Basic Server Test
```bash
# Test all components
python local_test_client.py --server YOUR_SERVER_IP

# Example output:
🌐 Test Client Configuration:
   Server: 192.168.1.100
   API: http://192.168.1.100:8002
   WebSocket: ws://192.168.1.100:8003/ws
   Frontend: http://192.168.1.100:5000

📡 Testing Server Connectivity...
✅ API Health: {'status': 'ok', 'database': 'connected'}
✅ Realtime Health: {'status': 'ok', 'connections': 0}

🔌 Testing API Endpoints...
✅ Card Catalog: 5 cards available
✅ Card Details: Solar Vanguard loaded successfully

🔐 Testing User Authentication...
✅ Registration: User created successfully
✅ JWT Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...

🔌 Testing WebSocket Connection...
✅ WebSocket: Connected successfully
📨 Welcome: connected (connection_id: conn_1642534567.123_0)
🏓 Ping/Pong: pong received

🎯 Testing Matchmaking System...
✅ Queue Joined: Mode 1v1
⏰ No match found within timeout (expected with 1 player)
👋 Queue Left: {'status': 'removed'}
```

### Specific Component Tests
```bash
# Test only API endpoints
python local_test_client.py --server YOUR_SERVER_IP --test-only api

# Test only WebSocket functionality
python local_test_client.py --server YOUR_SERVER_IP --test-only websocket

# Test only frontend pages
python local_test_client.py --server YOUR_SERVER_IP --test-only frontend

# Test console device authentication
python local_test_client.py --server YOUR_SERVER_IP --test-only device
```

### Interactive WebSocket Testing
```bash
# Interactive mode for manual testing
python local_test_client.py --server YOUR_SERVER_IP --interactive

# Example session:
✅ Connected to WebSocket
📨 {'type': 'connected', 'connection_id': 'conn_123', 'user_id': 1}

> ping
📤 Sent: {'type': 'ping'}
📨 {'type': 'pong'}

> queue.join
📤 Sent: {'type': 'queue.join', 'mode': '1v1'}
📨 {'type': 'queue.ack', 'mode': '1v1'}

> {"type": "custom", "data": "test"}
📤 Sent: {'type': 'custom', 'data': 'test'}
📨 {'type': 'error', 'error': 'Unknown message type: custom'}

> quit
```

## 🌐 Server Configuration

### Development Server
```bash
# Local development (same machine)
python local_test_client.py --server localhost
python local_test_client.py --server 127.0.0.1
```

### Remote Server
```bash
# Remote server by IP
python local_test_client.py --server 192.168.1.100
python local_test_client.py --server 10.0.0.50

# Remote server by hostname  
python local_test_client.py --server deckport-dev.local
```

### Production Server
```bash
# Production with HTTPS/WSS
python local_test_client.py --server deckport.ai --https

# This will test:
# API: https://api.deckport.ai
# WebSocket: wss://ws.deckport.ai/ws  
# Frontend: https://deckport.ai
```

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
ping YOUR_SERVER_IP
curl http://YOUR_SERVER_IP:8002/health
curl http://YOUR_SERVER_IP:8003/health

# Check firewall/ports
nmap -p 8002,8003,5000 YOUR_SERVER_IP
```

### Authentication Issues
```bash
# Test API registration manually
curl -X POST http://YOUR_SERVER_IP:8002/v1/auth/player/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Check if endpoints exist
curl http://YOUR_SERVER_IP:8002/v1/auth/player/login
```

### WebSocket Issues
```bash
# Test WebSocket manually with wscat (if installed)
npm install -g wscat
wscat -c "ws://YOUR_SERVER_IP:8003/ws?token=YOUR_JWT_TOKEN"
```

## 📊 What the Tests Validate

### ✅ Server Health
- API service running and responsive
- Database connectivity
- Real-time service running
- Frontend accessibility

### ✅ Authentication System
- User registration working
- Login functionality
- JWT token generation
- Token validation in WebSocket

### ✅ Real-time Communication
- WebSocket connection establishment
- Message sending/receiving
- Protocol compliance
- Error handling

### ✅ Matchmaking System
- Queue joining/leaving
- Match pairing logic
- Player notifications
- Database integration

### ✅ Game Protocol
- Message routing
- Type validation
- Error responses
- State synchronization

## 🎯 Benefits of Local Testing

### 🚀 **Faster Development**
- Test changes immediately from your local machine
- No need to SSH into server for every test
- Real-world network testing

### 🔍 **Better Debugging**
- See exact request/response data
- Monitor WebSocket messages in real-time
- Interactive testing mode

### 🛡️ **Comprehensive Validation**
- Test all components together
- Validate end-to-end flows
- Catch integration issues early

### 📈 **Production Readiness**
- Test against production-like environment
- Validate HTTPS/WSS functionality
- Performance testing under real network conditions

## 🎮 Example Test Session

```bash
# Full test run
python local_test_client.py --server 192.168.1.100

🚀 Deckport.ai Server Test Suite
==================================================

📡 Testing Server Connectivity...
✅ API Health: {'status': 'ok', 'database': 'connected'}
✅ Realtime Health: {'status': 'ok', 'connections': 0}

🔌 Testing API Endpoints...
✅ Card Catalog: 5 cards available
✅ Card Details: Solar Vanguard loaded successfully

🔐 Testing User Authentication...
✅ Registration: User created successfully
✅ JWT Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...

🔌 Testing WebSocket Connection...
✅ WebSocket: Connected successfully
📨 Welcome: connected (connection_id: conn_1642534567.123_0)
🏓 Ping/Pong: pong received

🎯 Testing Matchmaking System...
✅ Queue Joined: Mode 1v1
⏰ No match found within timeout (expected with 1 player)
👋 Queue Left: removed

🎉 Test suite completed!
```

**Perfect for testing your server from anywhere!** 🌐✨
