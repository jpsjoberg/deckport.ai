# 🧪 Video Streaming System Testing Guide

This guide provides comprehensive testing procedures for the video streaming system, including battle streaming and admin surveillance features.

## 📋 Prerequisites

### 1. Database Setup
```bash
# Apply database migrations
psql -h 127.0.0.1 -U deckport_app -d deckport -f database_migration_video_streaming.sql
```

### 2. API Server Running
```bash
# Start the API server
cd services/api
source venv/bin/activate
python wsgi.py
```

### 3. Frontend Server Running
```bash
# Start the frontend server
cd frontend
python app.py
```

### 4. Console Application
- Godot console application should be running
- Device should be registered and authenticated

## 🔧 Automated Testing

### Run the Test Suite
```bash
# Make the test script executable
chmod +x test_video_streaming.py

# Run all tests
python test_video_streaming.py

# Or test against a different server
python test_video_streaming.py http://your-server:8002
```

### Expected Results
- ✅ All API endpoints should respond correctly
- ✅ Arena system should load sample arenas
- ✅ Battle streaming should start/stop successfully
- ✅ Admin surveillance should work with proper authentication
- ✅ Security logging should capture all events

## 🎮 Manual Testing Procedures

### 1. Arena System Testing

#### Test Arena List
```bash
curl -X GET "http://127.0.0.1:8002/v1/arenas/list" | jq
```

**Expected Result:**
- Returns list of 10 sample arenas
- Each arena has id, name, theme, rarity, difficulty
- Pagination info included

#### Test Weighted Arena Selection
```bash
curl -X POST "http://127.0.0.1:8002/v1/arenas/weighted" \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_themes": ["nature", "crystal"],
    "preferred_rarities": ["rare", "epic"],
    "difficulty_preference": 5,
    "player_level": 10
  }' | jq
```

**Expected Result:**
- Returns a single arena based on preferences
- Arena should match preferred themes/rarities when possible

### 2. Battle Video Streaming Testing

#### Start Battle Stream
```bash
curl -X POST "http://127.0.0.1:8002/v1/video/battle/start" \
  -H "Content-Type: application/json" \
  -H "X-Device-UID: DECK_TEST_CONSOLE_01" \
  -d '{
    "opponent_console_id": 999,
    "battle_id": "test_battle_123",
    "enable_camera": false,
    "enable_screen_share": true,
    "enable_audio": false
  }' | jq
```

**Expected Result:**
- Returns stream_id, stream_url, rtmp_key
- Status should be "starting"
- Recording should be enabled

#### Check Stream Status
```bash
# Use the stream_id from previous response
curl -X GET "http://127.0.0.1:8002/v1/video/STREAM_ID/status" | jq
```

**Expected Result:**
- Shows stream details and participants
- Status should be "starting" or "active"

#### End Stream
```bash
curl -X POST "http://127.0.0.1:8002/v1/video/STREAM_ID/end" | jq
```

**Expected Result:**
- Status changes to "ended"
- Duration_seconds calculated
- Recording path provided

### 3. Admin Surveillance Testing

#### Get Admin Token
First, log in as admin through the web interface:
1. Go to `http://127.0.0.1:5000/admin/login`
2. Login with admin credentials
3. Extract the JWT token from browser dev tools or session

#### Start Surveillance
```bash
curl -X POST "http://127.0.0.1:8002/v1/video/admin/surveillance/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "console_id": 1,
    "reason": "Security testing",
    "enable_audio": true
  }' | jq
```

**Expected Result:**
- Returns surveillance stream_id
- Surveillance_url provided
- Recording automatically enabled

#### View Active Streams
```bash
curl -X GET "http://127.0.0.1:8002/v1/video/admin/active-streams" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" | jq
```

**Expected Result:**
- Lists all active video streams
- Shows both battle and surveillance streams

#### Get Stream Logs
```bash
curl -X GET "http://127.0.0.1:8002/v1/video/STREAM_ID/logs" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" | jq
```

**Expected Result:**
- Returns detailed event logs
- Shows stream creation, participant joins, etc.
- Security data included for surveillance streams

### 4. Console Application Testing

#### Test Battle Scene
1. Start the Godot console application
2. Complete QR login process
3. Navigate to Player Menu
4. Press "1" to Open Portal
5. Battle scene should load with:
   - Dynamic arena selection
   - Arena background video (or fallback animation)
   - Video streaming controls
   - Battle action buttons

