import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("API key is not set in .env file.")

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=api_key)

# Load the JSON rules from a file
with open('eligibility.json', 'r') as file:
    data = json.load(file)

# Construct the rules description with a clear end signal
rules_description = f"""
You are an assistant helping to determine social assistance eligibility based on the following rules:
- Personal monthly income must be less than {data["rules"]["personal_income"]["value"]} USD.
- House size must be less than {data["rules"]["house_size"]["value"]} square meters.
- The person must not be currently employed.

Please ask the user the necessary questions one by one, wait for their answers, and then determine if they are eligible. After providing the eligibility determination, conclude your response with the phrase "Assessment complete." Remember to keep your responses concise and focused.
"""

def check_eligibility_with_assistant():
    messages = [
        {"role": "system", "content": rules_description},
    ]

    while True:
        # Get assistant's message using the updated client syntax
        response = client.chat.completions.create(
            model="gpt-4",  # Replace with "gpt-3.5-turbo" if needed
            messages=messages
        )

        assistant_message = response.choices[0].message.content.strip()
        print(f"Assistant: {assistant_message}")

        messages.append({"role": "assistant", "content": assistant_message})

        # Check if the assistant has provided the final eligibility result
        if "assessment complete" in assistant_message.lower():
            break

        # Get user input
        user_input = input("You: ").strip()
        messages.append({"role": "user", "content": user_input})

    print("Conversation ended.")

# Run the eligibility check with the assistant
check_eligibility_with_assistant()