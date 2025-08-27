#!/usr/bin/env python3
"""
Test the actual webhook endpoint with simulated Stripe webhook data
"""
import requests
import json
import hashlib
import hmac
import time

# Webhook endpoint
WEBHOOK_URL = "https://api.deckport.ai/v1/shop/webhooks/stripe"

# Mock webhook secret (this won't work for real verification, but tests the flow)
WEBHOOK_SECRET = "whsec_test_webhook_secret_placeholder"

def create_stripe_signature(payload: str, secret: str, timestamp: int) -> str:
    """Create a Stripe-style webhook signature"""
    # Remove the whsec_ prefix if present
    if secret.startswith('whsec_'):
        secret = secret[6:]
    
    # Create the signed payload
    signed_payload = f"{timestamp}.{payload}"
    
    # Create HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"t={timestamp},v1={signature}"

def test_webhook_endpoint():
    """Test the webhook endpoint with various event types"""
    
    # Test events
    test_events = [
        {
            "id": "evt_test_webhook",
            "object": "event",
            "api_version": "2020-08-27",
            "created": int(time.time()),
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_12345",
                    "object": "payment_intent",
                    "amount": 2000,
                    "currency": "usd",
                    "status": "succeeded",
                    "metadata": {
                        "order_id": "test_order_123",
                        "session_id": "test_session_456"
                    }
                }
            }
        },
        {
            "id": "evt_test_subscription",
            "object": "event", 
            "api_version": "2020-08-27",
            "created": int(time.time()),
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test_12345",
                    "object": "subscription",
                    "customer": "cus_test_12345",
                    "status": "active",
                    "current_period_start": int(time.time()),
                    "current_period_end": int(time.time()) + 2592000,  # +30 days
                    "metadata": {
                        "user_id": "123",
                        "plan": "premium"
                    }
                }
            }
        }
    ]
    
    print("🧪 Testing Webhook Endpoint")
    print("=" * 50)
    
    for i, event in enumerate(test_events, 1):
        print(f"\n📨 Test {i}: {event['type']}")
        print("-" * 30)
        
        # Convert to JSON
        payload = json.dumps(event)
        timestamp = int(time.time())
        
        # Create signature (this will fail verification but tests the flow)
        signature = create_stripe_signature(payload, WEBHOOK_SECRET, timestamp)
        
        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Stripe-Signature': signature
        }
        
        try:
            # Send request
            response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Webhook processed successfully")
            elif response.status_code == 400:
                print("⚠️ Bad request (likely signature verification failed)")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"💥 Request failed: {e}")

def test_webhook_without_signature():
    """Test webhook endpoint without signature (should fail)"""
    print("\n🚫 Testing Webhook Without Signature")
    print("-" * 40)
    
    payload = json.dumps({
        "id": "evt_test",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_test"}}
    })
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected request without signature")
        else:
            print("❌ Should have rejected request without signature")
            
    except requests.exceptions.RequestException as e:
        print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    test_webhook_endpoint()
    test_webhook_without_signature()
    print("\n🏁 Webhook endpoint tests complete!")
