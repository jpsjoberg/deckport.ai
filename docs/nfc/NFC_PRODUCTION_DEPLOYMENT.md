# 🔒 NFC System Production Deployment Guide

**Complete production-ready NFC card system for Deckport.ai**

This guide covers deploying the secure, anti-cloning NFC card system in production environments.

---

## ✅ **Production Readiness Status**

### **🃏 Card Programming Tool**
- ✅ **Real NFC hardware** - Uses `nfcpy` library with actual readers
- ✅ **NTAG 424 DNA security** - Cryptographic key generation and programming
- ✅ **Database integration** - Links to card catalog and batch tracking
- ✅ **Hardware validation** - Checks NFC reader before programming
- ✅ **Error handling** - Comprehensive failure detection and reporting

### **🎮 Console NFC Manager**
- ✅ **Real hardware scanning** - Uses `nfc-list` and `nfc-poll` commands
- ✅ **Server authentication** - NTAG 424 DNA cryptographic verification
- ✅ **Battle integration** - Real-time card scanning during gameplay
- ✅ **Error handling** - Hardware detection and troubleshooting
- ✅ **Security logging** - Complete audit trail

### **🔐 API Security**
- ✅ **Cryptographic verification** - HMAC-SHA256 with derived keys
- ✅ **Anti-cloning protection** - Unique keys per card
- ✅ **Security logging** - Failed authentication attempts tracked
- ✅ **Master key management** - Environment variable configuration
- ✅ **Constant-time comparison** - Prevents timing attacks

---

## 🚀 **Production Deployment**

### **1. Server Environment Setup**

#### **Environment Variables**
```bash
# Add to your server environment
export NFC_MASTER_KEY="your_64_character_hex_master_key_here"
export API_BASE_URL="https://api.deckport.ai"
export CONSOLE_API_URL="http://127.0.0.1:8002"
```

#### **Master Key Generation**
```bash
# Generate secure 256-bit master key
openssl rand -hex 32 > nfc_master_key.txt
export NFC_MASTER_KEY=$(cat nfc_master_key.txt)

# Store securely (use key management service in production)
# AWS: AWS Secrets Manager
# Azure: Azure Key Vault  
# GCP: Google Secret Manager
```

#### **Database Migration**
```bash
# Apply NFC system database tables
cd /home/jp/deckport.ai
python -c "
from shared.database.connection import engine
from shared.models.nfc_trading_system import Base
Base.metadata.create_all(engine)
print('✅ NFC tables created')
"
```

### **2. Console Hardware Setup**

#### **NFC Reader Installation**
```bash
# Install NFC drivers on each console
sudo apt update
sudo apt install -y libnfc-bin libnfc-dev libusb-1.0-0-dev

# Add console user to dialout group
sudo usermod -a -G dialout deckport

# Test NFC reader
nfc-list
```

#### **Console Configuration**
```bash
# Update console environment
echo "API_BASE_URL=https://api.deckport.ai" >> /etc/environment
echo "NFC_ENABLED=true" >> /etc/environment

# Restart console service
sudo systemctl restart deckport-console
```

### **3. Card Programming Setup**

#### **Local Programming Station**
```bash
# Download programming tool
git clone https://github.com/your-org/deckport.ai.git
cd deckport.ai/tools/nfc-card-programmer

# Install dependencies
./install_nfc_dependencies.sh

# Configure API connection
export ADMIN_TOKEN="your_admin_jwt_token"
export API_URL="https://api.deckport.ai"

# Test hardware
python nfc_card_programmer.py --check-hardware
```

#### **Production Programming**
```bash
# List available cards
python nfc_card_programmer.py --list-cards

# Program production batch
python nfc_card_programmer.py \
  --product-sku RADIANT-001 \
  --batch-size 100 \
  --batch-code PRODUCTION-RADIANT-JAN2025
```

---

## 🔒 **Security Configuration**

### **Master Key Management**

#### **Development**
```bash
# Generate and store locally
openssl rand -hex 32 > master_key.txt
export NFC_MASTER_KEY=$(cat master_key.txt)
```

