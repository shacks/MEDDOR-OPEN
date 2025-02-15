import streamlit as st
from openai import OpenAI
from st_supabase_connection import SupabaseConnection
import anthropic
import json
import time
from .get_prompt import get_user_prompt_text
from .available_credits import deduct_credit

clientGPT = OpenAI(
   api_key = st.secrets["OPENAI_API_KEY"],
)
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=st.secrets["Claude_API_KEY"],
)
conn = st.connection("supabase",type=SupabaseConnection)

def generate_summary(input_text, model, tag):
    # Check and deduct credits first
    success, message = deduct_credit(st.experimental_user.email)
    if not success:
        raise Exception(f"Credit deduction failed: {message}")

    retries = 5
    for i in range(retries):
        try:
            user_prompt = get_user_prompt_text(conn)
            completion = clientGPT.chat.completions.create(
                model= model,
                store = True,
                metadata = {"category": tag},
                top_p =0.2,
                messages = [
                {"role": "system",
                "content": "You are a helpful assistant trained to summarize medical notes in french and english. You will be given a raw medical note or conversation transcript. Clear point form and no sentence. Use Medical abreveations."},
                {
                    "role": "user",
                    "content": f"""{user_prompt}

                    Résumez le texte suivant :  

                    {input_text}
                    """
                }
            ],
                max_tokens=1024
            )
            ai_output_text = completion.choices[0].message.content.strip()
            input_tokens = completion.usage.prompt_tokens 
            output_tokens = completion.usage.completion_tokens
            data = {
                "input_text": input_text,
                "ai_output_text": ai_output_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "tag": tag
                }
                
            response = conn.table("aiusage").insert(data).execute() 
            return ai_output_text, input_tokens, output_tokens
        except anthropic.InternalServerError as e:
            if i < retries - 1 and 'overloaded_error' in str(e):
                time.sleep(2 ** i)  # Exponential backoff
                continue
            else:
                raise e
        except Exception as e:
            raise e
    
def generate_summary_claude(input_text,model, tag):
    # Check and deduct credits first
    success, message = deduct_credit(st.experimental_user.email)
    if not success:
        raise Exception(f"Credit deduction failed: {message}")

    retries = 5
    for i in range(retries):
        try:
            user_prompt = get_user_prompt_text(conn)
            response = client.messages.create(
                model= model,
                max_tokens=1024,
                system="You are a helpful assistant trained to summarize medical notes or trascription between patent and doctor in french and english. You will be given a raw medical note or conversation transcript. Use Medical abreveations.",
                messages=[
                    {"role": "user", "content": f"""{user_prompt}

                    Résumez le texte suivant :

                    {input_text}
                    """}
                ]
            )
            ai_output_text = "".join(block.text for block in response.content)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            data = {
                "input_text": input_text,
                "ai_output_text": ai_output_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "tag": tag
                }
            response = conn.table("aiusage").insert(data).execute() 
            return ai_output_text, input_tokens, output_tokens
        except anthropic.InternalServerError as e:
            if i < retries - 1 and 'overloaded_error' in str(e):
                time.sleep(2 ** i)  # Exponential backoff
                continue
            else:
                raise e
        except Exception as e:
            raise e




