"""Load traces.json, shift timestamps to now, regenerate IDs, and upload."""

import json
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client


def parse_dt(s: str | None) -> datetime | None:
    if s is None:
        return None
    dt = datetime.fromisoformat(s)
    # Strip timezone — LangSmith stores naive datetimes (implicitly UTC)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def rebuild_dotted_order(
    old_dotted_order: str,
    id_map: dict[str, str],
    time_delta,
) -> str:
    """Rebuild dotted_order with new UUIDs and shifted timestamps.

    dotted_order looks like:
      20250101T000000000000Z<uuid>.20250101T000001000000Z<uuid>
    Each segment is a timestamp + uuid joined by dots.
    """
    segments = old_dotted_order.split(".")
    new_segments = []
    # Pattern: timestamp portion (e.g. 20250101T000000000000Z) followed by uuid
    pattern = re.compile(r"^(\d{8}T\d+Z)(.+)$")
    for seg in segments:
        m = pattern.match(seg)
        if not m:
            new_segments.append(seg)
            continue
        ts_str, old_id = m.group(1), m.group(2)
        # Parse the timestamp from dotted_order format
        # Format: YYYYMMDDTHHMMSSffffffZ
        dt = datetime.strptime(ts_str, "%Y%m%dT%H%M%S%fZ").replace(
            tzinfo=timezone.utc
        )
        shifted = dt + time_delta
        new_ts = shifted.strftime("%Y%m%dT%H%M%S%fZ")
        new_id = id_map.get(old_id, old_id)
        new_segments.append(f"{new_ts}{new_id}")
    return ".".join(new_segments)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project", default="lca-ls-project-copy", help="Target project name"
    )
    parser.add_argument(
        "--input", default="traces.json", help="Input file path"
    )
    args = parser.parse_args()

    with open(args.input) as f:
        runs = json.load(f)

    print(f"Loaded {len(runs)} runs from {args.input}")

    # Find latest start_time across all runs so shifted times stay in the past
    latest = None
    for run in runs:
        st = parse_dt(run["start_time"])
        if st is not None and (latest is None or st > latest):
            latest = st

    now = datetime.utcnow()
    time_delta = now - latest
    print(f"Latest start_time: {latest.isoformat()}")
    print(f"Shifting by: {time_delta}")

    # Build ID map: every unique old UUID -> new UUID
    # Important: trace_id == root run's id, so they must share the same new UUID.
    # We build a single unified map for all UUIDs.
    id_map = {}
    for run in runs:
        if run["id"] not in id_map:
            id_map[run["id"]] = str(uuid.uuid4())
        # trace_id is always the root run's id, so reuse that mapping
        if run["trace_id"] not in id_map:
            id_map[run["trace_id"]] = str(uuid.uuid4())
        if run["parent_run_id"] and run["parent_run_id"] not in id_map:
            id_map[run["parent_run_id"]] = str(uuid.uuid4())

    # Transform runs
    transformed = []
    for run in runs:
        new_run = dict(run)

        # Remap IDs
        new_run["id"] = id_map[run["id"]]
        new_run["trace_id"] = id_map[run["trace_id"]]
        if run["parent_run_id"]:
            new_run["parent_run_id"] = id_map.get(
                run["parent_run_id"], run["parent_run_id"]
            )

        # Shift timestamps — keep as datetime objects (not strings)
        st = parse_dt(run["start_time"])
        et = parse_dt(run["end_time"])
        if st:
            new_run["start_time"] = st + time_delta
        if et:
            new_run["end_time"] = et + time_delta

        # Rebuild dotted_order
        if run["dotted_order"]:
            new_run["dotted_order"] = rebuild_dotted_order(
                run["dotted_order"], id_map, time_delta
            )

        transformed.append(new_run)

    # Upload: split into create (start) + update (end) like normal tracing does
    client = Client()
    print(f"Uploading {len(transformed)} runs to project '{args.project}'...")

    batch_size = 50
    for i in range(0, len(transformed), batch_size):
        batch = transformed[i : i + batch_size]
        create_list = []
        update_list = []
        for r in batch:
            # Create with start_time and inputs (like SDK does at run start)
            create_list.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "run_type": r["run_type"],
                    "inputs": r["inputs"],
                    "start_time": r["start_time"],
                    "trace_id": r["trace_id"],
                    "dotted_order": r["dotted_order"],
                    "parent_run_id": r["parent_run_id"],
                    "extra": r["extra"],
                    "tags": r["tags"],
                    "session_name": args.project,
                }
            )
            # Update with end_time, outputs, error (like SDK does at run end)
            update_list.append(
                {
                    "id": r["id"],
                    "trace_id": r["trace_id"],
                    "dotted_order": r["dotted_order"],
                    "parent_run_id": r["parent_run_id"],
                    "outputs": r["outputs"],
                    "end_time": r["end_time"],
                    "error": r["error"],
                }
            )
        client.multipart_ingest(create=create_list, update=update_list)
        print(f"  Uploaded batch {i // batch_size + 1} ({len(batch)} runs)")

    print("Done!")


if __name__ == "__main__":
    main()
