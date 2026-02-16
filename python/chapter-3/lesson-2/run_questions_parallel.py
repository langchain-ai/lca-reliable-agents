"""
Run generated questions through an agent in parallel and save results.

Same as run_questions.py but runs multiple questions concurrently using
asyncio.gather with a semaphore to limit concurrency.

Usage:
    uv run python run_questions_parallel.py --questions test_questions.csv
    uv run python run_questions_parallel.py --questions test_questions.csv -c 10
    uv run python run_questions_parallel.py --questions test_questions.csv -c 5 -n 20
"""

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "officeflow_agent"))


async def main():
    parser = argparse.ArgumentParser(
        description="Run questions through an agent in parallel and save results"
    )
    parser.add_argument(
        "--questions", required=True, help="Path to the questions CSV"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output CSV path (default: <input>_results.csv)",
    )
    parser.add_argument(
        "-n", type=int, default=None,
        help="Only run the first n questions (default: run all)",
    )
    parser.add_argument(
        "-c", "--concurrency", type=int, default=5,
        help="Max concurrent agent calls (default: 5)",
    )
    args = parser.parse_args()

    # Determine output path
    questions_path = Path(args.questions)
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = questions_path.with_name(
            questions_path.stem + "_results" + questions_path.suffix
        )

    # Import agent and load knowledge base
    print("Loading agent...")
    from agent_v5 import chat, load_knowledge_base
    await load_knowledge_base()
    print()

    # Read questions
    rows: List[Dict] = []
    with open(questions_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    total_loaded = len(rows)
    if args.n is not None:
        rows = rows[:args.n]

    print(f"Loaded {total_loaded} questions from {questions_path}")
    if args.n is not None:
        print(f"Running first {len(rows)} of {total_loaded}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Output will be written to {output_path}\n")

    # Open output CSV and write header up front (incremental writes)
    output_fields = list(fieldnames) + ["_idx", "agent_response"]
    outfile = open(output_path, "w", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(outfile, fieldnames=output_fields)
    writer.writeheader()
    outfile.flush()

    # Semaphore to limit concurrency
    sem = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    completed = {"count": 0}
    total = len(rows)
    start_time = time.time()

    async def run_one(idx: int, row: Dict):
        question = row["question"]
        async with sem:
            try:
                result = await chat(question)
                response = result["output"]
            except Exception as e:
                response = f"[Error: {e}]"

        result = dict(row)
        result["_idx"] = idx
        result["agent_response"] = response

        # Write result immediately (completion order)
        async with write_lock:
            writer.writerow(result)
            outfile.flush()

        completed["count"] += 1
        elapsed = time.time() - start_time
        display_q = question[:60] + "..." if len(question) > 60 else question
        display_r = response[:60] + "..." if len(response) > 60 else response
        print(f"  [{completed['count']}/{total}] ({elapsed:.1f}s) {display_q}")
        print(f"        -> {display_r}")

    # Run all questions concurrently (limited by semaphore)
    tasks = [run_one(i, row) for i, row in enumerate(rows)]
    await asyncio.gather(*tasks)

    outfile.close()

    # Re-read and sort by original order, then rewrite without _idx
    sorted_rows = []
    with open(output_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sorted_rows.append(row)
    sorted_rows.sort(key=lambda r: int(r["_idx"]))

    final_fields = [f for f in output_fields if f != "_idx"]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=final_fields, extrasaction="ignore")
        writer.writeheader()
        for r in sorted_rows:
            writer.writerow(r)

    elapsed = time.time() - start_time
    print(f"\nWrote {completed['count']} results to {output_path} (sorted to original order)")
    print(f"Total time: {elapsed:.1f}s ({elapsed/completed['count']:.1f}s per question avg)")


if __name__ == "__main__":
    asyncio.run(main())
