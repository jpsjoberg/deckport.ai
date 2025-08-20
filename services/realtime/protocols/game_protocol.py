"""
WebSocket Game Protocol Definitions
Defines all message types and formats for real-time communication
"""

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

class MessageType(str, Enum):
    # Connection
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Matchmaking
    QUEUE_JOIN = "queue.join"
    QUEUE_LEAVE = "queue.leave" 
    QUEUE_ACK = "queue.ack"
    MATCH_FOUND = "match.found"
    
    # Match Management
    MATCH_READY = "match.ready"
    MATCH_START = "match.start"
    MATCH_END = "match.end"
    
    # Game State
    STATE_UPDATE = "state.update"
    STATE_APPLY = "state.apply"
    SYNC_REQUEST = "sync.request"
    SYNC_SNAPSHOT = "sync.snapshot"
    
    # Card Actions
    CARD_PLAY = "card.play"
    CARD_CANCEL = "card.cancel"
    
    # Arsenal Management
    ARSENAL_ADD = "arsenal.add"
    ARSENAL_REMOVE = "arsenal.remove"
    ARSENAL_UPDATED = "arsenal.updated"
    
    # Timer Events
    TIMER_TICK = "timer.tick"

class GameProtocol:
    """Protocol handler for game messages"""
    
    @staticmethod
    def create_message(msg_type: MessageType, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a standardized protocol message"""
        message = {
            "type": msg_type.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data:
            message.update(data)
            
        return message
    
    @staticmethod
    def create_error(error_code: str, message: str, details: Dict = None) -> Dict[str, Any]:
        """Create a standardized error message"""
        error_msg = {
            "type": MessageType.ERROR.value,
            "error_code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            error_msg["details"] = details
            
        return error_msg
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate incoming message format"""
        if not isinstance(message, dict):
            return False, "Message must be a JSON object"
        
        if 'type' not in message:
            return False, "Message type required"
        
        msg_type = message.get('type')
        if not isinstance(msg_type, str):
            return False, "Message type must be a string"
        
        # Validate specific message types
        if msg_type == MessageType.QUEUE_JOIN.value:
            if 'mode' not in message:
                return False, "Queue join requires mode"
                
        elif msg_type == MessageType.CARD_PLAY.value:
            required_fields = ['match_id', 'card_id', 'action']
            for field in required_fields:
                if field not in message:
                    return False, f"Card play requires {field}"
        
        elif msg_type == MessageType.STATE_UPDATE.value:
            required_fields = ['match_id', 'delta']
            for field in required_fields:
                if field not in message:
                    return False, f"State update requires {field}"
        
        return True, None

# Message format examples for documentation
PROTOCOL_EXAMPLES = {
    "queue_join": {
        "type": "queue.join",
        "mode": "1v1",
        "preferred_range": [900, 1100]  # Optional ELO range
    },
    
    "match_found": {
        "type": "match.found",
        "match_id": "match_12345",
        "opponent": {
            "id": 456,
            "display_name": "Player2",
            "elo_rating": 1050
        },
        "your_team": 0,
        "mode": "1v1"
    },
    
    "match_start": {
        "type": "match.start",
        "match_id": "match_12345",
        "seed": 1234567890,
        "rules": {
            "turn_time_seconds": 60,
            "play_window_seconds": 10
        },
        "arena": {
            "name": "Sunspire Plateau",
            "color": "RADIANT"
        }
    },
    
    "card_play": {
        "type": "card.play",
        "match_id": "match_12345", 
        "card_id": "player_card_789",
        "action": "summon",
        "target": None,
        "client_timestamp": "2025-01-18T06:30:45.123Z"
    },
    
    "state_update": {
        "type": "state.update",
        "match_id": "match_12345",
        "delta": {
            "player_1": {
                "energy": 3,
                "mana": {"RADIANT": 2}
            },
            "turn": 5,
            "phase": "main"
        }
    },
    
    "timer_tick": {
        "type": "timer.tick",
        "match_id": "match_12345",
        "server_timestamp": "2025-01-18T06:30:45.123Z",
        "phase": "main",
        "remaining_ms": 45000
    }
}
