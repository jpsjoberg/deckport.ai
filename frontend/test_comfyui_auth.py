#!/usr/bin/env python3
"""
ComfyUI Authentication Test
Tests connection with Basic Authentication credentials
"""

import sys
import os
import getpass
sys.path.append('/home/jp/deckport.ai/frontend')

from services.comfyui_service import ComfyUIService

def test_with_credentials():
    """Test ComfyUI connection with user-provided credentials"""
    print("🔐 ComfyUI Authentication Test")
    print("=" * 50)
    print("Testing connection to: https://c.getvideo.ai")
    print("This server requires Basic Authentication (username/password)")
    print()
    
    # Get credentials from user
    try:
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username is required")
            return False
        
        password = getpass.getpass("Enter password: ").strip()
        if not password:
            print("❌ Password is required")
            return False
            
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Test cancelled by user")
        return False
    
    print("\n🔍 Testing connection with provided credentials...")
    
    # Create ComfyUI service with credentials
    comfyui = ComfyUIService(
        host="https://c.getvideo.ai",
        timeout=30,
        client_id="deckport-admin-test"
    )
    
    # Set credentials manually (since we got them from user input)
    comfyui.username = username
    comfyui.password = password
    
    # Test basic connectivity
    print("   Testing server connectivity...")
    if comfyui.is_online():
        print("   ✅ Server is online and authentication successful!")
    else:
        print("   ❌ Server is offline or authentication failed")
        return False
    
    # Test system stats
    print("   Getting system statistics...")
    stats = comfyui.get_system_stats()
    if stats:
        print("   ✅ System stats retrieved successfully:")
        for key, value in stats.items():
            print(f"      {key}: {value}")
    else:
        print("   ❌ Failed to get system stats")
        return False
    
    # Test queue status
    print("   Checking queue status...")
    queue = comfyui.get_queue_status()
    if queue is not None:
        print("   ✅ Queue status retrieved successfully:")
        if isinstance(queue, dict):
            running = len(queue.get('queue_running', []))
            pending = len(queue.get('queue_pending', []))
            print(f"      Running jobs: {running}")
            print(f"      Pending jobs: {pending}")
        else:
            print(f"      Queue data: {queue}")
    else:
        print("   ❌ Failed to get queue status")
    
    print("\n🎉 Authentication test successful!")
    print("\nTo use these credentials in the admin panel, set environment variables:")
    print(f"export COMFYUI_HOST='https://c.getvideo.ai'")
    print(f"export COMFYUI_USERNAME='{username}'")
    print(f"export COMFYUI_PASSWORD='<your_password>'")
    
    return True

def test_environment_credentials():
    """Test with credentials from environment variables"""
    print("\n🔍 Testing with environment variables...")
    
    username = os.environ.get("COMFYUI_USERNAME")
    password = os.environ.get("COMFYUI_PASSWORD")
    
    if not username or not password:
        print("   ⚠️  No credentials in environment variables")
        print("   Set COMFYUI_USERNAME and COMFYUI_PASSWORD to test")
        return False
    
    print(f"   Using username: {username}")
    print("   Using password: ***")
    
    comfyui = ComfyUIService()
    
    if comfyui.is_online():
        print("   ✅ Authentication with environment credentials successful!")
        return True
    else:
        print("   ❌ Authentication failed with environment credentials")
        return False

def main():
    """Run authentication tests"""
    print("🚀 ComfyUI Authentication Test Suite")
    print("=" * 60)
    
    # Test with environment variables first
    env_success = test_environment_credentials()
    
    if not env_success:
        # If no environment credentials, ask user for manual input
        print("\n" + "=" * 60)
        manual_success = test_with_credentials()
        
        if manual_success:
            print("\n💡 TIP: Set environment variables to avoid entering credentials each time")
            return 0
        else:
            print("\n❌ Authentication test failed")
            return 1
    else:
        print("\n🎉 Environment credentials work perfectly!")
        return 0

if __name__ == "__main__":
    exit(main())
