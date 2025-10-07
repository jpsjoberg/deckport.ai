#!/usr/bin/env python3
"""
NFC Card Programmer for NTAG 424 DNA Cards
Production-ready version optimized for OMNIKEY 5422
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import requests
import secrets
from secure_programmer import SecureNTAG424Programmer
from crypto_security import get_crypto_manager

# Real NFC library imports
try:
    import nfc
    import nfc.clf
    NFC_AVAILABLE = True
except ImportError:
    NFC_AVAILABLE = False

# OMNIKEY specific imports
try:
    from omnikey_5422_reader import OmniekeyReader
    OMNIKEY_AVAILABLE = True
except ImportError:
    OMNIKEY_AVAILABLE = False

class NFCReader:
    """Universal NFC reader with OMNIKEY 5422 optimization"""
    
    def __init__(self):
        self.clf = None
        self.connected = False
        self.current_tag = None
        self.omnikey_reader = None
        
        if OMNIKEY_AVAILABLE:
            self.omnikey_reader = OmniekeyReader()
            self.reader_type = "OMNIKEY 5422"
            print("🎯 OMNIKEY 5422 specific reader available")
        else:
            self.reader_type = "Standard NFC"
    
    def connect(self) -> bool:
        """Connect to NFC reader"""
        # Try OMNIKEY first
        if self.omnikey_reader:
            if self.omnikey_reader.connect():
                self.connected = True
                return True
        
        # Fallback to standard nfcpy
        if NFC_AVAILABLE:
            try:
                self.clf = nfc.ContactlessFrontend()
                if self.clf:
                    self.connected = True
                    return True
            except:
                pass
        
        print("❌ No compatible NFC reader found")
        return False
    
    def wait_for_card(self, timeout: int = 30) -> Optional[str]:
        """Wait for card"""
        if not self.connected:
            return None
        
        if self.omnikey_reader:
            return self.omnikey_reader.wait_for_card(timeout)
        
        # Standard nfcpy fallback
        try:
            self.current_tag = self.clf.connect(rdwr={'on-connect': lambda tag: False})
            if self.current_tag:
                return self.current_tag.identifier.hex().upper()
        except:
            pass
        
        return None
    
    def disconnect(self):
        """Disconnect reader"""
        if self.omnikey_reader:
            self.omnikey_reader.disconnect()
        if self.clf:
            self.clf.close()
        self.connected = False

class NFCCardProgrammer:
    """Production-ready NTAG 424 DNA Card Programmer"""
    
    def __init__(self, api_url: str, admin_token: str, use_crypto: bool = True):
        self.api_url = api_url
        self.admin_token = admin_token
        self.use_crypto = use_crypto
        self.nfc_reader = NFCReader()
        self.master_key = self._load_or_generate_master_key()
        
        # Initialize crypto components for maximum security
        if use_crypto:
            try:
                self.crypto_manager = get_crypto_manager()
                self.secure_programmer = SecureNTAG424Programmer()
                print("🔒 Maximum security mode enabled")
            except ImportError as e:
                print(f"⚠️  Crypto libraries not available, using basic mode: {e}")
                self.use_crypto = False
        
        # Setup HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        })
    
    def _load_or_generate_master_key(self) -> bytes:
        """Load or generate master key"""
        key_file = "master_key.bin"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            print("🔑 Generating new master key...")
            master_key = secrets.token_bytes(32)
            with open(key_file, 'wb') as f:
                f.write(master_key)
            print("💾 Master key saved to master_key.bin")
            return master_key
    
    def list_available_cards(self, limit: int = 20):
        """List available cards from catalog"""
        try:
            response = self.session.get(f"{self.api_url}/v1/catalog/cards?page_size={limit}")
            
            if response.status_code == 200:
                data = response.json()
                cards = data.get('items', [])
                
                if cards:
                    print(f"📋 Available Cards (showing {len(cards)}):")
                    print("-" * 80)
                    for card in cards:
                        print(f"  {card['product_sku']:<15} | {card['name']:<25} | {card['rarity']:<10} | {card['category']}")
                    print("-" * 80)
                else:
                    print("❌ No cards found in catalog")
            else:
                print(f"❌ Failed to fetch cards: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error listing cards: {e}")
    
    def validate_product_sku(self, product_sku: str) -> Optional[dict]:
        """Validate product SKU"""
        try:
            response = self.session.get(f"{self.api_url}/v1/catalog/cards/{product_sku}")
            
            if response.status_code == 200:
                card_info = response.json()
                print(f"✅ Valid card: {card_info['name']} ({card_info['rarity']} {card_info['category']})")
                return card_info
            else:
                print(f"❌ Product SKU '{product_sku}' not found")
                return None
                
        except Exception as e:
            print(f"❌ Error validating SKU: {e}")
            return None
    
    def program_batch(self, product_sku: str, batch_size: int, batch_code: str = None):
        """Program a batch of cards"""
        print("\n🏭 Starting batch programming")
        print(f"📦 Product SKU: {product_sku}")
        print(f"🔢 Batch Size: {batch_size}")
        
        # Validate card exists
        card_info = self.validate_product_sku(product_sku)
        if not card_info:
            return
        
        # Generate batch code
        if not batch_code:
            batch_code = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create batch in database
        batch_id = self._create_batch(batch_code, product_sku, batch_size)
        if not batch_id:
            print("❌ Failed to create batch")
            return
        
        print(f"✅ Created batch: {batch_code} (ID: {batch_id})")
        
        # Connect to NFC reader
        if not self.nfc_reader.connect():
            print("❌ Failed to connect to NFC reader")
            return
        
        # Program cards
        programmed_cards = []
        for i in range(batch_size):
            print(f"\n📱 Programming card {i+1}/{batch_size}")
            
            card_uid = self.nfc_reader.wait_for_card(30)
            if card_uid:
                # Program immediately while card is still connected
                print("🚀 Programming immediately to maintain connection...")
                success = self._program_single_card(card_uid, product_sku, batch_code, i+1)
                if success:
                    programmed_cards.append({'uid': card_uid, 'serial': f"{batch_code}-{i+1:03d}"})
                    print(f"✅ Card {i+1} programmed: {card_uid}")
                else:
                    print(f"❌ Card {i+1} failed")
                    print("💡 Try keeping card firmly on reader during programming")
            else:
                print(f"⏭️ Skipping card {i+1} (timeout)")
        
        self.nfc_reader.disconnect()
        
        # Results
        print(f"\n📊 Batch Programming Summary")
        print(f"✅ Successfully programmed: {len(programmed_cards)}")
        print(f"❌ Failed: {batch_size - len(programmed_cards)}")
        print(f"📦 Batch Code: {batch_code}")
    
    def _create_batch(self, batch_code: str, product_sku: str, total_cards: int) -> Optional[int]:
        """Create batch in database"""
        try:
            response = self.session.post(
                f"{self.api_url}/v1/nfc-cards/admin/batches",
                json={
                    "batch_code": batch_code,
                    "product_sku": product_sku,
                    "total_cards": total_cards,
                    "production_date": datetime.now().isoformat()
                }
            )
            
            if response.status_code == 201:
                return response.json()["batch_id"]
            else:
                print(f"❌ Batch creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Batch creation error: {e}")
            return None
    
    def _program_single_card(self, card_uid: str, product_sku: str, batch_code: str, card_number: int) -> bool:
        """Program NTAG 424 DNA with maximum security or basic method"""
        
        # Use secure programming if crypto is enabled
        if self.use_crypto:
            return self._program_single_card_secure(card_uid, product_sku, batch_code, card_number)
        else:
            return self._program_single_card_basic(card_uid, product_sku, batch_code, card_number)
    
    def _program_single_card_secure(self, card_uid: str, product_sku: str, batch_code: str, card_number: int) -> bool:
        """Program NTAG 424 DNA with maximum cryptographic security"""
        try:
            print(f"🔒 Programming with MAXIMUM SECURITY: {card_uid}")
            
            # Generate serial number
            serial_number = f"{batch_code}-{card_number:03d}"
            
            # Use secure programmer
            success = self.secure_programmer.program_secure_card(card_uid, product_sku, serial_number)
            
            if success:
                # Get cryptographic authentication data
                auth_data = self.crypto_manager.get_card_auth_data(card_uid)
                
                # Register in database with crypto data
                response = self.session.post(
                    f"{self.api_url}/v1/nfc-cards/admin/program",
                    json={
                        "ntag_uid": card_uid,
                        "product_sku": product_sku,
                        "serial_number": serial_number,
                        "security_level": "NTAG424_CRYPTO_MAX",
                        "issuer_key_ref": auth_data['issuer_key_ref'],
                        "auth_key_hash": auth_data['auth_key_hash'],
                        "enc_key_hash": auth_data['enc_key_hash'],
                        "mac_key_hash": auth_data['mac_key_hash']
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Database registration successful")
                    print(f"🔑 Activation code: {result.get('activation_code', 'N/A')}")
                    print(f"🔐 Card secured with unique crypto keys")
                    return True
                else:
                    print(f"❌ Database registration failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Secure programming failed: {e}")
            return False
    
    def _program_single_card_basic(self, card_uid: str, product_sku: str, batch_code: str, card_number: int) -> bool:
        """Program NTAG 424 DNA using basic method (fallback)"""
        try:
            print(f"🔒 Programming NTAG 424 DNA using proven method: {card_uid}")
            
            # Use your exact proven working method (bypass wrapper classes)
            from smartcard.System import readers
            from smartcard.CardRequest import CardRequest
            from smartcard.util import toHexString
            
            # Direct connection like your working method
            reader = readers()[0]  # OMNIKEY 5422
            cardrequest = CardRequest(readers=[reader], timeout=10)
            cardservice = cardrequest.waitforcard()
            
            connection = cardservice.connection
            connection.connect()
            
            # Your proven NDEF programming sequence
            # Step 1: Select NDEF application
            ndef_aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
            select_ndef = [0x00, 0xA4, 0x04, 0x00, len(ndef_aid)] + ndef_aid
            response, sw1, sw2 = connection.transmit(select_ndef)
            
            if sw1 != 0x90:
                print(f"❌ NDEF app selection failed: SW={sw1:02X}{sw2:02X}")
                connection.disconnect()
                return False
            
            # Step 2: Select NDEF file directly (THE KEY STEP)
            select_ndef_file = [0x00, 0xA4, 0x00, 0x0C, 0x02, 0xE1, 0x04]
            response, sw1, sw2 = connection.transmit(select_ndef_file)
            
            if sw1 != 0x90:
                print(f"❌ NDEF file selection failed: SW={sw1:02X}{sw2:02X}")
                connection.disconnect()
                return False
            
            # Step 3: Write DECKPORT card data
            card_data_text = f"DECKPORT:{product_sku}:{card_uid[:8]}"
            ndef_record = self._create_ndef_text_record(card_data_text)
            
            # Step 4: Write NDEF length
            data_len = len(ndef_record)
            write_len = [0x00, 0xD6, 0x00, 0x00, 0x02, (data_len >> 8) & 0xFF, data_len & 0xFF]
            response, sw1, sw2 = connection.transmit(write_len)
            
            if sw1 != 0x90:
                print(f"❌ Length write failed: SW={sw1:02X}{sw2:02X}")
                connection.disconnect()
                return False
            
            # Step 5: Write NDEF data
            write_data = [0x00, 0xD6, 0x00, 0x02, len(ndef_record)] + list(ndef_record)
            response, sw1, sw2 = connection.transmit(write_data)
            
            if sw1 == 0x90:
                print("🎉 NTAG 424 DNA programming successful!")
                print(f"📝 Written: '{card_data_text}'")
                
                connection.disconnect()
                
                # Register in database
                response = self.session.post(
                    f"{self.api_url}/v1/nfc-cards/admin/program",
                    json={
                        "ntag_uid": card_uid,
                        "product_sku": product_sku,
                        "serial_number": f"{batch_code}-{card_number:03d}"
                    }
                )
                
                if response.status_code == 201:
                    print("✅ Card registered in database")
                    return True
                else:
                    print(f"❌ Database registration failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
            else:
                print(f"❌ Data write failed: SW={sw1:02X}{sw2:02X}")
                connection.disconnect()
                return False
                
        except Exception as e:
            print(f"❌ Card programming error: {e}")
            return False
    
    def _create_ndef_text_record(self, text: str) -> bytes:
        """Create NDEF text record using your proven working format"""
        text_bytes = text.encode('utf-8')
        language_code = b'en'
        
        payload = bytes([len(language_code)]) + language_code + text_bytes
        flags = 0xD1  # The exact flags from your working implementation
        type_field = b'T'
        
        return bytes([flags, len(type_field), len(payload)]) + type_field + payload

def interactive_mode(programmer, api_url):
    """Interactive menu"""
    while True:
        print("\n🎮 Interactive Mode")
        print("=" * 50)
        security_status = "🔒 MAXIMUM SECURITY" if programmer.use_crypto else "🔓 Basic Security"
        print(f"Security Mode: {security_status}")
        print("Options:")
        print("1. Program card batch")
        print("2. List available cards")
        print("3. Validate product SKU")
        print("4. Check NFC hardware")
        print("5. Test NFC reader")
        print("6. Toggle security mode")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "6":
            # Toggle security mode
            programmer.use_crypto = not programmer.use_crypto
            if programmer.use_crypto:
                try:
                    programmer.crypto_manager = get_crypto_manager()
                    programmer.secure_programmer = SecureNTAG424Programmer()
                    print("🔒 Switched to MAXIMUM SECURITY mode")
                except ImportError as e:
                    print(f"❌ Cannot enable crypto mode: {e}")
                    programmer.use_crypto = False
            else:
                print("🔓 Switched to Basic Security mode")
            continue
        elif choice == "7":
            break
        elif choice == "1":
            if not programmer:
                token = input("Enter admin token: ").strip()
                programmer = NFCCardProgrammer(api_url, token)
            
            sku = input("Product SKU: ").strip()
            try:
                batch_size = int(input("Batch size: ") or "1")
            except ValueError:
                print("❌ Invalid batch size")
                continue
            
            batch_code = input("Batch code (optional): ").strip() or None
            programmer.program_batch(sku, batch_size, batch_code)
            
        elif choice == "2":
            if not programmer:
                token = input("Enter admin token: ").strip()
                programmer = NFCCardProgrammer(api_url, token)
            programmer.list_available_cards()
            
        elif choice == "3":
            if not programmer:
                token = input("Enter admin token: ").strip()
                programmer = NFCCardProgrammer(api_url, token)
            sku = input("Product SKU to validate: ").strip()
            programmer.validate_product_sku(sku)
            
        elif choice == "4":
            reader = NFCReader()
            if reader.connect():
                print("✅ NFC reader connection successful")
                reader.disconnect()
            else:
                print("❌ NFC reader connection failed")
                
        elif choice == "5":
            reader = NFCReader()
            if reader.connect():
                print("📱 Place card on reader...")
                uid = reader.wait_for_card(10)
                if uid:
                    print(f"✅ Test successful: {uid}")
                else:
                    print("❌ No card detected")
                reader.disconnect()
        else:
            print("❌ Invalid option")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="NFC Card Programmer for NTAG 424 DNA Cards")
    
    parser.add_argument("--product-sku", help="Product SKU (e.g., HERO_CRIMSON_140)")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of cards (default: 10)")
    parser.add_argument("--batch-code", help="Custom batch code")
    parser.add_argument("--api-url", default="https://api.deckport.ai", help="API URL")
    parser.add_argument("--admin-token", help="Admin JWT token")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--list-cards", action="store_true", help="List available cards")
    parser.add_argument("--validate-sku", help="Validate product SKU")
    
    args = parser.parse_args()
    
    # Get admin token
    admin_token = args.admin_token or os.getenv("ADMIN_TOKEN")
    
    # Quick operations
    if args.list_cards or args.validate_sku:
        if not admin_token:
            print("❌ Admin token required")
            sys.exit(1)
        
        programmer = NFCCardProgrammer(args.api_url, admin_token)
        
        if args.list_cards:
            programmer.list_available_cards(50)
            return
        
        if args.validate_sku:
            programmer.validate_product_sku(args.validate_sku)
            return
    
    # Interactive mode
    if args.interactive:
        programmer = NFCCardProgrammer(args.api_url, admin_token) if admin_token else None
        interactive_mode(programmer, args.api_url)
    
    # Direct programming
    elif args.product_sku:
        if not admin_token:
            print("❌ Admin token required for programming")
            sys.exit(1)
        
        programmer = NFCCardProgrammer(args.api_url, admin_token)
        programmer.program_batch(args.product_sku, args.batch_size, args.batch_code)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
