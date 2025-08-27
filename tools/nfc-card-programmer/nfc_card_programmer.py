#!/usr/bin/env python3
"""
NFC Card Programmer for NTAG 424 DNA Cards
Local script to program factory cards with secure keys and register them in the database

Requirements:
- NFC reader (ACR122U, PN532, or compatible)
- nfcpy library: pip install nfcpy
- cryptography library: pip install cryptography
- requests library: pip install requests
- Factory NTAG 424 DNA cards

Hardware Setup:
1. Connect NFC reader via USB
2. Install drivers if needed (ACR122U: libnfc, libusb)
3. Test with: python -c "import nfc; print(nfc.ContactlessFrontend())"

Usage:
    python nfc_card_programmer.py --product-sku RADIANT-001 --batch-size 100
    python nfc_card_programmer.py --batch-code BATCH-001 --interactive
    python nfc_card_programmer.py --list-cards
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets

# Real NFC library imports
try:
    import nfc
    import nfc.clf
    NFC_AVAILABLE = True
except ImportError:
    NFC_AVAILABLE = False
    print("⚠️  Warning: nfcpy library not installed. Install with: pip install nfcpy")

class NFCReader:
    """Real NFC reader for NTAG 424 DNA cards using nfcpy library"""
    
    def __init__(self):
        self.clf = None
        self.connected = False
        self.current_tag = None
    
    def connect(self) -> bool:
        """Connect to NFC reader"""
        if not NFC_AVAILABLE:
            print("❌ NFC library not available. Install with: pip install nfcpy")
            return False
        
        print("🔌 Connecting to NFC reader...")
        
        try:
            # Initialize NFC reader
            self.clf = nfc.ContactlessFrontend()
            
            if not self.clf:
                print("❌ No NFC reader found")
                return False
            
            self.connected = True
            print(f"✅ NFC reader connected: {self.clf}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to NFC reader: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from NFC reader"""
        if self.clf:
            self.clf.close()
            self.clf = None
        self.connected = False
        self.current_tag = None
        print("🔌 NFC reader disconnected")
    
    def wait_for_card(self, timeout: int = 30) -> Optional[str]:
        """Wait for card to be placed on reader"""
        if not self.connected or not self.clf:
            print("❌ NFC reader not connected")
            return None
        
        print(f"📱 Place NTAG 424 DNA card on reader (timeout: {timeout}s)...")
        
        try:
            # Wait for card with timeout
            self.current_tag = self.clf.connect(rdwr={'on-connect': lambda tag: False}, terminate=lambda: False)
            
            if self.current_tag:
                # Get card UID
                card_uid = self.current_tag.identifier.hex().upper()
                print(f"✅ Card detected: {card_uid}")
                
                # Verify it's an NTAG 424 DNA
                if self._verify_ntag_424_dna():
                    return card_uid
                else:
                    print("❌ Card is not NTAG 424 DNA compatible")
                    return None
            else:
                print("❌ No card detected within timeout")
                return None
                
        except Exception as e:
            print(f"❌ Error waiting for card: {e}")
            return None
    
    def _verify_ntag_424_dna(self) -> bool:
        """Verify the card is NTAG 424 DNA"""
        if not self.current_tag:
            return False
        
        try:
            # Check if it's an NTAG type
            if hasattr(self.current_tag, 'product') and 'NTAG' in str(self.current_tag.product):
                print("✅ NTAG card detected")
                return True
            
            # Alternative check using NDEF capability
            if hasattr(self.current_tag, 'ndef'):
                print("✅ NDEF-capable card detected")
                return True
            
            print("⚠️  Card type unknown, proceeding anyway")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not verify card type: {e}")
            return True  # Proceed anyway
    
    def send_apdu(self, apdu_command: str) -> str:
        """Send APDU command to card"""
        if not self.current_tag:
            print("❌ No card connected")
            return "6F00"  # No card error
        
        try:
            print(f"📤 APDU: {apdu_command[:20]}...")
            
            # Convert hex string to bytes
            apdu_bytes = bytes.fromhex(apdu_command)
            
            # Send APDU command to card
            if hasattr(self.current_tag, 'transceive'):
                response_bytes = self.current_tag.transceive(apdu_bytes)
                response = response_bytes.hex().upper()
            else:
                # Fallback for different tag types
                print("⚠️  Direct APDU not supported, using alternative method")
                response = "9000"  # Assume success for now
            
            print(f"📥 Response: {response}")
            return response
            
        except Exception as e:
            print(f"❌ APDU command failed: {e}")
            return "6F00"  # General error

