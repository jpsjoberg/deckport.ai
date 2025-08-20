#!/usr/bin/env python3
"""
Local Test Client for Deckport.ai Server
Run this from your local development machine to test the remote server

Usage:
    python local_test_client.py --server your-server-ip
    python local_test_client.py --server deckport.ai
    python local_test_client.py --help
"""

import asyncio
import websockets
import json
import sys
import requests
import argparse
from datetime import datetime
import time

class DeckportTestClient:
    def __init__(self, server_host: str, use_https: bool = False):
        self.server_host = server_host
        self.protocol = "https" if use_https else "http"
        self.ws_protocol = "wss" if use_https else "ws"
        
        # Configure URLs based on your server setup
        if server_host in ["localhost", "127.0.0.1"]:
            # Local development
            self.api_url = f"{self.protocol}://{server_host}:8002"
            self.realtime_url = f"{self.ws_protocol}://{server_host}:8003/ws"
            self.frontend_url = f"{self.protocol}://{server_host}:5000"
        else:
            # Production server
            self.api_url = f"{self.protocol}://api.{server_host}"
            self.realtime_url = f"{self.ws_protocol}://ws.{server_host}/ws"
            self.frontend_url = f"{self.protocol}://{server_host}"
        
        self.session = requests.Session()
        self.session.timeout = 10
        
        print(f"🌐 Test Client Configuration:")
        print(f"   Server: {server_host}")
        print(f"   API: {self.api_url}")
        print(f"   WebSocket: {self.realtime_url}")
        print(f"   Frontend: {self.frontend_url}")
        print("")

    async def test_all(self):
        """Run all tests"""
        print("🚀 Deckport.ai Server Test Suite")
        print("=" * 50)
        
        # Test 1: Server connectivity
        await self.test_server_connectivity()
        
        # Test 2: API endpoints
        await self.test_api_endpoints()
        
        # Test 3: User authentication
        token = await self.test_user_authentication()
        
        if token:
            # Test 4: WebSocket connection
            await self.test_websocket_connection(token)
            
            # Test 5: Matchmaking
            await self.test_matchmaking(token)
        
        print("\n🎉 Test suite completed!")

    async def test_server_connectivity(self):
        """Test basic server connectivity"""
        print("\n📡 Testing Server Connectivity...")
        
        endpoints = [
            ("API Health", f"{self.api_url}/health"),
            ("Realtime Health", f"{self.realtime_url.replace('/ws', '/health').replace('ws://', 'http://').replace('wss://', 'https://')}")
        ]
        
        for name, url in endpoints:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {name}: {data}")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ {name}: Connection failed - {e}")

    async def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        # Test card catalog
        try:
            response = requests.get(f"{self.api_url}/v1/catalog/cards")
            if response.status_code == 200:
                cards = response.json()
                print(f"✅ Card Catalog: {len(cards.get('items', []))} cards available")
                
                # Test specific card
                if cards.get('items'):
                    first_card = cards['items'][0]
                    card_response = requests.get(f"{self.api_url}/v1/catalog/cards/{first_card['product_sku']}")
                    if card_response.status_code == 200:
                        print(f"✅ Card Details: {first_card['name']} loaded successfully")
                    else:
                        print(f"❌ Card Details: Failed to load {first_card['name']}")
            else:
                print(f"❌ Card Catalog: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Card Catalog: {e}")

    async def test_user_authentication(self):
        """Test user registration and login"""
        print("\n🔐 Testing User Authentication...")
        
        # Test user data
        test_email = f"testuser_{int(time.time())}@example.com"
        test_password = "password123"
        
        try:
            # Test registration
            register_data = {
                "email": test_email,
                "password": test_password,
                "display_name": "Test User"
            }
            
            response = requests.post(f"{self.api_url}/v1/auth/player/register", json=register_data)
            
            if response.status_code == 201:
                user_data = response.json()
                access_token = user_data["access_token"]
                print(f"✅ Registration: User created successfully")
                print(f"✅ JWT Token: {access_token[:30]}...")
                return access_token
            else:
                print(f"❌ Registration: HTTP {response.status_code} - {response.text}")
                
                # Try login instead
                login_data = {"email": test_email, "password": test_password}
                response = requests.post(f"{self.api_url}/v1/auth/player/login", json=login_data)
                
                if response.status_code == 200:
                    user_data = response.json()
                    access_token = user_data["access_token"]
                    print(f"✅ Login: User authenticated successfully")
                    return access_token
                else:
                    print(f"❌ Login: HTTP {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"❌ Authentication: {e}")
        
        return None

    async def test_websocket_connection(self, token: str):
        """Test WebSocket connection and basic messaging"""
        print("\n🔌 Testing WebSocket Connection...")
        
        try:
            # Connect with authentication
            ws_url = f"{self.realtime_url}?token={token}"
            
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket: Connected successfully")
                
                # Wait for welcome message
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                print(f"📨 Welcome: {welcome_data.get('type')} (connection_id: {welcome_data.get('connection_id')})")
                
                # Test ping/pong
                ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
                await websocket.send(json.dumps(ping_msg))
                
                pong_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_msg)
                print(f"🏓 Ping/Pong: {pong_data.get('type')} received")
                
                return True
                
        except asyncio.TimeoutError:
            print("❌ WebSocket: Timeout waiting for response")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"❌ WebSocket: Connection closed - {e}")
        except Exception as e:
            print(f"❌ WebSocket: {e}")
        
        return False

    async def test_matchmaking(self, token: str):
        """Test matchmaking system"""
        print("\n🎯 Testing Matchmaking System...")
        
        try:
            ws_url = f"{self.realtime_url}?token={token}"
            
            async with websockets.connect(ws_url) as websocket:
                # Skip welcome message
                await websocket.recv()
                
                print("1. Joining matchmaking queue...")
                queue_msg = {
                    "type": "queue.join",
                    "mode": "1v1",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(queue_msg))
                
                # Wait for queue acknowledgment
                queue_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                queue_data = json.loads(queue_response)
                
                if queue_data.get('type') == 'queue.ack':
                    print(f"✅ Queue Joined: Mode {queue_data.get('mode')}")
                    print(f"   Estimated wait: {queue_data.get('estimated_wait_seconds', 'unknown')} seconds")
                else:
                    print(f"❌ Queue Join Failed: {queue_data}")
                    return
                
                print("2. Waiting for match (15 seconds max)...")
                try:
                    match_msg = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    match_data = json.loads(match_msg)
                    
                    if match_data.get('type') == 'match.found':
                        print(f"🎉 Match Found!")
                        print(f"   Match ID: {match_data.get('match_id')}")
                        print(f"   Opponent: {match_data.get('opponent', {}).get('display_name')}")
                        print(f"   Your Team: {match_data.get('your_team')}")
                    else:
                        print(f"📨 Other message: {match_data}")
                        
                except asyncio.TimeoutError:
                    print("⏰ No match found within timeout (expected with 1 player)")
                
                # Leave queue
                print("3. Leaving queue...")
                leave_msg = {"type": "queue.leave"}
                await websocket.send(json.dumps(leave_msg))
                
                leave_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                leave_data = json.loads(leave_response)
                print(f"👋 Queue Left: {leave_data}")
                
        except Exception as e:
            print(f"❌ Matchmaking test failed: {e}")

    async def test_device_authentication(self):
        """Test console device authentication (if implemented)"""
        print("\n🎮 Testing Console Device Authentication...")
        
        # Test device registration
        try:
            device_data = {
                "device_uid": f"TEST_DEVICE_{int(time.time())}",
                "public_key": "-----BEGIN PUBLIC KEY-----\nTEST_KEY_FOR_DEMO\n-----END PUBLIC KEY-----"
            }
            
            response = requests.post(f"{self.api_url}/v1/auth/device/register", json=device_data)
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Device Registration: {result.get('status')} - {result.get('message')}")
            elif response.status_code == 404:
                print("ℹ️  Device endpoints not available (may need systemd service update)")
            else:
                print(f"❌ Device Registration: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Device Authentication: {e}")

    async def test_frontend_pages(self):
        """Test frontend page accessibility"""
        print("\n🌐 Testing Frontend Pages...")
        
        pages = [
            ("Landing Page", "/"),
            ("Card Catalog", "/cards"),
            ("Login Page", "/login"),
            ("Register Page", "/register")
        ]
        
        for name, path in pages:
            try:
                response = requests.get(f"{self.frontend_url}{path}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name}: Accessible")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {e}")

    async def interactive_mode(self, token: str):
        """Interactive mode for manual testing"""
        print("\n🎮 Interactive Mode - Manual WebSocket Testing")
        print("Commands: ping, queue.join, queue.leave, quit")
        print("=" * 50)
        
        try:
            ws_url = f"{self.realtime_url}?token={token}"
            
            async with websockets.connect(ws_url) as websocket:
                print("✅ Connected to WebSocket")
                
                # Skip welcome message
                welcome = await websocket.recv()
                print(f"📨 {json.loads(welcome)}")
                
                async def listen_for_messages():
                    """Listen for incoming messages"""
                    try:
                        while True:
                            message = await websocket.recv()
                            data = json.loads(message)
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] 📨 {data}")
                    except websockets.exceptions.ConnectionClosed:
                        print("🔌 WebSocket connection closed")
                
                async def send_commands():
                    """Send commands from user input"""
                    while True:
                        try:
                            command = input("\n> ")
                            
                            if command.lower() == 'quit':
                                break
                            elif command.lower() == 'ping':
                                msg = {"type": "ping"}
                            elif command.lower() == 'queue.join':
                                msg = {"type": "queue.join", "mode": "1v1"}
                            elif command.lower() == 'queue.leave':
                                msg = {"type": "queue.leave"}
                            else:
                                try:
                                    # Try to parse as JSON
                                    msg = json.loads(command)
                                except:
                                    print("❌ Invalid command. Use: ping, queue.join, queue.leave, or valid JSON")
                                    continue
                            
                            await websocket.send(json.dumps(msg))
                            print(f"📤 Sent: {msg}")
                            
                        except KeyboardInterrupt:
                            break
                        except Exception as e:
                            print(f"❌ Error: {e}")
                
                # Run both listening and sending concurrently
                await asyncio.gather(
                    listen_for_messages(),
                    send_commands()
                )
                
        except Exception as e:
            print(f"❌ Interactive mode failed: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Deckport.ai Local Test Client")
    parser.add_argument("--server", required=True, help="Server hostname or IP")
    parser.add_argument("--https", action="store_true", help="Use HTTPS/WSS")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--test-only", choices=["api", "websocket", "frontend", "device"], help="Run specific test only")
    
    args = parser.parse_args()
    
    client = DeckportTestClient(args.server, args.https)
    
    if args.test_only:
        # Run specific test
        if args.test_only == "api":
            await client.test_server_connectivity()
            await client.test_api_endpoints()
        elif args.test_only == "websocket":
            token = await client.test_user_authentication()
            if token:
                await client.test_websocket_connection(token)
        elif args.test_only == "frontend":
            await client.test_frontend_pages()
        elif args.test_only == "device":
            await client.test_device_authentication()
    elif args.interactive:
        # Interactive mode
        token = await client.test_user_authentication()
        if token:
            await client.interactive_mode(token)
    else:
        # Run all tests
        await client.test_all()

if __name__ == "__main__":
    asyncio.run(main())
