import streamlit as st
from datetime import date
from st_supabase_connection import SupabaseConnection, execute_query
import pandas as pd
from datetime import datetime

# Initialize Supabase connection
conn = st.connection("supabase", type=SupabaseConnection)

def show():
    tab1, tab2, tab3 = st.tabs(["Add Transaction", "View Transactions", "Categories"])

    with tab1:
        page_create_transaction()
    with tab2:
        page_view_transactions()
    with tab3:
        page_view_categories()

def update_categories():
    """Update available categories based on selected account"""
    account_origin = st.session_state.account_origin
    categories_data = conn.table("category").select("*").execute()
    df_categories = pd.DataFrame(categories_data.data) if categories_data.data else pd.DataFrame(columns=["name", "category"])
    
    if account_origin.startswith("B"):
        category_types = ["bank", "common"]
    elif account_origin.startswith("C"):
        category_types = ["credit", "common"]
    else:
        category_types = []
        
    st.session_state.available_categories = df_categories[df_categories['category'].isin(category_types)]['name'].tolist()

def page_create_transaction():
    st.title("Add New Transaction")
    
    # Initialize session states
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = []
    if 'available_categories' not in st.session_state:
        st.session_state.available_categories = []
    
    # Account and Category Selection (Outside Form)
    account_options = [
        "", "B- DJ", "B- QT", "B- TD CORP", 
        "B- TD Personal", "B- WS", "B- TD Joint", 
        "C- AMEX GOLD", "C- BRIM", "C- DJ", 
        "C- TD"
    ]
    
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Account Origin", account_options, key="account_origin", on_change=update_categories)
    with col2:
        account_destination = st.selectbox("Account Destination", account_options)
    
    # Categories selection
    selected_categories = st.multiselect("Categories", st.session_state.available_categories)
    
    # Transaction Details Form
    with st.form("transaction_form"):
        description = st.text_area("Description")
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Amount", step=0.01)
        with col2:
            date_of_transaction = st.date_input("Date of Transaction")
        
        trans_type = st.selectbox("Transaction Type", ["Income", "Expense"])
        
        uploaded_file = st.file_uploader(
            "Upload an image/PDF", 
            type=["png", "jpg", "jpeg", "pdf"], 
            accept_multiple_files=False
        )
        
        submit = st.form_submit_button("Save Transaction")
        
        if submit and description:
            file_path = None
            if uploaded_file:
                original_filename = uploaded_file.name
                file_ext = original_filename.rsplit('.', 1)[1].lower()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"{original_filename.rsplit('.', 1)[0]}_{timestamp}.{file_ext}"
                file_path = f"med_reciepts/{new_filename}"
                response_uploaded_file = conn.upload("files", "local", uploaded_file, file_path, "false")
                print(response_uploaded_file)

            # Insert transaction
            transaction_data = {
                "description": description,
                "amount": amount,
                "account_origin": st.session_state.account_origin,
                "account_destination": account_destination,
                "date": str(date_of_transaction),
                "type": trans_type,
                "categories": selected_categories,
                "file_path": file_path
            }
            response = conn.table("med_transactions").insert(transaction_data).execute()

            if response.data:
                st.success("Transaction saved successfully!")

def page_view_transactions():
    """View and filter existing transactions."""
    st.title("View Transactions")

    # Detect if user is on mobile
    is_mobile = st.session_state.get('is_mobile', False)

    try:
        # Fetch data from Supabase
        response = conn.table("med_transactions").select("*").execute()
        data = response.data
        if not data:
            st.info("No transactions found.")
            return

        # Convert to DataFrame and handle data types
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['categories'] = df['categories'].apply(lambda x: x if isinstance(x, list) else [])

        # Filters in expander to save space
        with st.expander("Filters", expanded=not is_mobile):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=df['date'].min().date(),
                    min_value=df['date'].min().date(),
                    max_value=df['date'].max().date()
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=df['date'].max().date(),
                    min_value=df['date'].min().date(),
                    max_value=df['date'].max().date()
                )
            type_filter = st.selectbox(
                "Transaction Type",
                options=["All", "Income", "Expense"],
                index=0
            )

        # Apply filters
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        if type_filter != "All":
            mask = mask & (df['type'] == type_filter)
        filtered_df = df[mask].copy()

        # Calculate and display totals
        total_income = filtered_df[filtered_df['type'] == 'Income']['amount'].sum()
        total_expense = filtered_df[filtered_df['type'] == 'Expense']['amount'].sum()
        net_amount = total_income - total_expense

        # Summary metrics
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Income", f"${total_income:,.2f}")
        with col2:
            st.metric("Expenses", f"${total_expense:,.2f}")
        with col3:
            st.metric("Net", f"${net_amount:,.2f}")

        # Display transactions
        st.subheader("Transactions")
        if not filtered_df.empty:
            display_df = filtered_df[['date', 'description', 'amount', 'type', 'account_origin', 'account_destination', 'categories', 'file_path']].copy()
            st.dataframe(display_df)
        else:
            st.info("No transactions match the selected filters.")

        bucket_id = "files"
        source_path = st.text_input("Enter source path")

        if st.button("Request download"):
            file_name, mime, data = conn.download(bucket_id, source_path)
            st.download_button(
                "Download file", data=data, 
                file_name=file_name, mime=mime,
            )

    except Exception as e:
        st.error(f"Error: {str(e)}")

def page_view_categories():
    """View and manage existing categories."""
    st.title("Manage Categories")

    # Fetch categories
    categories_data = conn.table("category").select("*").execute()
    existing_categories = [cat["name"] for cat in categories_data.data] if categories_data.data else []

    # Display categories
    st.write("Existing Categories:", existing_categories)

    # Add new category
    new_category = st.text_input("New Category")
    if st.button("Add Category") and new_category:
        response = conn.table("category").insert({"name": new_category}).execute()
        if response.data:
            st.success(f"Category '{new_category}' added successfully!")
        else:
            st.error("Error adding category.")

    # Delete category
    category_to_delete = st.selectbox("Select Category to Delete", existing_categories)
    if st.button("Delete Category") and category_to_delete:
        response = conn.table("category").delete().eq("name", category_to_delete).execute()
        if response.data:
            st.success(f"Category '{category_to_delete}' deleted successfully!")
        else:
            st.error("Error deleting category.")


if __name__ == "__main__":
    show()
