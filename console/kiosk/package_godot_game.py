#!/usr/bin/env python3
"""
Package Godot Game for Console Deployment
Takes exported Godot game and packages it for deployment system
"""

import os
import tarfile
import shutil
from pathlib import Path

# Configuration
GAME_BUILD_DIR = Path("/home/jp/deckport.ai/console/build")
DEPLOYMENT_ASSETS_DIR = Path("/home/jp/deckport.ai/console/kiosk/deployment_assets/godot-game")
STATIC_DEPLOY_DIR = Path("/home/jp/deckport.ai/static/deploy")

def find_godot_executable():
    """Find the Godot executable in the build directory"""
    possible_names = [
        "deckport_console.x86_64",
        "deckport_console",
        "console.x86_64", 
        "console",
        "game.x86_64",
        "game"
    ]
    
    for name in possible_names:
        exe_path = GAME_BUILD_DIR / name
        if exe_path.exists() and exe_path.is_file():
            return exe_path
    
    # Look for any .x86_64 file
    for file_path in GAME_BUILD_DIR.glob("*.x86_64"):
        if file_path.is_file():
            return file_path
    
    return None

def package_game():
    """Package the Godot game for deployment"""
    print("🎮 Packaging Godot Game for Deployment")
    print("=" * 50)
    
    # Find the game executable
    game_exe = find_godot_executable()
    if not game_exe:
        print("❌ No Godot executable found in build directory")
        print(f"📁 Checked: {GAME_BUILD_DIR}")
        print("🔍 Looking for files like: deckport_console.x86_64, game.x86_64, etc.")
        
        # List all files in build directory
        if GAME_BUILD_DIR.exists():
            print("\n📋 Files found in build directory:")
            for file_path in GAME_BUILD_DIR.iterdir():
                print(f"   {file_path.name} ({'file' if file_path.is_file() else 'directory'})")
        else:
            print(f"❌ Build directory doesn't exist: {GAME_BUILD_DIR}")
        
        return False
    
    print(f"✅ Found Godot executable: {game_exe.name}")
    
    # Check if executable is valid
    if game_exe.stat().st_size < 1000:  # Less than 1KB is probably not a real game
        print(f"⚠️ Warning: Executable seems very small ({game_exe.stat().st_size} bytes)")
    
    # Create deployment assets directory
    DEPLOYMENT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clear existing game assets
    for item in DEPLOYMENT_ASSETS_DIR.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    
    # Copy game executable
    game_dest = DEPLOYMENT_ASSETS_DIR / "game.x86_64"
    shutil.copy2(game_exe, game_dest)
    
    # Make executable
    os.chmod(game_dest, 0o755)
    
    print(f"✅ Copied game executable: {game_exe.name} → game.x86_64")
    
    # Copy any additional game files (PCK files, assets, etc.)
    additional_files = []
    for pattern in ["*.pck", "*.dat", "*.pak"]:
        additional_files.extend(GAME_BUILD_DIR.glob(pattern))
    
    for file_path in additional_files:
        dest_path = DEPLOYMENT_ASSETS_DIR / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"✅ Copied game asset: {file_path.name}")
    
    # Create game info file
    game_info = f"""Deckport Console Game Package

Game Executable: game.x86_64
Source: {game_exe}
Size: {game_exe.stat().st_size} bytes
Additional Files: {len(additional_files)}

Packaged: {os.popen('date').read().strip()}
Version: latest

This package contains the exported Godot game for Deckport consoles.
The game will be installed to /opt/godot-game/ on deployed consoles.
"""
    
    with open(DEPLOYMENT_ASSETS_DIR / "README.txt", "w") as f:
        f.write(game_info)
    
    # Create the deployment package
    print("\n📦 Creating deployment package...")
    
    with tarfile.open(STATIC_DEPLOY_DIR / "godot-game-latest.tar.gz", "w:gz") as tar:
        tar.add(DEPLOYMENT_ASSETS_DIR, arcname=".")
    
    print(f"✅ Game package created: {STATIC_DEPLOY_DIR / 'godot-game-latest.tar.gz'}")
    
    # Show package contents
    print("\n📋 Package contents:")
    with tarfile.open(STATIC_DEPLOY_DIR / "godot-game-latest.tar.gz", "r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile():
                print(f"   📄 {member.name} ({member.size} bytes)")
            else:
                print(f"   📁 {member.name}/")
    
    print("\n🎉 Godot game packaging complete!")
    print("🚀 Game is now ready for console deployment")
    
    return True

def main():
    """Main packaging function"""
    if not GAME_BUILD_DIR.exists():
        print(f"❌ Build directory not found: {GAME_BUILD_DIR}")
        print("📝 Please export your Godot project first")
        return False
    
    return package_game()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Next steps:")
        print("1. Your game is now packaged for deployment")
        print("2. Run console deployment: curl -sSL https://deckport.ai/deploy/console | bash")
        print("3. Console will download and install your game automatically")
    else:
        print("\n❌ Game packaging failed")
        print("📝 Make sure to export your Godot project to /home/jp/deckport.ai/console/build/ first")
    
    exit(0 if success else 1)
