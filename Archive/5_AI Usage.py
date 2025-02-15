import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# Define cost per token for input and output for each model in millions

FX = 1.44

input_token_costs = {
    "chatgpt-4o-latest": 2.5*FX,  # Example cost per million input tokens for GPT-4o (2.5USD per 1M tokens)
    "gpt-4o-mini": 0.15*FX,  # Example cost per million input tokens for ChatGPT-4o-Latest (5USD per 1M tokens)
    "claude-3-5-sonnet-latest": 3*FX,  # Example cost per million input tokens for Claude-3-5-Sonnet (3USD per 1M tokens)
    "claude-3-opus-latest":15*FX,
    "o1-mini": 3*FX,

}

output_token_costs = {
    "chatgpt-4o-latest": 10*FX,  # Example cost per million output tokens for GPT-4o (10USD per 1M tokens)
    "gpt-4o-mini": 0.6*FX,  # Example cost per million output tokens for ChatGPT-4o-Latest (5USD per 1M tokens)
    "claude-3-5-sonnet-latest": 15*FX,  # Example cost per million output tokens for Claude-3-5-Sonnet (15usd per 1M tokens)
    "claude-3-opus-latest":75*FX,
    "o1-mini": 12*FX,
}

# Establish connection to Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# Fetch data from the database
response = conn.table("aiusage").select("input_tokens, output_tokens, createdat, tag, model").execute()

# Check if data is fetched successfully
if response:
    # Convert data to a DataFrame for better display
    data = response.data
    df = pd.DataFrame(data)

    # Convert 'createdat' to a readable date format
    df['createdat'] = pd.to_datetime(df['createdat'])

    # Select only the required columns
    df = df[['input_tokens', 'output_tokens', 'createdat', 'tag', 'model']]

    #Add a date range filter
    st.header("AI Usage", divider="grey")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", df['createdat'].min().date())
    with col2:
        end_date = st.date_input("End date", df['createdat'].max().date())

    # Filter the DataFrame based on the selected date range
    mask = (df['createdat'].dt.date >= start_date) & (df['createdat'].dt.date <= end_date)
    filtered_df = df[mask]

    # Calculate costs based on input and output token costs in millions
    filtered_df['cost'] = filtered_df.apply(
        lambda row: (
            row['input_tokens'] / 1e6 * input_token_costs.get(row['model'], 0) +
            row['output_tokens'] / 1e6 * output_token_costs.get(row['model'], 0)
        ), axis=1
    )

    # Rename columns to more user-friendly names
    filtered_df = filtered_df.rename(columns={
    'createdat': 'Created At',
    'input_tokens': 'Input Tokens',
    'output_tokens': 'Output Tokens',
    'model': 'Model'
    })
    
    # Calculate total cost and cost summary by model
    total_cost = filtered_df['cost'].sum()
    model_cost_summary = filtered_df.groupby('Model')['cost'].sum()

    # Display the filtered data in a table format
    st.dataframe(filtered_df)

    # Display the cost summary
    st.subheader("Cost Summary")
    # Display the model cost summary with reduced space between rows
    for model, cost in model_cost_summary.items():
        st.markdown(f"<p style='margin: 0;'>Total Cost for {model}: ${cost:.2f}</p>", unsafe_allow_html=True)

    # Display the total cost in bold
    st.markdown(f"<p style='margin: 0; font-weight: bold;'>Total Cost: ${total_cost:.2f}</p>", unsafe_allow_html=True)
else:
    st.write("No data found.")
