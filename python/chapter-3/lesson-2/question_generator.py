"""
Generate test questions for a customer service agent.

Reads a category combinations CSV (from enumerate_categories.py) and a PRD,
then uses an LLM to generate realistic customer questions. For each row,
generates repeat_count questions. The tool_used column is set by code, not
the LLM: "query_database" when Information_type is "product", otherwise empty.

Usage:
    python question_generator.py --prd PRD.md --combos category_combinations.csv
    python question_generator.py --prd PRD.md --combos category_combinations.csv -o my_questions.csv
"""

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Initialize Anthropic client
# ---------------------------------------------------------------------------
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = Anthropic(api_key=api_key)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are generating a realistic customer question for a customer service agent.

<PRD>
{prd}
</PRD>

<ProductInventory>
{inventory}
</ProductInventory>

The question must reflect ALL of the following characteristics:

- User type: {user_type_desc}
- Information type: {info_type_desc}
- Question type: {question_type_desc}

RULES:
- Write ONE question only.
- The question must feel natural — something a real person would type or say.
- The question must address ONE topic only, UNLESS Question_type is
  "multi_intent", in which case multiple topics are allowed.
- When generating product questions, reference items from the <ProductInventory>
  above. Use the product names naturally (a customer wouldn't say the SKU).
- Do NOT repeat or closely duplicate any previously generated question.

Return ONLY a valid JSON object — no markdown fences, no extra text:
{{"question": "the customer question"}}

{previous_questions_section}"""

# ---------------------------------------------------------------------------
# Option descriptions
# ---------------------------------------------------------------------------

USER_TYPE_DESC = {
    "standard": "Standard consumer customer — normal, polite tone",
    "bulk_enterprise": "Bulk/enterprise buyer — professional, may mention company or volume needs",
    "frustrated": "Mildly frustrated customer — a bit annoyed but still reasonable. Think 'had a bad day' not 'losing their mind'. They might express mild impatience or disappointment but remain civil and coherent.",
}

INFO_TYPE_DESC = {
    "product": "Product question (availability, pricing, recommendations for office supplies)",
    "policy": "Policy question (returns, shipping, ordering, company info, locations, hours)",
    "out_of_scope": "Out-of-scope request (order placement, order tracking, returns processing, account changes, tech support)",
}

QUESTION_TYPE_DESC = {
    "clear": "Clear and specific request — well-articulated question about one topic",
    "vague": "Vague or ambiguous — unclear what they're asking for, but still one question",
    "multi_intent": "Multiple questions or intents in one query",
}

# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def generate_question(
    prd: str,
    inventory: str,
    user_type: str,
    info_type: str,
    question_type: str,
    previous_questions: List[str],
) -> str:
    """Call the LLM to generate one question. Returns the question string."""

    # Build previous-questions section
    if previous_questions:
        pq_lines = [
            "IMPORTANT — DO NOT REPEAT. These questions have already been "
            "generated. Your new question must be DIFFERENT from all of them:"
        ]
        for i, q in enumerate(previous_questions, 1):
            pq_lines.append(f"  {i}. {q}")
        previous_questions_section = "\n".join(pq_lines)
    else:
        previous_questions_section = ""

    prompt = SYSTEM_PROMPT.format(
        prd=prd,
        inventory=inventory,
        user_type_desc=USER_TYPE_DESC.get(user_type, user_type),
        info_type_desc=INFO_TYPE_DESC.get(info_type, info_type),
        question_type_desc=QUESTION_TYPE_DESC.get(question_type, question_type),
        previous_questions_section=previous_questions_section,
    )

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=512,
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": "Generate one question now. Return ONLY valid JSON.",
                }
            ],
            temperature=0.9,
        )

        content = response.content[0].text.strip()

        # Strip markdown fences if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        result = json.loads(content)
        return result.get("question", "")

    except Exception as e:
        print(f"    Error: {e}")
        return "[Error generating question]"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate test questions from category combinations and a PRD"
    )
    parser.add_argument(
        "--prd", required=True, help="Path to the PRD markdown file"
    )
    parser.add_argument(
        "--combos", required=True,
        help="Path to the category combinations CSV (from enumerate_categories.py)",
    )
    parser.add_argument(
        "--inventory", default="sample_of_inventory_with_prices.csv",
        help="Path to product inventory CSV (default: sample_of_inventory_with_prices.csv)",
    )
    parser.add_argument(
        "-o", "--output", default="generated_questions.csv",
        help="Output CSV path (default: generated_questions.csv)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load PRD
    # ------------------------------------------------------------------
    prd_path = Path(args.prd)
    if not prd_path.exists():
        raise FileNotFoundError(f"PRD file not found: {prd_path}")
    prd_text = prd_path.read_text(encoding="utf-8")
    print(f"Loaded PRD from {prd_path}")

    # ------------------------------------------------------------------
    # Load inventory
    # ------------------------------------------------------------------
    inv_path = Path(args.inventory)
    if not inv_path.exists():
        print(f"Warning: Inventory file not found: {inv_path}")
        inventory_text = "No inventory sample available."
    else:
        inventory_text = inv_path.read_text(encoding="utf-8").strip()
        print(f"Loaded inventory from {inv_path}")

    # ------------------------------------------------------------------
    # Read combinations CSV
    # ------------------------------------------------------------------
    combos_path = Path(args.combos)
    if not combos_path.exists():
        raise FileNotFoundError(f"Combinations file not found: {combos_path}")

    rows = []
    with open(combos_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"Loaded {len(rows)} combinations from {combos_path}")

    # ------------------------------------------------------------------
    # Generate questions
    # ------------------------------------------------------------------
    results: List[Dict] = []
    previous_questions: List[str] = []

    total_questions = sum(int(row.get("repeat_count", 1)) for row in rows)
    print(f"\nGenerating {total_questions} questions ({len(rows)} combos)...\n")

    count = 0
    for row in rows:
        user_type = row["User_type"]
        info_type = row["Information_type"]
        question_type = row["Question_type"]
        repeat_count = int(row.get("repeat_count", 1))

        for r in range(repeat_count):
            count += 1
            print(f"  [{count}/{total_questions}] {user_type}, {info_type}, {question_type}", end="")
            if repeat_count > 1:
                print(f" (repeat {r+1}/{repeat_count})", end="")
            print(" ...", end=" ", flush=True)

            question = generate_question(
                prd=prd_text,
                inventory=inventory_text,
                user_type=user_type,
                info_type=info_type,
                question_type=question_type,
                previous_questions=previous_questions,
            )

            # tool_used is rule-based
            tool_used = "query_database" if info_type == "product" else ""

            results.append({
                "question": question,
                "User_type": user_type,
                "Information_type": info_type,
                "Question_type": question_type,
                "tool_used": tool_used,
            })

            # Track for dedup
            if question and not question.startswith("[Error"):
                previous_questions.append(question)

            # Truncate question for display
            display_q = question[:80] + "..." if len(question) > 80 else question
            print(f"done — {display_q}")

    # ------------------------------------------------------------------
    # Write output CSV
    # ------------------------------------------------------------------
    output_path = Path(args.output)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "User_type", "Information_type", "Question_type", "tool_used"])
        for r in results:
            writer.writerow([
                r["question"],
                r["User_type"],
                r["Information_type"],
                r["Question_type"],
                r["tool_used"],
            ])

    print(f"\nWrote {len(results)} questions to {output_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    tool_count = sum(1 for r in results if r["tool_used"])
    print(f"  With tool_used=query_database: {tool_count}")
    print(f"  Without tool_used: {len(results) - tool_count}")


if __name__ == "__main__":
    main()
