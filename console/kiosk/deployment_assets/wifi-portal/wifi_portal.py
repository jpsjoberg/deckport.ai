#!/usr/bin/env python3
import os
import subprocess
import json
from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__)

def get_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        result = subprocess.run(
            ['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi'],
            capture_output=True, text=True
        )
        networks = []
        seen = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(':')
                if len(parts) >= 3 and parts[0] and parts[0] not in seen:
                    seen.add(parts[0])
                    networks.append({
                        'ssid': parts[0],
                        'signal': int(parts[1]) if parts[1] else 0,
                        'security': parts[2] if len(parts) > 2 else 'Open'
                    })
        return sorted(networks, key=lambda x: x['signal'], reverse=True)
    except Exception as e:
        print(f"Error scanning WiFi: {e}")
        return []

def connect_to_wifi(ssid, password):
    """Connect to WiFi network"""
    try:
        # Remove existing connection if it exists
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], 
                      capture_output=True)
        
        # Create new connection
        if password:
            result = subprocess.run(
                ['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password],
                capture_output=True, text=True
            )
        else:
            result = subprocess.run(
                ['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid],
                capture_output=True, text=True
            )
        
        if result.returncode == 0:
            # Test internet connectivity
            time.sleep(3)
            test = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                capture_output=True)
            if test.returncode == 0:
                # Create flag file to indicate successful connection
                open('/tmp/wifi_configured', 'w').close()
                return True
        return False
    except Exception as e:
        print(f"Error connecting to WiFi: {e}")
        return False

@app.route('/')
def index():
    networks = get_wifi_networks()
    return render_template('index.html', networks=networks)

@app.route('/scan')
def scan():
    networks = get_wifi_networks()
    return jsonify(networks)

@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password', '')
    
    if connect_to_wifi(ssid, password):
        # Continue with kiosk setup
        subprocess.run(['sudo', 'systemctl', 'start', 'deckport-kiosk.service'])
        return jsonify({'status': 'success', 'message': 'Connected successfully!'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to connect'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
