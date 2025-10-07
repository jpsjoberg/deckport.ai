# 📡 Console Log Upload Guide

**Guide Date:** September 15, 2025  
**Status:** 🎯 **Debug Log Upload System**  
**Purpose:** Upload deployment logs to server for analysis

## 🔍 **Log Upload Options Available**

I found your log upload system! You have multiple ways to send deployment logs to the server for analysis:

---

## 🚀 **Option 1: Manual Log Upload (Recommended)**

### **✅ Script Location:**
```bash
/home/jp/deckport.ai/console/kiosk/manual_log_upload.sh
```

### **✅ How to Use:**
```bash
# On the console that had deployment errors:
cd /home/jp/deckport.ai/console/kiosk
chmod +x manual_log_upload.sh
./manual_log_upload.sh
```

### **✅ What This Script Does:**
- **Collects comprehensive system info** - Hardware, graphics, drivers
- **Gathers all relevant logs** - X11, systemd, console, auth logs
- **Includes configuration** - Auto-login, X11, GRUB settings
- **Sends to server** - API endpoint for immediate analysis
- **Creates debug file** - `/tmp/console_debug_{timestamp}.json`

---

## 📡 **Option 2: Focused Log Sender**

### **✅ Script Location:**
```bash
/home/jp/deckport.ai/console/kiosk/focused_log_sender.sh
```

### **✅ How to Use:**
```bash
cd /home/jp/deckport.ai/console/kiosk
chmod +x focused_log_sender.sh
./focused_log_sender.sh
```

### **✅ What This Sends:**
- **Graphics hardware** detection
- **Graphics drivers** status
- **X11 logs** (critical for display issues)
- **Systemd services** status
- **Recent system logs** for troubleshooting

---

## 🔧 **Option 3: Emergency Diagnostics**

### **✅ Script Location:**
```bash
/home/jp/deckport.ai/console/kiosk/emergency_diagnostics.sh
```

### **✅ For Severe Issues:**
- **Complete system diagnosis**
- **Hardware detection**
- **Service status checks**
- **Network connectivity tests**

---

## 📊 **API Endpoints for Log Upload**

### **✅ Debug Upload Endpoints:**

#### **Comprehensive Upload:**
```bash
POST https://api.deckport.ai/v1/debug/upload
Content-Type: application/json

# Accepts structured debug data
```

#### **Simple Text Upload:**
```bash
POST https://api.deckport.ai/v1/debug/simple
Content-Type: text/plain

# Accepts any text data (easiest)
```

#### **Console Log Streaming:**
```bash
POST https://api.deckport.ai/v1/console-logs/crash-report
Content-Type: application/json

# For crash reports and emergency logs
```

---

## 🎯 **Recommended Upload Process**

### **✅ Step-by-Step:**

#### **1. Prepare Upload Script:**
```bash
# On your server (where deployment failed)
cd /home/jp/deckport.ai/console/kiosk
chmod +x manual_log_upload.sh
```

#### **2. Run Upload:**
```bash
./manual_log_upload.sh
```

#### **3. Expected Output:**
```
📡 Manual Console Log Upload to Server
======================================
Collecting system logs...
Sending logs to server...
✅ Log upload complete!
Check admin panel or database for logs.
```

#### **4. Check Server Logs:**
```bash
# On your server, check for uploaded debug files:
ls -la /tmp/console_debug_*.json
ls -la /tmp/simple_debug_*.txt

# Or check service logs:
sudo journalctl -u api.service | grep "DEBUG UPLOAD"
```

---

## 🔍 **What Gets Uploaded**

### **✅ Comprehensive System Information:**
- **System info** - Hardware, memory, disk usage
- **Graphics hardware** - GPU detection and drivers
- **X11 logs** - Display server errors (critical)
- **Systemd services** - Service status and logs
- **Network status** - Connectivity and configuration
- **Recent logs** - Last 10 minutes of system activity
- **Configuration files** - X11, GRUB, auto-login settings

### **✅ Debug Data Saved To:**
- **Server files** - `/tmp/console_debug_{timestamp}.json`
- **Service logs** - Visible in API service logs
- **Admin panel** - Accessible via admin interface

---

## 🚀 **Quick Upload Commands**

### **✅ For Deployment Errors:**
```bash
# Upload comprehensive debug info
cd /home/jp/deckport.ai/console/kiosk
./manual_log_upload.sh

# Upload specific error logs
echo "DEPLOYMENT ERROR: $(date)
$(journalctl --since '10 minutes ago' | tail -50)" | \
curl -X POST "https://api.deckport.ai/v1/debug/simple" -d @-
```

### **✅ For Graphics Issues:**
```bash
# Upload graphics-specific info
./focused_log_sender.sh
```

### **✅ For Emergency Issues:**
```bash
# Complete system diagnosis
./emergency_diagnostics.sh
```

---

## 📞 **Next Steps**

### **✅ To Upload Your Deployment Logs:**
1. **Navigate to kiosk directory:**
   ```bash
   cd /home/jp/deckport.ai/console/kiosk
   ```

2. **Run manual upload:**
   ```bash
   chmod +x manual_log_upload.sh
   ./manual_log_upload.sh
   ```

3. **Check upload success:**
   - Look for "✅ Log upload complete!" message
   - Check `/tmp/console_debug_*.json` files on server
   - Review API service logs for debug uploads

4. **Share debug file location:**
   - The script will create timestamped debug files
   - These contain all system info needed for analysis

**Run the manual_log_upload.sh script to send your deployment error logs to the server for analysis!** 📡🔍

---

*Log Upload Guide by the Deckport.ai Development Team - September 15, 2025*
