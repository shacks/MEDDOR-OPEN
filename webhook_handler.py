import stripe
import streamlit as st
from components.available_credits import add_credits

def handle_successful_payment(event):
    """Handle successful payment webhook event"""
    session = event.data.object
    user_email = session.metadata.get('user_email')
    
    if user_email:
        success, message = add_credits(user_email, 300)
        if not success:
            # Log the error for admin review
            print(f"Failed to add credits for {user_email}: {message}")
            return False
        return True
    return False

def verify_webhook_signature(payload, sig_header, webhook_secret):
    """Verify that the webhook came from Stripe"""
    try:
        stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return True
    except Exception as e:
        print(f"Webhook signature verification failed: {str(e)}")
        return False
