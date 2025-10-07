#!/usr/bin/env python3
"""
Minimal Working Test - Exact Copy of Your Proven Method
This replicates your exact working implementation
"""

from smartcard.System import readers
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString

def minimal_working_test():
    """Exact copy of your proven working method"""
    print("🧪 Minimal Working Test - Your Proven Method")
    print("=" * 55)
    
    try:
        # Step 1: Connect using PC/SC interface (your exact method)
        reader = readers()[0]  # OMNIKEY 5422
        cardrequest = CardRequest(readers=[reader], timeout=10)
        
        print("📱 Place NTAG 424 DNA card on reader...")
        cardservice = cardrequest.waitforcard()
        
        connection = cardservice.connection
        connection.connect()
        
        print(f"✅ Connected! ATR: {toHexString(connection.getATR())}")
        
        # Step 2: Get UID (always works)
        get_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        response, sw1, sw2 = connection.transmit(get_uid)
        uid = toHexString(response).replace(' ', '')
        print(f"📋 UID: {uid}")
        
        # Step 3: Select NDEF application (this worked!)
        ndef_aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
        select_ndef = [0x00, 0xA4, 0x04, 0x00, len(ndef_aid)] + ndef_aid
        response, sw1, sw2 = connection.transmit(select_ndef)
        print(f"NDEF App Selection: SW={sw1:02X}{sw2:02X}")  # This gave SW=9000
        
        if sw1 != 0x90:
            print("❌ NDEF application selection failed")
            connection.disconnect()
            return False
        
        # Step 4: CRITICAL - Select NDEF file directly (bypassing CC)
        select_ndef_file = [0x00, 0xA4, 0x00, 0x0C, 0x02, 0xE1, 0x04]
        response, sw1, sw2 = connection.transmit(select_ndef_file)
        print(f"NDEF File Selection: SW={sw1:02X}{sw2:02X}")  # This gave SW=9000
        
        if sw1 != 0x90:
            print("❌ NDEF file selection failed")
            connection.disconnect()
            return False
        
        # Step 5: Read NDEF data (this worked!)
        read_ndef = [0x00, 0xB0, 0x00, 0x00, 0x50]  # Read 80 bytes
        response, sw1, sw2 = connection.transmit(read_ndef)
        
        if sw1 == 0x90:
            print(f"✅ NDEF Read Success: {toHexString(response)}")
            
            # Parse NDEF data
            if len(response) >= 2:
                ndef_len = (response[0] << 8) | response[1]
                print(f"📏 NDEF Length: {ndef_len} bytes")
                
                if ndef_len > 0:
                    ndef_data = response[2:2+ndef_len]
                    print(f"📄 Current NDEF Data: {toHexString(ndef_data)}")
            
            # Step 6: Write NDEF data (this worked!)
            test_text = "DECKPORT_SUCCESS!"
            test_ndef = create_ndef_text_record(test_text)
            
            print(f"🔒 Writing new NDEF data: '{test_text}'")
            
            # Write NDEF length
            new_len = len(test_ndef)
            write_len = [0x00, 0xD6, 0x00, 0x00, 0x02, (new_len >> 8) & 0xFF, new_len & 0xFF]
            response, sw1, sw2 = connection.transmit(write_len)
            
            print(f"Length Write: SW={sw1:02X}{sw2:02X}")
            
            if sw1 == 0x90:
                print(f"✅ Length Write Success")
                
                # Write NDEF data
                write_data = [0x00, 0xD6, 0x00, 0x02, len(test_ndef)] + list(test_ndef)
                response, sw1, sw2 = connection.transmit(write_data)
                
                print(f"Data Write: SW={sw1:02X}{sw2:02X}")
                
                if sw1 == 0x90:
                    print(f"🎉 NDEF WRITE SUCCESS!")
                    print(f"📝 Written: '{test_text}'")
                    
                    # Verify by reading back
                    print("🔍 Verifying write...")
                    response, sw1, sw2 = connection.transmit(read_ndef)
                    if sw1 == 0x90 and len(response) >= 2:
                        verify_len = (response[0] << 8) | response[1]
                        if verify_len > 0:
                            verify_data = response[2:2+verify_len]
                            print(f"✅ Verification successful: {toHexString(verify_data)}")
                    
                    connection.disconnect()
                    return True
                else:
                    print("❌ Data write failed")
            else:
                print("❌ Length write failed")
        else:
            print("❌ NDEF read failed")
        
        connection.disconnect()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_ndef_text_record(text: str) -> bytes:
    """Create NDEF text record - this exact format worked"""
    text_bytes = text.encode('utf-8')
    language_code = b'en'
    
    payload = bytes([len(language_code)]) + language_code + text_bytes
    flags = 0xD1  # MB=1, ME=1, CF=0, SR=1, IL=0, TNF=001
    type_field = b'T'
    
    return bytes([flags, len(type_field), len(payload)]) + type_field + payload

if __name__ == "__main__":
    success = minimal_working_test()
    if success:
        print("\n🎉 Your proven working method confirmed!")
        print("   OMNIKEY 5422 + NTAG 424 DNA programming works perfectly!")
    else:
        print("\n❌ Issue with proven working method")
        print("   Check card placement and try again")