#### **Production**
```bash
# Use secure key management service
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "deckport/nfc-master-key" \
  --secret-string "$(openssl rand -hex 32)"

# Retrieve in application
export NFC_MASTER_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "deckport/nfc-master-key" \
  --query SecretString --output text)
```

### **Key Rotation**
```bash
# Generate new master key
NEW_KEY=$(openssl rand -hex 32)

# Update key management service
aws secretsmanager update-secret \
  --secret-id "deckport/nfc-master-key" \
  --secret-string "$NEW_KEY"

# Restart API services to pick up new key
sudo systemctl restart api.service

# Note: Existing cards will continue to work with old keys
# New cards will use the new key
```

### **Security Monitoring**
```sql
-- Monitor failed authentication attempts
SELECT 
  nfc_card_id,
  event_type,
  severity,
  COUNT(*) as attempts,
  MAX(timestamp) as last_attempt
FROM nfc_security_logs 
WHERE event_type = 'auth_failed' 
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY nfc_card_id, event_type, severity
HAVING COUNT(*) > 5;

-- Check for potential cloning attempts
SELECT 
  nfc_card_id,
  technical_data->>'console_id' as console_id,
  COUNT(*) as failed_attempts
FROM nfc_security_logs 
WHERE technical_data->>'potential_clone' = 'true'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY nfc_card_id, technical_data->>'console_id';
```

---

## 📊 **Production Monitoring**

### **Health Checks**

#### **API Endpoints**
```bash
# Test NFC authentication endpoint
curl -X POST https://api.deckport.ai/v1/nfc-cards/authenticate \
  -H "Content-Type: application/json" \
  -H "X-Device-UID: DECK_CONSOLE_001" \
  -d '{
    "nfc_uid": "04AA3AB2C1800001",
    "challenge": "base64_challenge_here",
    "response": "base64_response_here",
    "console_id": "DECK_CONSOLE_001"
  }'

# Test card catalog
curl https://api.deckport.ai/v1/catalog/cards
```

#### **Console NFC Status**
```bash
# Check NFC reader on console
nfc-list

# Test card detection
timeout 5 nfc-poll -1

# Check console logs
journalctl -u deckport-console -f | grep NFC
```

### **Performance Metrics**
```sql
-- Card authentication success rate
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as total_attempts,
  SUM(CASE WHEN event_type = 'auth_success' THEN 1 ELSE 0 END) as successful,
  ROUND(
    100.0 * SUM(CASE WHEN event_type = 'auth_success' THEN 1 ELSE 0 END) / COUNT(*), 
    2
  ) as success_rate_percent
FROM nfc_security_logs 
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Card programming statistics
SELECT 
  product_sku,
  COUNT(*) as total_programmed,
  SUM(CASE WHEN status = 'activated' THEN 1 ELSE 0 END) as activated,
  AVG(tap_counter) as avg_usage
FROM enhanced_nfc_cards 
GROUP BY product_sku
ORDER BY total_programmed DESC;
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **"NFC reader not detected"**
```bash
# Check USB connection
lsusb | grep -i nfc

# Check permissions
ls -la /dev/ttyUSB* /dev/ttyACM*

# Restart NFC service
sudo systemctl restart pcscd

# Test manually
nfc-list
```

#### **"Card authentication failed"**
```bash
# Check master key configuration
echo $NFC_MASTER_KEY | wc -c  # Should be 65 (64 hex + newline)

# Check API logs
journalctl -u api.service | grep "NTAG 424"

# Verify card was programmed correctly
python tools/nfc-card-programmer/nfc_card_programmer.py \
  --validate-sku RADIANT-001
```

#### **"Card not found in database"**
```sql
-- Check if card exists
SELECT * FROM enhanced_nfc_cards WHERE ntag_uid = '04AA3AB2C1800001';

-- Check batch status
SELECT 
  b.batch_code,
  b.total_cards,
  COUNT(c.id) as programmed_cards
FROM card_batches b
LEFT JOIN enhanced_nfc_cards c ON c.batch_id = b.id
GROUP BY b.id, b.batch_code, b.total_cards;
```

### **Security Incidents**

#### **Suspected Card Cloning**
```sql
-- Investigate suspicious activity
SELECT 
  c.ntag_uid,
  c.product_sku,
  c.serial_number,
  l.technical_data,
  l.timestamp
