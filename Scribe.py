import streamlit as st
from st_supabase_connection import SupabaseConnection
from components.available_credits import display_credits

# Initialize Supabase connection
conn = st.connection("supabase", type=SupabaseConnection)

def initialize_user_prompt(user_email):
    try:
        # Check if user has a prompt
        response = conn.table("prompts").select("*").eq("email", user_email).execute()
        
        # If no prompt exists, create default one
        if not response.data:
            default_prompt = """Given medical notes or transcription, produce a concise summary in standard medical format:
- No duplication of information between sections.
- All lab results must only appear in the "Labs" section.
- All future actions/items must be included in the "Action Plan" section.

**Sections:**
- **CC**: Reason for visit/consultation
- **HPI**: Patient complaints, history, context
- **Treatments Tried**: List
- **Physical Exam**: List
- **Labs**: All laboratory results
- **Imaging**: List
- **Diagnosis/Impression**: List
- **Action Plan**: List"""
            
            data = {
                "prompt": default_prompt,
                "email": user_email
            }
            conn.table("prompts").insert(data).execute()
            
    except Exception as e:
        st.error(f"Error initializing user prompt: {str(e)}")

# Authentication check
user_info = st.experimental_user

if not user_info or not user_info.is_logged_in:
    st.title("🏥 MedDor Notes")
    st.markdown("""
    ### Created by Doctors, for Doctors
    
    MedDor Notes is a streamlined medical note-taking solution that helps you focus on what matters most - patient care.
    
    #### 🔒 Privacy & Security
    * HIPAA compliant processing
    * No data storage - everything stays on your device
    * Secure AI processing for medical documentation
    
    #### ✨ Core Features
    * Record patient consultations
    * Convert recordings to text with AI
    * Analyze and summarize medical notes
    * Only $4.99/month
    
    """)
    
    # Login section using single column
    google_button = st.button("Google Login")

    if google_button:
        st.login(provider="google")
    
else:
    # Initialize user prompt if logged in
    if user_info.email:
        initialize_user_prompt(user_info.email)
    
    # Add logout button in top right
    _, _, _, logout_col = st.columns([1, 1, 1, 0.5])
    with logout_col:
        if st.button("Logout"):
            st.logout()
            
    st.header("🏥 MedDor Notes", divider="grey")
    
    # Display credits
    if user_info.email:
        display_credits(user_info.email)

    st.markdown("""
    Welcome! Select one of our core features below to get started. Visit Settings to customize your experience.
    """)

    # Core Features
    st.subheader("Core Features")
    st.page_link("pages/1_Audio Recorder.py", label="🎙️ Audio Recorder", help="Record and save audio consultations locally")
    st.page_link("pages/2_Audio  Summarization.py", label="🎯 Audio Summary", help="Convert and summarixe audio recordings")
    st.page_link("pages/3_Notes Summarization.py", label="📝 Notes Summary", help="AI-powered medical notes Summary")

    # Auxiliary Features
    st.divider()
    st.subheader("Additional Options", divider=False)
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/4_Payments & Settings.py", label="⚙️ Payments & Settings", help="Customize your AI prompt - The key to perfect summaries")
    with col2:
        st.page_link("pages/5_Support & Feedback.py", label="❓ Support", help="Get help and learn tips & tricks")

    # Footer
    st.divider()
    st.caption("MedDor Notes - Simple, Secure, Efficient")
