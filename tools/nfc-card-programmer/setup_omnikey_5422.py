#!/usr/bin/env python3
"""
OMNIKEY 5422 + NTAG 424 DNA Setup Script
Optimized for your specific hardware configuration
"""

import sys
import os
import subprocess
import requests

def check_dependencies():
    """Check if all dependencies are installed"""
    print("🔍 Checking Dependencies for OMNIKEY 5422")
    print("=" * 50)
    
    # Check Python libraries
    required_libs = ['nfc', 'cryptography', 'requests']
    missing_libs = []
    
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"✅ {lib}: Installed")
        except ImportError:
            print(f"❌ {lib}: Missing")
            missing_libs.append(lib)
    
    if missing_libs:
        print(f"\n📦 Install missing libraries:")
        print(f"pip install {' '.join(missing_libs)}")
        return False
    
    return True

def test_omnikey_5422():
    """Test OMNIKEY 5422 connection"""
    print("\n🔌 Testing OMNIKEY 5422 Connection")
    print("=" * 40)
    
    try:
        import nfc
        
        clf = nfc.ContactlessFrontend()
        
        if clf:
            reader_info = str(clf.device)
            print(f"✅ Reader connected: {reader_info}")
            
            # Check if it's OMNIKEY 5422
            if "076b:5422" in reader_info or "OMNIKEY" in reader_info:
                print("🎯 OMNIKEY 5422 detected - Professional grade!")
                print("📊 Supports: NTAG 424 DNA, NTAG 215, NTAG 213")
                return True
            else:
                print(f"⚠️  Different reader: {reader_info}")
                print("   OMNIKEY 5422 (076b:5422) recommended")
                return True  # Still functional
        else:
            print("❌ No NFC reader found")
            return False
            
    except Exception as e:
        print(f"❌ Reader test failed: {e}")
        return False

def test_server_connection():
    """Test connection to Deckport API server"""
    print("\n🌐 Testing Server Connection")
    print("=" * 35)
    
    try:
        # Test API connectivity
        response = requests.get('https://api.deckport.ai/health', timeout=10)
        
        if response.status_code == 200:
            print("✅ API server accessible")
            return True
        else:
            print(f"⚠️  API server returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False

def get_available_cards():
    """Get list of available cards for programming"""
    print("\n🎴 Available Cards for Programming")
    print("=" * 40)
    
    try:
        # Get admin token from environment
        admin_token = os.environ.get('ADMIN_TOKEN')
        
        if not admin_token:
            print("⚠️  No ADMIN_TOKEN set")
            print("   Get token from: https://deckport.ai/admin/login")
            print("   Then: export ADMIN_TOKEN='your_jwt_token'")
            return
        
        headers = {'Authorization': f'Bearer {admin_token}'}
        response = requests.get('https://api.deckport.ai/v1/admin/cards/stats', 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            total_cards = stats.get('total_cards', 0)
            print(f"✅ {total_cards} cards available for programming")
            print("   Use: python nfc_card_programmer.py --list-cards")
        else:
            print(f"❌ Card list failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting cards: {e}")

def main():
    """Main setup and test function"""
    print("🃏 OMNIKEY 5422 + NTAG 424 DNA Setup")
    print("=" * 50)
    print("Based on your hardware analysis:")
    print("  ✅ OMNIKEY 5422 Reader (076b:5422)")
    print("  ✅ NTAG 424 DNA Cards (7-byte UID)")
    print("  ✅ Professional-grade NFC system")
    print("  ✅ Enterprise security features")
    print()
    
    # Run all checks
    deps_ok = check_dependencies()
    reader_ok = test_omnikey_5422()
    server_ok = test_server_connection()
    
    if deps_ok and reader_ok and server_ok:
        print("\n🎉 System Ready for Card Programming!")
        print("=" * 45)
        print("Next steps:")
        print("1. Set admin token: export ADMIN_TOKEN='your_jwt_token'")
        print("2. Run: python nfc_card_programmer.py --interactive")
        print("3. Select cards from your 2600+ card catalog")
        print("4. Program NTAG 424 DNA cards with secure keys")
        
        get_available_cards()
    else:
        print("\n❌ Setup Issues Found")
        print("Fix the issues above before programming cards")

if __name__ == "__main__":
    main()
