---
name: langsmith-code-eval
description: Create code-based evaluators for LangSmith-traced agents with step-by-step collaborative guidance through inspection, evaluation logic, and testing.
---

# LangSmith Code Evaluator Creation

Create code-based evaluators for LangSmith-traced agents through a 9-step collaborative process.

## Workflow

### Step 1: Locate the Agent
Ask: "Where is your agent file located?"

### Step 2: Understand the Agent
Read the agent file. Identify:
- Main entry point function
- Tools/functions it calls
- Return format (string? dict with messages?)

### Step 3: Check for Traces
Ask: "Do you have recent traces in LangSmith?"
- If yes: Get project name
- If no: Ask to run agent once to generate a trace

### Step 4: Inspect Trace Structure
Run: `python scripts/inspect_trace.py PROJECT_NAME`

This shows where data lives:
- Tool calls in `run.outputs["messages"]`?
- Tool calls in `run.child_runs`?
- What's in inputs/outputs?

Use the returned structure dict programmatically:
```python
from inspect_trace import inspect_trace_structure

structure = inspect_trace_structure("project-name")
if "extract_from_messages" in structure["recommendations"]:
    # Tool calls are in run.outputs["messages"]
```

### Step 5: Clarify Evaluation Goals
Ask: "What behavior do you want to test for?"
- If stated: Confirm understanding
- If unclear: Ask clarifying questions
- Understand: Pass vs fail criteria? Different categories? Metadata?

### Step 6: Create the Evaluator
Write `eval_[name].py` using this signature:

```python
from langsmith.schemas import Run, Example

def evaluate_[name](run: Run, example: Example) -> dict:
    """Evaluate [specific behavior]."""

    # Extract data (based on Step 4)
    messages = run.outputs.get("messages", [])
    category = example.metadata.get("category") if example.metadata else None

    # Evaluation logic (based on Step 5)
    # ...

    return {
        "key": "evaluator_name",
        "score": 1 or 0,  # 1 = pass, 0 = fail
        "comment": "Specific feedback explaining the score"
    }
```

**Extract tool calls from messages:**
```python
for msg in messages:
    if msg.get("role") == "assistant" and msg.get("tool_calls"):
        for tc in msg["tool_calls"]:
            tool_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
```

**Category-based evaluation:**
```python
category = example.metadata.get("category", "unknown")
if category == "stock":
    score = 1 if made_db_call else 0
elif category == "weather":
    score = 1 if not made_db_call else 0
```

### Step 7: Create/Update Experiment Runner
Check if `run_experiment_with_eval.py` exists. If not, create:

```python
import asyncio
from langsmith import aevaluate
from [agent_module] import [agent_function]
from eval_[name] import evaluate_[name]
from dotenv import load_dotenv

load_dotenv()

async def agent_wrapper(inputs: dict) -> dict:
    result = await [agent_function](inputs["question"])
    return result

async def main():
    results = await aevaluate(
        agent_wrapper,
        data="DATASET_NAME",
        evaluators=[evaluate_[name]],
        experiment_prefix="eval-test",
        max_concurrency=5,
    )
    print(f"Results: {results}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 8: Configure Dataset
Ask: "What's your dataset name?"
Ask: "Please update the dataset name in the experiment runner"
Wait for confirmation.

### Step 9: Run the Evaluation
Execute: `uv run python run_experiment_with_eval.py`
Show the LangSmith URL when printed.

## Key Patterns

**Extracting from messages** (most reliable):
```python
messages = run.outputs.get("messages", [])
for msg in messages:
    if msg.get("role") == "assistant" and msg.get("tool_calls"):
        # Tool calls are here
```

**Extracting from child_runs** (if messages not available):
```python
def traverse_runs(run):
    if run.name == "tool_name":
        # Found it
    if hasattr(run, 'child_runs') and run.child_runs:
        for child in run.child_runs:
            traverse_runs(child)
```

**Using metadata:**
```python
category = example.metadata.get("category") if example.metadata else None
```

## Troubleshooting

**Can't find tool calls**: Re-run `inspect_trace.py` to see actual structure

**child_runs empty**: Agent should return messages in outputs

**Same score always**: Debug evaluation logic with print statements

**Dataset not found**: Verify name in LangSmith UI

## Reference

**Documentation:**
- [Code Evaluator SDK](https://docs.langchain.com/langsmith/code-evaluator-sdk) - Writing evaluators
- [Evaluate LLM Applications](https://docs.langchain.com/langsmith/evaluate-llm-application) - Running experiments

**Important:** Extensive LangSmith documentation exists. If unsure about trace structure, SDK usage, or evaluation patterns, **search documentation** rather than assuming.

**See parent project for complete example:**
- `agent_v4.py` - Returns messages in outputs
- `eval_tool_call_schema.py` - Tool call + schema discovery evaluator
- `run_experiment_with_code_eval.py` - Experiment runner
