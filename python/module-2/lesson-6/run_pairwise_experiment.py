import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from langsmith import aevaluate, evaluate
from officeflow_agent.agent_v4 import chat as chat_v4, load_knowledge_base as load_kb_v4
from officeflow_agent.agent_v5 import chat as chat_v5, load_knowledge_base as load_kb_v5
from eval_conciseness_pairwise import conciseness_evaluator
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

    # Step 1: Run experiment for agent v4
    print("\n" + "="*50)
    print("Running experiment for agent_v4...")
    print("="*50)
    v4_results = await aevaluate(
        chat_wrapper_v4,
        data=DATASET_NAME,
        experiment_prefix="agent-v4",
    )

    # Step 2: Run experiment for agent v5
    print("\n" + "="*50)
    print("Running experiment for agent_v5...")
    print("="*50)
    v5_results = await aevaluate(
        chat_wrapper_v5,
        data=DATASET_NAME,
        experiment_prefix="agent-v5",
    )

    # Get experiment names from results
    v4_experiment = v4_results.experiment_name
    v5_experiment = v5_results.experiment_name

    print(f"\nv4 experiment: {v4_experiment}")
    print(f"v5 experiment: {v5_experiment}")

    # Step 3: Run pairwise evaluation
    print("\n" + "="*50)
    print("Running pairwise evaluation...")
    print("="*50)
    evaluate(
        (v4_experiment, v5_experiment),
        evaluators=[conciseness_evaluator],
        randomize_order=True,
    )

    print("\n" + "="*50)
    print("Done! Check LangSmith for results.")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
