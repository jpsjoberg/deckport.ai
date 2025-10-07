#!/usr/bin/env python3
"""
Automated Godot Build and Deployment Packaging
Exports Godot game on server and packages for console deployment
"""

import os
import subprocess
import tarfile
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_DIR = Path("/home/jp/deckport.ai/console")
GODOT_EXECUTABLE = Path("/home/jp/deckport.ai/godot-headless")
BUILD_DIR = Path("/home/jp/deckport.ai/console/build")
DEPLOYMENT_ASSETS_DIR = Path("/home/jp/deckport.ai/console/kiosk/deployment_assets/godot-game")
STATIC_DEPLOY_DIR = Path("/home/jp/deckport.ai/static/deploy")

def setup_export_preset():
    """Create or update the Linux export preset"""
    print("⚙️ Setting up Linux export preset...")
    
    export_presets_path = PROJECT_DIR / "export_presets.cfg"
    
    export_preset_content = '''[preset.0]

name="Linux/X11"
platform="Linux/X11"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/deckport_console.x86_64"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=true
binary_format/embed_pck=true
texture_format/bptc=true
texture_format/s3tc=true
texture_format/etc=false
texture_format/etc2=false
binary_format/architecture="x86_64"
'''
    
    with open(export_presets_path, "w") as f:
        f.write(export_preset_content)
    
    print(f"✅ Export preset created: {export_presets_path}")

def export_godot_game():
    """Export the Godot game using headless Godot"""
    print("🎮 Exporting Godot game...")
    
    # Ensure build directory exists
    BUILD_DIR.mkdir(exist_ok=True)
    
    # Change to project directory
    os.chdir(PROJECT_DIR)
    
    # Export command
    cmd = [
        str(GODOT_EXECUTABLE),
        "--headless",
        "--export-release",
        "Linux/X11",
        str(BUILD_DIR / "deckport_console.x86_64")
    ]
    
    print(f"🔧 Running export command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Godot export completed successfully")
            
            # Check if executable was created
            exe_path = BUILD_DIR / "deckport_console.x86_64"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✅ Game executable created: {exe_path.name} ({size_mb:.1f} MB)")
                return True
            else:
                print("❌ Export completed but executable not found")
                return False
        else:
            print("❌ Godot export failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Godot export timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Export error: {e}")
        return False

def package_for_deployment():
    """Package the exported game for deployment"""
    print("📦 Packaging game for deployment...")
    
    # Find the game executable
    exe_path = BUILD_DIR / "deckport_console.x86_64"
    if not exe_path.exists():
        print("❌ Game executable not found")
        return False
    
    # Create deployment assets directory
    DEPLOYMENT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clear existing assets
    for item in DEPLOYMENT_ASSETS_DIR.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    
    # Copy game executable
    game_dest = DEPLOYMENT_ASSETS_DIR / "game.x86_64"
    shutil.copy2(exe_path, game_dest)
    os.chmod(game_dest, 0o755)
    
    print(f"✅ Copied game: {exe_path.name} → game.x86_64")
    
    # Copy any additional files (PCK, assets, etc.)
    additional_files = []
    for pattern in ["*.pck", "*.dat", "*.pak", "*.so"]:
        additional_files.extend(BUILD_DIR.glob(pattern))
    
    for file_path in additional_files:
        dest_path = DEPLOYMENT_ASSETS_DIR / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"✅ Copied asset: {file_path.name}")
    
    # Create game info
    game_info = f"""Deckport Console Game - Server Built

Built: {datetime.now().isoformat()}
Source: {PROJECT_DIR}
Executable: game.x86_64
Size: {exe_path.stat().st_size / (1024*1024):.1f} MB
Additional Files: {len(additional_files)}

This game was automatically built and packaged on the server.
Ready for console deployment via: curl -sSL https://deckport.ai/deploy/console | bash
"""
    
    with open(DEPLOYMENT_ASSETS_DIR / "README.txt", "w") as f:
        f.write(game_info)
    
    # Create deployment package
    with tarfile.open(STATIC_DEPLOY_DIR / "godot-game-latest.tar.gz", "w:gz") as tar:
        tar.add(DEPLOYMENT_ASSETS_DIR, arcname=".")
    
    package_size = (STATIC_DEPLOY_DIR / "godot-game-latest.tar.gz").stat().st_size / (1024*1024)
    print(f"✅ Deployment package created: godot-game-latest.tar.gz ({package_size:.1f} MB)")
    
    return True

def install_export_templates():
    """Download and install Godot export templates"""
    print("📥 Installing Godot export templates...")
    
    # Create templates directory
    templates_dir = Path.home() / ".local/share/godot/export_templates/4.2.2.stable"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Download templates
    templates_url = "https://github.com/godotengine/godot/releases/download/4.2.2-stable/Godot_v4.2.2-stable_export_templates.tpz"
    
    try:
        subprocess.run([
            "wget", "-q", "-O", "/tmp/godot_templates.tpz", templates_url
        ], check=True)
        
        # Extract templates
        subprocess.run([
            "unzip", "-q", "/tmp/godot_templates.tpz", "-d", "/tmp/godot_templates"
        ], check=True)
        
        # Copy to templates directory
        templates_src = Path("/tmp/godot_templates/templates")
        if templates_src.exists():
            shutil.copytree(templates_src, templates_dir, dirs_exist_ok=True)
            print("✅ Export templates installed")
            return True
        else:
            print("❌ Templates extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to install templates: {e}")
        return False

def main():
    """Main build and package function"""
    print("🚀 Deckport Console - Automated Build & Package")
    print("=" * 60)
    
    # Check Godot executable
    if not GODOT_EXECUTABLE.exists():
        print(f"❌ Godot executable not found: {GODOT_EXECUTABLE}")
        return False
    
    # Check project directory
    if not (PROJECT_DIR / "project.godot").exists():
        print(f"❌ Godot project not found: {PROJECT_DIR}/project.godot")
        return False
    
    print(f"✅ Godot executable: {GODOT_EXECUTABLE}")
    print(f"✅ Project directory: {PROJECT_DIR}")
    
    # Install export templates if needed
    if not install_export_templates():
        print("⚠️ Template installation failed, but continuing...")
    
    # Setup export preset
    setup_export_preset()
    
    # Export the game
    if not export_godot_game():
        print("❌ Game export failed")
        return False
    
    # Package for deployment
    if not package_for_deployment():
        print("❌ Game packaging failed")
        return False
    
    print("\n🎉 BUILD AND PACKAGE COMPLETE!")
    print("=" * 60)
    print("✅ Godot game exported successfully")
    print("✅ Game packaged for deployment")
    print("✅ Ready for console deployment")
    print("")
    print("🚀 Deploy to console with:")
    print("   curl -sSL https://deckport.ai/deploy/console | bash")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
