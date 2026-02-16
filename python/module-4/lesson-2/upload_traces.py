"""Upload traces with historical timestamps to LangSmith.

Uses the POST /runs REST endpoint directly (not multipart_ingest) because
the multipart endpoint enforces ±24h on start_time for creates, while the
single-run POST endpoint accepts any timestamp.
"""

import json
import uuid
import time
from datetime import datetime, timezone

import requests as http_requests
from dotenv import load_dotenv
load_dotenv()

from langsmith import Client


def parse_dt(s: str | None) -> datetime | None:
    if s is None:
        return None
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def build_dotted_order(start_time: datetime, run_id: str, parent_dotted: str | None = None) -> str:
    ts = start_time.strftime("%Y%m%dT%H%M%S%fZ")
    segment = f"{ts}{run_id}"
    if parent_dotted:
        return f"{parent_dotted}.{segment}"
    return segment


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project", default="lca-ls-project-copy", help="Target project name"
    )
    parser.add_argument(
        "--input", default="synthetic_traces.json", help="Input file path"
    )
    args = parser.parse_args()

    with open(args.input) as f:
        runs = json.load(f)

    print(f"Loaded {len(runs)} runs from {args.input}")

    # Regenerate all UUIDs
    id_map = {}
    for run in runs:
        for field in ("id", "trace_id", "parent_run_id"):
            old = run.get(field)
            if old and old not in id_map:
                id_map[old] = str(uuid.uuid4())

    # Transform runs with new IDs and proper dotted_orders
    transformed = []
    for run in runs:
        new_run = dict(run)
        new_run["id"] = id_map[run["id"]]
        new_run["trace_id"] = id_map[run["trace_id"]]
        new_run["parent_run_id"] = id_map[run["parent_run_id"]] if run["parent_run_id"] else None
        new_run["start_time"] = parse_dt(run["start_time"])
        new_run["end_time"] = parse_dt(run["end_time"])
        transformed.append(new_run)

    # Build dotted_orders: roots first, then children
    dotted_map = {}
    for r in transformed:
        if r["parent_run_id"] is None:
            r["dotted_order"] = build_dotted_order(r["start_time"], r["id"])
            dotted_map[r["id"]] = r["dotted_order"]

    for r in transformed:
        if r["parent_run_id"] is not None:
            parent_dotted = dotted_map.get(r["parent_run_id"], "")
            r["dotted_order"] = build_dotted_order(r["start_time"], r["id"], parent_dotted)
            dotted_map[r["id"]] = r["dotted_order"]

    # Upload via direct POST /runs (supports historical timestamps)
    client = Client()
    api_url = client.api_url
    headers = client._headers

    print(f"Uploading {len(transformed)} runs to project '{args.project}'...")

    # Upload roots first (parent_run_id is None), then children
    roots = [r for r in transformed if r["parent_run_id"] is None]
    children = [r for r in transformed if r["parent_run_id"] is not None]

    batch_size = 25  # smaller batches for sequential POST
    errors = 0

    for label, group in [("root", roots), ("child", children)]:
        print(f"  Uploading {len(group)} {label} runs...")
        for i in range(0, len(group), batch_size):
            batch = group[i : i + batch_size]
            for r in batch:
                payload = {
                    "id": r["id"],
                    "name": r["name"],
                    "run_type": r["run_type"],
                    "inputs": r["inputs"],
                    "outputs": r["outputs"],
                    "start_time": r["start_time"].isoformat(),
                    "end_time": r["end_time"].isoformat(),
                    "trace_id": r["trace_id"],
                    "dotted_order": r["dotted_order"],
                    "parent_run_id": r["parent_run_id"],
                    "extra": r["extra"],
                    "tags": r["tags"],
                    "error": r["error"],
                    "session_name": args.project,
                }
                resp = http_requests.post(
                    f"{api_url}/runs",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code not in (200, 201, 202):
                    errors += 1
                    if errors <= 3:
                        print(f"    Error {resp.status_code}: {resp.text[:200]}")
            batch_num = i // batch_size + 1
            total_batches = (len(group) + batch_size - 1) // batch_size
            print(f"    {label} batch {batch_num}/{total_batches} ({len(batch)} runs)")

    print(f"Done! ({errors} errors)")


if __name__ == "__main__":
    main()
