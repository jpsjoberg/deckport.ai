# 🔧 Environment Configuration Guide

**Last Updated**: August 25, 2025

## 📋 Overview

This guide covers how to configure environment variables for the Deckport.ai platform, including Stripe payment integration, database connections, and security settings.

## 🔐 Stripe Configuration

### Required Environment Variables

The following Stripe environment variables must be configured in the systemd service:

```bash
STRIPE_SECRET_KEY=sk_test_51234567890abcdef_your_test_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_51234567890abcdef_your_test_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### Getting Stripe Keys

1. **Create Stripe Account**: Sign up at [stripe.com](https://stripe.com)
2. **Access Dashboard**: Go to [dashboard.stripe.com](https://dashboard.stripe.com)
3. **Get API Keys**: Navigate to Developers > API keys
4. **Setup Webhooks**: Go to Developers > Webhooks and create endpoint

### Test vs Production Keys

- **Test Keys**: Start with `sk_test_` and `pk_test_` for development
- **Production Keys**: Use `sk_live_` and `pk_live_` for live environment
- **Never commit keys**: Keep all keys secure and out of version control

## ⚙️ Systemd Service Configuration

### Current Configuration

The API service is configured in `/etc/systemd/system/api.service`:

```ini
[Unit]
Description=Deckport API Service (New Structure)
Wants=network-online.target
After=network-online.target

[Service]
User=jp
Group=www-data
WorkingDirectory=/home/jp/deckport.ai/services/api
Environment="PATH=/home/jp/deckport.ai/services/api/venv/bin"
Environment="PYTHONPATH=/home/jp/deckport.ai"
Environment="PUBLIC_API_URL=https://api.deckport.ai"
Environment="CONSOLE_API_URL=http://127.0.0.1:8002"
Environment="STRIPE_SECRET_KEY=sk_test_placeholder"
Environment="STRIPE_PUBLISHABLE_KEY=pk_test_placeholder"
Environment="STRIPE_WEBHOOK_SECRET=whsec_placeholder"
ExecStart=/home/jp/deckport.ai/services/api/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8002 wsgi:app
Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
```

### Updating Environment Variables

1. **Edit Service File**:
   ```bash
   sudo nano /etc/systemd/system/api.service
   ```

2. **Update Environment Variables**:
   Replace placeholder values with actual keys

3. **Reload and Restart**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart api.service
   ```

4. **Verify Status**:
   ```bash
   sudo systemctl status api.service
   ```

## 🔒 Security Best Practices

### Environment Variable Security

1. **Use Test Keys First**: Always start with test keys for development
2. **Secure Production Keys**: Store production keys securely
3. **Regular Rotation**: Rotate keys periodically
4. **Access Control**: Limit who can access production keys
5. **Monitoring**: Monitor for unauthorized key usage

### Key Management

- **Development**: Use test keys in development environment
- **Staging**: Use test keys in staging environment  
- **Production**: Use live keys only in production
- **Backup**: Keep secure backup of production keys

## 🧪 Testing Configuration

### Verify Stripe Integration

1. **Check Service Status**:
   ```bash
   sudo systemctl status api.service
   ```

2. **Check Logs**:
   ```bash
   sudo journalctl -u api.service -f
   ```

3. **Test API Health**:
   ```bash
   curl http://localhost:8002/health
   ```

4. **Test Shop Endpoints**:
   ```bash
   curl http://localhost:8002/v1/shop/products
   ```

### Expected Results

- ✅ No "Stripe API key not configured" warnings in logs
- ✅ API service running without errors
- ✅ Shop endpoints responding correctly
- ✅ Payment processing functional (with test keys)

## 📚 Additional Configuration

### Database Connection
```bash
DATABASE_URL=postgresql://deckport_user:password@localhost:5432/deckport_db
```

### JWT Security
```bash
JWT_SECRET_KEY=your_secure_jwt_secret
ADMIN_JWT_SECRET=your_secure_admin_jwt_secret
```

### NFC Configuration
```bash
NFC_ENCRYPTION_KEY=your_nfc_encryption_key
NFC_READER_TYPE=ACR122U
```

## 🎯 Production Checklist

- [ ] Stripe live keys configured
- [ ] Webhook endpoints configured in Stripe dashboard
- [ ] SSL certificates installed
- [ ] Database connection secured
- [ ] JWT secrets generated and configured
- [ ] NFC encryption keys set
- [ ] Service monitoring enabled
- [ ] Backup procedures in place

## 🔗 Related Documentation

- [Stripe Setup Guide](STRIPE_SETUP.md)
- [System Services](SYSTEMD_SERVICES.md)
- [Authentication System](AUTHENTICATION_SYSTEM.md)
- [Testing Guide](TESTING_GUIDE.md)
