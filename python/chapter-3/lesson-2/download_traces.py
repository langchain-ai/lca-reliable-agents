"""Download the last 100 root traces from lca-ls-project and save to traces.json."""

import json
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client


def serialize_run(run) -> dict:
    """Convert a Run object to a JSON-serializable dict."""
    return {
        "id": str(run.id),
        "name": run.name,
        "run_type": run.run_type,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "trace_id": str(run.trace_id),
        "dotted_order": run.dotted_order,
        "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None,
        "extra": run.extra,
        "error": run.error,
        "tags": run.tags,
    }


def main():
    client = Client()
    project_name = "lca-ls-project"

    print(f"Fetching last 100 root runs from '{project_name}'...")
    root_runs = list(
        client.list_runs(project_name=project_name, is_root=True, limit=100)
    )
    print(f"Found {len(root_runs)} root runs.")

    all_runs = []
    for i, root in enumerate(root_runs):
        trace_runs = list(client.list_runs(trace_id=root.trace_id))
        print(
            f"  [{i + 1}/{len(root_runs)}] trace {root.trace_id}: "
            f"{len(trace_runs)} runs"
        )
        for run in trace_runs:
            all_runs.append(serialize_run(run))

    output_path = "traces.json"
    with open(output_path, "w") as f:
        json.dump(all_runs, f, indent=2, default=str)

    print(f"\nSaved {len(all_runs)} total runs to {output_path}")


if __name__ == "__main__":
    main()
