# 🔌 Deckport Console NFC Reader Specification

**Specification Date:** September 13, 2025  
**Version:** 1.0  
**Status:** 🎯 **Production Hardware Requirements**

## 🎯 **Executive Summary**

This specification defines the exact NFC reader hardware requirements for Deckport gaming consoles. The reader must support **NTAG 424 DNA cards** with **cryptographic authentication**, provide **reliable console integration**, and deliver **professional gaming experience**.

---

## 🃏 **Deckport Card Technology**

### **Card Specifications**
- **Chip Type:** NTAG 424 DNA (NXP Semiconductors)
- **Security:** AES-128 encryption with dynamic authentication
- **Memory:** 416 bytes user memory + secure areas
- **UID:** 7-byte unique identifier per card
- **Standards:** ISO/IEC 14443 Type A
- **Frequency:** 13.56 MHz
- **Data Rate:** Up to 424 kbps

### **Card Physical Properties**
- **Size:** Standard trading card (63mm × 88mm)
- **Thickness:** 0.76mm (standard card thickness)
- **Material:** Premium PVC with embedded NFC chip
- **Durability:** Gaming-grade construction for frequent handling
- **Design:** Full-color artwork with NFC chip embedded

---

## 🔧 **NFC Reader Hardware Requirements**

### **🔴 CRITICAL REQUIREMENTS (Must Have)**

#### **1. Chip Compatibility**
- **✅ NTAG 424 DNA Support:** Full read/write capability
- **✅ ISO/IEC 14443 Type A:** Complete protocol support
- **✅ Frequency:** 13.56 MHz operation
- **✅ Data Rates:** 106, 212, 424 kbps support
- **✅ APDU Commands:** Application Protocol Data Unit support
- **✅ Cryptographic Operations:** AES-128 encryption/decryption

#### **2. Physical Interface**
- **✅ USB Connection:** USB 2.0+ for console integration
- **✅ Driver Support:** Linux kernel driver compatibility
- **✅ Hot-Pluggable:** USB plug-and-play operation
- **✅ Power:** USB-powered (no external power required)
- **✅ Cable Length:** 1.5-2 meters for flexible console placement

#### **3. Reading Performance**
- **✅ Read Range:** 0-50mm (optimal: 10-30mm)
- **✅ Read Speed:** < 100ms card detection
- **✅ Authentication Speed:** < 500ms NTAG 424 DNA crypto
- **✅ Error Rate:** < 0.1% false reads
- **✅ Reliability:** 99.9%+ successful reads
- **✅ Durability:** 1,000,000+ read cycles

#### **4. Software Compatibility**
- **✅ Linux Support:** Ubuntu 20.04+ drivers
- **✅ libnfc Compatible:** Works with libnfc library
- **✅ PC/SC Compatible:** Works with PC/SC daemon
- **✅ Python Integration:** Compatible with pynfc/smartcard
- **✅ Command Line:** Works with nfc-list, nfc-poll commands

### **🟡 PREFERRED FEATURES (Highly Recommended)**

#### **5. Professional Features**
- **🟡 Multiple Card Detection:** Read multiple cards simultaneously
- **🟡 Anti-Collision:** Handle multiple cards in field
- **🟡 Status LEDs:** Visual feedback for scan status
- **🟡 Audio Feedback:** Beep on successful scan
- **🟡 EMI Shielding:** Electromagnetic interference protection

#### **6. Gaming Experience**
- **🟡 Fast Scanning:** < 50ms detection time
- **🟡 Reliable Range:** Consistent 20-40mm read distance
- **🟡 Card Presence Detection:** Detect when card removed
- **🟡 Multiple Format Support:** Support other NFC tag types
- **🟡 Firmware Updates:** Updateable firmware via USB

### **🟢 OPTIONAL FEATURES (Nice to Have)**

#### **7. Advanced Features**
- **🟢 Contactless Interface:** No physical card insertion required
- **🟢 Multiple Protocols:** Support for other NFC standards
- **🟢 SDK Support:** Manufacturer SDK for custom integration
- **🟢 Embedded Processing:** On-device cryptographic processing
- **🟢 Ruggedized Design:** Gaming/kiosk environment durability

---

## 🏆 **Recommended NFC Readers**

### **🥇 PRIMARY RECOMMENDATION: OMNIKEY 5422**

#### **Why OMNIKEY 5422 is Ideal:**
- **✅ Professional Grade:** Designed for kiosk/terminal applications
- **✅ NTAG 424 DNA:** Full support with cryptographic operations
- **✅ Linux Drivers:** Excellent Ubuntu/Linux compatibility
- **✅ PC/SC Support:** Works with existing console code
- **✅ Durability:** 1,000,000+ read cycles
- **✅ Gaming Performance:** < 100ms read times
- **✅ USB Powered:** No external power required

