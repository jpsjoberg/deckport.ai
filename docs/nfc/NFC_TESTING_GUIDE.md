# 🧪 NFC Card System Testing Guide

## 🎯 **TESTING OVERVIEW**

This guide provides comprehensive testing procedures for the NTAG 424 DNA card system, from database setup to end-to-end user workflows.

---

## 🗄️ **DATABASE TESTING**

### **1. Run Migration**
```bash
# Connect to PostgreSQL
psql -h localhost -U deckport_app -d deckport

# Run the migration
\i migrations/nfc_trading_system_migration.sql

# Verify tables were created
\dt enhanced_nfc_cards
\dt card_activation_codes
\dt card_trades
\dt card_public_pages
\dt card_upgrades
\dt nfc_security_logs
\dt card_batches
```

### **2. Verify Sample Data**
```sql
-- Check sample batches
SELECT * FROM card_batches;

-- Check sample cards
SELECT * FROM enhanced_nfc_cards;

-- Check activation codes
SELECT nfc_card_id, activation_code, expires_at FROM card_activation_codes;
```

### **3. Test Constraints**
```sql
-- Test unique constraints
INSERT INTO enhanced_nfc_cards (ntag_uid, product_sku) 
VALUES ('04523AB2C1800001', 'TEST-001'); -- Should fail (duplicate UID)

-- Test foreign key constraints
INSERT INTO card_trades (seller_player_id, nfc_card_id, trade_code) 
VALUES (999, 1, 'TEST123'); -- Should fail (invalid player_id)

-- Test check constraints
INSERT INTO card_trades (asking_price) VALUES (-10); -- Should fail (negative price)
```

---

## 🔌 **API TESTING**

### **1. Start API Server**
```bash
cd services/api
python -m gunicorn --workers 1 --bind 127.0.0.1:8002 wsgi:app --reload
```

### **2. Test Admin Endpoints**

#### **Create Card Batch**
```bash
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/admin/batches \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_code": "TEST-BATCH-001",
    "product_sku": "RADIANT-001",
    "production_date": "2025-01-20T10:00:00Z",
    "total_cards": 10
  }'
```

#### **Program Card**
```bash
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/admin/program \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ntag_uid": "04AA11BB22CC33DD",
    "product_sku": "RADIANT-001",
    "batch_id": 1,
    "serial_number": "TEST-001-001",
    "issuer_key_ref": "abc123def456",
    "security_level": "MOCK"
  }'
```

### **3. Test Player Endpoints**

#### **Activate Card**
```bash
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/activate \
  -H "Authorization: Bearer YOUR_PLAYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "04523AB2C1800001",
    "activation_code": "12345678"
  }'
```

#### **Initiate Trade**
```bash
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/trade/initiate \
  -H "Authorization: Bearer YOUR_PLAYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_card_id": 1,
    "asking_price": 25.00
  }'
```

### **4. Test Console Authentication**
```bash
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/authenticate \
  -H "X-Device-UID: TEST_CONSOLE_001" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "04523AB2C1800001",
    "challenge": "YWJjZGVmZ2hpams=",
    "response": "bXl0ZXN0cmVzcG9uc2U=",
    "console_id": 1
  }'
```

### **5. Test Public Pages**
```bash
# View public card page
curl http://127.0.0.1:8002/v1/nfc-cards/public/radiant-001-1
```

---

## 🖥️ **LOCAL PROGRAMMING SCRIPT TESTING**

### **1. Setup Environment**
```bash
# Install dependencies
pip install requests cryptography

# Set environment variables
export ADMIN_TOKEN="your_admin_jwt_token"
export API_URL="http://127.0.0.1:8002"
```

### **2. Test Mock Programming**
```bash
# Run in interactive mode
python scripts/nfc_card_programmer.py \
  --product-sku RADIANT-001 \
  --batch-size 5 \
  --interactive

# Run batch mode
python scripts/nfc_card_programmer.py \
  --product-sku AZURE-014 \
  --batch-size 10 \
  --batch-code TEST-BATCH-002
```

### **3. Verify Programming Results**
```sql
-- Check programmed cards
SELECT ntag_uid, product_sku, serial_number, status 
FROM enhanced_nfc_cards 
WHERE batch_id = (SELECT id FROM card_batches WHERE batch_code = 'TEST-BATCH-002');

-- Check activation codes
SELECT c.ntag_uid, ac.activation_code, ac.expires_at
FROM enhanced_nfc_cards c
JOIN card_activation_codes ac ON c.id = ac.nfc_card_id
WHERE c.batch_id = (SELECT id FROM card_batches WHERE batch_code = 'TEST-BATCH-002');
```

---

## 📱 **MOBILE APP TESTING (Future)**

### **1. NFC Reading Test**
- Place NTAG 424 DNA card on NFC-enabled phone
- Verify UID is read correctly
- Test with multiple card types (NTAG 424 DNA, NTAG 213, etc.)

### **2. Activation Flow Test**
1. Scan card with mobile app
2. Enter 8-digit activation code
3. Verify card is activated in database
4. Check public page is created

### **3. Trading Flow Test**
1. Initiate trade from mobile app
2. Generate trade code
3. Second user scans card + enters trade code
4. Verify ownership transfer

---

## 🎮 **CONSOLE INTEGRATION TESTING**

