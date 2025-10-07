#!/usr/bin/env python3
"""
OMNIKEY 5422 Specific NFC Reader
Uses PC/SC protocol for professional-grade OMNIKEY readers
"""

import time
from typing import Optional

# PC/SC library for professional smartcard readers
try:
    from smartcard.System import readers
    from smartcard.util import toHexString, toBytes
    from smartcard.CardConnection import CardConnection
    from smartcard.CardType import AnyCardType
    from smartcard.CardRequest import CardRequest
    from smartcard.Exceptions import CardRequestTimeoutException, CardConnectionException
    PCSC_AVAILABLE = True
except ImportError:
    PCSC_AVAILABLE = False
    print("⚠️  Warning: pyscard library not installed. Install with: pip install pyscard")

class OmniekeyReader:
    """OMNIKEY 5422 specific NFC reader using PC/SC protocol"""
    
    def __init__(self):
        self.connection = None
        self.connected = False
        self.reader = None
        
    def connect(self) -> bool:
        """Connect to OMNIKEY 5422 reader"""
        if not PCSC_AVAILABLE:
            print("❌ pyscard library not available. Install with: pip install pyscard")
            return False
        
        print("🔌 Connecting to OMNIKEY 5422 via PC/SC...")
        
        try:
            # Get available readers
            available_readers = readers()
            
            if not available_readers:
                print("❌ No smartcard readers found")
                return False
            
            # Find OMNIKEY 5422
            omnikey_reader = None
            for reader in available_readers:
                reader_name = str(reader)
                print(f"📱 Found reader: {reader_name}")
                
                if "OMNIKEY" in reader_name or "5422" in reader_name or "HID" in reader_name:
                    omnikey_reader = reader
                    print(f"✅ OMNIKEY 5422 detected: {reader_name}")
                    break
            
            if not omnikey_reader:
                # Use first available reader as fallback
                omnikey_reader = available_readers[0]
                print(f"⚠️  Using first available reader: {omnikey_reader}")
            
            self.reader = omnikey_reader
            self.connected = True
            return True
            
        except Exception as e:
            print(f"❌ OMNIKEY connection failed: {e}")
            return False
    
    def wait_for_card(self, timeout: int = 30) -> Optional[str]:
        """Wait for NTAG 424 DNA card and MAINTAIN connection for programming"""
        if not self.connected:
            print("❌ OMNIKEY reader not connected")
            return None
        
        print(f"📱 Place NTAG 424 DNA card on OMNIKEY 5422 (timeout: {timeout}s)...")
        
        try:
            # Create card request
            cardtype = AnyCardType()
            cardrequest = CardRequest(timeout=timeout, cardType=cardtype, readers=[self.reader])
            
            # Wait for card
            cardservice = cardrequest.waitforcard()
            
            if cardservice:
                # Connect to card and KEEP connection for programming
                cardservice.connection.connect()
                self.connection = cardservice.connection
                
                # Get card ATR (Answer To Reset)
                atr = cardservice.connection.getATR()
                atr_hex = toHexString(atr).replace(' ', '')
                print(f"📋 Card ATR: {atr_hex}")
                
                # Get card UID using standard NFC commands
                uid = self._get_card_uid()
                
                if uid:
                    print(f"✅ Card UID detected: {uid}")
                    print("🔗 Card connection maintained for programming")
                    # DON'T disconnect here - keep connection for programming
                    return uid
                else:
                    print("❌ Could not read card UID")
                    self.connection = None
                    return None
            else:
                print("❌ No card detected within timeout")
                return None
                
        except CardRequestTimeoutException:
            print("⏰ Card detection timeout - no card placed")
            return None
        except Exception as e:
            print(f"❌ Error waiting for card: {e}")
            return None
    
    def _get_card_uid(self) -> Optional[str]:
        """Get card UID using APDU commands"""
        if not self.connection:
            return None
        
        try:
            # Standard APDU command to get UID (works with NTAG 424 DNA)
            # Command: FF CA 00 00 00 (Get Data - UID)
            get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            
            response, sw1, sw2 = self.connection.transmit(get_uid_command)
            
            if sw1 == 0x90 and sw2 == 0x00:  # Success
                # Convert response to hex string
                uid_hex = toHexString(response).replace(' ', '').upper()
                return uid_hex
            else:
                print(f"⚠️  UID command failed: {sw1:02X}{sw2:02X}")
                
                # Alternative: Try different UID command
                alt_command = [0xFF, 0xCA, 0x01, 0x00, 0x00]
                response, sw1, sw2 = self.connection.transmit(alt_command)
                
                if sw1 == 0x90 and sw2 == 0x00:
                    uid_hex = toHexString(response).replace(' ', '').upper()
                    return uid_hex
                else:
                    print(f"❌ Alternative UID command failed: {sw1:02X}{sw2:02X}")
                    return None
                    
        except Exception as e:
            print(f"❌ UID reading error: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from OMNIKEY 5422"""
        try:
            if self.connection:
                self.connection.disconnect()
                self.connection = None
            
            self.connected = False
            print("🔌 OMNIKEY 5422 disconnected")
            
        except Exception as e:
            print(f"⚠️  Disconnect error: {e}")
    
    def is_card_connected(self) -> bool:
        """Check if card is still connected"""
        if not self.connection:
            return False
        
        try:
            # Test connection with a simple command
            get_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            response, sw1, sw2 = self.connection.transmit(get_uid)
            return sw1 == 0x90
        except:
            return False
    
    def program_ntag_424_dna(self, card_keys: dict) -> bool:
        """Program NTAG 424 DNA using proven working method"""
        if not self.connection:
            print("❌ No card connection")
            return False
        
        # Skip connection test - proceed directly since card was just detected
        print("✅ Using existing card connection - proceeding with programming")
        
        try:
            print("🔒 Programming NTAG 424 DNA using proven method...")
            
            # Step 1: Select NDEF application (from your working doc)
            ndef_aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
            select_ndef = [0x00, 0xA4, 0x04, 0x00, len(ndef_aid)] + ndef_aid
            response, sw1, sw2 = self.connection.transmit(select_ndef)
            
            if sw1 != 0x90:
                print(f"❌ NDEF app selection failed: SW={sw1:02X}{sw2:02X}")
                return False
            
            print("✅ NDEF application selected")
            
            # Step 2: Select NDEF file directly (THE KEY STEP from your doc)
            select_ndef_file = [0x00, 0xA4, 0x00, 0x0C, 0x02, 0xE1, 0x04]
            response, sw1, sw2 = self.connection.transmit(select_ndef_file)
            
            if sw1 != 0x90:
                print(f"❌ NDEF file selection failed: SW={sw1:02X}{sw2:02X}")
                return False
            
            print("✅ NDEF file selected")
            
            # Step 3: Create NDEF record with card programming data
            card_info = f"DECKPORT:{card_keys.get('issuer_key_ref', 'UNKNOWN')[:8]}"
            ndef_record = self._create_ndef_text_record(card_info)
            
            # Step 4: Write NDEF length (from your working method)
            data_len = len(ndef_record)
            write_len = [0x00, 0xD6, 0x00, 0x00, 0x02, (data_len >> 8) & 0xFF, data_len & 0xFF]
            response, sw1, sw2 = self.connection.transmit(write_len)
            
            if sw1 != 0x90:
                print(f"❌ Length write failed: SW={sw1:02X}{sw2:02X}")
                return False
            
            print("✅ NDEF length written")
            
            # Step 5: Write NDEF data (from your working method)
            write_data = [0x00, 0xD6, 0x00, 0x02, len(ndef_record)] + list(ndef_record)
            response, sw1, sw2 = self.connection.transmit(write_data)
            
            if sw1 == 0x90:
                print("🎉 NTAG 424 DNA programming successful!")
                print(f"📝 Written: '{card_info}'")
                return True
            else:
                print(f"❌ Data write failed: SW={sw1:02X}{sw2:02X}")
                return False
            
        except Exception as e:
            print(f"❌ Programming error: {e}")
            return False
    
    def _create_ndef_text_record(self, text: str) -> bytes:
        """Create NDEF text record using your working format"""
        text_bytes = text.encode('utf-8')
        language_code = b'en'
        
        payload = bytes([len(language_code)]) + language_code + text_bytes
        flags = 0xD1  # MB=1, ME=1, CF=0, SR=1, IL=0, TNF=001 (exact from your doc)
        type_field = b'T'
        
        return bytes([flags, len(type_field), len(payload)]) + type_field + payload

def test_omnikey_5422():
    """Test OMNIKEY 5422 functionality"""
    print("🧪 Testing OMNIKEY 5422 Reader")
    print("=" * 35)
    
    reader = OmniekeyReader()
    
    if reader.connect():
        print("✅ OMNIKEY 5422 connected successfully")
        
        # Test card detection
        uid = reader.wait_for_card(timeout=10)
        
        if uid:
            print(f"✅ Card detected: {uid}")
        else:
            print("⚠️  No card detected (place card on reader)")
        
        reader.disconnect()
        return True
    else:
        print("❌ Failed to connect to OMNIKEY 5422")
        return False

if __name__ == "__main__":
    test_omnikey_5422()