#### **Technical Specifications:**
```
Model: HID OMNIKEY 5422
USB ID: 076b:5422
Interface: USB 2.0 Type A
Power: USB Bus Powered (5V, <500mA)
Dimensions: 100 × 70 × 12 mm
Cable: 1.8m USB cable
Operating Temp: -20°C to 70°C
Humidity: 0-95% RH non-condensing
Certifications: FCC, CE, RoHS
```

#### **NFC Capabilities:**
```
Standards: ISO/IEC 14443 Type A/B
Frequency: 13.56 MHz
Data Rates: 106, 212, 424 kbps
Read Range: 0-50mm (optimal: 20-40mm)
Card Types: NTAG 424 DNA, MIFARE, DESFire
Security: AES-128, 3DES, RSA
APDU Support: Full T=CL protocol
```

### **🥈 SECONDARY OPTION: ACR122U**

#### **Why ACR122U is Good Alternative:**
- **✅ Cost Effective:** Lower cost option
- **✅ Wide Compatibility:** Works with most NFC libraries
- **✅ Linux Support:** Good driver support
- **✅ Community Support:** Large user base and documentation
- **⚠️ Consumer Grade:** Less durable than professional readers

#### **Technical Specifications:**
```
Model: ACS ACR122U
USB ID: 072f:2200
Interface: USB Full Speed
Power: USB Bus Powered (5V, <200mA)
Dimensions: 98 × 65 × 12.8 mm
Cable: 1.2m USB cable
Operating Temp: -10°C to 50°C
```

### **🥉 BUDGET OPTION: PN532 Module**

#### **For Development/Testing:**
- **✅ Low Cost:** Under $20
- **✅ NTAG 424 DNA:** Basic support
- **✅ GPIO Integration:** Direct hardware integration
- **⚠️ Development Only:** Not suitable for production kiosks

---

## 🔌 **Console Integration Requirements**

### **Hardware Integration**

#### **Physical Mounting**
- **Placement:** Console front panel or side-mounted
- **Accessibility:** Easy card access for players
- **Protection:** Tamper-resistant mounting
- **Visibility:** Clear scan area indication
- **Ergonomics:** Natural card placement position

#### **Electrical Connection**
- **USB Port:** Dedicated USB 2.0+ port on console
- **Power Management:** USB power with sleep/wake support
- **Cable Management:** Clean cable routing inside console
- **EMI Protection:** Shielded connection to prevent interference

### **Software Integration**

#### **Linux Driver Stack**
```bash
# Required Linux packages
sudo apt install libnfc-bin pcscd pcsc-tools

# For OMNIKEY 5422
sudo systemctl enable pcscd
sudo systemctl start pcscd

# For ACR122U  
sudo modprobe pn533_usb
sudo udevadm control --reload-rules
```

#### **Godot Integration**
```gdscript
# In console/nfc_manager.gd (already implemented)

# Supported reader detection
var supported_readers = {
    "076b:5422": "OMNIKEY 5422 Professional",
    "072f:2200": "ACR122U",
    "1fc9:000d": "PN532"
}

# Hardware detection methods
func detect_nfc_reader():
    # Method 1: libnfc detection
    var nfc_output = []
    OS.execute("nfc-list", [], nfc_output)
    
    # Method 2: PC/SC detection  
    OS.execute("pcsc_scan", ["-n"], pcsc_output)
    
    # Method 3: USB device detection
    OS.execute("lsusb", [], usb_output)
```

---

## 📊 **Performance Specifications**

### **Gaming Performance Requirements**
| Metric | Requirement | Target | Notes |
|--------|-------------|---------|-------|
| **Scan Detection** | < 200ms | < 100ms | Card presence detection |
| **UID Reading** | < 300ms | < 150ms | Basic card identification |
| **NTAG 424 Auth** | < 1000ms | < 500ms | Full cryptographic auth |
| **Read Range** | 10-50mm | 20-40mm | Optimal gaming distance |
| **Read Success Rate** | > 99% | > 99.9% | Reliable card reading |
| **False Positive Rate** | < 0.1% | < 0.01% | Accurate detection |

### **Durability Requirements**
| Component | Requirement | Target | Gaming Context |
|-----------|-------------|---------|----------------|
| **Read Cycles** | 500,000+ | 1,000,000+ | Heavy gaming use |
| **Operating Hours** | 8,760+ | 17,520+ | 24/7 kiosk operation |
| **Temperature Range** | -10°C to 50°C | -20°C to 70°C | Various environments |
| **Humidity Tolerance** | 0-80% RH | 0-95% RH | High humidity areas |
| **Vibration Resistance** | Gaming standard | Industrial grade | Console movement |

---

## 🔐 **Security Requirements**

