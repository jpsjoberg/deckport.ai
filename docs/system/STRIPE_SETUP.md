# Stripe Integration Setup

## Environment Variables

Add these environment variables to your `.env` file:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# For production, use live keys:
# STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
# STRIPE_SECRET_KEY=sk_live_your_live_secret_key
```

## Stripe Dashboard Setup

### 1. Create Stripe Account
- Go to https://stripe.com and create an account
- Complete business verification for live payments

### 2. Get API Keys
- Go to Developers > API keys
- Copy your Publishable key and Secret key
- Use test keys for development, live keys for production

### 3. Setup Webhooks
- Go to Developers > Webhooks
- Click "Add endpoint"
- Set endpoint URL: `https://yourdomain.com/v1/shop/webhooks/stripe`
- Select events to listen for:
  - `payment_intent.succeeded`
  - `payment_intent.payment_failed`
  - `checkout.session.completed`
- Copy the webhook signing secret

### 4. Configure Payment Methods
- Go to Settings > Payment methods
- Enable desired payment methods (cards, digital wallets, etc.)

## Testing

### Test Card Numbers
Use these test card numbers in development:

- **Visa**: 4242424242424242
- **Visa (debit)**: 4000056655665556
- **Mastercard**: 5555555555554444
- **American Express**: 378282246310005
- **Declined card**: 4000000000000002

### Test Scenarios
- Use any future expiry date (e.g., 12/34)
- Use any 3-digit CVC (4 digits for Amex)
- Use any ZIP code

## Production Checklist

- [ ] Replace test keys with live keys
- [ ] Update webhook endpoint to production URL
- [ ] Configure webhook signing secret
- [ ] Test with real payment methods
- [ ] Set up proper error monitoring
- [ ] Configure tax rates if needed
- [ ] Set up refund policies

## API Endpoints

### Customer Endpoints
- `POST /v1/shop/checkout/create-session` - Create checkout session
- `GET /v1/shop/checkout/session/{id}` - Get session data
- `POST /v1/shop/checkout/process` - Process completed payment

### Webhook Endpoint
- `POST /v1/shop/webhooks/stripe` - Handle Stripe events

## Security Notes

- Never expose secret keys in frontend code
- Always validate webhooks with signing secret
- Use HTTPS in production
- Implement proper error handling
- Log payment events for auditing
