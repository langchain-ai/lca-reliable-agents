"""
Trace Structure Inspector for LangSmith

Use this to understand the structure of your agent's traces before building an evaluator.
"""

from langsmith import Client
from typing import Optional
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def inspect_trace_structure(
    project_name: str,
    run_id: Optional[str] = None,
    show_sample_data: bool = True
) -> dict:
    """
    Inspect the structure of a LangSmith trace to understand where data lives.

    Args:
        project_name: The LangSmith project name
        run_id: Optional specific run ID to inspect. If None, fetches most recent.
        show_sample_data: Whether to show sample values from the trace

    Returns:
        dict with structure information that can be used programmatically
    """
    client = Client()

    # Fetch the run
    if run_id:
        run = client.read_run(run_id)
    else:
        runs = list(client.list_runs(
            project_name=project_name,
            is_root=True,
            limit=1
        ))
        if not runs:
            raise ValueError(f"No runs found in project '{project_name}'")
        run = client.read_run(runs[0].id)

    print("=" * 80)
    print("TRACE STRUCTURE ANALYSIS")
    print("=" * 80)
    print(f"\nProject: {project_name}")
    print(f"Run ID: {run.id}")
    print(f"Run Name: {run.name}")
    print(f"Run Type: {run.run_type}")

    # Analyze structure
    structure = {
        "run_id": str(run.id),
        "run_name": run.name,
        "run_type": run.run_type,
        "has_inputs": bool(run.inputs),
        "has_outputs": bool(run.outputs),
        "has_child_run_ids": bool(hasattr(run, 'child_run_ids') and run.child_run_ids),
        "inputs": {},
        "outputs": {},
        "child_runs_info": [],
        "metadata": run.metadata if hasattr(run, 'metadata') and run.metadata else None
    }

    # Analyze inputs
    print("\n" + "=" * 80)
    print("INPUTS")
    print("=" * 80)
    if run.inputs:
        print(f"\nKeys in run.inputs: {list(run.inputs.keys())}")
        structure["inputs"]["keys"] = list(run.inputs.keys())

        for key, value in run.inputs.items():
            value_type = type(value).__name__
            structure["inputs"][key] = {"type": value_type}

            if show_sample_data:
                if isinstance(value, (str, int, float, bool)):
                    sample = str(value)[:100]
                    print(f"  {key} ({value_type}): {sample}{'...' if len(str(value)) > 100 else ''}")
                elif isinstance(value, list):
                    print(f"  {key} ({value_type}): List with {len(value)} items")
                    if value and len(value) > 0:
                        print(f"    First item type: {type(value[0]).__name__}")
                        structure["inputs"][key]["list_item_type"] = type(value[0]).__name__
                elif isinstance(value, dict):
                    print(f"  {key} ({value_type}): Dict with keys: {list(value.keys())}")
                    structure["inputs"][key]["dict_keys"] = list(value.keys())
                else:
                    print(f"  {key} ({value_type})")
    else:
        print("No inputs found")

    # Analyze outputs
    print("\n" + "=" * 80)
    print("OUTPUTS")
    print("=" * 80)
    if run.outputs:
        print(f"\nKeys in run.outputs: {list(run.outputs.keys())}")
        structure["outputs"]["keys"] = list(run.outputs.keys())

        for key, value in run.outputs.items():
            value_type = type(value).__name__
            structure["outputs"][key] = {"type": value_type}

            if show_sample_data:
                if isinstance(value, (str, int, float, bool)):
                    sample = str(value)[:100]
                    print(f"  {key} ({value_type}): {sample}{'...' if len(str(value)) > 100 else ''}")
                elif isinstance(value, list):
                    print(f"  {key} ({value_type}): List with {len(value)} items")
                    if value and len(value) > 0:
                        print(f"    First item type: {type(value[0]).__name__}")
                        structure["outputs"][key]["list_item_type"] = type(value[0]).__name__

                        # Special handling for messages array
                        if key == "messages" and isinstance(value[0], dict):
                            print(f"    Looks like a messages array!")
                            print(f"    Message roles found: {set(m.get('role') for m in value if isinstance(m, dict))}")
                            structure["outputs"][key]["is_messages_array"] = True
                            structure["outputs"][key]["message_roles"] = list(set(m.get('role') for m in value if isinstance(m, dict)))

                            # Check for tool calls in messages
                            has_tool_calls = any(
                                m.get('role') == 'assistant' and m.get('tool_calls')
                                for m in value if isinstance(m, dict)
                            )
                            if has_tool_calls:
                                print(f"    ✓ Contains tool calls in assistant messages!")
                                structure["outputs"][key]["has_tool_calls"] = True

                                # Extract tool names
                                tool_names = set()
                                for m in value:
                                    if isinstance(m, dict) and m.get('role') == 'assistant' and m.get('tool_calls'):
                                        for tc in m.get('tool_calls', []):
                                            if isinstance(tc, dict):
                                                tool_names.add(tc.get('function', {}).get('name'))
                                print(f"    Tools called: {tool_names}")
                                structure["outputs"][key]["tool_names"] = list(tool_names)

                elif isinstance(value, dict):
                    print(f"  {key} ({value_type}): Dict with keys: {list(value.keys())}")
                    structure["outputs"][key]["dict_keys"] = list(value.keys())
                else:
                    print(f"  {key} ({value_type})")
    else:
        print("No outputs found")

    # Analyze child runs
    print("\n" + "=" * 80)
    print("CHILD RUNS")
    print("=" * 80)

    if hasattr(run, 'child_run_ids') and run.child_run_ids:
        print(f"\n✓ Has {len(run.child_run_ids)} child run IDs")
        structure["num_child_runs"] = len(run.child_run_ids)

        # Fetch a few child runs to see structure
        print("\nFetching child runs to inspect structure...")
        for i, child_id in enumerate(run.child_run_ids[:3]):  # Just first 3
            child_run = client.read_run(child_id)
            child_info = {
                "name": child_run.name,
                "type": child_run.run_type,
                "has_inputs": bool(child_run.inputs),
                "has_outputs": bool(child_run.outputs),
            }

            print(f"\n  Child Run {i+1}:")
            print(f"    Name: {child_run.name}")
            print(f"    Type: {child_run.run_type}")

            if child_run.inputs:
                print(f"    Input keys: {list(child_run.inputs.keys())}")
                child_info["input_keys"] = list(child_run.inputs.keys())

                # Show sample for tool calls
                if "query" in child_run.inputs:
                    print(f"    Query: {child_run.inputs['query'][:80]}...")

            if child_run.outputs:
                print(f"    Output keys: {list(child_run.outputs.keys())}")
                child_info["output_keys"] = list(child_run.outputs.keys())

            structure["child_runs_info"].append(child_info)

        if len(run.child_run_ids) > 3:
            print(f"\n  ... and {len(run.child_run_ids) - 3} more child runs")

    else:
        print("\n✗ No child run IDs found")
        structure["num_child_runs"] = 0

    # Metadata
    if structure["metadata"]:
        print("\n" + "=" * 80)
        print("METADATA")
        print("=" * 80)
        print(f"\nMetadata keys: {list(structure['metadata'].keys())}")

    # Summary and recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS FOR EVALUATOR")
    print("=" * 80)

    recommendations = []

    # Check if messages are in outputs
    if (structure["outputs"].get("keys") and "messages" in structure["outputs"]["keys"] and
        structure["outputs"].get("messages", {}).get("is_messages_array")):
        print("\n✓ Agent returns messages in outputs")
        print("  Recommendation: Extract tool calls from run.outputs['messages']")
        print("  This is the most reliable approach.")
        recommendations.append("extract_from_messages")

        if structure["outputs"]["messages"].get("has_tool_calls"):
            print(f"\n✓ Tool calls found in messages")
            print(f"  Tools: {structure['outputs']['messages'].get('tool_names')}")
    else:
        print("\n✗ Agent does not return messages in outputs")
        if structure["num_child_runs"] > 0:
            print("  Recommendation: Extract tool calls from run.child_runs")
            print("  Note: This requires traversing the child run tree")
            recommendations.append("extract_from_child_runs")
        else:
            print("  Warning: No obvious place to find tool calls")
            print("  Consider updating agent to return messages in outputs")

    structure["recommendations"] = recommendations

    # Return structure for programmatic use
    print("\n" + "=" * 80)
    return structure


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python inspect_trace.py <project_name> [run_id]")
        print("\nExample:")
        print("  python inspect_trace.py my-langsmith-project")
        print("  python inspect_trace.py my-langsmith-project 019c546c-2ce6-7853-8ac5-939a88d7c4a4")
        sys.exit(1)

    project_name = sys.argv[1]
    run_id = sys.argv[2] if len(sys.argv) > 2 else None

    structure = inspect_trace_structure(project_name, run_id)

    print("\n" + "=" * 80)
    print("Structure data saved for programmatic use")
    print("=" * 80)
    print("\nYou can import this function and use the returned dict:")
    print("  from inspect_trace import inspect_trace_structure")
    print("  structure = inspect_trace_structure('your-project')")
    print("  if 'extract_from_messages' in structure['recommendations']:")
    print("      # Extract from run.outputs['messages']")
