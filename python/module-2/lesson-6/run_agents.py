import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from langsmith import aevaluate
from officeflow_agent.agent_v4 import chat as chat_v4, load_knowledge_base as load_kb_v4
from officeflow_agent.agent_v5 import chat as chat_v5, load_knowledge_base as load_kb_v5
from dotenv import load_dotenv

load_dotenv()

DATASET_NAME = "officeflow-dataset"

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
    await load_kb_v4()
    await load_kb_v5()

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