### **NTAG 424 DNA Security Features**
- **✅ AES-128 Encryption:** Hardware-level data protection
- **✅ Dynamic Authentication:** Unique response per scan
- **✅ Tamper Detection:** Physical security monitoring
- **✅ Secure Messaging:** Encrypted communication protocol
- **✅ Key Derivation:** Secure key generation and management
- **✅ Anti-Cloning:** Cryptographic proof of authenticity

### **Reader Security Requirements**
- **✅ Secure Communication:** Encrypted USB communication
- **✅ Firmware Protection:** Signed firmware updates only
- **✅ Key Storage:** Secure key storage (if applicable)
- **✅ Anti-Tampering:** Physical tamper detection
- **✅ Access Control:** Controlled API access

---

## 🛠️ **Installation & Setup**

### **Hardware Installation**
1. **Mount reader** in console front panel
2. **Connect USB cable** to dedicated console port
3. **Install Linux drivers** (libnfc + PC/SC)
4. **Configure permissions** for console user account
5. **Test basic functionality** with nfc-list command

### **Software Configuration**
```bash
# Install required packages
sudo apt update
sudo apt install libnfc-bin pcscd pcsc-tools

# Configure libnfc
sudo nano /etc/nfc/libnfc.conf
# Add: device.connstring = "pn532_uart:/dev/ttyS0"

# Configure PC/SC (for OMNIKEY)
sudo systemctl enable pcscd
sudo systemctl start pcscd

# Test installation
nfc-list
pcsc_scan -n
```

### **Console Integration**
```gdscript
# The console already supports multiple readers
# via console/nfc_manager.gd:

# 1. Automatic detection of supported readers
# 2. Multi-method scanning (libnfc + PC/SC)
# 3. NTAG 424 DNA authentication
# 4. Server-side card validation
# 5. Error handling and recovery
```

---

## 💰 **Cost Analysis**

### **Reader Options by Price**

#### **Professional Grade (Recommended)**
- **OMNIKEY 5422:** $150-200
  - Best durability and performance
  - Professional kiosk applications
  - Full NTAG 424 DNA support
  - 5-year lifespan in heavy use

#### **Commercial Grade**
- **ACR122U:** $30-50
  - Good performance and compatibility
  - Suitable for moderate use
  - Wide software support
  - 2-3 year lifespan

#### **Development Grade**
- **PN532 Module:** $15-25
  - Basic functionality
  - Development and testing only
  - Limited durability
  - 1 year lifespan

### **Total Cost of Ownership**
```
OMNIKEY 5422: $200 + 5-year lifespan = $40/year
ACR122U: $40 + 2-year lifespan = $20/year
PN532: $20 + 1-year lifespan = $20/year + replacement hassle
```

**Recommendation:** OMNIKEY 5422 for production consoles

---

## 🎮 **Gaming-Specific Requirements**

### **User Experience**
- **⚡ Fast Response:** < 100ms scan-to-game response
- **🎯 Intuitive Placement:** Natural card positioning
- **💡 Visual Feedback:** LEDs indicate scan status
- **🔊 Audio Feedback:** Sound confirmation of successful scan
- **🛡️ Error Recovery:** Clear error messages and retry options

### **Kiosk Environment**
- **🔒 Tamper Resistant:** Secure mounting in console
- **🧹 Easy Cleaning:** Accessible for maintenance
- **⚡ Power Efficient:** Low power consumption
- **🌡️ Temperature Stable:** Consistent performance in various environments
- **📶 EMI Resistant:** No interference from console electronics

### **Gaming Performance**
- **🎲 Multi-Card Support:** Rapid scanning of multiple cards
- **⚔️ Battle Integration:** Real-time card validation during gameplay
- **🏆 Tournament Ready:** Reliable performance under heavy use
- **🔄 Continuous Operation:** 24/7 kiosk mode support

---

## 🔍 **Testing & Validation**

### **Hardware Testing**
- **📡 Connectivity Test:** USB detection and driver loading
- **🔍 Scan Test:** Card detection and UID reading
- **🔐 Security Test:** NTAG 424 DNA authentication
- **⚡ Performance Test:** Speed and reliability testing
- **🌡️ Environmental Test:** Temperature and humidity testing

### **Integration Testing**
- **🎮 Console Integration:** Full console system testing
- **🌐 API Integration:** Server authentication testing
- **⚔️ Battle Testing:** Real-time gameplay card scanning
- **👥 Multi-Player Testing:** Simultaneous card scanning
- **🔄 Stress Testing:** Extended operation testing

### **Quality Assurance**
- **📊 Success Rate:** > 99.9% successful scans
- **⚡ Speed Verification:** < 100ms average scan time
- **🔒 Security Validation:** Cryptographic authentication working
- **🛡️ Error Handling:** Graceful failure and recovery
- **📈 Performance Monitoring:** Long-term reliability tracking

---

## 📋 **Procurement Specification**

