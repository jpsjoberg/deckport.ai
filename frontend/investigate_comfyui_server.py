#!/usr/bin/env python3
"""
ComfyUI Server Investigation Script
Tests different endpoints and methods to understand the API structure
"""

import requests
import json
from urllib.parse import urljoin

def investigate_server(base_url="https://c.getvideo.ai"):
    """Investigate what endpoints are available on the ComfyUI server"""
    print(f"🔍 Investigating ComfyUI server: {base_url}")
    print("=" * 60)
    
    # Common ComfyUI endpoints to test
    endpoints = [
        "",                    # Root
        "/",                   # Root with slash
        "/system_stats",       # System statistics
        "/queue",             # Queue status
        "/history",           # Generation history
        "/prompt",            # Prompt submission
        "/view",              # Image viewing
        "/upload/image",      # Image upload
        "/api",               # API root
        "/api/v1",            # API v1
        "/docs",              # API documentation
        "/openapi.json",      # OpenAPI spec
        "/health",            # Health check
        "/status",            # Status
        "/info",              # Info
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Deckport-Admin/1.0',
        'Accept': 'application/json, text/html, */*',
    })
    
    results = {}
    
    for endpoint in endpoints:
        url = urljoin(base_url, endpoint)
        print(f"\n📡 Testing: {url}")
        
        try:
            # Test GET request
            response = session.get(url, timeout=10)
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            # Try to parse content
            content_type = response.headers.get('content-type', '').lower()
            
            if 'json' in content_type:
                try:
                    data = response.json()
                    print(f"   JSON Response: {json.dumps(data, indent=2)[:500]}...")
                except:
                    print(f"   JSON Parse Failed")
            elif 'html' in content_type:
                print(f"   HTML Content Length: {len(response.text)}")
                if '<title>' in response.text:
                    title_start = response.text.find('<title>') + 7
                    title_end = response.text.find('</title>')
                    if title_end > title_start:
                        title = response.text[title_start:title_end]
                        print(f"   Page Title: {title}")
            else:
                print(f"   Content Length: {len(response.content)}")
                print(f"   Content Preview: {response.text[:200]}...")
            
            results[endpoint] = {
                'status': response.status_code,
                'content_type': content_type,
                'success': response.status_code < 400
            }
            
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
            results[endpoint] = {'status': 'timeout', 'success': False}
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 Connection Error: {e}")
            results[endpoint] = {'status': 'connection_error', 'success': False}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[endpoint] = {'status': 'error', 'success': False}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INVESTIGATION SUMMARY")
    print("=" * 60)
    
    successful_endpoints = [ep for ep, result in results.items() if result.get('success', False)]
    failed_endpoints = [ep for ep, result in results.items() if not result.get('success', False)]
    
    print(f"✅ Successful endpoints ({len(successful_endpoints)}):")
    for ep in successful_endpoints:
        status = results[ep]['status']
        content_type = results[ep].get('content_type', 'unknown')
        print(f"   {ep or '/':<20} [{status}] {content_type}")
    
    print(f"\n❌ Failed endpoints ({len(failed_endpoints)}):")
    for ep in failed_endpoints:
        status = results[ep]['status']
        print(f"   {ep or '/':<20} [{status}]")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if any('401' in str(result.get('status', '')) for result in results.values()):
        print("   • Server requires authentication (401 errors)")
        print("   • Check if API key or token is needed")
    
    if successful_endpoints:
        print("   • Server is responding to some endpoints")
        print("   • Try the successful endpoints for API access")
    else:
        print("   • No endpoints responding successfully")
        print("   • Server might not be a standard ComfyUI instance")
    
    return results

def test_authentication_methods(base_url="https://c.getvideo.ai"):
    """Test different authentication methods"""
    print(f"\n🔐 Testing authentication methods for: {base_url}")
    print("-" * 40)
    
    test_endpoint = "/system_stats"
    url = urljoin(base_url, test_endpoint)
    
    auth_methods = [
        ("No Auth", {}),
        ("Bearer Token", {"Authorization": "Bearer test-token"}),
        ("API Key Header", {"X-API-Key": "test-key"}),
        ("API Key Param", {"api_key": "test-key"}),
        ("Basic Auth", {"Authorization": "Basic dGVzdDp0ZXN0"}),  # test:test
    ]
    
    for method_name, headers in auth_methods:
        print(f"   Testing {method_name}...")
        try:
            if "api_key" in headers:
                # Test as query parameter
                response = requests.get(url, params=headers, timeout=10)
            else:
                # Test as header
                response = requests.get(url, headers=headers, timeout=10)
            
            print(f"      Status: {response.status_code}")
            if response.status_code != 401:
                print(f"      Response: {response.text[:100]}...")
        except Exception as e:
            print(f"      Error: {e}")

def main():
    """Run the investigation"""
    print("🕵️ ComfyUI Server Investigation")
    print("This will help us understand how to connect to your external server")
    
    # Main investigation
    results = investigate_server()
    
    # Authentication testing
    test_authentication_methods()
    
    # Final recommendations
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS")
    print("=" * 60)
    print("""
Based on the investigation results:

1. If you see 401 errors:
   - The server is running but requires authentication
   - Check if you have API credentials for c.getvideo.ai
   - Look for API documentation on their website

2. If you see successful responses:
   - We can proceed with API integration
   - Note which endpoints work for ComfyUI functionality

3. If no endpoints work:
   - The server might not expose ComfyUI API publicly
   - Consider setting up your own ComfyUI instance
   - Or check if there's a different API endpoint structure

4. Alternative options:
   - Set up local ComfyUI instance
   - Use a different ComfyUI hosting service
   - Configure authentication if credentials are available
""")

if __name__ == "__main__":
    main()
