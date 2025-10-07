#!/usr/bin/env python3
"""
Test script to verify curl | bash execution works properly
"""

from flask import Flask, make_response

app = Flask(__name__)

@app.route('/test-script')
def test_script():
    """Return a simple test script"""
    script = '''#!/bin/bash

echo "🧪 Testing curl | bash execution..."
echo "✅ Script is executing properly!"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Timestamp: $(date)"

# Test if we can run basic commands
if command -v curl >/dev/null 2>&1; then
    echo "✅ curl is available"
else
    echo "❌ curl is not available"
fi

if command -v sudo >/dev/null 2>&1; then
    echo "✅ sudo is available"
else
    echo "❌ sudo is not available"
fi

echo "🎉 Test script completed successfully!"
'''
    
    response = make_response(script)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9999, debug=True)
