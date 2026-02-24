from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import uuid
from langsmith import traceable
from langsmith.wrappers import wrap_openai

load_dotenv()

# Initialize clients
client = wrap_openai(OpenAI())

# Configuration
THREAD_ID = str(uuid.uuid4())

# Using a local file to store thread history. For production use, use a persistent storage solution.
THREAD_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "thread_history.json")

def get_thread_history() -> list:
    if not os.path.exists(THREAD_HISTORY_FILE):
        return []
    with open(THREAD_HISTORY_FILE, "r") as f:
        return json.load(f)

def save_thread_history(messages: list):
    with open(THREAD_HISTORY_FILE, "w") as f:
        json.dump(messages, f, indent=2, default=str)

@traceable(name="Name Agent", metadata={"thread_id": THREAD_ID})
def chat_pipeline(messages: list):
    # Automatically fetch history if it exists
    history_messages = get_thread_history()

    # Combine history with new messages
    all_messages = history_messages + messages

    # Invoke the model
    chat_completion = client.chat.completions.create(
        model="gpt-5-nano",
        messages=all_messages
    )

    # Return the complete conversation including input and response
    response_message = chat_completion.choices[0].message
    full_conversation = all_messages + [{"role": response_message.role, "content": response_message.content}]
    save_thread_history(full_conversation)

    return {
        "messages": full_conversation
    }

if __name__ == "__main__":
    # Clear history from previous runs
    if os.path.exists(THREAD_HISTORY_FILE):
        os.remove(THREAD_HISTORY_FILE)

    # First message
    messages = [{"content": "Hi, my name is Sally", "role": "user"}]
    result = chat_pipeline(messages)
    print(result["messages"][-1])

    # Follow up message - agent should remember the name
    messages = [{"content": "What's my name?", "role": "user"}]
    result = chat_pipeline(messages)
    print(result["messages"][-1])