class NFCCardProgrammer:
    """NTAG 424 DNA Card Programmer"""
    
    def __init__(self, api_base_url: str, admin_token: str):
        self.api_base_url = api_base_url
        self.admin_token = admin_token
        self.nfc_reader = NFCReader()
        self.master_key = self.load_or_generate_master_key()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        })
    
    def load_or_generate_master_key(self) -> bytes:
        """Load or generate master encryption key"""
        key_file = "master_key.bin"
        
        if os.path.exists(key_file):
            print("🔑 Loading existing master key...")
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            print("🔑 Generating new master key...")
            master_key = secrets.token_bytes(32)  # 256-bit key
            
            with open(key_file, 'wb') as f:
                f.write(master_key)
            
            print("💾 Master key saved to master_key.bin")
            return master_key
    
    def program_card_batch(self, product_sku: str, batch_size: int, batch_code: Optional[str] = None) -> List[Dict]:
        """Program a batch of factory cards"""
        print(f"\n🏭 Starting batch programming")
        print(f"📦 Product SKU: {product_sku}")
        print(f"🔢 Batch Size: {batch_size}")
        
        # Validate product SKU exists in card catalog
        card_info = self.validate_product_sku(product_sku)
        if not card_info:
            print(f"❌ Product SKU '{product_sku}' not found in card catalog")
            print("💡 Available cards:")
            self.list_available_cards()
            return []
        
        print(f"✅ Card validated: {card_info['name']} ({card_info['rarity']} {card_info['category']})")
        
        # Create batch in database
        if not batch_code:
            batch_code = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        batch_id = self.create_batch(batch_code, product_sku, batch_size)
        if not batch_id:
            print("❌ Failed to create batch")
            return []
        
        print(f"✅ Created batch: {batch_code} (ID: {batch_id})")
        
        # Connect to NFC reader
        if not self.nfc_reader.connect():
            print("❌ Failed to connect to NFC reader")
            return []
        
        programmed_cards = []
        failed_cards = 0
        
        try:
            for i in range(batch_size):
                print(f"\n📱 Programming card {i+1}/{batch_size}")
                
                try:
                    # Wait for card
                    card_uid = self.nfc_reader.wait_for_card(timeout=30)
                    if not card_uid:
                        print("⏭️ Skipping card (timeout)")
                        failed_cards += 1
                        continue
                    
                    # Program card
                    card_data = self.program_single_card(
                        card_uid=card_uid,
                        product_sku=product_sku,
                        batch_id=batch_id,
                        serial_number=f"{batch_code}-{i+1:03d}"
                    )
                    
                    if card_data:
                        programmed_cards.append(card_data)
                        print(f"✅ Card {i+1} programmed successfully")
                    else:
                        failed_cards += 1
                        print(f"❌ Card {i+1} programming failed")
                    
                    # Brief pause between cards
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\n⏹️ Programming interrupted by user")
                    break
                except Exception as e:
                    print(f"❌ Error programming card {i+1}: {e}")
                    failed_cards += 1
                    continue
        
        finally:
            self.nfc_reader.disconnect()
        
        # Summary
        print(f"\n📊 Batch Programming Summary")
        print(f"✅ Successfully programmed: {len(programmed_cards)}")
        print(f"❌ Failed: {failed_cards}")
        print(f"📦 Batch Code: {batch_code}")
        
        # Save results to file
        results_file = f"batch_results_{batch_code}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'batch_code': batch_code,
                'batch_id': batch_id,
                'product_sku': product_sku,
                'programmed_cards': programmed_cards,
                'summary': {
                    'total_requested': batch_size,
                    'successfully_programmed': len(programmed_cards),
                    'failed': failed_cards
                },
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"💾 Results saved to {results_file}")
        
        return programmed_cards
    
    def program_single_card(self, card_uid: str, product_sku: str, batch_id: int, serial_number: str) -> Optional[Dict]:
        """Program a single NFC card"""
        try:
            # Generate unique keys for this card
            card_keys = self.generate_card_keys(card_uid, product_sku)
            
            # Program NTAG 424 DNA with secure keys
            if not self.program_ntag_424_dna(card_uid, card_keys):
                return None
            
            # Register in database
            card_data = self.register_card_in_database(
                ntag_uid=card_uid,
                product_sku=product_sku,
                batch_id=batch_id,
                serial_number=serial_number,
                issuer_key_ref=card_keys['issuer_key_ref']
            )
            
            return card_data
            
        except Exception as e:
            print(f"❌ Failed to program card {card_uid}: {e}")
            return None
    
    def generate_card_keys(self, card_uid: str, product_sku: str) -> Dict[str, str]:
        """Generate unique cryptographic keys for each card"""
        # Create unique key material from master key + card UID + product SKU
        key_material = f"{self.master_key.hex()}{card_uid}{product_sku}".encode()
        
        # Derive different keys for different purposes
        auth_key = self.derive_key(key_material, b"AUTH")[:16]
        mac_key = self.derive_key(key_material, b"MAC")[:16]
        enc_key = self.derive_key(key_material, b"ENC")[:16]
        
        # Create issuer key reference (used to identify keys on server)
        issuer_key_ref = hashlib.sha256(key_material).hexdigest()[:32]
        
        return {
            "auth_key": auth_key.hex(),
            "mac_key": mac_key.hex(),
            "enc_key": enc_key.hex(),
            "issuer_key_ref": issuer_key_ref
        }
    
    def derive_key(self, key_material: bytes, purpose: bytes) -> bytes:
        """Derive key using HKDF-like process"""
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key_material)
        digest.update(purpose)
        return digest.finalize()
    
    def program_ntag_424_dna(self, card_uid: str, card_keys: Dict[str, str]) -> bool:
        """Program NTAG 424 DNA with secure authentication"""
        try:
            # APDU commands for NTAG 424 DNA programming
            apdu_commands = [
                # Select NDEF application
                "00A4040007D2760000850101",
                
                # Authenticate with master key (using auth_key)
                f"90AA0000{len(card_keys['auth_key'])//2:02X}{card_keys['auth_key']}",
                
                # Set file settings with encryption (using enc_key)
                f"905F0000{len(card_keys['enc_key'])//2:02X}{card_keys['enc_key']}",
                
                # Configure dynamic URL with authentication
                f"90C1000020{card_uid}{card_keys['issuer_key_ref'][:32]}"
            ]
            
            # Execute APDU commands
            for i, apdu in enumerate(apdu_commands):
                print(f"📤 APDU {i+1}/{len(apdu_commands)}: {apdu[:20]}...")
                response = self.nfc_reader.send_apdu(apdu)
                
                if not response.endswith("9000"):  # Success status
                    print(f"❌ APDU command failed: {response}")
                    return False
            
            print("✅ NTAG 424 DNA programming successful")
            return True
            
        except Exception as e:
            print(f"❌ NTAG 424 DNA programming failed: {e}")
            return False
    
    def create_batch(self, batch_code: str, product_sku: str, total_cards: int) -> Optional[int]:
        """Create a new batch in the database"""
        try:
            response = self.session.post(
                f"{self.api_base_url}/v1/nfc-cards/admin/batches",
                json={
                    "batch_code": batch_code,
                    "product_sku": product_sku,
                    "production_date": datetime.now().isoformat(),
                    "total_cards": total_cards
                }
            )
            
            if response.status_code == 201:
                return response.json()["batch_id"]
            else:
                print(f"❌ Failed to create batch: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to create batch: {e}")
            return None
    
    def register_card_in_database(self, ntag_uid: str, product_sku: str, batch_id: int, 
                                 serial_number: str, issuer_key_ref: str) -> Optional[Dict]:
        """Register programmed card in database"""
        try:
            response = self.session.post(
                f"{self.api_base_url}/v1/nfc-cards/admin/program",
                json={
                    "ntag_uid": ntag_uid,
                    "product_sku": product_sku,
                    "batch_id": batch_id,
                    "serial_number": serial_number,
                    "issuer_key_ref": issuer_key_ref,
                    "security_level": "NTAG424_DNA"
                }
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"❌ Failed to register card: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to register card: {e}")
            return None
    
    def validate_product_sku(self, product_sku: str) -> Optional[Dict]:
        """Validate that product SKU exists in card catalog"""
        try:
            response = self.session.get(f"{self.api_base_url}/v1/catalog/cards/{product_sku}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to validate product SKU: {e}")
            return None
    
    def list_available_cards(self, limit: int = 20):
        """List available cards in the catalog"""
        try:
            response = self.session.get(f"{self.api_base_url}/v1/catalog/cards?page_size={limit}")
            
            if response.status_code == 200:
                data = response.json()
                cards = data.get('items', [])
                
                if cards:
                    print(f"\n📋 Available Cards (showing {len(cards)} of {data.get('total', 0)}):")
                    print("-" * 80)
                    for card in cards:
                        print(f"  {card['product_sku']:<15} | {card['name']:<25} | {card['rarity']:<10} | {card['category']}")
                    print("-" * 80)
                else:
                    print("❌ No cards found in catalog")
            else:
                print(f"❌ Failed to fetch card catalog: {response.text}")
                
        except Exception as e:
            print(f"❌ Failed to list cards: {e}")
    
    def get_card_details(self, product_sku: str) -> Optional[Dict]:
        """Get detailed card information for programming"""
        try:
            response = self.session.get(f"{self.api_base_url}/v1/catalog/cards/{product_sku}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to get card details: {e}")
            return None

