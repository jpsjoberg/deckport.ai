# 🃏 NFC Card Programmer Usage Guide

## 📋 **Overview**

The `nfc_card_programmer.py` script allows you to program physical NTAG 424 DNA cards with secure keys and register them in your database. Each programmed card is linked to a specific card design from your card catalog.

## 🚀 **Quick Start**

### **1. Download and Setup (OMNIKEY 5422 Optimized)**
```bash
# Navigate to NFC programmer directory
cd /home/jp/deckport.ai/tools/nfc-card-programmer/

# Install dependencies (optimized for OMNIKEY 5422)
pip install -r requirements.txt

# Or use automated installer
./install_nfc_dependencies.sh

# Test your OMNIKEY 5422 setup
python setup_omnikey_5422.py

# Set your admin token
export ADMIN_TOKEN="your_admin_jwt_token_here"
```

### **2. First Time Usage (Interactive Mode)**
```bash
# Start in interactive mode to explore available cards
python scripts/nfc_card_programmer.py --interactive
```

This will show you a menu:
```
🎮 Interactive Mode
==================================================

Options:
1. Program card batch
2. List available cards
3. Validate product SKU
4. Test NFC reader
5. Exit
```

### **3. See Available Cards**
```bash
# List all available cards in your catalog
python scripts/nfc_card_programmer.py --list-cards
```

Output example (from your 2600+ card catalog):
```
📋 Available Cards in Catalog
==================================================
  HERO_CRIMSON_140 | Burn Knight              | LEGENDARY  | HERO
  EERIE_MASTER     | Eerie Master             | RARE       | HERO  
  WILD_HUNT_CRUSH  | Wild Hunt Crush          | COMMON     | ACTION_FAST
  BLOOMING_KEEPER  | Blooming Keeper          | RARE       | CREATURE
  ... (2600+ cards available)
```

### **4. Validate a Specific Card**
```bash
# Check if a product SKU exists and see its details
python nfc_card_programmer.py --validate-sku HERO_CRIMSON_140
```

Output example (from your catalog):
```
🔍 Validating Product SKU: HERO_CRIMSON_140
==================================================
✅ Valid card: Burn Knight
   Product SKU: HERO_CRIMSON_140
   Rarity: LEGENDARY
   Category: HERO
   Mana Colors: ["CRIMSON"]
   Artwork: Generated with ComfyUI (frame-aware composition)
   Status: Ready for OMNIKEY 5422 programming
```

## 🏭 **Programming Card Batches**

### **Command Line Mode (OMNIKEY 5422)**
```bash
# Program Burn Knight cards (your legendary hero)
python nfc_card_programmer.py \
  --product-sku HERO_CRIMSON_140 \
  --batch-size 10 \
  --api-url https://api.deckport.ai

# Program with custom batch code
python nfc_card_programmer.py \
  --product-sku EERIE_MASTER \
  --batch-size 25 \
  --batch-code HEROES-BATCH-001 \
  --api-url https://api.deckport.ai
```

### **Interactive Mode Programming**
1. Run `python scripts/nfc_card_programmer.py --interactive`
2. Choose option `1. Program card batch`
3. The script will show available cards
4. Enter the Product SKU (e.g., `RADIANT-001`)
5. Enter batch size (e.g., `10`)
6. Optionally enter a custom batch code
7. Follow the prompts to place cards on the NFC reader

## 🔧 **How It Works**

### **1. Card Validation**
- Script checks if the Product SKU exists in your card catalog
- Validates the card has all required information (name, rarity, stats, etc.)
- Shows an error if the SKU doesn't exist

### **2. Batch Creation**
- Creates a production batch record in the database
- Generates a unique batch code (e.g., `BATCH-20250120-143022`)
- Tracks total cards, programmed cards, sold cards, activated cards

### **3. NFC Programming**
- Generates unique cryptographic keys for each card
- Programs NTAG 424 DNA with secure APDU commands
- Each card gets a unique issuer key reference

### **4. Database Registration**
- Registers each programmed card in the `enhanced_nfc_cards` table
- Links the card to the correct product SKU
- Generates activation codes for each card
- Creates serial numbers (e.g., `BATCH-001-001`, `BATCH-001-002`)

## 📊 **Programming Results**

