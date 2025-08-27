#!/usr/bin/env python3
"""
Simple test to verify video streaming system components
"""

import sys
import os
import psycopg2
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

def test_database_connection():
    """Test database connection and video streaming tables"""
    print("🔗 Testing database connection...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="deckport",
            user="deckport_app",
            password="N0D3-N0D3-N0D3#M0nk3y33"
        )
        
        cursor = conn.cursor()
        
        # Test video streaming tables exist
        tables_to_check = [
            'video_streams',
            'video_stream_participants', 
            'video_stream_logs',
            'arenas'
        ]
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}': {count} records")
        
        # Test arena data
        cursor.execute("SELECT id, name, mana_color, video_background_url FROM arenas LIMIT 5")
        arenas = cursor.fetchall()
        
        print(f"\n🏟️ Sample arenas:")
        for arena in arenas:
            print(f"  - ID {arena[0]}: {arena[1]} ({arena[2]}) - Video: {arena[3] or 'None'}")
        
        # Test enum types
        cursor.execute("SELECT unnest(enum_range(NULL::video_stream_type))")
        stream_types = [row[0] for row in cursor.fetchall()]
        print(f"\n📹 Video stream types: {', '.join(stream_types)}")
        
        cursor.close()
        conn.close()
        
        print("✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_video_streaming_models():
    """Test video streaming model imports"""
    print("\n🎥 Testing video streaming models...")
    
    try:
        # Test model imports
        from shared.models.base import (
            VideoStream, VideoStreamParticipant, VideoStreamLog,
            VideoStreamType, VideoStreamStatus, VideoCallParticipantRole,
            Arena, ArenaTheme, ArenaRarity
        )
        
        print("✅ All video streaming models imported successfully")
        
        # Test enum values
        print(f"📹 Stream types: {[t.value for t in VideoStreamType]}")
        print(f"📊 Stream statuses: {[s.value for s in VideoStreamStatus]}")
        print(f"👥 Participant roles: {[r.value for r in VideoCallParticipantRole]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model import test failed: {e}")
        return False

def test_api_routes():
    """Test API route imports"""
    print("\n🔗 Testing API route imports...")
    
    try:
        # Test route imports
        from services.api.routes.arenas import arenas_bp
        from services.api.routes.video_streaming import video_streaming_bp
        
        print("✅ Arena routes imported successfully")
        print("✅ Video streaming routes imported successfully")
        
        # Check route endpoints
        arena_rules = list(arenas_bp.url_map.iter_rules())
        video_rules = list(video_streaming_bp.url_map.iter_rules())
        
        print(f"🏟️ Arena endpoints: {len(arena_rules)} routes")
        print(f"📹 Video streaming endpoints: {len(video_rules)} routes")
        
        return True
        
    except Exception as e:
        print(f"❌ API route test failed: {e}")
        return False

def test_console_components():
    """Test console component files exist"""
    print("\n🎮 Testing console components...")
    
    components = [
        'console/arena_video_manager.gd',
        'console/video_stream_manager.gd', 
        'console/battle_scene.gd',
        'console/player_menu.gd'
    ]
    
    all_exist = True
    for component in components:
        if os.path.exists(component):
            size = os.path.getsize(component)
            print(f"✅ {component}: {size} bytes")
        else:
            print(f"❌ {component}: Not found")
            all_exist = False
    
    return all_exist

def test_admin_templates():
    """Test admin template files exist"""
    print("\n👁️ Testing admin surveillance templates...")
    
    templates = [
        'frontend/admin_routes/video_surveillance.py',
        'frontend/templates/admin/video_surveillance/dashboard.html',
        'frontend/templates/admin/video_surveillance/view.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print(f"✅ {template}: {size} bytes")
        else:
            print(f"❌ {template}: Not found")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🧪 Video Streaming System Component Tests")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Video Streaming Models", test_video_streaming_models),
        ("API Routes", test_api_routes),
        ("Console Components", test_console_components),
        ("Admin Templates", test_admin_templates)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🧪 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Video streaming system is ready!")
    else:
        print(f"\n⚠️ {total-passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
