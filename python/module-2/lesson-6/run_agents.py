import asyncio
import sys
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent.parent / "officeflow-agent"
sys.path.insert(0, str(agent_dir))

from langsmith import aevaluate
from agent_v4 import chat as chat_v4, load_knowledge_base as load_kb_v4
from agent_v5 import chat as chat_v5, load_knowledge_base as load_kb_v5
from dotenv import load_dotenv

load_dotenv()

DATASET_NAME = "officeflow-dataset"
KB_DIR = str(agent_dir / "knowledge_base")

async def chat_wrapper_v4(inputs: dict) -> dict:
    question = inputs.get("question", "")
    result = await chat_v4(question)
    return {"answer": result["output"]}

async def chat_wrapper_v5(inputs: dict) -> dict:
    question = inputs.get("question", "")
    result = await chat_v5(question)
    return {"answer": result["output"]}

async def main():
    # Load knowledge bases for both agents
    print("Loading knowledge bases...")
    await load_kb_v4(KB_DIR)
    await load_kb_v5(KB_DIR)

    # Run experiment for agent v4
    print("\nRunning experiment for agent_v4...")
    v4_results = await aevaluate(
        chat_wrapper_v4,
        data=DATASET_NAME,
        experiment_prefix="agent-v4",
    )

    # Run experiment for agent v5
    print("\nRunning experiment for agent_v5...")
    v5_results = await aevaluate(
        chat_wrapper_v5,
        data=DATASET_NAME,
        experiment_prefix="agent-v5",
    )

    print(f"\nv4 experiment: {v4_results.experiment_name}")
    print(f"v5 experiment: {v5_results.experiment_name}")
    print("Done! Use these experiment names in the pairwise evaluation.")

if __name__ == "__main__":
    asyncio.run(main())
