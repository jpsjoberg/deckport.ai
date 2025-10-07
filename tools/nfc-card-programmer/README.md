# 🃏 NFC Card Programmer

**Professional NTAG 424 DNA card programming tool for Deckport.ai**

This tool allows you to program physical NFC cards with secure cryptographic keys and register them in your database. Each programmed card is linked to a specific card design from your card catalog.

---

## 📋 **Overview**

The NFC Card Programmer bridges your digital card catalog with physical NTAG 424 DNA cards:

- ✅ **Validates card designs** from your database
- 🔒 **Programs secure keys** using NTAG 424 DNA technology
- 📊 **Tracks production batches** for quality control
- 🎯 **Generates activation codes** for customer activation
- 🔐 **Anti-cloning protection** with unique cryptographic keys

---

## 🚀 **Quick Start**

### **1. Download & Setup**
```bash
# Download this folder to your local machine
# Navigate to the folder
cd tools/nfc-card-programmer

# Install dependencies (Linux/Ubuntu)
./install_nfc_dependencies.sh

# Or install manually:
pip install nfcpy cryptography requests
```

### **2. Connect Hardware**
- Connect your NFC reader via USB (ACR122U, PN532, etc.)
- Ensure drivers are installed
- Test hardware:
```bash
python nfc_card_programmer.py --check-hardware
```

### **3. Get Admin Token**
```bash
# Login to your API server to get admin JWT token
curl -X POST http://your-server:8002/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@deckport.ai", "password": "admin123"}'

# Set the token (copy from response)
export ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### **4. Start Programming**
```bash
# Interactive mode (recommended for first time)
python nfc_card_programmer.py --interactive --api-url http://your-server:8002

# Or direct batch programming
python nfc_card_programmer.py \
  --product-sku RADIANT-001 \
  --batch-size 50 \
  --api-url http://your-server:8002
```

---

## 🛠️ **Hardware Requirements**

### **NFC Readers**
| Reader | Status | Notes |
|--------|--------|-------|
| **OMNIKEY 5422** | ✅ **RECOMMENDED** | Professional grade, 076b:5422, enterprise security |
| **ACR122U** | ✅ Compatible | USB, popular, good compatibility |
| **PN532** | ✅ Compatible | Arduino/Pi module, budget option |
| **ACR1252U** | ✅ Compatible | USB contactless, premium option |

**🎯 Optimized for OMNIKEY 5422 (your hardware)**

### **Cards**
- **NTAG 424 DNA** blank cards (required for security features)
- Alternative: NTAG 213/215/216 (basic compatibility)

### **System Requirements**
- **OS**: Linux (Ubuntu/Debian), macOS, Windows
- **Python**: 3.8+
- **USB**: Available USB port for NFC reader
- **Permissions**: Access to USB devices (dialout group on Linux)

---

## 📖 **Usage Guide**

### **Command Line Options**

```bash
# Check hardware setup
python nfc_card_programmer.py --check-hardware

# List available cards from catalog
python nfc_card_programmer.py --list-cards

# Validate a specific card SKU
python nfc_card_programmer.py --validate-sku RADIANT-001

# Interactive mode with menu
python nfc_card_programmer.py --interactive

# Program batch of cards
python nfc_card_programmer.py \
  --product-sku RADIANT-001 \
  --batch-size 100 \
  --batch-code CUSTOM-BATCH-001

# Specify API server
python nfc_card_programmer.py \
  --api-url http://192.168.1.100:8002 \
  --list-cards
```

### **Interactive Mode**

Run `python nfc_card_programmer.py --interactive` to access the menu:

```
🎮 Interactive Mode
==================================================

Options:
1. Program card batch
2. List available cards
3. Validate product SKU
4. Check NFC hardware
5. Test NFC reader
6. Exit
```

**Option 1: Program Card Batch**
- Shows available cards from your catalog
- Prompts for Product SKU (e.g., `RADIANT-001`)
- Asks for batch size (number of cards)
- Optional custom batch code
- Programs cards one by one

**Option 2: List Available Cards**
- Shows all cards in your database catalog
- Displays SKU, name, rarity, category
- Helps you choose which cards to program

**Option 3: Validate Product SKU**
- Checks if a specific SKU exists
- Shows card details (stats, rarity, etc.)
- Useful before starting large batches

**Option 4: Check NFC Hardware**
- Tests NFC reader connection
- Verifies drivers are working
- Troubleshooting information

**Option 5: Test NFC Reader**
- Waits for card placement
- Shows detected card UID
- Tests basic card communication

---

## 🔧 **Installation Guide**

### **Automatic Installation (Linux)**
```bash
# Run the installation script
./install_nfc_dependencies.sh

