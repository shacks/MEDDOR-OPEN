import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import datetime
import base64
from openai import OpenAI
import json

# Initialize connections
conn = st.connection("supabase", type=SupabaseConnection)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def process_image_with_openai(image_base64):
    try:
        receipt_schema = {
            "name": "ReceiptSchema",
            "description": "Defines the structure of a receipt",
            "schema": {
                "type": "object",
                "properties": {
                    "total_amount": {
                        "type": "number",
                        "description": "The total amount from the receipt"
                    },
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "The date on the receipt in YYYY-MM-DD format"
                    },
                    "vendor_name": {
                        "type": "string",
                        "description": "The name of the store or vendor"
                    },
                    "items_list": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of items purchased"
                    }
                },
                "required": ["total_amount", "date", "vendor_name", "items_list"]
            }
        }

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a receipt analysis assistant. Extract the required information and respond in the specified JSON format."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this receipt and extract the key information."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_schema", "json_schema": receipt_schema},
            max_tokens=500
        )
        parsed_response = json.loads(response.choices[0].message.content)
        # Store raw response in function output
        return parsed_response, response.choices[0].message.content
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None, None

def show():
    st.title("📸 Bill Upload via Camera")
    
    # Camera input
    camera_image = st.camera_input("Take a picture of the bill")
    
    if camera_image:
        # Display the captured image
        st.image(camera_image)
        
        # Convert image to base64
        bytes_data = camera_image.getvalue()
        base64_image = base64.b64encode(bytes_data).decode()
        
        # Process image with OpenAI
        with st.spinner("Processing image..."):
            extracted_data, raw_response = process_image_with_openai(base64_image)
        
        if extracted_data:
            st.success("Bill processed successfully!")
            
            # Add debug expander
            with st.expander("🔍 Debug: View AI Response"):
                st.code(raw_response, language="json")
            
            # Create form for verification/editing
            with st.form("transaction_form"):
                description = st.text_input("Description", 
                                         value=extracted_data.get('vendor_name', ''))
                amount = st.number_input("Amount", 
                                       value=float(extracted_data.get('total_amount', 0)))
                date_str = extracted_data.get('date', datetime.now().strftime('%Y-%m-%d'))
                date_of_transaction = st.date_input("Date", 
                                                  value=datetime.strptime(date_str, '%Y-%m-%d'))
                
                # Account options
                account_options = ["", "TD", "Simplii", "BRIM", "WealthSimple", 
                                 "Tangerine", "American"]
                col1, col2 = st.columns(2)
                with col1:
                    account_origin = st.selectbox("Account Origin", account_options)
                with col2:
                    account_destination = st.selectbox("Account Destination", 
                                                     account_options)
                
                # Transaction type
                trans_type = st.selectbox("Transaction Type", ["expense", "income"])
                
                # Tags
                tags_data = conn.table("tags").select("*").execute()
                existing_tags = [tag["name"] for tag in tags_data.data] if tags_data.data else []
                selected_tags = st.multiselect("Tags", existing_tags)
                
                # Items list display
                if 'items_list' in extracted_data:
                    st.write("Items detected:", extracted_data['items_list'])
                
                submitted = st.form_submit_button("Save Transaction")
                
                if submitted:
                    try:
                        # Save image
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        file_path = f"med_reciepts/receipt_{timestamp}.jpg"
                        conn.upload("files", "local", camera_image, file_path, "false")
                        
                        # Save transaction
                        transaction_data = {
                            "description": description,
                            "amount": amount,
                            "account_origin": account_origin,
                            "account_destination": account_destination,
                            "date": str(date_of_transaction),
                            "type": trans_type,
                            "tags": selected_tags,
                            "file_path": file_path
                        }
                        
                        response = conn.table("med_transactions").insert(transaction_data).execute()
                        
                        if response.data:
                            st.success("Transaction saved successfully!")
                            
                    except Exception as e:
                        st.error(f"Error saving transaction: {str(e)}")

if __name__ == "__main__":
    show()
