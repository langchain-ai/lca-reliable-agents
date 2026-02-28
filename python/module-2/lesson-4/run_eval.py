"""
Run the schema-before-query evaluator against the officeflow-dataset.

Usage:
    uv run --env-file ../../.env python run_eval.py
"""
import asyncio
import sys
from pathlib import Path

from langsmith import evaluate
from langsmith import uuid7

# Add the agent directory to path
agent_dir = str(Path(__file__).resolve().parent.parent.parent / "officeflow-agent")
sys.path.insert(0, agent_dir)

import agent_v5
from agent_v5 import chat, load_knowledge_base
from eval_schema_check import schema_before_query


async def setup():
    """Load knowledge base before running evals."""
    kb_dir = str(Path(agent_dir) / "knowledge_base")
    await load_knowledge_base(kb_dir)


def run_agent(inputs: dict) -> dict:
    """Invoke the agent with a fresh thread_id each time."""
    agent_v5.thread_id = str(uuid7())
    return asyncio.run(chat(inputs["question"]))


if __name__ == "__main__":
    asyncio.run(setup())

    results = evaluate(
        run_agent,
        data="officeflow-dataset",
        evaluators=[schema_before_query],
        experiment_prefix="schema-check-v5",
    )