# Log out and log back in (to apply group changes)
# Test the setup
python nfc_card_programmer.py --check-hardware
```

### **Manual Installation**

#### **Linux (Ubuntu/Debian)**
```bash
# System dependencies
sudo apt update
sudo apt install -y libnfc-bin libnfc-dev libusb-1.0-0-dev pkg-config python3-dev python3-pip

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Python dependencies
pip3 install nfcpy cryptography requests

# Log out and log back in
# Test: nfc-list
```

#### **macOS**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install libnfc libusb pkg-config python3

# Python dependencies
pip3 install nfcpy cryptography requests
```

#### **Windows**
```bash
# Install Python 3.8+ from python.org
# Install Visual Studio Build Tools

# Python dependencies
pip install nfcpy cryptography requests

# Note: Windows NFC support varies by reader
# ACR122U has best Windows compatibility
```

---

## 🎯 **Programming Workflow**

### **1. Card Catalog Validation**
```bash
# Check what cards are available
python nfc_card_programmer.py --list-cards

# Example output:
📋 Available Cards in Catalog
==================================================
  RADIANT-001     | Solar Vanguard           | EPIC       | CREATURE
  AZURE-014       | Tidecaller Sigil         | RARE       | ENCHANTMENT
  VERDANT-007     | Forest Guardian          | COMMON     | CREATURE
  CRIMSON-003     | Fire Dragon              | LEGENDARY  | CREATURE
```

### **2. Batch Creation**
```bash
# Program 50 Solar Vanguard cards
python nfc_card_programmer.py \
  --product-sku RADIANT-001 \
  --batch-size 50
```

### **3. Card Programming Process**
For each card:
1. **Place card** on NFC reader
2. **Detect card** UID (e.g., `04AA3AB2C1800001`)
3. **Generate keys** unique to this card
4. **Program NTAG 424 DNA** with secure APDU commands
5. **Register in database** with activation code
6. **Move to next card**

### **4. Results & Tracking**
```bash
📊 Batch Programming Summary
✅ Successfully programmed: 48
❌ Failed: 2
📦 Batch Code: BATCH-20250120-143022
💾 Results saved to batch_results_BATCH-20250120-143022.json
```

**Results file contains:**
- List of all programmed cards
- Card UIDs and activation codes
- Batch statistics
- Timestamp and metadata

---

## 🔒 **Security Features**

### **NTAG 424 DNA Security**
- **Unique Keys**: Each card gets cryptographically unique keys
- **Anti-Cloning**: Hardware-level protection against duplication
- **Secure Communication**: Encrypted APDU commands
- **Authentication**: Server validates card authenticity

### **Key Generation**
```python
# Each card gets unique keys derived from:
master_key + card_uid + product_sku = unique_card_keys
```

### **Database Integration**
- **Card Registration**: Links physical card to digital template
- **Activation Codes**: 8-digit secure codes for customer activation
- **Audit Trail**: Complete history of card programming and usage
- **Batch Tracking**: Quality control and production management

---

## 🗄️ **Database Integration**

### **What Gets Created**

#### **Card Batch Record**
```sql
INSERT INTO card_batches (
  batch_code, product_sku, total_cards, 
  programmed_cards, production_date
) VALUES (
  'BATCH-20250120-143022', 'RADIANT-001', 50, 
  48, '2025-01-20T14:30:22Z'
);
```

#### **NFC Card Records**
```sql
INSERT INTO enhanced_nfc_cards (
  ntag_uid, product_sku, batch_id, serial_number,
  issuer_key_ref, security_level, status
) VALUES (
  '04AA3AB2C1800001', 'RADIANT-001', 15, 
  'BATCH-20250120-143022-001', 'abc123...', 
  'NTAG424_DNA', 'PROGRAMMED'
);
```

#### **Activation Codes**
```sql
INSERT INTO card_activation_codes (
  nfc_card_id, activation_code, code_hash,
  expires_at, delivery_method
) VALUES (
  234, '12345678', 'hashed_code',
  '2026-01-20T14:30:22Z', 'EMAIL'
);
```

### **Card Linking Flow**
```
Card Catalog (RADIANT-001) → NFC Card (04AA...) → Player Activation
     ↓                           ↓                      ↓
"Solar Vanguard"            Physical Card          Owned by Player
Epic Creature              + Activation Code       + Upgrades
Attack: 3, Health: 5       + Secure Keys          + Battle History
```

---

## 🧪 **Testing & Troubleshooting**