FROM enhanced_nfc_cards c
JOIN nfc_security_logs l ON l.nfc_card_id = c.id
WHERE l.technical_data->>'potential_clone' = 'true'
ORDER BY l.timestamp DESC;

-- Revoke compromised cards
UPDATE enhanced_nfc_cards 
SET status = 'revoked', 
    updated_at = NOW()
WHERE id IN (suspicious_card_ids);
```

#### **Mass Authentication Failures**
```bash
# Check for system-wide issues
grep "auth_failed" /var/log/api.log | tail -100

# Verify master key hasn't changed unexpectedly
echo $NFC_MASTER_KEY

# Check database connectivity
psql -d deckport -c "SELECT COUNT(*) FROM enhanced_nfc_cards;"
```

---

## 📈 **Scaling Considerations**

### **High-Volume Card Programming**
```bash
# Parallel programming stations
# Station 1: RADIANT cards
python nfc_card_programmer.py --product-sku RADIANT-001 --batch-size 100

# Station 2: AZURE cards  
python nfc_card_programmer.py --product-sku AZURE-014 --batch-size 100

# Station 3: VERDANT cards
python nfc_card_programmer.py --product-sku VERDANT-007 --batch-size 100
```

### **Multi-Console Deployment**
```bash
# Console deployment script
for console in console-001 console-002 console-003; do
  ssh $console "
    sudo apt install -y libnfc-bin libnfc-dev
    sudo usermod -a -G dialout deckport
    echo 'API_BASE_URL=https://api.deckport.ai' | sudo tee -a /etc/environment
    sudo systemctl restart deckport-console
  "
done
```

### **Database Optimization**
```sql
-- Add indexes for performance
CREATE INDEX idx_nfc_cards_uid ON enhanced_nfc_cards(ntag_uid);
CREATE INDEX idx_nfc_cards_status ON enhanced_nfc_cards(status);
CREATE INDEX idx_nfc_cards_owner ON enhanced_nfc_cards(owner_player_id);
CREATE INDEX idx_security_logs_card ON nfc_security_logs(nfc_card_id);
CREATE INDEX idx_security_logs_timestamp ON nfc_security_logs(timestamp);

-- Partition large tables by date
CREATE TABLE nfc_security_logs_2025_01 PARTITION OF nfc_security_logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

---

## 🎯 **Production Checklist**

### **Pre-Deployment**
- [ ] Master key generated and stored securely
- [ ] Database tables created and indexed
- [ ] API endpoints tested with real cards
- [ ] Console NFC hardware tested
- [ ] Card programming tool validated
- [ ] Security logging configured
- [ ] Monitoring dashboards set up

### **Go-Live**
- [ ] Deploy API with NFC_MASTER_KEY
- [ ] Update all consoles with NFC drivers
- [ ] Program initial card batches
- [ ] Test end-to-end card flow
- [ ] Monitor authentication success rates
- [ ] Verify security logging works
- [ ] Test card trading (if enabled)

### **Post-Deployment**
- [ ] Monitor authentication metrics
- [ ] Check for security incidents
- [ ] Validate card programming quality
- [ ] Review performance metrics
- [ ] Plan key rotation schedule
- [ ] Document operational procedures

---

## 🔐 **Security Best Practices**

1. **Master Key Security**
   - Use hardware security modules (HSM) in production
   - Implement key rotation every 90 days
   - Never store keys in code or config files
   - Use separate keys for different environments

2. **Network Security**
   - Use HTTPS for all API communication
   - Implement rate limiting on authentication endpoints
   - Monitor for unusual authentication patterns
   - Use VPN for console-to-server communication

3. **Physical Security**
   - Secure card programming stations
   - Control access to blank cards
   - Implement batch tracking and auditing
   - Use tamper-evident packaging for cards

4. **Operational Security**
   - Regular security audits
   - Incident response procedures
   - Staff training on security protocols
   - Regular backup and recovery testing

**The NFC system is now fully production-ready with enterprise-grade security!** 🃏🔒⚡
