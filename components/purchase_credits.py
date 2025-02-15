import streamlit as st
import stripe
from components.available_credits import add_credits, get_user_credits

# Initialize Stripe with the API key from Streamlit secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def create_checkout_session(user_email):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cad',
                    'product_data': {
                        'name': '300 AI Credits',
                        'description': 'Credits for AI analysis and responses',
                    },
                    'unit_amount': 499,  # Amount in cents (4.99 CAD)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=st.secrets["BASE_URL"] + "/Payments_%26_Settings?success=true",
            cancel_url=st.secrets["BASE_URL"] + "/Payments_%26_Settings?canceled=true",
            customer_email=user_email,
            metadata={'user_email': user_email}
        )
        return checkout_session
    except Exception as e:
        st.error(f"Error creating checkout session: {str(e)}")
        return None

def purchase_credits_section():
    """Display the purchase credits section"""
    user_info = st.experimental_user
    
    if user_info and user_info.is_logged_in:
        user_email = user_info.email
        current_credits = get_user_credits(user_email)
        
        st.write("### Purchase Credits")
        st.write(f"Current Balance: {current_credits} credits")
        st.write("Purchase 300 AI Credits for $4.99 CAD")
        
        if st.button("Purchase Credits", key="purchase_button"):
            checkout_session = create_checkout_session(user_email)
            if checkout_session:
                st.markdown(f'<a href="{checkout_session.url}" target="_blank">Click here to make payment</a>', unsafe_allow_html=True)
        
        # Initialize session state for tracking credit addition
        if 'credits_added' not in st.session_state:
            st.session_state.credits_added = False
        
        # Handle successful payment
        if st.query_params.get("success") == "true" and not st.session_state.credits_added:
            success, message = add_credits(user_email, 300)
            if success:
                st.success("Payment successful! 300 credits have been added to your account.")
                st.balloons()
                # Mark credits as added in session state
                st.session_state.credits_added = True
                # Clear the success parameter by creating new query params without 'success'
                st.query_params.clear()
                
            else:
                st.error(f"Error adding credits: {message}")
    else:
        st.warning("Please login to purchase credits")
