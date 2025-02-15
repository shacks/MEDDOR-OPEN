import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import datetime
import logging
import PyPDF2
from components.generate_summary import parse_bank_statement_with_ai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase connection
conn = st.connection("supabase", type=SupabaseConnection)

def extract_amount_with_type(debit_col, credit_col):
    """Determine the amount as debit (-) or credit (+)"""
    if debit_col and debit_col.strip():
        try:
            return -abs(float(debit_col.replace(',', '').replace('$', '').strip()))
        except ValueError:
            return None
    elif credit_col and credit_col.strip():
        try:
            return abs(float(credit_col.replace(',', '').replace('$', '').strip()))
        except ValueError:
            return None
    return None

def parse_date(date_text):
    """Parse date from text using specific formats"""
    if not date_text or not isinstance(date_text, str):
        return None
        
    for date_format in ['%b%d', '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d']:
        try:
            date = datetime.strptime(date_text.strip(), date_format).date()
            # If only month and day, add current year
            if date_format == '%b%d':
                date = date.replace(year=datetime.now().year)
            return date
        except ValueError:
            continue
    return None

def extract_pdf_text(pdf_file):
    """Extract text content from PDF file"""
    try:
        # Ensure we're at the start of the file
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = []
        for page in pdf_reader.pages:
            text.append(page.extract_text())
        
        combined_text = "\n".join(text)
        if not combined_text.strip():
            st.warning("No text could be extracted from the PDF. The file might be scanned or image-based.")
            return None
        return combined_text
    except Exception as e:
        st.error(f"Error extracting PDF text: {str(e)}")
        logger.error(f"PDF extraction error: {str(e)}")
        return None

def get_available_categories():
    """Fetch available categories from database"""
    categories_data = conn.table("category").select("*").or_("category.eq.bank,category.eq.common").execute()
    return [cat["name"] for cat in categories_data.data] if categories_data.data else []