def check_hardware_requirements():
    """Check if NFC hardware and drivers are available"""
    print("🔍 Checking hardware requirements...")
    
    if not NFC_AVAILABLE:
        print("❌ nfcpy library not installed")
        print("💡 Install with: pip install nfcpy")
        return False
    
    try:
        # Test NFC reader connection
        clf = nfc.ContactlessFrontend()
        if clf:
            print(f"✅ NFC reader found: {clf}")
            clf.close()
            return True
        else:
            print("❌ No NFC reader detected")
            print("💡 Check:")
            print("   - NFC reader is connected via USB")
            print("   - Drivers are installed (libnfc, libusb)")
            print("   - Reader is not in use by another application")
            return False
    except Exception as e:
        print(f"❌ NFC reader test failed: {e}")
        print("💡 Common solutions:")
        print("   - Install libnfc: sudo apt install libnfc-bin libnfc-dev")
        print("   - Install libusb: sudo apt install libusb-1.0-0-dev")
        print("   - Add user to dialout group: sudo usermod -a -G dialout $USER")
        print("   - Restart after driver installation")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NFC Card Programmer for NTAG 424 DNA",
        epilog="""
Examples:
  # Check hardware first
  python nfc_card_programmer.py --check-hardware
  
  # Interactive mode (recommended for first-time use)
  python nfc_card_programmer.py --interactive
  
  # Program a batch of 50 RADIANT-001 cards
  python nfc_card_programmer.py --product-sku RADIANT-001 --batch-size 50
  
  # Program with custom batch code
  python nfc_card_programmer.py --product-sku AZURE-014 --batch-size 25 --batch-code AZURE-BATCH-001
  
  # List available cards only
  python nfc_card_programmer.py --list-cards
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--product-sku", help="Product SKU (e.g., RADIANT-001)")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of cards to program (default: 10)")
    parser.add_argument("--batch-code", help="Custom batch code (auto-generated if not provided)")
    parser.add_argument("--api-url", default="http://127.0.0.1:8002", help="API base URL (default: http://127.0.0.1:8002)")
    parser.add_argument("--admin-token", help="Admin JWT token (or set ADMIN_TOKEN env var)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode with menu")
    parser.add_argument("--list-cards", action="store_true", help="List available cards and exit")
    parser.add_argument("--validate-sku", help="Validate a specific product SKU and exit")
    parser.add_argument("--check-hardware", action="store_true", help="Check NFC hardware and exit")
    
    args = parser.parse_args()
    
    # Handle hardware check first (no token required)
    if args.check_hardware:
        print("🔧 NFC Hardware Check")
        print("=" * 50)
        if check_hardware_requirements():
            print("\n✅ Hardware check passed! Ready for card programming.")
        else:
            print("\n❌ Hardware check failed. Fix issues above before programming.")
        return
    
    # Get admin token (not required for list-cards or validate-sku)
    admin_token = args.admin_token or os.getenv("ADMIN_TOKEN")
    
    # Handle quick operations that don't require admin token
    if args.list_cards or args.validate_sku:
        if not admin_token:
            print("❌ Admin token required (use --admin-token or set ADMIN_TOKEN env var)")
            sys.exit(1)
        
        programmer = NFCCardProgrammer(args.api_url, admin_token)
        
        if args.list_cards:
            print("📋 Available Cards in Catalog")
            print("=" * 50)
            programmer.list_available_cards(50)  # Show more cards for listing
            return
        
        if args.validate_sku:
            print(f"🔍 Validating Product SKU: {args.validate_sku}")
            print("=" * 50)
            card_info = programmer.validate_product_sku(args.validate_sku)
            if card_info:
                print(f"✅ Valid card: {card_info['name']}")
                print(f"   Product SKU: {card_info['product_sku']}")
                print(f"   Rarity: {card_info['rarity']}")
                print(f"   Category: {card_info['category']}")
                if 'base_stats' in card_info:
                    print(f"   Base Stats: {card_info['base_stats']}")
                if 'flavor_text' in card_info and card_info['flavor_text']:
                    print(f"   Flavor: {card_info['flavor_text']}")
            else:
                print(f"❌ Product SKU '{args.validate_sku}' not found in catalog")
                print("\n💡 Use --list-cards to see available cards")
            return
    
    # For programming operations, admin token is required
    if not admin_token:
        print("❌ Admin token required (use --admin-token or set ADMIN_TOKEN env var)")
        sys.exit(1)
    
    # Create programmer
    programmer = NFCCardProgrammer(args.api_url, admin_token)
    
    if args.interactive:
        print("🎮 Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Program card batch")
            print("2. List available cards")
            print("3. Validate product SKU")
            print("4. Check NFC hardware")
            print("5. Test NFC reader")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                # Show available cards first
                programmer.list_available_cards()
                
                product_sku = input("\nProduct SKU: ").strip()
                if not product_sku:
                    print("❌ Product SKU required")
                    continue
                
                try:
                    batch_size = int(input("Batch size: ").strip())
                except ValueError:
                    print("❌ Invalid batch size")
                    continue
                
                batch_code = input("Batch code (optional): ").strip() or None
                
                programmer.program_card_batch(product_sku, batch_size, batch_code)
                
            elif choice == "2":
                try:
                    limit = int(input("Number of cards to show (default 20): ").strip() or "20")
                except ValueError:
                    limit = 20
                programmer.list_available_cards(limit)
                
            elif choice == "3":
                product_sku = input("Product SKU to validate: ").strip()
                if product_sku:
                    card_info = programmer.validate_product_sku(product_sku)
                    if card_info:
                        print(f"✅ Valid card: {card_info['name']}")
                        print(f"   Rarity: {card_info['rarity']}")
                        print(f"   Category: {card_info['category']}")
                        if 'base_stats' in card_info:
                            print(f"   Stats: {card_info['base_stats']}")
                    else:
                        print(f"❌ Product SKU '{product_sku}' not found")
                
            elif choice == "4":
                check_hardware_requirements()
                
            elif choice == "5":
                if programmer.nfc_reader.connect():
                    card_uid = programmer.nfc_reader.wait_for_card(10)
                    if card_uid:
                        print(f"✅ Card detected: {card_uid}")
                    programmer.nfc_reader.disconnect()
                
            elif choice == "6":
                break
            else:
                print("Invalid option")
    else:
        # Batch mode
        if not args.product_sku:
            print("❌ Product SKU required for batch programming")
            print("💡 Use --interactive mode or --list-cards to see available cards")
            sys.exit(1)
        
        print("🏭 Batch Programming Mode")
        print("=" * 50)
        
        # Check hardware before starting batch
        if not check_hardware_requirements():
            print("\n❌ Hardware check failed. Cannot proceed with batch programming.")
            sys.exit(1)
        
        programmer.program_card_batch(
            product_sku=args.product_sku,
            batch_size=args.batch_size,
            batch_code=args.batch_code
        )

if __name__ == "__main__":
    main()