### **1. Update Godot NFC Manager**
```gdscript
# Test authentication flow
func test_card_authentication():
    var nfc_uid = "04523AB2C1800001"
    var challenge = "test_challenge_123"
    var response = "test_response_456"
    
    var auth_result = await authenticate_card_with_server(nfc_uid, challenge, response)
    
    if auth_result.success:
        print("✅ Card authenticated successfully")
        print("Player: ", auth_result.player_data.username)
        print("Card: ", auth_result.card_data.product_sku)
    else:
        print("❌ Authentication failed: ", auth_result.error)
```

### **2. Test Battle Integration**
```gdscript
# Test card usage in battle
func test_card_in_battle():
    var card_data = {
        "id": 1,
        "product_sku": "RADIANT-001",
        "owner_id": 123,
        "authenticated": true
    }
    
    # Simulate card play
    var can_play = try_play_card(card_data)
    print("Can play card: ", can_play)
```

---

## 🔒 **SECURITY TESTING**

### **1. Authentication Testing**
```bash
# Test invalid activation code
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/activate \
  -H "Authorization: Bearer YOUR_PLAYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "04523AB2C1800001",
    "activation_code": "99999999"
  }'
# Should return 400 error

# Test expired activation code
# (Manually set expires_at to past date in database)

# Test card not found
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/activate \
  -H "Authorization: Bearer YOUR_PLAYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "INVALID_UID_123",
    "activation_code": "12345678"
  }'
# Should return 404 error
```

### **2. Trading Security Testing**
```bash
# Test self-trading prevention
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/trade/complete \
  -H "Authorization: Bearer SAME_PLAYER_TOKEN_AS_SELLER" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "04523AB2C1800001",
    "trade_code": "ABC123DEF456"
  }'
# Should return 400 error

# Test card mismatch
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/trade/complete \
  -H "Authorization: Bearer YOUR_PLAYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "WRONG_CARD_UID",
    "trade_code": "ABC123DEF456"
  }'
# Should return 400 error
```

### **3. Clone Detection Testing**
```sql
-- Simulate clone attempt (same UID, different issuer_key_ref)
INSERT INTO enhanced_nfc_cards (ntag_uid, product_sku, issuer_key_ref) 
VALUES ('04523AB2C1800001', 'RADIANT-001', 'different_key_ref');
-- Should be detected by authentication system
```

---

## 📊 **PERFORMANCE TESTING**

### **1. Database Performance**
```sql
-- Test query performance with indexes
EXPLAIN ANALYZE SELECT * FROM enhanced_nfc_cards WHERE ntag_uid = '04523AB2C1800001';
EXPLAIN ANALYZE SELECT * FROM card_trades WHERE status = 'pending' AND expires_at > NOW();
EXPLAIN ANALYZE SELECT * FROM nfc_security_logs WHERE event_type = 'auth_success' ORDER BY timestamp DESC LIMIT 100;
```

### **2. API Performance**
```bash
# Use Apache Bench to test API performance
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8002/v1/nfc-cards/public/radiant-001-1

# Test concurrent card activations
for i in {1..10}; do
  curl -X POST http://127.0.0.1:8002/v1/nfc-cards/activate \
    -H "Authorization: Bearer YOUR_PLAYER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"nfc_uid\": \"TEST_UID_$i\", \"activation_code\": \"1234567$i\"}" &
done
wait
```

---

## 🐛 **ERROR HANDLING TESTING**

### **1. Network Failures**
```bash
# Test API timeout
curl --max-time 1 http://127.0.0.1:8002/v1/nfc-cards/activate

# Test invalid JSON
curl -X POST http://127.0.0.1:8002/v1/nfc-cards/activate \
  -H "Content-Type: application/json" \
  -d 'invalid json data'
```

### **2. Database Failures**
```sql
-- Simulate database connection failure
-- (Stop PostgreSQL service temporarily)

-- Test with missing foreign key references
INSERT INTO card_trades (seller_player_id, nfc_card_id, trade_code) 
VALUES (999999, 999999, 'TEST123');
```

---

## ✅ **SUCCESS CRITERIA**

### **Database Tests**
- [ ] All tables created successfully
- [ ] All indexes created and working
- [ ] All constraints enforced correctly
- [ ] Sample data inserted without errors

### **API Tests**
- [ ] All endpoints return correct HTTP status codes
- [ ] Authentication works for admin and player endpoints
- [ ] Error handling returns appropriate error messages
- [ ] Response times under 200ms for simple queries

### **Security Tests**
- [ ] Invalid activation codes rejected
- [ ] Expired codes rejected
- [ ] Clone attempts detected and logged
- [ ] Trading security measures work correctly

### **Performance Tests**
- [ ] Database queries use indexes efficiently
- [ ] API handles 100+ concurrent requests
- [ ] Memory usage stays under 500MB
- [ ] No memory leaks during extended testing

### **Integration Tests**
- [ ] End-to-end card lifecycle works (program → sell → activate → trade)
- [ ] Console authentication works with real cards
- [ ] Mobile app can read and activate cards
- [ ] Public pages display correctly

---

## 🚀 **NEXT STEPS AFTER TESTING**

1. **Fix Issues**: Address any bugs found during testing
2. **Performance Optimization**: Optimize slow queries and endpoints
3. **Security Hardening**: Implement additional security measures
4. **Documentation**: Update API documentation with test results
5. **Beta Testing**: Deploy to staging environment for user testing

This comprehensive testing guide ensures the NFC card system is **secure, performant, and reliable** before production deployment! 🎯