### **🎯 RECOMMENDED PURCHASE: OMNIKEY 5422**

#### **Exact Model Information**
```
Manufacturer: HID Global
Model: OMNIKEY 5422
Part Number: 5422CL-AKU
USB Vendor ID: 076b
USB Product ID: 5422
Certifications: FCC ID: 2AOKB-5422, CE, RoHS
```

#### **Technical Specifications**
```
NFC Standards: ISO/IEC 14443 Type A/B
Supported Cards: NTAG 424 DNA, MIFARE DESFire, MIFARE Classic
Frequency: 13.56 MHz ± 7 kHz
Data Rates: 106, 212, 424 kbps
Read Range: 0-50mm
Power: USB Bus Power (5V, 400mA max)
Interface: USB 2.0 Full Speed
Dimensions: 100 × 70 × 12 mm
Weight: 80g
Cable: 1.8m USB Type A
Operating Temp: -20°C to 70°C
Storage Temp: -40°C to 85°C
Humidity: 0-95% RH non-condensing
```

#### **Software Support**
```
Linux Drivers: PC/SC compatible
Libraries: libpcsclite, pcsc-tools
Commands: pcsc_scan, opensc-tool
Python: smartcard, pyscard libraries
Godot: Via OS.execute() system calls
```

### **Procurement Requirements**
1. **Quantity:** 1 per console + 10% spare units
2. **Warranty:** Minimum 2-year manufacturer warranty
3. **Support:** Technical support for integration issues
4. **Documentation:** Complete SDK and integration guides
5. **Compliance:** FCC, CE, RoHS certifications required

---

## 🔧 **Installation Guide**

### **Physical Installation**
1. **Mount reader** in console front panel
   - Position for natural card placement
   - Secure mounting to prevent tampering
   - Clear visual indication of scan area

2. **Connect USB cable**
   - Route cable cleanly inside console
   - Connect to dedicated USB port
   - Secure cable to prevent disconnection

3. **Test physical installation**
   - Verify reader is detected by system
   - Test card placement and scanning
   - Validate mounting stability

### **Software Configuration**
```bash
# 1. Install drivers and tools
sudo apt update
sudo apt install pcscd pcsc-tools libnfc-bin

# 2. Start PC/SC daemon
sudo systemctl enable pcscd
sudo systemctl start pcscd

# 3. Test reader detection
pcsc_scan -n
lsusb | grep 076b:5422

# 4. Test card reading
# (Place NTAG 424 DNA card on reader)
pcsc_scan -r

# 5. Configure permissions
sudo usermod -a -G scard,pcscd deckport
sudo udevadm control --reload-rules
```

### **Console Integration**
The console's `nfc_manager.gd` already supports OMNIKEY 5422:
- **✅ Automatic detection** via USB ID scanning
- **✅ PC/SC integration** with pcsc_scan commands
- **✅ Error handling** with troubleshooting messages
- **✅ Server authentication** with NTAG 424 DNA support

---

## 📊 **Validation Checklist**

### **Hardware Validation**
- [ ] **Reader detected** by `lsusb` command
- [ ] **Drivers loaded** successfully
- [ ] **PC/SC daemon** running without errors
- [ ] **Card detection** working with test cards
- [ ] **UID reading** consistent and accurate

### **Security Validation**
- [ ] **NTAG 424 DNA** authentication working
- [ ] **Cryptographic responses** validated
- [ ] **Server integration** functioning
- [ ] **Anti-cloning** protection active
- [ ] **Secure communication** established

### **Gaming Performance**
- [ ] **Scan speed** < 100ms consistently
- [ ] **Read reliability** > 99.9% success rate
- [ ] **Multiple cards** handled correctly
- [ ] **Error recovery** working smoothly
- [ ] **Console integration** seamless

---

## 🎯 **Final Recommendation**

### **Production Console Specification**
**Purchase:** HID OMNIKEY 5422 NFC Reader  
**Quantity:** 1 per console + 10% spares  
**Integration:** USB connection with PC/SC drivers  
**Software:** Already supported by existing console code  

### **Why This Choice**
1. **✅ Professional Grade:** Designed for kiosk applications
2. **✅ Perfect Compatibility:** Supports all Deckport requirements
3. **✅ Proven Reliability:** Used in banking and gaming terminals
4. **✅ Future Proof:** Supports advanced NFC features
5. **✅ Cost Effective:** Best total cost of ownership

### **Alternative for Budget Builds**
**Purchase:** ACS ACR122U  
**Use Case:** Development, testing, or budget installations  
**Limitations:** Lower durability, consumer-grade construction  

---

**The OMNIKEY 5422 provides the perfect balance of performance, security, and durability for professional Deckport console deployments, while the existing console code already supports it fully.**

---

*NFC Reader Specification by the Deckport.ai Hardware Team - September 13, 2025*
