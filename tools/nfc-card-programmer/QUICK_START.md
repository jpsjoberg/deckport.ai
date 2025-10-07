# 🚀 Quick Start Guide - OMNIKEY 5422 + NTAG 424 DNA

## ⚡ **Fastest Setup**

### **Step 1: Setup Environment**
```bash
cd /path/to/nfc-card-programmer/

# Load admin token
source config.env

# OR set manually
export ADMIN_TOKEN="your_jwt_token_here"
```

### **Step 2: Run Interactive Mode**
```bash
# Start the programmer
python3 nfc_card_programmer.py --interactive
```

**⚠️ Important: Run these as separate commands, not together!**

## 🎯 **Correct Command Syntax**

### ✅ **Correct Way**
```bash
# First: Load environment
source config.env

# Then: Run programmer  
python3 nfc_card_programmer.py --interactive
```

### ❌ **Wrong Way**
```bash
# DON'T do this (causes argument error)
python3 nfc_card_programmer.py source config.env python nfc_card_programmer.py --interactive
```

## 📋 **Quick Commands**

### **List Cards**
```bash
source config.env
python3 nfc_card_programmer.py --list-cards
```

### **Validate Card**
```bash
source config.env  
python3 nfc_card_programmer.py --validate-sku HERO_CRIMSON_140
```

### **Program Cards**
```bash
source config.env
python3 nfc_card_programmer.py --product-sku HERO_CRIMSON_140 --batch-size 5
```

### **Interactive Mode**
```bash
source config.env
python3 nfc_card_programmer.py --interactive
```

## 🔧 **Troubleshooting**

### **"unrecognized arguments: source config.env"**
**Solution**: Run `source config.env` first, then run the Python script separately.

### **"'NFCCardProgrammer' object has no attribute 'api_url'"**  
**Solution**: Fixed in latest version - update your script.

### **"Failed to list cards"**
**Solution**: Ensure `ADMIN_TOKEN` is set and API server is accessible.

## 🎴 **Ready for Card Programming**

**Your setup:**
- ✅ **OMNIKEY 5422**: Professional NFC reader
- ✅ **NTAG 424 DNA**: Enterprise security cards  
- ✅ **2600+ cards**: Available in catalog
- ✅ **Proven method**: Working APDU sequence implemented

**Start programming your physical cards! 📱🔒**
