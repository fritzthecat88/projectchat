import os
import json
import streamlit as st
from eligibility_tool import eligibility_tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ────────────────────────────────────────────────────────────────────────────
# API-key handling (unchanged)
try:
    api_key = st.secrets["api_key"]["key"]
except KeyError:
    raise ValueError("API key is not set in Streamlit secrets.")
if not api_key:
    raise ValueError("API key is empty in Streamlit secrets.")

st.title("Aplikacija za Bisholina")

# ────────────────────────────────────────────────────────────────────────────
# Build LangChain agent that knows our StructuredTool
llm = ChatOpenAI(
    openai_api_key=api_key,         
    model_name="gpt-3.5-turbo-0125",
    temperature=0
)

# Create a proper prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that collects only the data needed to "
               "determine entitlement to the Serbian child allowance. "
               "Ask questions one by one, and remember what the user has already told you. "
               "Don't repeat questions you've already asked. "
               "When all fields are gathered, call `check_child_allowance` exactly once, "
               "then explain the result in plain Serbian."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# Create the agent with the correct parameters
agent = create_openai_tools_agent(
    llm=llm,
    tools=[eligibility_tool],
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent, 
    tools=[eligibility_tool],
    verbose=True  # Set to False in production
)

def ask_gpt(prompt: str, chat_history: list) -> str:
    """Route user text through the LangChain agent and return the assistant's reply."""
    result = agent_executor.invoke({
        "input": prompt,
        "chat_history": chat_history
    })
    return result["output"]

# ────────────────────────────────────────────────────────────────────────────
# Initialise chat history once
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hello! Can you start answering my questions so we can see "
                "if you are eligible for FSA?"
            )
        }
    ]

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input box
prompt = st.chat_input("What is up?")
if prompt:
    # Convert messages to chat history format for LangChain
    chat_history = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_history.append(("human", msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(("ai", msg["content"]))
    
    response = ask_gpt(prompt, chat_history)
    
    # update history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # render user + assistant bubbles
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        st.markdown(response)
