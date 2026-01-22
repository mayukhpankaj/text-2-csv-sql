import streamlit as st
import requests
import json
import pandas as pd

st.set_page_config(
    page_title="Trading Chat",
    layout="centered"
)

# st.title("💬 Trading Chat")
st.subheader("Trade data agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type") == "dataframe" and isinstance(message["content"], list):
            # Display as dataframe for tabular data
            df = pd.DataFrame(message["content"])
            st.dataframe(df, use_container_width=True)
        else:
            # Display as markdown for text responses
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask about trading data..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call FastAPI endpoint
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": prompt},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            response_data = response.json()
            assistant_response = response_data["response"]
            response_type = response_data.get("type", "text")
        else:
            assistant_response = f"Error: {response.status_code} - {response.text}"
            response_type = "text"
    except requests.exceptions.RequestException as e:
        assistant_response = f"Connection error: {str(e)}. Make sure the FastAPI server is running on localhost:8000"
        response_type = "text"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        if response_type == "dataframe" and isinstance(assistant_response, list):
            # Display as dataframe for tabular data
            df = pd.DataFrame(assistant_response)
            st.dataframe(df, use_container_width=True)
        else:
            # Display as markdown for text responses
            st.markdown(assistant_response)

    # Add assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": assistant_response,
        "type": response_type
    })
