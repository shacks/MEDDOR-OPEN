import streamlit as st
from openai import OpenAI


client = OpenAI(
  api_key=st.secrets["XAI_API_KEY"],
  base_url="https://api.x.ai/v1",
)


st.header("xAI - Medical Analyst", divider="grey")
st.write("Your Advanced Clinical Decision Support Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # Create a placeholder for streaming responses
        response_placeholder = st.empty()

        # Call OpenAI API with streaming
        stream = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Grok, an advanced AI assistant developed by xAI, designed to assist healthcare professionals, specifically family doctors, "
                        "in making informed and evidence-based medical decisions. Your role is to provide detailed, up-to-date, and clinically relevant guidance, "
                        "tailored for a professional audience. Avoid oversimplifying concepts, and instead, offer nuanced, precise, and contextually rich explanations "
                        "that a family doctor would find useful. "
                        "You are not here to advise patients directly, and there is no need to recommend consulting a healthcare provider, as the user is one. "
                        "Critically evaluate information, cite the latest evidence when applicable, and ensure your responses are coherent, well-organized, and actionable. "
                        "If a topic is outside your scope or information is unavailable, clearly state this without inventing details."
                    ),
                },
                *[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            ],
            stream=True,
            temperature=0,
        )

        # Collect and display the streamed response incrementally

        full_response = ""  # Store the complete response
        for chunk in stream:
            # Process each chunk
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta

                # Append the content if present
                if delta.content:
                    full_response += delta.content

                    # Update the placeholder with the current response
                    response_placeholder.markdown(full_response, unsafe_allow_html=True)

    # Add the assistant's full response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