After programming, you get:

### **Console Output**
```
📊 Batch Programming Summary
✅ Successfully programmed: 48
❌ Failed: 2
📦 Batch Code: BATCH-20250120-143022
💾 Results saved to batch_results_BATCH-20250120-143022.json
```

### **Results File**
```json
{
  "batch_code": "BATCH-20250120-143022",
  "batch_id": 15,
  "product_sku": "RADIANT-001",
  "programmed_cards": [
    {
      "card_id": 234,
      "ntag_uid": "04AA3AB2C1800001",
      "activation_code": "12345678"
    }
  ],
  "summary": {
    "total_requested": 50,
    "successfully_programmed": 48,
    "failed": 2
  },
  "timestamp": "2025-01-20T14:30:22.123456"
}
```

## 🗄️ **Database Integration**

### **What Gets Created**

1. **Card Batch Record**
   ```sql
   INSERT INTO card_batches (batch_code, product_sku, total_cards, ...)
   VALUES ('BATCH-20250120-143022', 'RADIANT-001', 50, ...);
   ```

2. **NFC Card Records**
   ```sql
   INSERT INTO enhanced_nfc_cards (ntag_uid, product_sku, batch_id, serial_number, ...)
   VALUES ('04AA3AB2C1800001', 'RADIANT-001', 15, 'BATCH-20250120-143022-001', ...);
   ```

3. **Activation Codes**
   ```sql
   INSERT INTO card_activation_codes (nfc_card_id, activation_code, code_hash, ...)
   VALUES (234, '12345678', 'hashed_code', ...);
   ```

### **Linking to Card Catalog**
- The `product_sku` field links the physical NFC card to the card design
- When a player scans the card, the system knows it's a "Solar Vanguard" with specific stats
- The card catalog provides the name, artwork, abilities, stats, etc.
- The NFC card provides the ownership, activation status, upgrade history, etc.

## 🔒 **Security Features**

### **Unique Keys Per Card**
- Each card gets unique cryptographic keys derived from:
  - Master key (stored in `master_key.bin`)
  - Card UID (unique NFC identifier)
  - Product SKU (card type)

### **NTAG 424 DNA Programming**
- Authentication keys for secure access
- MAC keys for message authentication
- Encryption keys for data protection
- Dynamic URL configuration for anti-cloning

### **Activation Codes**
- 8-digit secure activation codes
- SHA-256 hashed storage
- 1-year expiration
- One-time use only

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **"Product SKU not found"**
```bash
❌ Product SKU 'INVALID-001' not found in card catalog
💡 Available cards:
```

**Solution**: Use `--list-cards` to see available SKUs, or add the card to your catalog first.

#### **"Admin token required"**
```bash
❌ Admin token required (use --admin-token or set ADMIN_TOKEN env var)
```

**Solution**: 
```bash
export ADMIN_TOKEN="your_jwt_token"
# OR
python scripts/nfc_card_programmer.py --admin-token "your_jwt_token" --list-cards
```

#### **"Failed to create batch"**
**Solution**: Check your API server is running and the admin token is valid.

#### **"NFC reader connection failed"**
**Solution**: 
- Check NFC reader is connected
- Install proper NFC drivers
- Replace `MockNFCReader` with real NFC library

### **Testing Without Hardware**
The script includes a `MockNFCReader` for testing:
- Simulates card detection after 3 seconds
- Generates mock card UIDs
- Simulates APDU command responses
- Perfect for testing the database integration

## 📈 **Production Workflow**

### **Recommended Process**
1. **Design Cards**: Create card designs in your card catalog
2. **Validate Setup**: Test with `--interactive` mode and small batches
3. **Program Batches**: Program cards in batches of 50-100
4. **Quality Control**: Verify random cards from each batch
5. **Ship to Store**: Physical cards go to your e-commerce fulfillment
6. **Customer Purchase**: Customer buys card online
7. **Activation**: Customer receives activation code via email
8. **Card Activation**: Customer taps card + enters code in mobile app

### **Batch Tracking**
- Each batch has a unique code for tracking
- Database tracks: programmed → sold → activated
- Admin dashboard shows batch statistics
- Quality control notes stored per batch

This system ensures **secure, traceable, and scalable** physical card production! 🎯