### **Hardware Testing**
```bash
# Test NFC reader detection
python nfc_card_programmer.py --check-hardware

# Test card detection
python nfc_card_programmer.py --interactive
# Choose option 5 (Test NFC reader)
```

### **Common Issues**

#### **"No NFC reader detected"**
```bash
# Check USB connection
lsusb | grep -i nfc

# Check permissions
ls -la /dev/ttyUSB* /dev/ttyACM*

# Restart services
sudo systemctl restart pcscd

# Test manually
nfc-list
```

#### **"nfcpy library not installed"**
```bash
# Install nfcpy
pip install nfcpy

# Or with user flag
pip install --user nfcpy
```

#### **"Admin token required"**
```bash
# Get admin token from your server
curl -X POST http://your-server:8002/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@deckport.ai", "password": "admin123"}'

# Set environment variable
export ADMIN_TOKEN="your_jwt_token_here"

# Or pass directly
python nfc_card_programmer.py --admin-token "your_jwt_token" --list-cards
```

#### **"Product SKU not found"**
```bash
# List available cards
python nfc_card_programmer.py --list-cards

# Check specific SKU
python nfc_card_programmer.py --validate-sku RADIANT-001

# Make sure your card catalog has cards in the database
```

#### **"Card programming failed"**
- Ensure card is NTAG 424 DNA (or compatible)
- Check card is properly placed on reader
- Verify card is not write-protected
- Try different card from batch

### **Debug Mode**
```bash
# Enable verbose logging
export DEBUG=1
python nfc_card_programmer.py --interactive

# Check API connectivity
curl -s http://your-server:8002/health
```

---

## 📊 **Production Workflow**

### **Recommended Process**
1. **Design Cards**: Create card designs in your card catalog
2. **Validate Setup**: Test with `--check-hardware` and small batches
3. **Program Batches**: Program cards in batches of 50-100
4. **Quality Control**: Verify random cards from each batch
5. **Ship to Store**: Physical cards go to your e-commerce fulfillment
6. **Customer Purchase**: Customer buys card online
7. **Activation**: Customer receives activation code via email/SMS
8. **Card Activation**: Customer taps card + enters code in mobile app

### **Batch Management**
```bash
# Small test batch first
python nfc_card_programmer.py --product-sku RADIANT-001 --batch-size 5

# Production batches
python nfc_card_programmer.py --product-sku RADIANT-001 --batch-size 100

# Custom batch codes for tracking
python nfc_card_programmer.py \
  --product-sku RADIANT-001 \
  --batch-size 100 \
  --batch-code RADIANT-PRODUCTION-001
```

### **Quality Control**
- Test random cards from each batch
- Verify activation codes work
- Check card UIDs are unique
- Validate database records
- Store batch results files for auditing

---

## 🔧 **Advanced Configuration**

### **Environment Variables**
```bash
# Admin token (recommended)
export ADMIN_TOKEN="your_jwt_token_here"

# API server URL
export API_URL="http://192.168.1.100:8002"

# Debug mode
export DEBUG=1
```

### **Custom Master Key**
```bash
# The script generates master_key.bin automatically
# To use custom key, replace the file:
openssl rand -out master_key.bin 32

# Or set environment variable:
export MASTER_KEY_FILE="/path/to/your/master_key.bin"
```

### **Batch Naming**
```bash
# Auto-generated: BATCH-20250120-143022
# Custom naming:
python nfc_card_programmer.py \
  --batch-code "PRODUCTION-RADIANT-001-JAN2025" \
  --product-sku RADIANT-001 \
  --batch-size 100
```

---

## 📁 **File Structure**

```
tools/nfc-card-programmer/
├── README.md                    # This file
├── nfc_card_programmer.py       # Main programming script
├── install_nfc_dependencies.sh  # Dependency installation
├── master_key.bin              # Generated master key (keep secure!)
├── batch_results_*.json        # Programming results (auto-generated)
└── logs/                       # Optional log directory
```

---

## 🚀 **Next Steps**

1. **Download this folder** to your local machine
2. **Install dependencies** with `./install_nfc_dependencies.sh`
3. **Connect NFC reader** and test with `--check-hardware`
4. **Get admin token** from your API server
5. **Start with interactive mode** to explore available cards
6. **Program test batch** of 5-10 cards first
7. **Scale to production batches** of 50-100 cards

---

## 📞 **Support**

- **Hardware Issues**: Check NFC reader compatibility and drivers
- **API Issues**: Verify server is running and admin token is valid
- **Card Issues**: Ensure using NTAG 424 DNA cards
- **Database Issues**: Check card catalog has the product SKUs you want

**This tool is production-ready for secure, scalable physical card manufacturing!** 🃏⚡🔒
