"""
Run tool usage evaluation against the officeflow-dataset.

Usage:
    uv run python run_tool_usage_eval.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(usecwd=True))

from langsmith import aevaluate

# Import the agent - adjust path as needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "officeflow-agent"))
from agent_v4 import chat, load_knowledge_base

# Import evaluators
from eval_tool_usage import evaluators


async def target(inputs: dict) -> dict:
    """
    Target function that wraps the agent for evaluation.

    Args:
        inputs: dict with 'question' key from dataset

    Returns:
        dict with agent outputs
    """
    question = inputs["question"]
    result = await chat(question)
    return result


async def main():
    # Load knowledge base before running evaluation
    print("Loading knowledge base...")
    await load_knowledge_base(kb_dir="../officeflow-agent/knowledge_base")
    print()

    print("Running tool usage evaluation...")
    print("=" * 60)

    results = await aevaluate(
        target,
        data="officeflow-dataset",
        evaluators=evaluators,
        experiment_prefix="tool-usage-eval",
        max_concurrency=2,  # Limit concurrency to avoid rate limits
    )

    print()
    print("=" * 60)
    print("Evaluation complete! View results in LangSmith.")


if __name__ == "__main__":
    asyncio.run(main())
