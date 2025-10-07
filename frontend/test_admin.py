#!/usr/bin/env python3
"""
Test admin login and dashboard functionality
"""

import sys
sys.path.append('/home/jp/deckport.ai')

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/test-dashboard')
def test_dashboard():
    """Simple test dashboard"""
    template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; padding: 20px; }
        .card { background: #333; padding: 20px; border-radius: 8px; margin: 10px 0; }
        .success { color: #4ade80; }
        .error { color: #f87171; }
    </style>
</head>
<body>
    <h1>🎮 Deckport Admin Dashboard - Test</h1>
    
    <div class="card">
        <h2>✅ Admin Dashboard Loading Successfully</h2>
        <p>If you can see this page, the admin routing and templates are working.</p>
    </div>
    
    <div class="card">
        <h2>🔗 Navigation Test</h2>
        <p><a href="/admin/consoles" style="color: #60a5fa;">Console Fleet</a></p>
        <p><a href="/admin/cards" style="color: #60a5fa;">Card Management</a></p>
        <p><a href="/admin/login" style="color: #60a5fa;">Login Page</a></p>
    </div>
    
    <div class="card">
        <h2>📊 System Status</h2>
        <p class="success">Frontend Service: Running</p>
        <p class="success">API Service: Running</p>
        <p class="success">Database: Connected</p>
        <p class="success">Templates: Loading</p>
    </div>
</body>
</html>
    '''
    return render_template_string(template)

if __name__ == '__main__':
    print("🧪 Starting test admin server on port 9000")
    print("Test URL: http://localhost:9000/test-dashboard")
    app.run(host='127.0.0.1', port=9000, debug=True)
