import os
import json
import streamlit as st

# ✨ new imports for LangChain + deterministic checker
from eligibility_tool import eligibility_tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI

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

agent = create_openai_functions_agent(
    llm=llm,
    tools=[eligibility_tool],
    system_message=(
        "You are a helpful assistant that collects only the data needed to "
        "determine entitlement to the Serbian child allowance. "
        "When all fields are gathered, call `check_child_allowance` exactly once, "
        "then explain the result in plain Serbian."
    )
)
agent_executor = AgentExecutor(agent=agent, tools=[eligibility_tool])

def ask_gpt(prompt: str) -> str:
    """Route user text through the LangChain agent and return the assistant’s reply."""
    result = agent_executor.invoke({"input": prompt})
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
    response = ask_gpt(prompt)

    # update history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})

    # render user + assistant bubbles
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        st.markdown(response)
