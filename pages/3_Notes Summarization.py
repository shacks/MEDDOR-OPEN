import streamlit as st
from st_supabase_connection import SupabaseConnection
from components.generate_summary import generate_summary, generate_summary_claude
import datetime
from st_copy_to_clipboard import st_copy_to_clipboard
import time

if not st.experimental_user.is_logged_in:
    st.warning("⚠️ Please log in to access Notes Summarization. Return to the main page to sign in.")
    st.page_link("Scribe.py", label="🏠 Return to Homepage", use_container_width=True)
else:
    # Create a supabase client
    conn = st.connection("supabase",type=SupabaseConnection)

    MODELS = {
    "claude-3-5-sonnet-latest": "claude-3-5-sonnet-latest",
    "gpt-4o-mini": "gpt-4o-mini",

    }

    st.header("Notes Summarization", divider="grey")
    model = st.selectbox(
            "🤖 Model",
            options=list(MODELS.keys()),

        )

    # 1. Collect inputs
    input_text = st.text_area("Input Text", help="Put your rough notes here", height=350)

    # 2. Initialize session_state variables (only once)
    if "ai_output_text" not in st.session_state:
        st.session_state.ai_output_text = ""


    # 3. Button to create summary (only updates session_state)
    if st.button("Create Summary"):
        st.session_state["start_time"] = time.time()
        if model in ["chatgpt-4o-latest", "gpt-4o-mini", "o1-mini"]:
            ai_output_text, input_tokens, output_tokens = generate_summary(input_text, model, "Handwritten")    
        elif model in ["claude-3-5-sonnet-latest","claude-3-5-haiku-latest"]:
            ai_output_text, input_tokens, output_tokens = generate_summary_claude(input_text,model,"Handwritten")


        # Store the results in session_state
        st.session_state.ai_output_text = ai_output_text
        st.session_state.input_tokens = input_tokens
        st.session_state.output_tokens = output_tokens
        

    # 4. Show the summary output and cost (if we have any)
    if st.session_state.ai_output_text:
        st.markdown("### AI-Generated Summary")
        st.markdown(st.session_state.ai_output_text)
        st_copy_to_clipboard(st.session_state.ai_output_text)