def delete_statement(statement_id):
    """Delete a statement by ID"""
    try:
        conn.table("bank_statements").delete().eq("id", statement_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error deleting statement: {str(e)}")
        return False

def convert_date(date_value):
    """Convert various date formats to string"""
    if isinstance(date_value, (datetime, date)):
        return date_value.strftime('%Y-%m-%d')
    elif isinstance(date_value, str):
        return date_value
    elif pd.isna(date_value):
        return None
    return str(date_value)

def calculate_amount(row):
    """Calculate amount from debit and credit fields"""
    if pd.notna(row['debit']):
        return -float(row['debit'])
    elif pd.notna(row['credit']):
        return float(row['credit'])
    return 0.0

def show():
    try:
        st.title("Bank Statements Uploader")
        
        # Initialize session state for transactions
        if 'current_transactions' not in st.session_state:
            st.session_state.current_transactions = None
            
        tab1, tab2, tab3 = st.tabs(["Upload Statements", "Review & Categorize", "Edit Data"])
        
        with tab1:
            # Account selection
            account_options = ["", "B- TD CORP", "B- TD Personal", "C- AMEX GOLD"]
            st.selectbox("Select Account", account_options, key='current_account')
            
            # File uploader
            uploaded_pdfs = st.file_uploader("Upload PDF Statements", 
                                           type=["pdf"], 
                                           accept_multiple_files=True)
            
            process_button = st.button("Process Statements")
            
            if uploaded_pdfs and process_button:
                all_transactions = []
                progress_bar = st.progress(0)
                
                for index, pdf_file in enumerate(uploaded_pdfs):
                    progress = (index + 1) / len(uploaded_pdfs)
                    progress_bar.progress(progress)
                    
                    with st.expander(f"Processing {pdf_file.name}"):
                        st.info("Extracting text from PDF...")
                        pdf_text = extract_pdf_text(pdf_file)
                        
                        if pdf_text:
                            st.info("Text extracted successfully. Processing with AI...")
                            st.text_area("Extracted Text (Debug)", pdf_text, height=100)
                            
                            transactions, raw_response = parse_bank_statement_with_ai(
                                pdf_text, 
                                st.session_state.current_account
                            )
                            
                            if transactions:
                                st.success(f"Found {len(transactions)} transactions")
                                st.info("AI Response (Debug)")
                                st.code(raw_response, language="json")
                                
                                # Show extracted data
                                df = pd.DataFrame(transactions)
                                st.dataframe(df)
                                
                                # Add transactions to the list
                                all_transactions.extend(transactions)
                            else:
                                st.error("No transactions could be extracted from the PDF")
                        else:
                            st.error("Could not extract text from PDF")
                
                progress_bar.empty()
                
                # Store processed transactions in session state
                if all_transactions:
                    st.session_state.current_transactions = all_transactions
                    st.success(f"Total transactions processed: {len(all_transactions)}")
            
            # Save button outside the processing loop
            if st.session_state.current_transactions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"Ready to save {len(st.session_state.current_transactions)} transactions")
                with col2:
                    if st.button("Save All to Database"):
                        try:
                            with st.spinner("Saving transactions..."):
                                successful = 0
                                for transaction in st.session_state.current_transactions:
                                    # Validate required fields
                                    if not transaction.get('transaction_date') or not transaction.get('description'):
                                        continue
                                        
                                    # Convert amount to debit/credit
                                    debit = None
                                    credit = None
                                    
                                    if transaction.get('debit'):
                                        debit = abs(float(transaction['debit']))
                                        credit = 0
                                    elif transaction.get('credit'):
                                        credit = abs(float(transaction['credit']))
                                        debit = 0
                                    else:
                                        # Skip transactions without amounts
                                        continue
                                    
                                    transaction_data = {
                                        "account_number": transaction.get("account_number"),
                                        "transaction_date": transaction.get("transaction_date"),
                                        "description": transaction.get("description"),
                                        "debit": debit,
                                        "credit": credit,
                                        "balance": transaction.get("balance", 0)
                                    }
                                    
                                    try:
                                        logger.info(f"Saving transaction: {transaction_data}")
                                        response = conn.table("bank_statements").insert(transaction_data).execute()
                                        
                                        # Check if the response contains data
                                        if response.data:
                                            successful += 1
                                        else:
                                            logger.error(f"Failed to save transaction: {transaction_data}")
                                            
                                    except Exception as e:
                                        logger.error(f"Error saving transaction: {str(e)}")
                                        st.error(f"Error saving transaction: {str(e)}")
                                        continue
                                
                                if successful > 0:
                                    st.success(f"Successfully saved {successful} transactions!")
                                    # Clear the session state after successful save
                                    st.session_state.current_transactions = None
                                    # Rerun to refresh the page
                                    st.rerun()
                                else:
                                    st.error("No transactions were saved successfully")
                                
                        except Exception as e:
                            st.error(f"Error during save process: {str(e)}")
                            logger.error(f"Save process error: {str(e)}")

        with tab2:
            response = conn.table("bank_statements").select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                available_categories = get_available_categories()
                
                # Add filters in one row
                col1, col2, col3 = st.columns(3)
                with col1:
                    start_date = st.date_input("Start Date", df['transaction_date'].min())
                with col2:
                    end_date = st.date_input("End Date", df['transaction_date'].max())
                with col3:
                    category_filter = st.radio(
                        "Category Filter",
                        ["All", "Uncategorized", "Categorized"],
                        horizontal=True
                    )
                
                # Filter data
                mask = (pd.to_datetime(df['transaction_date']) >= pd.to_datetime(start_date)) & \
                       (pd.to_datetime(df['transaction_date']) <= pd.to_datetime(end_date))
                
                if category_filter == "Uncategorized":
                    mask = mask & (df['category'].isna() | (df['category'] == ''))
                elif category_filter == "Categorized":
                    mask = mask & (df['category'].notna() & (df['category'] != ''))
                
                filtered_df = df[mask]

                # Custom CSS for compact layout
                st.markdown("""
                    <style>
                        div[data-testid="column"] {padding: 0px !important;}
                        div[data-testid="stHorizontalBlock"] {gap: 0.5rem !important;}
                        div[data-testid="stSelectbox"] {min-height: 0px !important;}
                    </style>
                """, unsafe_allow_html=True)

                # Display transactions in compact format
                for idx, row in filtered_df.iterrows():
                    st.container().markdown("""
                        <div style="border: 1px solid #eee; padding: 5px; margin-bottom: 5px;">
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # First row: Date, Description, Credit/Debit/Balance
                    col1, col2, col3, col4, col5 = st.columns([2, 6, 2, 2, 2])
                    with col1:
                        st.write(f"{row['transaction_date']}")
                    with col2:
                        st.write(f"{row['description'][:50]}")
                    with col3:
                        if pd.notna(row['debit']):
                            st.write(f"${abs(float(row['debit'])):,.2f} DR")
                        else:
                            st.write("")
                    with col4:
                        if pd.notna(row['credit']):
                            st.write(f"${abs(float(row['credit'])):,.2f} CR")
                        else:
                            st.write("")
                    with col5:
                        if pd.notna(row['balance']):
                            st.write(f"${float(row['balance']):,.2f}")
                        else:
                            st.write("")
                    
                    # Second row: Category dropdown and Delete button
                    col1, col2 = st.columns([11, 1])
                    with col1:
                        current_category = row.get('category', '')
                        categories_with_empty = [""] + available_categories
                        try:
                            selected_index = categories_with_empty.index(current_category)
                        except ValueError:
                            selected_index = 0
                            
                        selected_category = st.selectbox(
                            "Category",  # Added label back
                            categories_with_empty,
                            index=selected_index,
                            key=f"category_{row['id']}"
                        )
                        if selected_category != current_category:
                            conn.table("bank_statements").update(
                                {"category": selected_category if selected_category else None}
                            ).eq("id", row['id']).execute()
                    
                    with col2:
                        if st.button("🗑️", key=f"del_{row['id']}", help="Delete"):
                            if delete_statement(row['id']):
                                st.success("Deleted!")
                                st.rerun()

                # Summary metrics at the bottom
                st.divider()
                total_debit = filtered_df['debit'].sum() or 0
                total_credit = filtered_df['credit'].sum() or 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Debits", f"${abs(total_debit):,.2f}")
                with col2:
                    st.metric("Total Credits", f"${total_credit:,.2f}")
                with col3:
                    st.metric("Net", f"${(total_credit - total_debit):,.2f}")

        with tab3:
            # Editable data table view
            st.title("Edit Transactions")
            response = conn.table("bank_statements").select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                
                # Calculate amount for display
                df['amount'] = df.apply(calculate_amount, axis=1)
                
                # Convert date columns to datetime
                date_columns = ['transaction_date', 'statement_date', 'posting_date']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col]).dt.date
                
                # Convert to editable format
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "description": st.column_config.TextColumn("Description"),
                        "debit": st.column_config.NumberColumn("Debit", format="$%.2f"),
                        "credit": st.column_config.NumberColumn("Credit", format="$%.2f"),
                        "balance": st.column_config.NumberColumn("Balance", format="$%.2f"),
                        "category": st.column_config.SelectboxColumn(
                            "Category",
                            options=[""] + get_available_categories()
                        ),
                        "transaction_date": st.column_config.DateColumn("Transaction Date"),
                    },
                    hide_index=True,
                )
                
                if st.button("Save Changes"):
                    for _, row in edited_df.iterrows():
                        # Convert dates to string format for database
                        update_data = {
                            "description": row["description"],
                            "amount": float(row["amount"]),
                            "category": row["category"] if row["category"] else None,
                            "transaction_date": convert_date(row["transaction_date"]),
                            "statement_date": convert_date(row["statement_date"]),
                            "posting_date": convert_date(row["posting_date"]),
                        }
                        conn.table("bank_statements").update(update_data).eq("id", row["id"]).execute()
                    st.success("Changes saved successfully!")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    show()
