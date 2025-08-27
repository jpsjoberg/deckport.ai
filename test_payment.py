#!/usr/bin/env python3
import stripe
import json

# Set the API key from the file
with open('stripe', 'r') as f:
    stripe.api_key = f.read().strip()

try:
    # Create a test payment intent
    payment_intent = stripe.PaymentIntent.create(
        amount=2000,  # $20.00
        currency='usd',
        payment_method_types=['card'],
        metadata={
            'test_payment': 'webhook_test',
            'order_id': 'test_order_123'
        }
    )
    
    print('Payment Intent Created:')
    print(f'ID: {payment_intent.id}')
    print(f'Amount: ${payment_intent.amount/100:.2f}')
    print(f'Status: {payment_intent.status}')
    print(f'Client Secret: {payment_intent.client_secret}')
    
    # Now let's try to confirm it with a test card
    print('\nConfirming payment with test card...')
    
    confirmed_payment = stripe.PaymentIntent.confirm(
        payment_intent.id,
        payment_method='pm_card_visa'  # Test card that succeeds
    )
    
    print(f'Payment Status: {confirmed_payment.status}')
    print(f'Payment ID: {confirmed_payment.id}')
    
    if confirmed_payment.status == 'succeeded':
        print('✅ Payment succeeded! This should trigger a webhook.')
    else:
        print(f'⚠️ Payment status: {confirmed_payment.status}')
    
except Exception as e:
    print(f'Error: {e}')
