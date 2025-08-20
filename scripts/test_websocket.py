#!/usr/bin/env python3
"""
WebSocket Test Client for Deckport Realtime Service
Tests matchmaking and real-time communication
"""

import asyncio
import websockets
import json
import sys
import requests
from datetime import datetime

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')
from shared.auth.jwt_handler import create_access_token

REALTIME_URL = "ws://127.0.0.1:8003/ws"
API_URL = "http://127.0.0.1:8002"

async def test_websocket_connection():
    """Test basic WebSocket connection with authentication"""
    print("🧪 Testing WebSocket Connection...")
    
    # First, create a test user and get a token
    print("1. Creating test user...")
    
    # Register test user
    register_data = {
        "email": "testplayer@example.com",
        "password": "password123",
        "display_name": "Test Player"
    }
    
    try:
        response = requests.post(f"{API_URL}/v1/auth/player/register", json=register_data)
        if response.status_code == 201:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"✅ User registered, token: {access_token[:20]}...")
        elif response.status_code == 409:
            # User already exists, try to login
            login_data = {"email": register_data["email"], "password": register_data["password"]}
            response = requests.post(f"{API_URL}/v1/auth/player/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"✅ User logged in, token: {access_token[:20]}...")
            else:
                print(f"❌ Login failed: {response.text}")
                return
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Test WebSocket connection
    print("2. Testing WebSocket connection...")
    
    try:
        # Connect with token in query params
        ws_url = f"{REALTIME_URL}?token={access_token}"
        
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Wait for welcome message
            welcome_msg = await websocket.recv()
            welcome_data = json.loads(welcome_msg)
            print(f"📨 Welcome message: {welcome_data}")
            
            # Test ping
            print("3. Testing ping...")
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await websocket.send(json.dumps(ping_msg))
            
            pong_msg = await websocket.recv()
            pong_data = json.loads(pong_msg)
            print(f"🏓 Pong received: {pong_data}")
            
            # Test queue join
            print("4. Testing matchmaking queue...")
            queue_msg = {
                "type": "queue.join",
                "mode": "1v1",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(queue_msg))
            
            # Wait for queue acknowledgment
            queue_response = await websocket.recv()
            queue_data = json.loads(queue_response)
            print(f"🎯 Queue response: {queue_data}")
            
            # Wait a bit for any additional messages
            print("5. Waiting for additional messages...")
            try:
                additional_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                additional_data = json.loads(additional_msg)
                print(f"📨 Additional message: {additional_data}")
            except asyncio.TimeoutError:
                print("⏰ No additional messages (expected)")
            
            # Test queue leave
            print("6. Testing queue leave...")
            leave_msg = {
                "type": "queue.leave", 
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(leave_msg))
            
            leave_response = await websocket.recv()
            leave_data = json.loads(leave_response)
            print(f"👋 Leave response: {leave_data}")
            
            print("✅ WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

async def test_two_player_matchmaking():
    """Test matchmaking with two players"""
    print("\n🎮 Testing Two-Player Matchmaking...")
    
    # Create two test users
    users = []
    for i in range(2):
        user_data = {
            "email": f"player{i+1}@example.com",
            "password": "password123",
            "display_name": f"Player {i+1}"
        }
        
        try:
            # Try to register
            response = requests.post(f"{API_URL}/v1/auth/player/register", json=user_data)
            if response.status_code == 409:
                # User exists, login instead
                login_data = {"email": user_data["email"], "password": user_data["password"]}
                response = requests.post(f"{API_URL}/v1/auth/player/login", json=login_data)
            
            if response.status_code in [200, 201]:
                token_data = response.json()
                users.append({
                    "email": user_data["email"],
                    "token": token_data["access_token"],
                    "user_id": token_data["user"]["id"]
                })
                print(f"✅ Player {i+1} ready: {user_data['email']}")
            else:
                print(f"❌ Failed to create Player {i+1}: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Error creating Player {i+1}: {e}")
            return
    
    # Connect both players to WebSocket
    print("Connecting both players to WebSocket...")
    
    async def player_session(player_info, player_num):
        """Individual player WebSocket session"""
        ws_url = f"{REALTIME_URL}?token={player_info['token']}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"✅ Player {player_num} connected")
                
                # Wait for welcome
                welcome = await websocket.recv()
                print(f"📨 Player {player_num} welcome: {json.loads(welcome)}")
                
                # Join queue
                queue_msg = {"type": "queue.join", "mode": "1v1"}
                await websocket.send(json.dumps(queue_msg))
                print(f"🎯 Player {player_num} joined queue")
                
                # Wait for responses
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        data = json.loads(message)
                        print(f"📨 Player {player_num} received: {data['type']} - {data}")
                        
                        # If match found, we're done
                        if data.get('type') == 'match.found':
                            print(f"🎉 Player {player_num} found match!")
                            break
                            
                    except asyncio.TimeoutError:
                        print(f"⏰ Player {player_num} timeout waiting for match")
                        break
                        
        except Exception as e:
            print(f"❌ Player {player_num} error: {e}")
    
    # Run both player sessions concurrently
    await asyncio.gather(
        player_session(users[0], 1),
        player_session(users[1], 2)
    )

async def main():
    """Main test function"""
    print("🚀 Deckport Realtime Service Test Suite")
    print(f"API URL: {API_URL}")
    print(f"WebSocket URL: {REALTIME_URL}")
    print("")
    
    # Test 1: Basic connection
    await test_websocket_connection()
    
    # Test 2: Two-player matchmaking
    await test_two_player_matchmaking()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
