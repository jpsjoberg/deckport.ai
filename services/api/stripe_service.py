"""
Stripe Payment Service
Handles all Stripe payment processing, webhooks, and customer management
"""

import os
import stripe
import logging
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class StripeService:
    """Service for handling Stripe payments"""
    
    def __init__(self):
        if not stripe.api_key:
            logger.warning("Stripe API key not configured - payments will fail")
    
    def create_payment_intent(self, amount: Decimal, currency: str = "usd", 
                            customer_email: str = None, metadata: Dict = None) -> Dict:
        """Create a Stripe Payment Intent"""
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            payment_intent_data = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "automatic_payment_methods": {"enabled": True},
                "metadata": metadata or {}
            }
            
            # Add customer if email provided
            if customer_email:
                customer = self.get_or_create_customer(customer_email)
                if customer:
                    payment_intent_data["customer"] = customer["id"]
            
            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
            
            logger.info(f"Created Stripe Payment Intent: {payment_intent.id} for ${amount}")
            
            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount_cents,
                "currency": currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Payment Intent creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        except Exception as e:
            logger.error(f"Unexpected error creating Payment Intent: {e}")
            return {
                "success": False,
                "error": "Payment processing unavailable"
            }
    
    def confirm_payment_intent(self, payment_intent_id: str) -> Dict:
        """Confirm a Payment Intent (for server-side confirmation)"""
        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            return {
                "success": True,
                "status": payment_intent.status,
                "payment_intent": payment_intent
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Payment Intent confirmation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[Dict]:
        """Retrieve a Payment Intent by ID"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "customer": payment_intent.customer,
                "metadata": payment_intent.metadata
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve Payment Intent {payment_intent_id}: {e}")
            return None
    
    def get_or_create_customer(self, email: str, name: str = None) -> Optional[Dict]:
        """Get existing customer or create new one"""
        try:
            # Search for existing customer
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
                logger.info(f"Found existing Stripe customer: {customer.id}")
            else:
                # Create new customer
                customer_data = {"email": email}
                if name:
                    customer_data["name"] = name
                
                customer = stripe.Customer.create(**customer_data)
                logger.info(f"Created new Stripe customer: {customer.id}")
            
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Customer creation/retrieval failed: {e}")
            return None
    
    def create_checkout_session(self, line_items: List[Dict], success_url: str, 
                              cancel_url: str, customer_email: str = None,
                              metadata: Dict = None) -> Dict:
        """Create a Stripe Checkout Session (alternative to Payment Intents)"""
        try:
            session_data = {
                "payment_method_types": ["card"],
                "line_items": line_items,
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {}
            }
            
            if customer_email:
                session_data["customer_email"] = customer_email
            
            session = stripe.checkout.Session.create(**session_data)
            
            logger.info(f"Created Stripe Checkout Session: {session.id}")
            
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url,
                "payment_intent": session.payment_intent
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Checkout Session creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict:
        """Handle Stripe webhook events"""
        if not STRIPE_WEBHOOK_SECRET:
            logger.error("Stripe webhook secret not configured")
            return {"success": False, "error": "Webhook not configured"}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            
            logger.info(f"Received Stripe webhook: {event['type']}")
            
            # Handle different event types
            event_type = event["type"]
            event_data = event["data"]["object"]
            
            # One-time payment events
            if event_type == "payment_intent.succeeded":
                return self._handle_payment_succeeded(event_data)
            elif event_type == "payment_intent.payment_failed":
                return self._handle_payment_failed(event_data)
            elif event_type == "checkout.session.completed":
                return self._handle_checkout_completed(event_data)
            
            # Subscription lifecycle events
            elif event_type == "customer.subscription.created":
                return self._handle_subscription_created(event_data)
            elif event_type == "customer.subscription.updated":
                return self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                return self._handle_subscription_cancelled(event_data)
            
            # Subscription payment events
            elif event_type == "invoice.payment_succeeded":
                return self._handle_invoice_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                return self._handle_invoice_payment_failed(event_data)
            elif event_type == "invoice.created":
                return self._handle_invoice_created(event_data)
            elif event_type == "invoice.finalized":
                return self._handle_invoice_finalized(event_data)
            
            # Customer events
            elif event_type == "customer.created":
                return self._handle_customer_created(event_data)
            elif event_type == "customer.updated":
                return self._handle_customer_updated(event_data)
            elif event_type == "customer.deleted":
                return self._handle_customer_deleted(event_data)
            
            # Payment method events
            elif event_type == "payment_method.attached":
                return self._handle_payment_method_attached(event_data)
            elif event_type == "payment_method.detached":
                return self._handle_payment_method_detached(event_data)
            
            # Trial and billing events
            elif event_type == "customer.subscription.trial_will_end":
                return self._handle_trial_will_end(event_data)
            elif event_type == "invoice.upcoming":
                return self._handle_upcoming_invoice(event_data)
            
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"success": True, "message": "Event received but not handled"}
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return {"success": False, "error": "Invalid payload"}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return {"success": False, "error": "Invalid signature"}
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return {"success": False, "error": "Webhook processing failed"}
    
    def _handle_payment_succeeded(self, payment_intent: Dict) -> Dict:
        """Handle successful payment"""
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        
        # Extract metadata to identify the order
        metadata = payment_intent.get("metadata", {})
        session_id = metadata.get("session_id")
        order_id = metadata.get("order_id")
        
        if session_id:
            # Update checkout session or order status
            # This will be handled by the shop service
            return {
                "success": True,
                "action": "payment_confirmed",
                "session_id": session_id,
                "order_id": order_id,
                "payment_intent_id": payment_intent["id"]
            }
        
        return {"success": True, "message": "Payment processed"}
    
    def _handle_payment_failed(self, payment_intent: Dict) -> Dict:
        """Handle failed payment"""
        logger.warning(f"Payment failed: {payment_intent['id']}")
        
        metadata = payment_intent.get("metadata", {})
        session_id = metadata.get("session_id")
        
        return {
            "success": True,
            "action": "payment_failed",
            "session_id": session_id,
            "payment_intent_id": payment_intent["id"],
            "failure_reason": payment_intent.get("last_payment_error", {}).get("message")
        }
    
    def _handle_checkout_completed(self, session: Dict) -> Dict:
        """Handle completed checkout session"""
        logger.info(f"Checkout completed: {session['id']}")
        
        return {
            "success": True,
            "action": "checkout_completed",
            "session_id": session["id"],
            "payment_intent_id": session.get("payment_intent"),
            "customer_email": session.get("customer_details", {}).get("email")
        }
    
    def refund_payment(self, payment_intent_id: str, amount: int = None, 
                      reason: str = None) -> Dict:
        """Refund a payment"""
        try:
            refund_data = {"payment_intent": payment_intent_id}
            
            if amount:
                refund_data["amount"] = amount
            if reason:
                refund_data["reason"] = reason
            
            refund = stripe.Refund.create(**refund_data)
            
            logger.info(f"Created refund: {refund.id} for payment {payment_intent_id}")
            
            return {
                "success": True,
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Refund failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    # === SUBSCRIPTION WEBHOOK HANDLERS ===
    
    def _handle_subscription_created(self, subscription: Dict) -> Dict:
        """Handle new subscription creation"""
        logger.info(f"Subscription created: {subscription['id']}")
        
        return {
            "success": True,
            "action": "subscription_created",
            "subscription_id": subscription["id"],
            "customer_id": subscription["customer"],
            "status": subscription["status"],
            "current_period_start": subscription["current_period_start"],
            "current_period_end": subscription["current_period_end"],
            "trial_end": subscription.get("trial_end"),
            "metadata": subscription.get("metadata", {})
        }
    
    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription updates (plan changes, etc.)"""
        logger.info(f"Subscription updated: {subscription['id']}")
        
        return {
            "success": True,
            "action": "subscription_updated",
            "subscription_id": subscription["id"],
            "customer_id": subscription["customer"],
            "status": subscription["status"],
            "current_period_start": subscription["current_period_start"],
            "current_period_end": subscription["current_period_end"],
            "cancel_at_period_end": subscription["cancel_at_period_end"],
            "metadata": subscription.get("metadata", {})
        }
    
    def _handle_subscription_cancelled(self, subscription: Dict) -> Dict:
        """Handle subscription cancellation"""
        logger.info(f"Subscription cancelled: {subscription['id']}")
        
        return {
            "success": True,
            "action": "subscription_cancelled",
            "subscription_id": subscription["id"],
            "customer_id": subscription["customer"],
            "status": subscription["status"],
            "ended_at": subscription.get("ended_at"),
            "cancellation_reason": subscription.get("cancellation_details", {}).get("reason"),
            "metadata": subscription.get("metadata", {})
        }
    
    def _handle_invoice_payment_succeeded(self, invoice: Dict) -> Dict:
        """Handle successful subscription payment"""
        logger.info(f"Invoice payment succeeded: {invoice['id']}")
        
        return {
            "success": True,
            "action": "subscription_payment_succeeded",
            "invoice_id": invoice["id"],
            "subscription_id": invoice.get("subscription"),
            "customer_id": invoice["customer"],
            "amount_paid": Decimal(invoice["amount_paid"]) / 100,
            "currency": invoice["currency"],
            "period_start": invoice["period_start"],
            "period_end": invoice["period_end"],
            "billing_reason": invoice.get("billing_reason")
        }
    
    def _handle_invoice_payment_failed(self, invoice: Dict) -> Dict:
        """Handle failed subscription payment"""
        logger.warning(f"Invoice payment failed: {invoice['id']}")
        
        return {
            "success": True,
            "action": "subscription_payment_failed",
            "invoice_id": invoice["id"],
            "subscription_id": invoice.get("subscription"),
            "customer_id": invoice["customer"],
            "amount_due": Decimal(invoice["amount_due"]) / 100,
            "currency": invoice["currency"],
            "attempt_count": invoice.get("attempt_count", 0),
            "next_payment_attempt": invoice.get("next_payment_attempt")
        }
    
    def _handle_invoice_created(self, invoice: Dict) -> Dict:
        """Handle invoice creation (before payment attempt)"""
        logger.info(f"Invoice created: {invoice['id']}")
        
        return {
            "success": True,
            "action": "invoice_created",
            "invoice_id": invoice["id"],
            "subscription_id": invoice.get("subscription"),
            "customer_id": invoice["customer"],
            "amount_due": Decimal(invoice["amount_due"]) / 100,
            "currency": invoice["currency"],
            "due_date": invoice.get("due_date")
        }
    
    def _handle_invoice_finalized(self, invoice: Dict) -> Dict:
        """Handle invoice finalization (ready for payment)"""
        logger.info(f"Invoice finalized: {invoice['id']}")
        
        return {
            "success": True,
            "action": "invoice_finalized",
            "invoice_id": invoice["id"],
            "subscription_id": invoice.get("subscription"),
            "customer_id": invoice["customer"],
            "amount_due": Decimal(invoice["amount_due"]) / 100,
            "currency": invoice["currency"]
        }
    
    def _handle_customer_created(self, customer: Dict) -> Dict:
        """Handle customer creation"""
        logger.info(f"Customer created: {customer['id']}")
        
        return {
            "success": True,
            "action": "customer_created",
            "customer_id": customer["id"],
            "email": customer.get("email"),
            "name": customer.get("name"),
            "metadata": customer.get("metadata", {})
        }
    
    def _handle_customer_updated(self, customer: Dict) -> Dict:
        """Handle customer updates"""
        logger.info(f"Customer updated: {customer['id']}")
        
        return {
            "success": True,
            "action": "customer_updated",
            "customer_id": customer["id"],
            "email": customer.get("email"),
            "name": customer.get("name"),
            "metadata": customer.get("metadata", {})
        }
    
    def _handle_customer_deleted(self, customer: Dict) -> Dict:
        """Handle customer deletion"""
        logger.info(f"Customer deleted: {customer['id']}")
        
        return {
            "success": True,
            "action": "customer_deleted",
            "customer_id": customer["id"]
        }
    
    def _handle_payment_method_attached(self, payment_method: Dict) -> Dict:
        """Handle payment method attachment to customer"""
        logger.info(f"Payment method attached: {payment_method['id']}")
        
        return {
            "success": True,
            "action": "payment_method_attached",
            "payment_method_id": payment_method["id"],
            "customer_id": payment_method.get("customer"),
            "type": payment_method["type"]
        }
    
    def _handle_payment_method_detached(self, payment_method: Dict) -> Dict:
        """Handle payment method detachment from customer"""
        logger.info(f"Payment method detached: {payment_method['id']}")
        
        return {
            "success": True,
            "action": "payment_method_detached",
            "payment_method_id": payment_method["id"],
            "type": payment_method["type"]
        }
    
    def _handle_trial_will_end(self, subscription: Dict) -> Dict:
        """Handle trial ending soon notification"""
        logger.info(f"Trial will end for subscription: {subscription['id']}")
        
        return {
            "success": True,
            "action": "trial_will_end",
            "subscription_id": subscription["id"],
            "customer_id": subscription["customer"],
            "trial_end": subscription.get("trial_end")
        }
    
    def _handle_upcoming_invoice(self, invoice: Dict) -> Dict:
        """Handle upcoming invoice notification"""
        logger.info(f"Upcoming invoice: {invoice['id']}")
        
        return {
            "success": True,
            "action": "upcoming_invoice",
            "invoice_id": invoice["id"],
            "subscription_id": invoice.get("subscription"),
            "customer_id": invoice["customer"],
            "amount_due": Decimal(invoice["amount_due"]) / 100,
            "currency": invoice["currency"],
            "period_start": invoice["period_start"],
            "period_end": invoice["period_end"]
        }

# Global instance
stripe_service = StripeService()
