"""Load traces.json, shift timestamps to now, regenerate IDs, and upload via RunTree."""

import json
from collections import defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client, uuid7
from langsmith.run_trees import RunTree


def parse_dt(s: str | None) -> datetime | None:
    if s is None:
        return None
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="default", help="Target project name")
    parser.add_argument("--input", default="synthetic_traces.json", help="Input file path")
    args = parser.parse_args()

    with open(args.input) as f:
        runs = json.load(f)

    print(f"Loaded {len(runs)} runs from {args.input}")

    # Calculate time shift so traces appear recent
    latest = max(parse_dt(r["start_time"]) for r in runs if r["start_time"])
    time_delta = datetime.now(timezone.utc).replace(tzinfo=None) - latest
    print(f"Shifting timestamps by: {time_delta}")

    # Build ID map (uuid7 for time-ordering)
    id_map = {}
    for run in runs:
        for field in ("id", "trace_id", "parent_run_id"):
            old_id = run.get(field)
            if old_id and old_id not in id_map:
                id_map[old_id] = str(uuid7())

    # Group runs by trace and transform
    traces = defaultdict(list)
    for run in runs:
        traces[run["trace_id"]].append({
            "id": id_map[run["id"]],
            "parent_run_id": id_map.get(run["parent_run_id"]),
            "name": run["name"],
            "run_type": run["run_type"],
            "inputs": run["inputs"],
            "outputs": run.get("outputs"),
            "error": run.get("error"),
            "extra": run.get("extra"),
            "tags": run.get("tags"),
            "start_time": parse_dt(run["start_time"]) + time_delta,
            "end_time": parse_dt(run["end_time"]) + time_delta if run.get("end_time") else None,
        })

    client = Client()
    print(f"Uploading {len(traces)} traces to project '{args.project}'...")

    for i, trace_runs in enumerate(traces.values()):
        # Sort by start_time, root first (no parent)
        trace_runs.sort(key=lambda r: (r["parent_run_id"] is not None, r["start_time"]))

        tree_map = {}
        root_tree = None

        for run in trace_runs:
            if run["parent_run_id"] is None:
                # Root run
                root_tree = RunTree(
                    id=run["id"],
                    name=run["name"],
                    run_type=run["run_type"],
                    inputs=run["inputs"],
                    start_time=run["start_time"],
                    extra=run.get("extra"),
                    tags=run.get("tags"),
                    project_name=args.project,
                    client=client,
                )
                tree_map[run["id"]] = root_tree
            else:
                # Child run
                parent = tree_map.get(run["parent_run_id"])
                if parent:
                    child = parent.create_child(
                        name=run["name"],
                        run_type=run["run_type"],
                        run_id=run["id"],
                        inputs=run["inputs"],
                        start_time=run["start_time"],
                        extra=run.get("extra"),
                        tags=run.get("tags"),
                    )
                    tree_map[run["id"]] = child

        # End all runs (children first)
        for run in reversed(trace_runs):
            tree = tree_map.get(run["id"])
            if tree:
                tree.end(outputs=run.get("outputs"), error=run.get("error"), end_time=run["end_time"])

        if root_tree:
            root_tree.post(exclude_child_runs=False)

        if (i + 1) % 10 == 0:
            print(f"  Uploaded {i + 1}/{len(traces)} traces")

    # Wait for all background operations to complete
    print("Flushing...")
    client.flush()
    print("Done!")


if __name__ == "__main__":
    main()
