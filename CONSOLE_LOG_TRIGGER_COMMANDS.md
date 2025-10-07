# 📡 Console Log Trigger Commands

**Command Date:** September 15, 2025  
**Purpose:** 🎯 **Trigger log collection on console remotely**  
**Method:** Curl commands that make console run scripts and upload logs

## 🚀 **Remote Log Collection Commands**

Here are the exact curl commands to trigger log collection on your deployed console:

---

## 🔧 **Option 1: Trigger Console Log Upload (Recommended)**

### **✅ Command to Run on Console:**
```bash
# This curl command triggers the console to collect and upload logs
curl -X POST "https://api.deckport.ai/v1/admin/devices/CONSOLE_DEVICE_UID/collect-logs" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -d '{
         "log_types": ["deployment", "system", "graphics"],
         "since": "30 minutes ago",
         "upload_to_server": true
     }'
```

### **✅ What This Does:**
- **Triggers console** to run log collection script
- **Collects deployment logs** from last 30 minutes
- **Uploads to server** automatically
- **Returns** upload confirmation

---

## 📡 **Option 2: Direct Debug Upload (Simplest)**

### **✅ From Console (No Authentication Needed):**
```bash
# Run this directly on the console that had deployment errors
curl -X POST "https://api.deckport.ai/v1/debug/simple" \
     -H "Content-Type: text/plain" \
     -d "DEPLOYMENT ERROR REPORT: $(date)
Console: $(hostname)
Error: Failed to download game

=== RECENT LOGS ===
$(journalctl --since '30 minutes ago' | grep -i 'deploy\|download\|error\|fail' | tail -20)

=== SYSTEM INFO ===
$(uname -a)
$(free -h | grep Mem)
$(df -h / | tail -1)

=== NETWORK TEST ===
$(curl -s -I https://deckport.ai/deploy/assets/godot-game/latest | head -1)
"
```

---

## 🎯 **Option 3: Console Script Execution**

### **✅ Trigger Script on Console:**
```bash
# This tells the console to run its log upload script
curl -X POST "https://api.deckport.ai/v1/admin/devices/CONSOLE_DEVICE_UID/remote-command" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
         "command": "upload_logs",
         "parameters": {
             "type": "deployment_error",
             "since": "30 minutes ago"
         }
     }'
```

---

## 🔍 **Option 4: Emergency Log Collection**

### **✅ For Severe Issues:**
```bash
# Comprehensive system diagnosis
curl -X POST "https://api.deckport.ai/v1/debug/upload" \
     -H "Content-Type: application/json" \
     -d "{
         \"console_id\": \"$(hostname)-$(date +%s)\",
         \"error_type\": \"deployment_failure\",
         \"error_message\": \"Failed to download game during deployment\",
         \"system_logs\": \"$(journalctl --since '1 hour ago' | tail -100 | sed 's/\"/\\\\\"/g')\",
         \"deployment_logs\": \"$(grep -i deploy /var/log/* 2>/dev/null | tail -20)\",
         \"network_test\": \"$(curl -s -I https://deckport.ai/deploy/console | head -1)\"
     }"
```

---

## 📊 **Upload Endpoints Available**

### **✅ Debug Endpoints (No Auth Required):**
- **Simple Upload:** `POST /v1/debug/simple` (text data)
- **Structured Upload:** `POST /v1/debug/upload` (JSON data)
- **Console Logs:** `POST /v1/console-logs/stream` (formatted logs)

### **✅ Admin Endpoints (Auth Required):**
- **Remote Commands:** `POST /v1/admin/devices/{uid}/remote-command`
- **Log Collection:** `POST /v1/admin/devices/{uid}/collect-logs`
- **Console Management:** `POST /v1/admin/devices/{uid}/reboot`

---

## 🎯 **Recommended for Your Deployment Error**

### **✅ Quick Upload (Run This):**
```bash
curl -X POST "https://api.deckport.ai/v1/debug/simple" \
     -H "Content-Type: text/plain" \
     -d "DEPLOYMENT ERROR: $(date)
Console: $(hostname)
Error: Failed to download game

Recent deployment logs:
$(journalctl --since '30 minutes ago' | grep -i 'deploy\|download\|curl\|error' | tail -15)

Network connectivity:
$(curl -s -I https://deckport.ai/deploy/console | head -1)
$(curl -s -I https://deckport.ai/deploy/assets/godot-game/latest | head -1)
"
```

### **✅ Expected Response:**
```json
{
    "success": true,
    "file": "/tmp/simple_debug_20250915_123456.txt",
    "size": 1234
}
```

### **✅ After Upload:**
- **Debug file created** on server with timestamp
- **Logs available** for immediate analysis
- **Error diagnosis** can begin

---

## 📞 **Run This Command:**

**Use this simple curl command from your console:**

```bash
curl -X POST "https://api.deckport.ai/v1/debug/simple" \
     -H "Content-Type: text/plain" \
     -d "DEPLOYMENT ERROR: $(date)
Console: $(hostname)
Error: Failed to download game

$(journalctl --since '30 minutes ago' | grep -E 'deploy|download|error|fail' | tail -20)"
```

**This will upload your deployment error logs to the server where I can analyze them and help fix the download issue!** 📡🔍🚀

---

*Console Log Trigger Commands by the Deckport.ai Development Team - September 15, 2025*
