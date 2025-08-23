#!/usr/bin/env python3
"""
ComfyUI Connection Test Script
Tests connectivity and functionality with ComfyUI server
"""

import sys
import os
import json
import time
sys.path.append('/home/jp/deckport.ai/frontend')

from services.comfyui_service import get_comfyui_service

def test_basic_connection():
    """Test basic ComfyUI server connectivity"""
    print("🔍 Testing basic ComfyUI connection...")
    
    comfyui = get_comfyui_service()
    print(f"   Target server: {comfyui.host}")
    
    if comfyui.is_online():
        print("✅ ComfyUI server is online and responding")
        return True
    else:
        print("❌ ComfyUI server is offline or unreachable")
        print(f"   Make sure ComfyUI is running at: {comfyui.host}")
        return False

def test_system_stats():
    """Test system statistics endpoint"""
    print("🔍 Testing system statistics...")
    
    comfyui = get_comfyui_service()
    stats = comfyui.get_system_stats()
    
    if stats:
        print("✅ System stats retrieved successfully:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        return True
    else:
        print("❌ Failed to retrieve system stats")
        return False

def test_queue_status():
    """Test queue status endpoint"""
    print("🔍 Testing queue status...")
    
    comfyui = get_comfyui_service()
    queue = comfyui.get_queue_status()
    
    if queue is not None:
        print("✅ Queue status retrieved successfully:")
        if 'queue_running' in queue:
            running = len(queue.get('queue_running', []))
            pending = len(queue.get('queue_pending', []))
            print(f"   Running: {running}, Pending: {pending}")
        else:
            print(f"   Queue data: {queue}")
        return True
    else:
        print("❌ Failed to retrieve queue status")
        return False

def test_workflow_loading():
    """Test workflow template loading"""
    print("🔍 Testing workflow template loading...")
    
    comfyui = get_comfyui_service()
    workflow_path = "/home/jp/deckport.ai/cardmaker.ai/art-generation.json"
    
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow template not found: {workflow_path}")
        return False
    
    workflow = comfyui.load_workflow_template(workflow_path)
    
    if workflow:
        print("✅ Workflow template loaded successfully")
        print(f"   Nodes in workflow: {len(workflow)}")
        
        # Check for expected nodes
        has_clip_encode = any(node.get('class_type') == 'CLIPTextEncode' for node in workflow.values())
        has_random_noise = any(node.get('class_type') == 'RandomNoise' for node in workflow.values())
        
        print(f"   Has CLIPTextEncode: {has_clip_encode}")
        print(f"   Has RandomNoise: {has_random_noise}")
        
        return True
    else:
        print("❌ Failed to load workflow template")
        return False

def test_prompt_injection():
    """Test prompt injection functionality"""
    print("🔍 Testing prompt injection...")
    
    comfyui = get_comfyui_service()
    workflow_path = "/home/jp/deckport.ai/cardmaker.ai/art-generation.json"
    
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow template not found: {workflow_path}")
        return False
    
    original_workflow = comfyui.load_workflow_template(workflow_path)
    if not original_workflow:
        print("❌ Failed to load workflow for testing")
        return False
    
    test_prompt = "A majestic dragon breathing fire in a fantasy landscape"
    test_seed = 12345
    
    modified_workflow = comfyui.inject_prompt(original_workflow, test_prompt, test_seed)
    
    # Check if prompt was injected
    prompt_found = False
    seed_found = False
    
    for node in modified_workflow.values():
        if (isinstance(node, dict) and 
            node.get('class_type') == 'CLIPTextEncode' and
            'inputs' in node and
            node['inputs'].get('text') == test_prompt):
            prompt_found = True
        
        if (isinstance(node, dict) and 
            node.get('class_type') == 'RandomNoise' and
            'inputs' in node and
            node['inputs'].get('noise_seed') == test_seed):
            seed_found = True
    
    if prompt_found and seed_found:
        print("✅ Prompt and seed injection working correctly")
        return True
    elif prompt_found:
        print("⚠️  Prompt injection working, but seed injection failed")
        return False
    else:
        print("❌ Prompt injection failed")
        return False

def test_full_generation_workflow():
    """Test a complete generation workflow (if server is online)"""
    print("🔍 Testing complete generation workflow...")
    
    comfyui = get_comfyui_service()
    
    if not comfyui.is_online():
        print("⚠️  Skipping generation test - server offline")
        return False
    
    test_prompt = "A simple test image - blue circle on white background"
    
    print(f"   Submitting test prompt: '{test_prompt}'")
    print("   ⚠️  This will actually generate an image!")
    
    # Ask for confirmation
    try:
        response = input("   Continue with actual generation? (y/N): ").strip().lower()
        if response != 'y':
            print("   Generation test skipped by user")
            return True
    except (EOFError, KeyboardInterrupt):
        print("   Generation test skipped")
        return True
    
    try:
        image_data = comfyui.generate_card_art(test_prompt, seed=42)
        
        if image_data:
            print(f"✅ Generation successful! Image size: {len(image_data)} bytes")
            
            # Save test image
            test_output = "/tmp/comfyui_test.png"
            with open(test_output, 'wb') as f:
                f.write(image_data)
            print(f"   Test image saved to: {test_output}")
            
            return True
        else:
            print("❌ Generation failed - no image data returned")
            return False
            
    except Exception as e:
        print(f"❌ Generation failed with error: {e}")
        return False

def print_setup_instructions():
    """Print ComfyUI setup instructions"""
    print("\n" + "="*60)
    print("🛠️  COMFYUI SETUP INSTRUCTIONS")
    print("="*60)
    print("""
To set up ComfyUI for testing:

1. Clone ComfyUI repository:
   git clone https://github.com/comfyanonymous/ComfyUI.git
   cd ComfyUI

2. Install dependencies:
   pip install -r requirements.txt

3. Download required models:
   - FLUX.1-dev model: Download to ComfyUI/models/unet/
   - T5XXL encoder: Download to ComfyUI/models/clip/
   - VAE model: Download to ComfyUI/models/vae/

4. Start ComfyUI server:
   python main.py --listen 0.0.0.0 --port 8188

5. Verify it's running:
   curl http://localhost:8188/system_stats

6. Set environment variable (optional):
   export COMFYUI_HOST="http://localhost:8188"

For external server, replace localhost with your server IP.
""")

def main():
    """Run all ComfyUI tests"""
    print("🚀 ComfyUI Connection Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("System Statistics", test_system_stats),
        ("Queue Status", test_queue_status),
        ("Workflow Loading", test_workflow_loading),
        ("Prompt Injection", test_prompt_injection),
        ("Full Generation", test_full_generation_workflow),
    ]
    
    results = []
    server_online = False
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            # Track if server is online for conditional tests
            if test_name == "Basic Connection" and result:
                server_online = True
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if not server_online:
        print_setup_instructions()
        print("\n⚠️  ComfyUI server is not running. See setup instructions above.")
    elif passed == len(results):
        print("\n🎉 All tests passed! ComfyUI integration is fully functional.")
    else:
        print("\n⚠️  Some tests failed. Check server configuration and network connectivity.")
    
    return 0 if server_online else 1

if __name__ == "__main__":
    exit(main())
