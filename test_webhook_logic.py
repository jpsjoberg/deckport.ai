#!/usr/bin/env python3
"""
Test script to verify webhook handler logic without requiring actual Stripe events
"""
import sys
import os
sys.path.append('/home/jp/deckport.ai/services/api')

from stripe_service import stripe_service

# Test data for different webhook events
test_events = {
    "payment_intent.succeeded": {
        "id": "pi_test_12345",
        "amount": 2000,
        "currency": "usd",
        "status": "succeeded",
        "metadata": {
            "order_id": "test_order_123",
            "session_id": "test_session_456"
        }
    },
    "customer.subscription.created": {
        "id": "sub_test_12345",
        "customer": "cus_test_12345",
        "status": "active",
        "current_period_start": 1640995200,
        "current_period_end": 1643673600,
        "trial_end": None,
        "metadata": {
            "user_id": "123",
            "plan": "premium"
        }
    },
    "invoice.payment_succeeded": {
        "id": "in_test_12345",
        "subscription": "sub_test_12345",
        "customer": "cus_test_12345",
        "amount_paid": 2999,
        "currency": "usd",
        "period_start": 1640995200,
        "period_end": 1643673600,
        "billing_reason": "subscription_cycle"
    },
    "invoice.payment_failed": {
        "id": "in_test_67890",
        "subscription": "sub_test_12345",
        "customer": "cus_test_12345",
        "amount_due": 2999,
        "currency": "usd",
        "attempt_count": 1,
        "next_payment_attempt": 1641081600
    }
}

def test_webhook_handlers():
    """Test all webhook event handlers"""
    print("🧪 Testing Webhook Event Handlers\n")
    
    for event_type, event_data in test_events.items():
        print(f"Testing: {event_type}")
        print("-" * 50)
        
        try:
            # Get the handler method name
            handler_name = f"_handle_{event_type.replace('.', '_')}"
            
            # Check if handler exists
            if hasattr(stripe_service, handler_name):
                handler = getattr(stripe_service, handler_name)
                result = handler(event_data)
                
                print(f"✅ Handler found: {handler_name}")
                print(f"📤 Result: {result}")
                
                # Verify result structure
                if result.get("success"):
                    print(f"✅ Success: {result.get('action', 'N/A')}")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
            else:
                print(f"❌ Handler not found: {handler_name}")
                
        except Exception as e:
            print(f"💥 Error testing {event_type}: {e}")
            
        print("\n")

def test_webhook_routing():
    """Test the main webhook routing logic"""
    print("🔀 Testing Webhook Event Routing\n")
    
    # Create a mock webhook event
    mock_event = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": test_events["payment_intent.succeeded"]
        }
    }
    
    print("Mock event structure:")
    print(f"Event type: {mock_event['type']}")
    print(f"Data object keys: {list(mock_event['data']['object'].keys())}")
    print()
    
    # Test the routing logic (without signature verification)
    try:
        event_type = mock_event["type"]
        event_data = mock_event["data"]["object"]
        
        print(f"Routing event: {event_type}")
        
        # Simulate the routing logic from handle_webhook
        if event_type == "payment_intent.succeeded":
            result = stripe_service._handle_payment_succeeded(event_data)
            print(f"✅ Routed to: _handle_payment_succeeded")
            print(f"📤 Result: {result}")
        else:
            print(f"❌ No routing found for: {event_type}")
            
    except Exception as e:
        print(f"💥 Routing error: {e}")

if __name__ == "__main__":
    print("🚀 Stripe Webhook Handler Test Suite")
    print("=" * 60)
    print()
    
    test_webhook_handlers()
    test_webhook_routing()
    
    print("🏁 Test Complete!")
