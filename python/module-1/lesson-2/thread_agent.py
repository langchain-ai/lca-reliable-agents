from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
from langsmith import traceable, Client
import langsmith as ls
from langsmith.wrappers import wrap_openai

load_dotenv()

# Initialize clients
client = wrap_openai(OpenAI())
langsmith_client = Client()

# Configuration
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
THREAD_ID = str(uuid.uuid4())
langsmith_extra = {
    "project_name": LANGSMITH_PROJECT,
    "metadata": {"session_id": THREAD_ID}
}

# gets a history of all LLM calls in the thread to construct conversation history
def get_thread_history(thread_id: str, project_name: str):
    # Filter runs by the specific thread and project
    filter_string = f'and(in(metadata_key, ["session_id","conversation_id","thread_id"]), eq(metadata_value, "{thread_id}"))'
    # Only grab the LLM runs
    runs = [r for r in langsmith_client.list_runs(
        project_name=project_name,
        filter=filter_string,
        run_type="llm"
    )]

    # If no history exists, return empty list (new conversation)
    if not runs:
        return []

    # Sort by start time to get the most recent interaction
    runs = sorted(runs, key=lambda run: run.start_time, reverse=True)

    # Reconstruct the conversation state
    latest_run = runs[0]
    return latest_run.inputs['messages'] + [latest_run.outputs['choices'][0]['message']]

@traceable(name="Name Agent")
def chat_pipeline(messages: list):
    # Automatically fetch history if it exists
    run_tree = ls.get_current_run_tree()
    history_messages = get_thread_history(
        run_tree.extra["metadata"]["session_id"],
        run_tree.session_name
    )

    # Combine history with new messages
    all_messages = history_messages + messages

    # Invoke the model
    chat_completion = client.chat.completions.create(
        model="gpt-5-nano",
        messages=all_messages
    )

    # Return the complete conversation including input and response
    response_message = chat_completion.choices[0].message
    return {
        "messages": all_messages + [response_message]
    }

if __name__ == "__main__":
    # First message
    messages = [{"content": "Hi, my name is Sally", "role": "user"}]
    result = chat_pipeline(messages, langsmith_extra=langsmith_extra)
    print(result["messages"][-1])

    # Follow up message - agent should remember the name
    messages = [{"content": "What's my name?", "role": "user"}]
    result = chat_pipeline(messages, langsmith_extra=langsmith_extra)
    print(result["messages"][-1])
