#!/usr/bin/env python3
"""
Production Console Registration System
Handles secure console registration with proper RSA key generation and API communication
"""

import json
import requests
import subprocess
import os
import sys
import socket
import uuid
from datetime import datetime
from pathlib import Path

class ConsoleRegistration:
    """Handles secure console registration with Deckport API"""
    
    def __init__(self, api_server="https://api.deckport.ai"):
        self.api_server = api_server
        self.console_dir = Path("/opt/deckport-console")
        self.keys_dir = self.console_dir / "keys"
        self.config_file = self.console_dir / "console.conf"
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
        
        # Also log to file if possible
        try:
            log_file = Path("/var/log/deckport-console.log")
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except:
            pass  # Ignore logging errors
    
    def generate_rsa_keys(self):
        """Generate RSA key pair for console authentication"""
        self.log("Generating RSA key pair for console authentication...")
        
        # Ensure keys directory exists
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        private_key_path = self.keys_dir / "console_private.pem"
        public_key_path = self.keys_dir / "console_public.pem"
        
        try:
            # Generate private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(private_key_path), "2048"
            ], check=True, capture_output=True)
            
            # Generate public key from private key
            subprocess.run([
                "openssl", "rsa", "-in", str(private_key_path), 
                "-pubout", "-out", str(public_key_path)
            ], check=True, capture_output=True)
            
            # Set proper permissions
            os.chmod(private_key_path, 0o600)
            os.chmod(public_key_path, 0o644)
            
            # Change ownership to kiosk user (if kiosk user exists)
            try:
                subprocess.run(["chown", "kiosk:kiosk", str(private_key_path), str(public_key_path)], check=True)
            except subprocess.CalledProcessError:
                # Kiosk user doesn't exist (probably testing on main server)
                self.log("Kiosk user not found, keeping root ownership", "WARNING")
            
            self.log("RSA key pair generated successfully", "SUCCESS")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to generate RSA keys: {e}", "ERROR")
            return False
    
    def get_public_key(self):
        """Read and return the public key"""
        public_key_path = self.keys_dir / "console_public.pem"
        
        if not public_key_path.exists():
            self.log("Public key file not found", "ERROR")
            return None
        
        try:
            with open(public_key_path, 'r') as f:
                public_key = f.read().strip()
            
            self.log("Public key loaded successfully")
            return public_key
            
        except Exception as e:
            self.log(f"Failed to read public key: {e}", "ERROR")
            return None
    
    def get_system_info(self):
        """Gather system information for registration"""
        self.log("Gathering system information...")
        
        try:
            # Get MAC address
            mac_address = None
            result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'ether' in line:
                    mac_address = line.split()[1]
                    break
            
            # Get IP address
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            # Get CPU info
            cpu_info = "Unknown"
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_info = line.split(":")[1].strip()
                            break
            except:
                pass
            
            # Get memory info
            memory_gb = 1
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal"):
                            memory_kb = int(line.split()[1])
                            memory_gb = memory_kb // (1024 * 1024)
                            break
            except:
                pass
            
            system_info = {
                "mac_address": mac_address,
                "ip_address": ip_address,
                "hostname": hostname,
                "cpu": cpu_info,
                "memory_gb": memory_gb
            }
            
            self.log(f"System info gathered: {hostname} ({ip_address})")
            return system_info
            
        except Exception as e:
            self.log(f"Failed to gather system info: {e}", "ERROR")
            return {}
    
    def register_console(self, console_id, location="Unknown", game_version="latest"):
        """Register console with Deckport API"""
        self.log(f"Registering console: {console_id}")
        
        # Generate keys if they don't exist
        if not (self.keys_dir / "console_public.pem").exists():
            if not self.generate_rsa_keys():
                return False
        
        # Get public key
        public_key = self.get_public_key()
        if not public_key:
            return False
        
        # Get system information
        system_info = self.get_system_info()
        
        # Prepare registration data
        registration_data = {
            "device_uid": console_id,
            "public_key": public_key,
            "location": {
                "name": location,
                "source": "manual"
            },
            "hardware_info": system_info
        }
        
        try:
            # Make registration request
            self.log(f"Sending registration request to {self.api_server}")
            
            response = requests.post(
                f"{self.api_server}/v1/auth/device/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self.log(f"Registration response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.log("Console registered successfully!", "SUCCESS")
                
                # Save registration info
                self.save_console_config(console_id, location, game_version, system_info)
                
                return True
                
            elif response.status_code == 409:
                # Already registered
                result = response.json()
                if result.get("status") == "pending":
                    self.log("Console registration pending admin approval", "WARNING")
                    return True
                else:
                    self.log(f"Console already registered: {result.get('error', 'Unknown')}", "WARNING")
                    return True
                    
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", "Unknown error")
                except:
                    error_msg = response.text[:200]
                
                self.log(f"Registration failed: {error_msg}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Network error during registration: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Unexpected error during registration: {e}", "ERROR")
            return False
    
    def save_console_config(self, console_id, location, game_version, system_info):
        """Save console configuration"""
        self.log("Saving console configuration...")
        
        # Ensure directory exists
        self.console_dir.mkdir(parents=True, exist_ok=True)
        
        config_content = f"""# Deckport Console Configuration
CONSOLE_ID={console_id}
GAME_VERSION={game_version}
LOCATION={location}
DEPLOYMENT_SERVER=https://deckport.ai
API_SERVER=https://api.deckport.ai
API_ENDPOINT=https://api.deckport.ai/v1
REGISTERED_AT={datetime.now().isoformat()}
MAC_ADDRESS={system_info.get('mac_address', 'unknown')}
IP_ADDRESS={system_info.get('ip_address', 'unknown')}
HOSTNAME={system_info.get('hostname', 'unknown')}
"""
        
        try:
            with open(self.config_file, 'w') as f:
                f.write(config_content)
            
            # Set proper permissions
            os.chmod(self.config_file, 0o644)
            try:
                subprocess.run(["chown", "kiosk:kiosk", str(self.config_file)], check=True)
            except subprocess.CalledProcessError:
                # Kiosk user doesn't exist (probably testing on main server)
                pass
            
            self.log("Console configuration saved successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to save console configuration: {e}", "ERROR")
            return False

def main():
    """Main registration function"""
    if len(sys.argv) < 2:
        console_id = f"console-{int(datetime.now().timestamp())}"
    else:
        console_id = sys.argv[1]
    
    location = sys.argv[2] if len(sys.argv) > 2 else "Unknown"
    game_version = sys.argv[3] if len(sys.argv) > 3 else "latest"
    
    print("🎮 Deckport Console Registration")
    print("=" * 50)
    print(f"Console ID: {console_id}")
    print(f"Location: {location}")
    print(f"Game Version: {game_version}")
    print("=" * 50)
    
    # Create registration handler
    registration = ConsoleRegistration()
    
    # Attempt registration
    if registration.register_console(console_id, location, game_version):
        print("\n🎉 Console registration completed successfully!")
        print("✅ Console is now registered with Deckport")
        print("✅ Configuration saved")
        print("✅ Ready for kiosk mode")
        return True
    else:
        print("\n❌ Console registration failed")
        print("⚠️ Console will continue without registration")
        print("📝 Check network connectivity and API availability")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
