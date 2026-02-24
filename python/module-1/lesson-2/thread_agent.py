from openai import OpenAI
from dotenv import load_dotenv
from langsmith import traceable, uuid7
from langsmith.wrappers import wrap_openai

load_dotenv()

# Initialize clients
client = wrap_openai(OpenAI())

# Configuration
THREAD_ID = str(uuid7())

# Conversation history store (use a database in production)
thread_store: dict[str, list] = {}

def get_thread_history(thread_id: str) -> list:
    return thread_store.get(thread_id, [])

def save_thread_history(thread_id: str, messages: list):
    thread_store[thread_id] = messages

@traceable(name="Name Agent", metadata={"thread_id": THREAD_ID})
def chat_pipeline(messages: list):
    # Automatically fetch history if it exists
    history_messages = get_thread_history(THREAD_ID)

    # Combine history with new messages
    all_messages = history_messages + messages

    # Invoke the model
    chat_completion = client.chat.completions.create(
        model="gpt-5-nano",
        messages=all_messages
    )

    # Save and return the complete conversation including input and response
    response_message = chat_completion.choices[0].message
    full_conversation = all_messages + [{"role": response_message.role, "content": response_message.content}]
    save_thread_history(THREAD_ID, full_conversation)

    return {
        "messages": full_conversation
    }

if __name__ == "__main__":
    # First message
    messages = [{"content": "Hi, my name is Sally", "role": "user"}]
    result = chat_pipeline(messages)
    print(result["messages"][-1])

    # Follow up message - agent should remember the name
    messages = [{"content": "What's my name?", "role": "user"}]
    result = chat_pipeline(messages)
    print(result["messages"][-1])
