# 🔔 Stripe Webhook Events for Subscriptions

**Last Updated**: August 25, 2025  
**Status**: Production Ready ✅

## 📋 Overview

This document lists all Stripe webhook events that the Deckport.ai platform handles for both one-time payments and monthly subscriptions.

## 🔗 Webhook Endpoint

**URL**: `https://your-domain.com/v1/shop/webhooks/stripe`  
**Method**: `POST`  
**Authentication**: Stripe signature verification

## 📨 Supported Webhook Events

### 💳 One-Time Payment Events

| Event | Description | Action |
|-------|-------------|--------|
| `payment_intent.succeeded` | Payment completed successfully | Confirm order, fulfill items |
| `payment_intent.payment_failed` | Payment failed | Release inventory, notify customer |
| `checkout.session.completed` | Checkout session completed | Process order completion |

### 🔄 Subscription Lifecycle Events

| Event | Description | Action |
|-------|-------------|--------|
| `customer.subscription.created` | New subscription started | Activate user account, grant access |
| `customer.subscription.updated` | Subscription modified | Update user permissions, plan changes |
| `customer.subscription.deleted` | Subscription cancelled | Revoke access, cleanup resources |

### 💰 Subscription Payment Events

| Event | Description | Action |
|-------|-------------|--------|
| `invoice.payment_succeeded` | Monthly payment successful | Extend subscription, send receipt |
| `invoice.payment_failed` | Monthly payment failed | Send dunning emails, retry logic |
| `invoice.created` | Invoice generated | Prepare for payment attempt |
| `invoice.finalized` | Invoice ready for payment | Send invoice to customer |

### 👤 Customer Management Events

| Event | Description | Action |
|-------|-------------|--------|
| `customer.created` | New customer created | Initialize customer profile |
| `customer.updated` | Customer details changed | Update local customer data |
| `customer.deleted` | Customer deleted | Cleanup customer data |

### 💳 Payment Method Events

| Event | Description | Action |
|-------|-------------|--------|
| `payment_method.attached` | Payment method added | Update billing info |
| `payment_method.detached` | Payment method removed | Handle payment method changes |

### ⏰ Trial and Billing Events

| Event | Description | Action |
|-------|-------------|--------|
| `customer.subscription.trial_will_end` | Trial ending in 3 days | Send trial ending notification |
| `invoice.upcoming` | Invoice will be created soon | Send billing reminder |

## 🔧 Stripe Dashboard Configuration

### Required Webhook Events for Subscriptions

When setting up your webhook in the [Stripe Dashboard](https://dashboard.stripe.com/webhooks), select these events:

#### Core Subscription Events:
- ✅ `customer.subscription.created`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`
- ✅ `invoice.payment_succeeded`
- ✅ `invoice.payment_failed`
- ✅ `invoice.created`
- ✅ `invoice.finalized`

#### Customer Management:
- ✅ `customer.created`
- ✅ `customer.updated`
- ✅ `customer.deleted`

#### Payment Methods:
- ✅ `payment_method.attached`
- ✅ `payment_method.detached`

#### Trial and Notifications:
- ✅ `customer.subscription.trial_will_end`
- ✅ `invoice.upcoming`

#### One-Time Payments:
- ✅ `payment_intent.succeeded`
- ✅ `payment_intent.payment_failed`
- ✅ `checkout.session.completed`

## 🎯 Event Processing Flow

### Subscription Creation Flow:
1. **`customer.created`** → Initialize customer profile
2. **`customer.subscription.created`** → Activate subscription, grant access
3. **`invoice.created`** → First invoice generated
4. **`invoice.payment_succeeded`** → First payment processed

### Monthly Billing Flow:
1. **`invoice.upcoming`** → Billing reminder (7 days before)
2. **`invoice.created`** → Invoice generated
3. **`invoice.finalized`** → Invoice ready for payment
4. **`invoice.payment_succeeded`** → Payment successful, extend access
   - OR **`invoice.payment_failed`** → Payment failed, retry logic

### Subscription Cancellation Flow:
1. **`customer.subscription.updated`** → `cancel_at_period_end = true`
2. **`customer.subscription.deleted`** → Subscription ended, revoke access

## 🔒 Security

### Webhook Signature Verification
```python
# Automatic signature verification using Stripe library
event = stripe.Webhook.construct_event(
    payload, signature, STRIPE_WEBHOOK_SECRET
)
```

### Environment Variables Required:
```bash
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

## 🧪 Testing Webhooks

### Stripe CLI Testing:
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8002/v1/shop/webhooks/stripe

# Trigger test events
stripe trigger customer.subscription.created
stripe trigger invoice.payment_succeeded
stripe trigger invoice.payment_failed
```

### Manual Testing:
```bash
# Test webhook endpoint (should return signature error)
curl -X POST http://localhost:8002/v1/shop/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## 📊 Webhook Response Format

All webhook handlers return structured responses:

```json
{
  "success": true,
  "action": "subscription_created",
  "subscription_id": "sub_1234567890",
  "customer_id": "cus_1234567890",
  "status": "active",
  "current_period_start": 1640995200,
  "current_period_end": 1643673600,
  "metadata": {}
}
```

## 🚨 Error Handling

### Failed Webhook Processing:
- **Invalid Signature**: Returns 400 error
- **Processing Error**: Returns 500 error, Stripe will retry
- **Unknown Event**: Returns 200 success (logged but not processed)

### Retry Logic:
- Stripe automatically retries failed webhooks
- Exponential backoff: 1s, 5s, 30s, 2m, 15m, 1h, 6h, 24h
- After 3 days, webhooks are disabled

## 🔗 Related Documentation

- [Environment Setup](ENVIRONMENT_SETUP.md)
- [Stripe Setup Guide](STRIPE_SETUP.md)
- [System Services](SYSTEMD_SERVICES.md)
- [Testing Guide](TESTING_GUIDE.md)

---

*This webhook configuration supports both one-time payments and recurring subscriptions, providing complete coverage for all Stripe billing scenarios.*
