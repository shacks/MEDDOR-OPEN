import streamlit as st

DEFAULT_PROMPT = """Étant donné des notes médicales ou une transcription, produisez un résumé concis dans un format médical standard :  
- Aucune duplication d'information entre les sections.  
- Tous les résultats de laboratoire doivent uniquement apparaître dans la section "Labs".  
- Toutes les actions ou éléments futurs (par exemple, tests prévus, références, suivis) doivent être inclus dans la section "Plan d'action".  
**Sections :**  
- **RC** : Raison de la visite/consultation (doit être un titre court, pas une phrase complète ; les détails seront fournis dans d'autres sections).  
- **HMA** : Plaintes du patient, antécédents, contexte (sous-sections pour les systèmes pertinents uniquement).  
- **Traitements essayés** : Liste.  
- **Examen physique** : Liste.  
- **Labs** : Tous les résultats de laboratoire (liste).  
- **Imagerie** : Liste.  
- **Diagnostic/Impression** : Liste.  
- **Plan d'action** : Liste (inclut toutes les actions ou éléments futurs)."""

def get_user_prompt_text(conn):
    """
    Get the user's custom prompt or return default if none exists
    Args:
        conn: Supabase connection instance
    Returns:
        str: The prompt text
    """
    user_email = st.experimental_user.email if st.experimental_user else None
    
    if not user_email:
        return DEFAULT_PROMPT
    
    try:
        response = conn.table("prompts").select("*").eq("email", user_email).execute()
        if response.data and response.data[0].get("prompt"):
            return response.data[0]["prompt"]
        return DEFAULT_PROMPT
    except Exception as e:
        st.error(f"Error fetching prompt: {str(e)}")
        return DEFAULT_PROMPT
