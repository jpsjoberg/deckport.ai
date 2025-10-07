#!/usr/bin/env python3
"""
Console Log Streamer
Monitors console log files and streams them to the Deckport server for debugging
"""

import os
import sys
import time
import json
import requests
import gzip
import base64
from datetime import datetime
from pathlib import Path
import subprocess
import signal
import threading
from queue import Queue

class ConsoleLogStreamer:
    """Streams console logs to Deckport server in real-time"""
    
    def __init__(self):
        self.config_file = "/opt/deckport-console/console.conf"
        self.api_server = "https://api.deckport.ai"
        self.console_id = None
        self.device_uid = None
        self.log_queue = Queue()
        self.running = False
        self.upload_interval = 30  # Upload logs every 30 seconds
        
        # Log files to monitor
        self.log_files = {
            'console': '/var/log/deckport-console.log',
            'syslog': '/var/log/syslog',
            'auth': '/var/log/auth.log',
            'kern': '/var/log/kern.log',
            'xorg': '/var/log/Xorg.0.log',
            'systemd': None  # Will use journalctl
        }
        
        self.load_config()
    
    def load_config(self):
        """Load console configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            if key == 'CONSOLE_ID':
                                self.console_id = value
                            elif key == 'API_SERVER':
                                self.api_server = value
                            elif key.endswith('device_uid'):  # Handle device_uid variations
                                self.device_uid = value
                
                print(f"📋 Config loaded: Console ID = {self.console_id}")
            else:
                print("⚠️ Console config file not found")
                
        except Exception as e:
            print(f"❌ Error loading config: {e}")
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def read_log_file(self, file_path, max_lines=100):
        """Read last N lines from a log file"""
        try:
            if not os.path.exists(file_path):
                return []
            
            # Use tail to get last N lines efficiently
            result = subprocess.run(
                ['tail', '-n', str(max_lines), file_path],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                return [line for line in lines if line.strip()]
            else:
                return []
                
        except Exception as e:
            self.log(f"Error reading {file_path}: {e}", "ERROR")
            return []
    
    def get_systemd_logs(self, max_lines=50):
        """Get recent systemd logs"""
        try:
            result = subprocess.run([
                'journalctl', '--no-pager', '--lines', str(max_lines), 
                '--output', 'json', '--since', '1 hour ago'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logs = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            logs.append({
                                'timestamp': log_entry.get('__REALTIME_TIMESTAMP'),
                                'unit': log_entry.get('_SYSTEMD_UNIT', 'unknown'),
                                'message': log_entry.get('MESSAGE', ''),
                                'priority': log_entry.get('PRIORITY', '6')
                            })
                        except:
                            continue
                return logs
            else:
                return []
                
        except Exception as e:
            self.log(f"Error reading systemd logs: {e}", "ERROR")
            return []
    
    def collect_system_state(self):
        """Collect current system state for debugging"""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'uptime': subprocess.getoutput('uptime'),
                'memory': subprocess.getoutput('free -h'),
                'disk': subprocess.getoutput('df -h'),
                'processes': subprocess.getoutput('ps aux | head -20'),
                'network': subprocess.getoutput('ip addr show'),
                'services': subprocess.getoutput('systemctl status deckport-kiosk.service --no-pager'),
                'x_status': subprocess.getoutput('DISPLAY=:0 xset q 2>&1 || echo "X not running"'),
                'game_status': subprocess.getoutput('pgrep -f "game.x86_64" || echo "Game not running"')
            }
            return state
        except Exception as e:
            self.log(f"Error collecting system state: {e}", "ERROR")
            return {}
    
    def stream_logs(self):
        """Stream logs to server"""
        try:
            # Collect logs from all sources
            all_logs = []
            
            for log_name, log_path in self.log_files.items():
                if log_name == 'systemd':
                    # Special handling for systemd logs
                    systemd_logs = self.get_systemd_logs()
                    for entry in systemd_logs:
                        all_logs.append({
                            'level': 'INFO',
                            'message': entry['message'],
                            'source': f"systemd.{entry['unit']}",
                            'timestamp': datetime.now().isoformat(),
                            'data': entry
                        })
                elif log_path and os.path.exists(log_path):
                    # Read regular log files
                    lines = self.read_log_file(log_path, 50)
                    for line in lines:
                        all_logs.append({
                            'level': 'INFO',
                            'message': line,
                            'source': log_name,
                            'timestamp': datetime.now().isoformat(),
                            'data': {'file': log_path}
                        })
            
            if not all_logs:
                self.log("No logs to stream", "WARNING")
                return True
            
            # Send logs to server
            payload = {
                'console_id': self.console_id,
                'device_uid': self.device_uid,
                'logs': all_logs
            }
            
            response = requests.post(
                f"{self.api_server}/v1/console-logs/stream",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Streamed {result.get('processed_logs', 0)} log entries", "SUCCESS")
                return True
            else:
                self.log(f"❌ Log streaming failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error streaming logs: {e}", "ERROR")
            return False
    
    def upload_crash_report(self, crash_type="unknown", error_message="", additional_logs=None):
        """Upload crash report with full system state"""
        try:
            self.log(f"🚨 Uploading crash report: {crash_type}", "CRITICAL")
            
            # Collect comprehensive system state
            system_state = self.collect_system_state()
            
            # Collect log files
            log_files = {}
            for log_name, log_path in self.log_files.items():
                if log_path and os.path.exists(log_path):
                    try:
                        # Read entire log file for crash analysis
                        with open(log_path, 'r') as f:
                            log_content = f.read()
                        
                        # Compress large logs
                        if len(log_content) > 10000:  # Compress if > 10KB
                            compressed = gzip.compress(log_content.encode('utf-8'))
                            log_files[log_name] = {
                                'content': base64.b64encode(compressed).decode('utf-8'),
                                'compressed': True,
                                'original_size': len(log_content)
                            }
                        else:
                            log_files[log_name] = {
                                'content': log_content,
                                'compressed': False,
                                'original_size': len(log_content)
                            }
                    except Exception as e:
                        log_files[log_name] = {'error': str(e)}
            
            # Add additional logs if provided
            if additional_logs:
                log_files.update(additional_logs)
            
            # Send crash report
            payload = {
                'console_id': self.console_id,
                'device_uid': self.device_uid,
                'crash_type': crash_type,
                'error_message': error_message,
                'system_state': system_state,
                'log_files': log_files
            }
            
            response = requests.post(
                f"{self.api_server}/v1/console-logs/crash-report",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for crash reports
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Crash report uploaded: ID {result.get('crash_report_id')}", "SUCCESS")
                return True
            else:
                self.log(f"❌ Crash report upload failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error uploading crash report: {e}", "ERROR")
            return False
    
    def start_streaming(self):
        """Start continuous log streaming"""
        self.log("🚀 Starting console log streaming...")
        self.running = True
        
        while self.running:
            try:
                self.stream_logs()
                time.sleep(self.upload_interval)
            except KeyboardInterrupt:
                self.log("🛑 Log streaming stopped by user", "INFO")
                break
            except Exception as e:
                self.log(f"❌ Streaming error: {e}", "ERROR")
                time.sleep(10)  # Wait before retry
    
    def stop_streaming(self):
        """Stop log streaming"""
        self.running = False
        self.log("🛑 Log streaming stopped", "INFO")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Received shutdown signal, stopping log streamer...")
    sys.exit(0)

def main():
    """Main function"""
    # Handle shutdown signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("📡 Deckport Console Log Streamer")
    print("=" * 40)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "crash":
            # Upload crash report
            crash_type = sys.argv[2] if len(sys.argv) > 2 else "manual"
            error_msg = sys.argv[3] if len(sys.argv) > 3 else "Manual crash report"
            
            streamer = ConsoleLogStreamer()
            streamer.upload_crash_report(crash_type, error_msg)
            
        elif command == "upload":
            # One-time log upload
            streamer = ConsoleLogStreamer()
            streamer.stream_logs()
            
        elif command == "daemon":
            # Run as daemon
            streamer = ConsoleLogStreamer()
            streamer.start_streaming()
            
        else:
            print("Usage: console_log_streamer.py {crash|upload|daemon}")
            print("  crash  - Upload crash report")
            print("  upload - One-time log upload") 
            print("  daemon - Continuous log streaming")
    else:
        # Default: one-time upload
        streamer = ConsoleLogStreamer()
        streamer.stream_logs()

if __name__ == "__main__":
    main()
