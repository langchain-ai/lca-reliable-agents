import asyncio
import sys
from pathlib import Path

# Add parent directories to path for imports
python_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(python_dir))
sys.path.insert(0, str(python_dir / "officeflow-agent"))

from langsmith import aevaluate
from agent_v4 import chat, load_knowledge_base
from dotenv import load_dotenv

load_dotenv()

# Dataset with bound evaluator in UI
dataset_name = "officeflow-dataset"

async def chat_wrapper(inputs: dict) -> dict:
    """Wrapper to adapt dataset inputs to chat function signature."""
    question = inputs.get("question", "")
    result = await chat(question)
    return {"answer": result["output"], "messages": result["messages"]}

async def main():
    # Load knowledge base before running evaluation
    kb_path = str(python_dir / "officeflow-agent" / "knowledge_base")
    print(f"Loading knowledge base from {kb_path}...")
    await load_knowledge_base(kb_dir=kb_path)
    print()

    # Evaluator bound to dataset will run automatically
    results = await aevaluate(
        chat_wrapper,
        data=dataset_name
    )
    print(f"Evaluation complete! Results: {results}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
