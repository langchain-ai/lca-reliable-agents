import asyncio
from langsmith import aevaluate
from officeflow_agent.agent_v4 import chat
from dotenv import load_dotenv

load_dotenv()

# Dataset with bound evaluator in UI
dataset_name = "officeflow-db-code-test"

async def chat_wrapper(inputs: dict) -> dict:
    """Wrapper to adapt dataset inputs to chat function signature."""
    question = inputs.get("question", "")
    result = await chat(question)
    return {"answer": result["output"], "messages": result["messages"]}

async def main():
    # Evaluator bound to dataset will run automatically
    results = await aevaluate(
        chat_wrapper,
        data=dataset_name
    )
    print(f"Evaluation complete! Results: {results}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
