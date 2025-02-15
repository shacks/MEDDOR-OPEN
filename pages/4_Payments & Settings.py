import streamlit as st
from st_supabase_connection import SupabaseConnection
from components.available_credits import display_credits
from components.purchase_credits import purchase_credits_section

if not st.experimental_user.is_logged_in:
    st.warning("⚠️ Please log in to access Settings. Return to the main page to sign in.")
    st.page_link("Scribe.py", label="🏠 Return to Homepage", use_container_width=True)
else:
    # Initialize Supabase connection
    conn = st.connection("supabase", type=SupabaseConnection)


    st.title("Settings")

    # Get user email from experimental_user
    user_data = st.experimental_user
    user_email = st.experimental_user.email if st.experimental_user else None

    def get_user_prompt():
        if user_email:
            response = conn.table("prompts").select("*").eq("email", user_email).execute()
            return response.data[0] if response.data else None
        return None

    # Display AI Credits using the new component
    if user_email:
        #display_credits(user_email)
        purchase_credits_section()
    
    def save_or_update_prompt(prompt_text):
        if not user_email:
            st.error("User email is required")
            return False
            
        data = {
            "prompt": prompt_text,
            "email": user_email  # Using 'email' to match DB column name
        }
        
        try:
            existing_prompt = get_user_prompt()
            if existing_prompt:
                conn.table("prompts").update(data).eq("email", user_email).execute()
            else:
                conn.table("prompts").insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return False


    if user_email:
        tab1, tab2 = st.tabs(["Custom Prompt", "Prompt Guide"])
        
        with tab1:
            try:
                existing_prompt = get_user_prompt()
                
                new_prompt = st.text_area(
                    "Your custom prompt",
                    value=existing_prompt["prompt"] if existing_prompt else "",
                    help="You can only save one custom prompt. Saving a new one will replace the existing one.",
                    height=350
                )
                
                if st.button("Save Prompt"):
                    if new_prompt:
                        save_or_update_prompt(new_prompt)
                        st.success("Prompt saved successfully!")
                        st.rerun()
                    
            except Exception as e:
                st.error(f"Error managing prompt: {str(e)}")
        
        with tab2:
            st.subheader("🎯 The Power of Your Prompt")
            st.markdown("""
            ### Why Your Prompt Matters
            
            The success of MedDor Notes in your practice largely depends on how well your prompt is crafted. 
            Think of it as training your personal medical assistant - the better your instructions, the better the results.

            While we provide a default prompt that works well for general use, **customizing it to your specific needs can dramatically improve the quality of your summaries**. 
            
            Many users report a 70-80% improvement in summary quality after fine-tuning their prompts to match their:
            - Specialty requirements
            - Preferred note format
            - Common scenarios
            - Documentation style
            """)

            st.subheader("The Art of Prompt Engineering")
            with st.expander("Learn how to write effective prompts"):
                st.markdown("""
                ### Tips for Writing Effective Prompts

                1. **Be Specific**
                - Clearly define the expected format
                - Specify what should and shouldn't be included
                - Use explicit instructions for section organization

                2. **Set Clear Rules**
                - Define how to handle duplicate information
                - Specify where specific types of data should appear
                - State any medical formatting requirements

                3. **Common Improvements**
                - Add instructions for handling abbreviations
                - Specify preferred units for lab results
                - Define how to handle uncertain or unclear information
                - Add rules for prioritizing critical information

                4. **Testing Your Prompt**
                - Start with a small test note
                - Check if all sections are properly organized
                - Verify that information isn't duplicated
                - Ensure critical details aren't omitted
                """)

            st.subheader("Example Templates")
            example_tab1, example_tab2 = st.tabs(["English Template", "French Template"])
            
            with example_tab1:
                st.markdown("""
                ```
                Given medical notes or transcription, produce a concise summary in standard medical format:
                - No duplication of information between sections.
                - All lab results must only appear in the "Labs" section.
                - All future actions/items (e.g., planned tests, referrals, follow-ups) must be included in the "Action Plan" section.
                
                **Sections:**
                - **CC**: Reason for visit/consultation (should be a short title, not a complete sentence; details will be provided in other sections).
                - **HPI**: Patient complaints, history, context (subsections for relevant systems only).
                - **Treatments Tried**: List.
                - **Physical Exam**: List.
                - **Labs**: All laboratory results (list).
                - **Imaging**: List.
                - **Diagnosis/Impression**: List.
                - **Action Plan**: List (includes all future actions/items).
                ```
                """)
                
            with example_tab2:
                st.markdown("""
                ```
                À partir des notes médicales ou de la transcription, produire un résumé concis au format médical standard:
                - Pas de duplication d'informations entre les sections.
                - Tous les résultats de laboratoire doivent apparaître uniquement dans la section "Laboratoires".
                - Toutes les actions/éléments futurs (tests prévus, références, suivis) doivent être inclus dans la section "Plan d'action".
                
                **Sections:**
                - **Raison**: Motif de la visite/consultation (doit être un titre court, pas une phrase complète).
                - **Histoire**: Plaintes du patient, antécédents, contexte (sous-sections pour les systèmes pertinents uniquement).
                - **Traitements Essayés**: Liste.
                - **Examen Physique**: Liste.
                - **Laboratoires**: Tous les résultats de laboratoire (liste).
                - **Imagerie**: Liste.
                - **Diagnostic/Impression**: Liste.
                - **Plan d'Action**: Liste (inclut toutes les actions/éléments futurs).
                ```
                """)

    else:
        st.warning("Please log in to manage your custom prompt")