#### Test Video Streaming in Battle
1. In battle scene, click "Enable Video Streaming"
2. Should see:
   - Video container becomes visible
   - Stream connection attempt in logs
   - Status updates in UI

#### Test Surveillance Warning
1. Admin starts surveillance of the console
2. Console should show:
   - Red overlay warning
   - "ADMIN SURVEILLANCE ACTIVE" message
   - Flashing warning indicator

### 5. Admin Dashboard Testing

#### Access Surveillance Dashboard
1. Go to `http://127.0.0.1:5000/admin/surveillance`
2. Should see:
   - List of active streams
   - Available consoles
   - Start surveillance controls

#### Start Surveillance via Web Interface
1. Click "Start Surveillance" button
2. Select a console
3. Enter reason for surveillance
4. Click "Start Surveillance"
5. Should redirect to surveillance view

#### View Surveillance Stream
1. Click "View" on an active surveillance stream
2. Should see:
   - Stream information
   - Live video placeholder
   - Stream controls
   - Activity logs

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check database connection
psql -h 127.0.0.1 -U deckport_app -d deckport -c "SELECT 1;"
```

#### API Server Not Responding
```bash
# Check if API server is running
curl http://127.0.0.1:8002/v1/health

# Check server logs
journalctl -u api.service -f
```

#### Console Not Connecting
```bash
# Check console logs in Godot
# Look for device authentication errors
# Verify device_uid persistence
```

#### Video Streaming Fails
- Check camera permissions
- Verify RTMP server configuration
- Check network connectivity
- Review stream logs for errors

### Debug Commands

#### Check Database Tables
```sql
-- Check if tables were created
\dt video*
\dt arenas

-- Check sample data
SELECT * FROM arenas LIMIT 5;
SELECT * FROM video_streams;
```

#### Monitor API Logs
```bash
# Watch API logs
tail -f services/api/logs/app.log

# Watch system logs
journalctl -u api.service -f
```

#### Check Console Logs
In Godot console, look for:
- Device authentication success
- Arena loading messages
- Video streaming attempts
- Surveillance warnings

## 📊 Expected Test Results

### Successful Test Run Should Show:
- ✅ 15+ tests passing
- ✅ All API endpoints responding
- ✅ Arena system functional
- ✅ Battle streaming working
- ✅ Admin surveillance operational
- ✅ Security logging active

### Performance Benchmarks:
- Arena list: < 500ms response time
- Stream start: < 2s setup time
- Surveillance start: < 1s activation
- Database queries: < 100ms average

## 🔒 Security Validation

### Verify Security Features:
1. **Authentication**: All endpoints require proper tokens
2. **Authorization**: Admin-only endpoints reject non-admin users
3. **Logging**: All video activities are logged
4. **Notifications**: Users are warned of surveillance
5. **Recording**: All surveillance is automatically recorded
6. **Audit Trail**: Complete event history maintained

### Security Test Checklist:
- [ ] Unauthenticated requests are rejected
- [ ] Invalid tokens are rejected
- [ ] Admin surveillance requires admin role
- [ ] All video calls are logged
- [ ] Surveillance warnings are displayed
- [ ] Recordings are created and stored
- [ ] Audit logs capture all events

## 📈 Performance Testing

### Load Testing (Optional):
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test arena list endpoint
ab -n 100 -c 10 http://127.0.0.1:8002/v1/arenas/list

# Test weighted arena selection
ab -n 50 -c 5 -p arena_request.json -T application/json http://127.0.0.1:8002/v1/arenas/weighted
```

### Memory Usage:
- Monitor API server memory usage during tests
- Check for memory leaks in long-running streams
- Verify proper cleanup when streams end

## 📝 Test Documentation

After testing, document:
1. **Test Results**: Pass/fail status for each component
2. **Performance Metrics**: Response times and resource usage
3. **Issues Found**: Bugs or unexpected behavior
4. **Security Validation**: Confirmation of security features
5. **Recommendations**: Improvements or optimizations needed

## 🚀 Next Steps

After successful testing:
1. **Production Deployment**: Deploy to production environment
2. **Monitoring Setup**: Configure monitoring and alerting
3. **User Training**: Train admins on surveillance features
4. **Documentation**: Update user documentation
5. **Maintenance**: Schedule regular testing and updates
