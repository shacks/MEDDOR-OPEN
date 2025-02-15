import streamlit as st
from st_supabase_connection import SupabaseConnection, execute_query
from typing import Tuple, Optional

def get_user_credits(user_email):
    """Get user credits from the prompts table"""
    if not user_email:
        return None
        
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
        query = conn.table("prompts").select("credit").eq("email", user_email)
        response = execute_query(query, ttl=0)
        return response.data[0]["credit"] if response.data else None
    except Exception as e:
        st.error(f"Error fetching credits: {str(e)}")
        return None

def display_credits(user_email):
    """Display user credits with proper formatting"""
    credits = get_user_credits(user_email)
    
    if credits is not None:
        st.info(f"🎯 Available AI Credits: {credits}")
    else:
        st.warning("No credit information available")

def deduct_credit(user_email: str, amount: int = 1) -> Tuple[bool, str]:
    """Deduct credits from user's account
    Returns:
        tuple: (bool, str) - (success, message)
    """
    if not user_email:
        return False, "No user email provided"
        
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
        
        # Get current credits
        current_credits = get_user_credits(user_email)
              
        if current_credits is None:
            return False, "No credit information found"
            
        if current_credits < amount:
            return False, f"Insufficient credits: {current_credits} available, {amount} needed"
            
        # Update credits in database
        new_credits = current_credits - amount
        result = conn.table("prompts").update({"credit": new_credits}).eq("email", user_email).execute()
        
        # Check if the update affected any rows
        if not result.data:
            return False, f"No rows updated for email: {user_email}"
            
        # Verify the new credit value
        updated_credits = get_user_credits(user_email)
        if updated_credits != new_credits:
            return False, f"Credit update failed: expected {new_credits}, got {updated_credits}"
            
        return True, f"Credits deducted successfully. Remaining: {new_credits}"
        
    except Exception as e:
        error_msg = f"Error in deduct_credit: {str(e)}"
        st.error(error_msg)
        print(error_msg)  # For server-side logging
        return False, error_msg

def add_credits(user_email, amount=300):
    """Add credits to user's account
    Returns:
        tuple: (bool, str) - (success, message)
    """
    if not user_email:
        return False, "No user email provided"
        
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
        
        # Get current credits
        current_credits = get_user_credits(user_email)
        if current_credits is None:
            return False, "No credit information found"
            
        # Update credits in database
        new_credits = current_credits + amount
        result = conn.table("prompts").update({"credit": new_credits}).eq("email", user_email).execute()
        
        # Check if the update affected any rows
        if hasattr(result, 'count') and result.count == 0:
            return False, f"No rows updated for email: {user_email}"
            
        return True, f"Credits added successfully. New balance: {new_credits}"
        
    except Exception as e:
        error_msg = f"Error in add_credits: {str(e)}"
        st.error(error_msg)
        print(error_msg)  # For server-side logging
        return False, error_msg
