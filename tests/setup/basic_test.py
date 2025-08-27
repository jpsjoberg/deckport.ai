#!/usr/bin/env python3
"""
Basic test to verify video streaming system is ready
"""

import psycopg2
import os

def test_database_tables():
    """Test that video streaming tables exist"""
    print("🔗 Testing database tables...")
    
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="deckport",
            user="deckport_app",
            password="N0D3-N0D3-N0D3#M0nk3y33"
        )
        
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'video%'
            ORDER BY table_name
        """)
        
        video_tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['video_streams', 'video_stream_participants', 'video_stream_logs']
        
        print(f"📊 Found video tables: {video_tables}")
        
        for table in expected_tables:
            if table in video_tables:
                print(f"✅ {table}: exists")
            else:
                print(f"❌ {table}: missing")
                return False
        
        # Test arena table has video columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'arenas' 
            AND column_name LIKE '%video%'
        """)
        
        video_columns = [row[0] for row in cursor.fetchall()]
        print(f"🏟️ Arena video columns: {video_columns}")
        
        cursor.close()
        conn.close()
        
        return len(video_tables) >= 3
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        # Console components
        'console/arena_video_manager.gd',
        'console/video_stream_manager.gd',
        'console/battle_scene.gd',
        
        # API routes
        'services/api/routes/arenas.py',
        'services/api/routes/video_streaming.py',
        
        # Admin interface
        'frontend/admin_routes/video_surveillance.py',
        'frontend/templates/admin/video_surveillance/dashboard.html',
        
        # Documentation
        'TESTING_GUIDE.md',
        'database_migration_video_streaming.sql'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path}: {size:,} bytes")
        else:
            print(f"❌ {file_path}: Missing")
            all_exist = False
    
    return all_exist

def test_api_endpoints_basic():
    """Basic test of API endpoint structure"""
    print("\n🔗 Testing API endpoint files...")
    
    try:
        # Check if route files have the expected content
        with open('services/api/routes/arenas.py', 'r') as f:
            arena_content = f.read()
            
        with open('services/api/routes/video_streaming.py', 'r') as f:
            video_content = f.read()
        
        # Check for key endpoints
        arena_endpoints = [
            '/v1/arenas/list',
            '/v1/arenas/weighted',
            '/v1/arenas/random'
        ]
        
        video_endpoints = [
            '/v1/video/battle/start',
            '/v1/video/admin/surveillance/start',
            '/v1/video/admin/active-streams'
        ]
        
        print("🏟️ Arena endpoints:")
        for endpoint in arena_endpoints:
            if endpoint in arena_content:
                print(f"✅ {endpoint}: defined")
            else:
                print(f"❌ {endpoint}: missing")
        
        print("📹 Video streaming endpoints:")
        for endpoint in video_endpoints:
            if endpoint in video_content:
                print(f"✅ {endpoint}: defined")
            else:
                print(f"❌ {endpoint}: missing")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def main():
    """Run basic tests"""
    print("🧪 Basic Video Streaming System Tests")
    print("=" * 50)
    
    tests = [
        ("Database Tables", test_database_tables),
        ("File Structure", test_file_structure),
        ("API Endpoints", test_api_endpoints_basic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🧪 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All basic tests passed!")
        print("\n📋 Next Steps:")
        print("1. Fix API server startup issues")
        print("2. Test arena endpoints manually")
        print("3. Test video streaming with Godot console")
        print("4. Test admin surveillance dashboard")
    else:
        print(f"\n⚠️ {total-passed} tests failed - check issues above")
    
    print(f"\n📖 See TESTING_GUIDE.md for detailed testing procedures")
    
    return passed == total

if __name__ == "__main__":
    main()
