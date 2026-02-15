"""
Run generated questions through an agent and save results.

Reads a questions CSV (from question_generator.py), runs each question
through the agent, and writes an output CSV with the agent's response.

Usage:
    uv run python run_questions.py --questions test_questions.csv
    uv run python run_questions.py --questions test_questions.csv -o custom_results.csv
"""

import argparse
import asyncio
import csv
from pathlib import Path
from typing import Dict, List


async def main():
    parser = argparse.ArgumentParser(
        description="Run questions through an agent and save results"
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
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "officeflow_agent"))
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
    print(f"Output will be written to {output_path}\n")

    # Run each question through the agent
    results: List[Dict] = []
    for i, row in enumerate(rows):
        question = row["question"]
        display_q = question[:80] + "..." if len(question) > 80 else question
        print(f"  [{i+1}/{len(rows)}] {display_q}")

        try:
            result = await chat(question)
            response = result["output"]
        except Exception as e:
            print(f"    Error: {e}")
            response = f"[Error: {e}]"

        result = dict(row)
        result["agent_response"] = response
        results.append(result)

        display_r = response[:80] + "..." if len(response) > 80 else response
        print(f"           -> {display_r}\n")

    # Write output CSV
    output_fields = list(fieldnames) + ["agent_response"]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"Wrote {len(results)} results to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
