#!/usr/bin/env python3
"""
Direct NTAG 424 DNA Programming Test
Test your proven working method directly without connection tests
"""

import time
from omnikey_5422_reader import OmniekeyReader

def test_direct_programming():
    """Test programming without connection verification"""
    print("🧪 Direct NTAG 424 DNA Programming Test")
    print("=" * 50)
    
    reader = OmniekeyReader()
    
    if not reader.connect():
        print("❌ Failed to connect to OMNIKEY 5422")
        return False
    
    print("📱 Place NTAG 424 DNA card on reader...")
    card_uid = reader.wait_for_card(30)
    
    if not card_uid:
        print("❌ No card detected")
        reader.disconnect()
        return False
    
    print(f"✅ Card detected: {card_uid}")
    
    # Verify we have the connection object
    if not reader.connection:
        print("❌ No connection object available")
        reader.disconnect()
        return False
    
    print("✅ Connection object confirmed")
    
    # Program immediately using the active connection
    print("🚀 Programming immediately using active connection...")
    
    try:
        # Use your proven working APDU sequence directly
        print("🔒 Step 1: Select NDEF application...")
        ndef_aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
        select_ndef = [0x00, 0xA4, 0x04, 0x00, len(ndef_aid)] + ndef_aid
        
        # Use the connection directly
        connection = reader.connection
        response, sw1, sw2 = connection.transmit(select_ndef)
        
        print(f"📥 NDEF App Selection: SW={sw1:02X}{sw2:02X}")
        
        if sw1 == 0x90:
            print("✅ NDEF application selected successfully")
            
            print("🔒 Step 2: Select NDEF file...")
            select_ndef_file = [0x00, 0xA4, 0x00, 0x0C, 0x02, 0xE1, 0x04]
            response, sw1, sw2 = connection.transmit(select_ndef_file)
            
            print(f"📥 NDEF File Selection: SW={sw1:02X}{sw2:02X}")
            
            if sw1 == 0x90:
                print("✅ NDEF file selected successfully")
                
                # Create simple NDEF record
                test_text = f"DECKPORT:RUIN_MONARCH:{card_uid[:8]}"
                ndef_record = create_ndef_text_record(test_text)
                
                print(f"🔒 Step 3: Write NDEF length ({len(ndef_record)} bytes)...")
                write_len = [0x00, 0xD6, 0x00, 0x00, 0x02, (len(ndef_record) >> 8) & 0xFF, len(ndef_record) & 0xFF]
                response, sw1, sw2 = connection.transmit(write_len)
                
                print(f"📥 Length Write: SW={sw1:02X}{sw2:02X}")
                
                if sw1 == 0x90:
                    print("✅ NDEF length written successfully")
                    
                    print("🔒 Step 4: Write NDEF data...")
                    write_data = [0x00, 0xD6, 0x00, 0x02, len(ndef_record)] + list(ndef_record)
                    response, sw1, sw2 = connection.transmit(write_data)
                    
                    print(f"📥 Data Write: SW={sw1:02X}{sw2:02X}")
                    
                    if sw1 == 0x90:
                        print("🎉 NTAG 424 DNA programming successful!")
                        print(f"📝 Written: '{test_text}'")
                        reader.disconnect()
                        return True
                    else:
                        print(f"❌ Data write failed: SW={sw1:02X}{sw2:02X}")
                else:
                    print(f"❌ Length write failed: SW={sw1:02X}{sw2:02X}")
            else:
                print(f"❌ NDEF file selection failed: SW={sw1:02X}{sw2:02X}")
        else:
            print(f"❌ NDEF app selection failed: SW={sw1:02X}{sw2:02X}")
    
    except Exception as e:
        print(f"❌ Programming error: {e}")
    
    reader.disconnect()
    return False

def create_ndef_text_record(text: str) -> bytes:
    """Create NDEF text record using proven working format"""
    text_bytes = text.encode('utf-8')
    language_code = b'en'
    
    payload = bytes([len(language_code)]) + language_code + text_bytes
    flags = 0xD1  # MB=1, ME=1, CF=0, SR=1, IL=0, TNF=001
    type_field = b'T'
    
    return bytes([flags, len(type_field), len(payload)]) + type_field + payload

if __name__ == "__main__":
    success = test_direct_programming()
    if success:
        print("\n🎉 Direct programming test successful!")
        print("   The OMNIKEY 5422 + NTAG 424 DNA programming works!")
    else:
        print("\n❌ Direct programming test failed")
        print("   Check card placement and try again")
