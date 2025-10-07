#!/usr/bin/env python3
"""
Simple test deployment script to verify curl | bash works
"""

from flask import Flask, make_response

app = Flask(__name__)

@app.route('/test')
def test_script():
    """Return a simple test script that actually executes"""
    script = '''#!/bin/bash

echo "🧪 TESTING CURL | BASH EXECUTION"
echo "================================="
echo "✅ Script is executing!"
echo "User: $(whoami)"
echo "Date: $(date)"
echo "Working directory: $(pwd)"

# Test a simple operation
echo "Creating test file..."
touch /tmp/deckport-test-$(date +%s).txt
echo "✅ Test file created"

echo "🎉 Test completed successfully!"
echo "If you see this message, curl | bash is working correctly."
'''
    
    response = make_response(script)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

if __name__ == '__main__':
    print("🧪 Starting simple test server on port 8888")
    print("Test with: curl -sSL http://127.0.0.1:8888/test | bash")
    app.run(host='127.0.0.1', port=8888, debug=False)
