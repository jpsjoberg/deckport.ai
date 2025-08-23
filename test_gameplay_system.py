#!/usr/bin/env python3
"""
Test script for the Deckport gameplay system
Tests the core gameplay engine, matchmaking, and API endpoints
"""

import requests
import json
import time
import sys
import os

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

API_BASE_URL = "http://127.0.0.1:8002"

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_create_test_match():
    """Test creating a test match"""
    print("\n🎮 Testing match creation...")
    
    # Create test match
    match_data = {
        "mode": "1v1",
        "players": [
            {"player_id": 1, "console_id": "test_console_1"},
            {"player_id": 2, "console_id": "test_console_2"}
        ]
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/v1/gameplay/matches", json=match_data)
        if response.status_code == 200:
            result = response.json()
            match_id = result.get("match_id")
            print(f"✅ Match created successfully: {match_id}")
            return match_id
        else:
            print(f"❌ Match creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Match creation error: {e}")
        return None

def test_start_match(match_id):
    """Test starting a match"""
    print(f"\n🚀 Testing match start for match {match_id}...")
    
    try:
        response = requests.post(f"{API_BASE_URL}/v1/gameplay/matches/{match_id}/start")
        if response.status_code == 200:
            result = response.json()
            print("✅ Match started successfully")
            print(f"   Game state initialized with {len(result.get('game_state', {}).get('players', {}))} players")
            return result.get("game_state")
        else:
            print(f"❌ Match start failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Match start error: {e}")
        return None

def test_get_match_state(match_id, team=None):
    """Test getting match state"""
    print(f"\n📊 Testing match state retrieval for match {match_id}...")
    
    url = f"{API_BASE_URL}/v1/gameplay/matches/{match_id}/state"
    if team is not None:
        url += f"?team={team}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            state = response.json()
            print("✅ Match state retrieved successfully")
            print(f"   Turn: {state.get('turn', 'N/A')}")
            print(f"   Phase: {state.get('phase', 'N/A')}")
            print(f"   Current Player: {state.get('current_player', 'N/A')}")
            if team is not None:
                print(f"   Your Turn: {state.get('your_turn', 'N/A')}")
            return state
        else:
            print(f"❌ Match state retrieval failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Match state error: {e}")
        return None

def test_play_card(match_id):
    """Test playing a card"""
    print(f"\n🃏 Testing card play for match {match_id}...")
    
    card_data = {
        "player_team": 0,
        "card_id": "test_card_001",
        "action": "play",
        "target": None
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/v1/gameplay/matches/{match_id}/play-card", json=card_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Card played successfully")
            return result
        else:
            print(f"❌ Card play failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Card play error: {e}")
        return None

def test_force_advance_phase(match_id):
    """Test force advancing phase (admin function)"""
    print(f"\n⏭️ Testing force phase advance for match {match_id}...")
    
    # This requires admin token, so it might fail
    try:
        response = requests.post(f"{API_BASE_URL}/v1/gameplay/matches/{match_id}/advance-phase")
        if response.status_code == 200:
            print("✅ Phase advanced successfully")
            return True
        else:
            print(f"⚠️ Phase advance failed (expected without admin token): {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Phase advance error (expected): {e}")
        return False

def test_matchmaking_queue():
    """Test matchmaking queue operations"""
    print("\n🎯 Testing matchmaking queue...")
    
    # Join queue
    queue_data = {
        "player_id": 1,
        "console_id": "test_console_1",
        "mode": "1v1"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/v1/gameplay/queue/join", json=queue_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Joined queue successfully - Status: {result.get('status')}")
            
            # Check queue status
            response = requests.get(f"{API_BASE_URL}/v1/gameplay/queue/status?player_id=1&mode=1v1")
            if response.status_code == 200:
                status = response.json()
                print(f"   Queue position: {status.get('position', 'N/A')}")
                print(f"   In queue: {status.get('in_queue', False)}")
            
            # Leave queue
            leave_data = {"player_id": 1, "mode": "1v1"}
            response = requests.post(f"{API_BASE_URL}/v1/gameplay/queue/leave", json=leave_data)
            if response.status_code == 200:
                print("✅ Left queue successfully")
                return True
            else:
                print(f"❌ Failed to leave queue: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to join queue: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Queue test error: {e}")
        return False

def test_active_matches():
    """Test getting active matches"""
    print("\n📋 Testing active matches retrieval...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/v1/gameplay/matches/active")
        if response.status_code == 200:
            result = response.json()
            matches = result.get("active_matches", [])
            print(f"✅ Retrieved {len(matches)} active matches")
            for match in matches:
                print(f"   Match {match.get('id')}: {match.get('status')} ({match.get('participants')} players)")
            return True
        else:
            print(f"❌ Failed to get active matches: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Active matches error: {e}")
        return False

def main():
    """Run all tests"""
    print("🎮 Deckport Gameplay System Test Suite")
    print("=" * 50)
    
    # Test API health first
    if not test_api_health():
        print("\n❌ API is not available. Make sure the API service is running on port 8002.")
        return False
    
    # Test matchmaking queue
    test_matchmaking_queue()
    
    # Test match creation and gameplay
    match_id = test_create_test_match()
    if match_id:
        # Start the match
        game_state = test_start_match(match_id)
        if game_state:
            # Get match state
            test_get_match_state(match_id)
            test_get_match_state(match_id, team=0)  # Player perspective
            
            # Try to play a card (will likely fail due to game rules)
            test_play_card(match_id)
            
            # Force advance phase (will fail without admin token)
            test_force_advance_phase(match_id)
            
            # Get updated state
            test_get_match_state(match_id)
    
    # Test active matches
    test_active_matches()
    
    print("\n" + "=" * 50)
    print("🎮 Test suite completed!")
    print("\nNote: Some tests may fail due to game rules or missing admin authentication.")
    print("This is expected behavior for a properly secured system.")
    
    return True

if __name__ == "__main__":
    main()
