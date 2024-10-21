import os
import json
import openai
import streamlit as st



# Access the API key from Streamlit secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Check if the API key was successfully retrieved
if not openai_api_key:
    raise ValueError("API key is not set in Streamlit secrets.")


openai.api_key = openai_api_key

# Your OpenAI API calls here

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=api_key)

st.title("FSA ZA BISHU")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input here some changes will be needed
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.markdown(ask_gpt())
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})


#here a test of api call which will be ask_gpt but simpler form
def ask_gpt(prompt):
    response = client.chat.completions.create(  # Correct method for chat completions
        model="gpt-4-turbo",  # Use GPT-4 Turbo
        messages=[
            {"role": "system", "content": "You are an assistant helping to determine social assistance eligibility."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.5
    )
    return response['choices'][0]['message']['content'].strip()
ask_gpt(prompt)

