"""
Deckport.ai Real-time WebSocket Service
Handles matchmaking, game state synchronization, and real-time communication
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from shared.auth.jwt_handler import verify_token
from shared.utils.logging import setup_logging
from handlers.matchmaking import MatchmakingHandler
from handlers.game_state import GameStateHandler
from protocols.game_protocol import GameProtocol

# Load environment
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Deckport Realtime Service",
    description="WebSocket service for real-time gameplay and matchmaking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logger = setup_logging("realtime", os.getenv("LOG_LEVEL", "INFO"))

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, str] = {}  # user_id -> connection_id
        self.match_connections: Dict[str, List[str]] = {}  # match_id -> [connection_ids]
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        if user_id:
            self.user_connections[user_id] = connection_id
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            # Remove from user connections
            user_id = None
            for uid, cid in self.user_connections.items():
                if cid == connection_id:
                    user_id = uid
                    break
            
            if user_id:
                del self.user_connections[user_id]
            
            # Remove from match connections
            for match_id, connection_ids in self.match_connections.items():
                if connection_id in connection_ids:
                    connection_ids.remove(connection_id)
                    if not connection_ids:
                        del self.match_connections[match_id]
                    break
            
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id} (user: {user_id})")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(json.dumps(message))
    
    async def send_to_user(self, message: dict, user_id: int):
        connection_id = self.user_connections.get(user_id)
        if connection_id:
            await self.send_personal_message(message, connection_id)
    
    async def send_to_match(self, message: dict, match_id: str):
        connection_ids = self.match_connections.get(match_id, [])
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)

# Global connection manager
manager = ConnectionManager()

# Initialize handlers (will be created when needed)
matchmaking_handler = None
game_state_handler = None
protocol = GameProtocol()

def get_handlers():
    """Get or create handlers"""
    global matchmaking_handler, game_state_handler
    if matchmaking_handler is None:
        matchmaking_handler = MatchmakingHandler(manager)
    if game_state_handler is None:
        game_state_handler = GameStateHandler(manager)
    return matchmaking_handler, game_state_handler

async def get_current_user(websocket: WebSocket) -> Optional[dict]:
    """Extract user info from WebSocket connection"""
    # Get token from query params or headers
    token = None
    
    # Try query params first
    if hasattr(websocket, 'query_params'):
        token = websocket.query_params.get('token')
    
    if not token:
        # Try headers
        for name, value in websocket.headers.items():
            if name.lower() == 'authorization' and value.startswith('Bearer '):
                token = value.split(' ')[1]
                break
    
    if not token:
        return None
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        return None
    
    return {
        'user_id': payload.get('user_id'),
        'email': payload.get('email'),
        'type': payload.get('type'),
        'device_uid': payload.get('device_uid'),
        'console_id': payload.get('console_id')
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "realtime",
        "connections": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication"""
    connection_id = f"conn_{datetime.utcnow().timestamp()}_{len(manager.active_connections)}"
    user_info = await get_current_user(websocket)
    
    if not user_info:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    user_id = user_info.get('user_id')
    await manager.connect(websocket, connection_id, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "connection_id": connection_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Route message to appropriate handler
            await route_message(message, connection_id, user_info)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(connection_id)

async def route_message(message: dict, connection_id: str, user_info: dict):
    """Route incoming WebSocket messages to appropriate handlers"""
    message_type = message.get('type')
    
    if not message_type:
        await manager.send_personal_message({
            "type": "error",
            "error": "Message type required"
        }, connection_id)
        return
    
    try:
        # Get handlers
        mm_handler, gs_handler = get_handlers()
        
        # Start polling if not started
        if not mm_handler._polling_started:
            await mm_handler.start_queue_polling()
        
        # Route to handlers
        if message_type.startswith('queue.'):
            await mm_handler.handle_message(message, connection_id, user_info)
        elif message_type.startswith('match.'):
            await gs_handler.handle_message(message, connection_id, user_info)
        elif message_type == 'ping':
            await manager.send_personal_message({"type": "pong"}, connection_id)
        else:
            await manager.send_personal_message({
                "type": "error", 
                "error": f"Unknown message type: {message_type}"
            }, connection_id)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "error": "Message processing failed"
        }, connection_id)

if __name__ == "__main__":
    logger.info("Starting Deckport Realtime Service")
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8003,
        reload=True,
        log_level="info"
    )
