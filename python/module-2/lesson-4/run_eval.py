import asyncio
import sys
from pathlib import Path
from langsmith import aevaluate

# Add the agent directory to the path
agent_dir = Path(__file__).resolve().parent.parent.parent / "officeflow-agent"
sys.path.insert(0, str(agent_dir))

from agent_v4 import chat, load_knowledge_base
from eval_schema_check import sql_starts_with_schema_check

DATASET_NAME = "officeflow-dataset"
EXPERIMENT_PREFIX = "schema-check-eval"


async def target(inputs: dict) -> dict:
    return await chat(inputs["question"])


async def main():
    # Load knowledge base before running evals
    await load_knowledge_base(str(agent_dir / "knowledge_base"))

    results = await aevaluate(
        target,
        data=DATASET_NAME,
        evaluators=[sql_starts_with_schema_check],
        experiment_prefix=EXPERIMENT_PREFIX,
        max_concurrency=2,
    )
    print("Evaluation complete! View results at the link above.")


if __name__ == "__main__":
    asyncio.run(main())
