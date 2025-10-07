#!/usr/bin/env python3
"""
Setup script for Arena Creation Engine
Installs dependencies and sets up environment
"""

import subprocess
import sys
import os
from pathlib import Path

def setup_arena_creation():
    """Setup arena creation engine dependencies and environment"""
    
    print("🏗️ Setting up Arena Creation Engine")
    print("=" * 50)
    
    # Install Python dependencies
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            "/home/jp/deckport.ai/requirements-arena-creation.txt"
        ], check=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Create required directories
    print("📁 Creating asset directories...")
    base_path = Path('/home/jp/deckport.ai')
    directories = [
        base_path / 'static' / 'arenas' / 'images',
        base_path / 'static' / 'arenas' / 'clips', 
        base_path / 'static' / 'arenas' / 'sequences',
        base_path / 'static' / 'arenas' / 'music',
        base_path / 'static' / 'arenas' / 'final',
        base_path / 'temp' / 'arena_creation'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    
    # Check API keys
    print("🔑 Checking API keys...")
    required_keys = ['ANTHROPIC_API_KEY', 'ELEVENLABS_API_KEY', 'COMFYUI_HOST', 'COMFYUI_USERNAME', 'COMFYUI_PASSWORD']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print("⚠️ Missing configuration:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease set these environment variables before using the arena creation engine.")
        print("Example:")
        print("export ANTHROPIC_API_KEY='your-anthropic-key'")
        print("export ELEVENLABS_API_KEY='your-elevenlabs-key'") 
        print("export COMFYUI_HOST='https://c.getvideo.ai'")
        print("export COMFYUI_USERNAME='your-username'")
        print("export COMFYUI_PASSWORD='your-password'")
    else:
        print("✅ All API keys and services configured")
    
    # Test ComfyUI connection
    print("🎨 Testing ComfyUI connection...")
    try:
        from frontend.services.comfyui_service import ComfyUIService
        comfyui = ComfyUIService()
        if comfyui.is_online():
            print("✅ ComfyUI service is online and responsive")
        else:
            print("⚠️ ComfyUI service is not responding")
    except Exception as e:
        print(f"❌ ComfyUI test failed: {e}")
    
    # Test imports
    print("🧪 Testing imports...")
    try:
        import anthropic
        import elevenlabs
        import cv2
        import moviepy
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    print("\n🎉 Arena Creation Engine setup complete!")
    print("\nNext steps:")
    print("1. Set API keys if missing")
    print("2. Access /admin/arenas/create in admin panel")
    print("3. Generate your first batch of AI arenas")
    
    return True

if __name__ == "__main__":
    success = setup_arena_creation()
    sys.exit(0 if success else 1)
