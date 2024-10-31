import os
import json
from openai import OpenAI
import streamlit as st


# Access the API key from Streamlit secrets
try:
    api_key = st.secrets["api_key"]["key"]
except KeyError:
    raise ValueError("API key is not set in Streamlit secrets.")

# Check if the API key was successfully retrieved
if not api_key:
    raise ValueError("API key is empty in Streamlit secrets.")

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=api_key)

st.title("Aplikacija za Bisholina")





#here a test of api call which will be ask_gpt but simpler form
def ask_gpt(prompt):
    response = client.chat.completions.create(  # Correct method for chat completions
        model="gpt-4o-mini",  # Use GPT-4 Turbo
        messages=[
            {"role": "system", "content": "You are an assistant helping to determine social assistance eligibility."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! Can you start answering my questions so we can see if you are eligible for FSA?"}]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input here some changes will be needed
prompt = st.chat_input("What is up?")

if prompt:
    response = ask_gpt(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)

    




