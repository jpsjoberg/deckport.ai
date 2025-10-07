# 🎯 Correct Usage Instructions - OMNIKEY 5422

## ⚡ **Step-by-Step Commands (Run Separately!)**

### **On Your Mac:**

#### **Step 1: Navigate to Directory**
```bash
cd /path/to/DECKPORT/nfc-card-programmer/
```

#### **Step 2: Load Environment (SEPARATE COMMAND)**
```bash
source config.env
```

#### **Step 3: Run Programmer (SEPARATE COMMAND)**
```bash
python3 nfc_card_programmer.py --interactive
```

## ❌ **Common Mistakes**

### **Wrong (Causes Error):**
```bash
# DON'T do this - causes "unrecognized arguments" error
python3 nfc_card_programmer.py source config.env python nfc_card_programmer.py --interactive
```

### **Right (Works):**
```bash
# DO this - run commands separately
source config.env
python3 nfc_card_programmer.py --interactive
```

## 🔧 **If You Get Connection Errors**

### **"Connection refused to 127.0.0.1:8002"**
**Cause**: Environment variables not loaded properly

**Solution:**
```bash
# Make sure you run this first:
source config.env

# Then verify the token is set:
echo $ADMIN_TOKEN

# Should show your JWT token, not empty
```

### **Alternative: Set Token Manually**
```bash
export ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
python3 nfc_card_programmer.py --interactive
```

## 📱 **Expected Working Flow**

```bash
cd /path/to/nfc-card-programmer/
source config.env
python3 nfc_card_programmer.py --interactive

# Should show:
🎯 OMNIKEY 5422 specific reader available
🔑 Loading existing master key...

🎮 Interactive Mode
==================================================
Options:
1. Program card batch
2. List available cards  
3. Validate product SKU
4. Check NFC hardware
5. Test NFC reader
6. Exit

Select option (1-6): 2

📋 Available Cards (showing 20):
  HERO_CRIMSON_140 | Burn Knight              | LEGENDARY  | HERO
  ORRERY_REACTOR   | Orrery Reactor           | EPIC       | STRUCTURE
  ... (your cards)
```

## 🎯 **Ready for Programming**

**Once the card list works, you can program cards:**
- **Option 1**: Program card batch with your OMNIKEY 5422
- **NTAG 424 DNA**: Will use proven working method
- **Database**: Cards register in your catalog

**Follow the correct command sequence and NFC card programming will work! 📱✅**
