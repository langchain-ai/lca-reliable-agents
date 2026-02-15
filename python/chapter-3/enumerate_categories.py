"""
Enumerate all combinations of test categories and options.

Generates a CSV with one row per combination (cartesian product).
Edit the CATEGORIES list below to add/remove categories or options.

Usage:
    python enumerate_categories.py
    python enumerate_categories.py -o my_combos.csv
"""

import argparse
import csv
import itertools
from pathlib import Path

# ---------------------------------------------------------------------------
# Categories and options — edit these as needed
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        "name": "User_type",
        "options": [
            ("standard", "Standard consumer customer - normal, polite tone"),
            ("bulk_enterprise", "Bulk/enterprise buyer - professional, may mention company/volume needs"),
            ("frustrated", "Frustrated customer"),
        ],
    },
    {
        "name": "Information_type",
        "options": [
            ("product", "Product question (availability, pricing, recommendations)"),
            ("policy", "Policy question (returns, shipping, ordering, company info)"),
            ("out_of_scope", "Out-of-scope request (order placement, tracking, returns processing, account changes, tech support)"),
        ],
    },
    {
        "name": "Question_type",
        "options": [
            ("clear", "Clear and specific request - well-articulated question about one topic"),
            ("vague", "Vague or ambiguous - unclear what they're asking for, but still one question"),
            ("multi_intent", "Multiple questions or intents in one query - this is the ONLY case where multiple questions are allowed"),
        ],
    },
]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Enumerate all combinations of test categories"
    )
    parser.add_argument(
        "-o", "--output", default="category_combinations.csv",
        help="Output CSV path (default: category_combinations.csv)",
    )
    parser.add_argument(
        "-r", "--repeat", type=int, default=1,
        help="Repeat count per combination (default: 1)",
    )
    args = parser.parse_args()

    # Build header from category names
    header = [cat["name"] for cat in CATEGORIES] + ["repeat_count"]

    # Get just the option keys for each category
    option_keys = [[key for key, _ in cat["options"]] for cat in CATEGORIES]

    # Generate all combinations
    combos = list(itertools.product(*option_keys))

    # Write CSV
    output_path = Path(args.output)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for combo in combos:
            writer.writerow(list(combo) + [args.repeat])

    print(f"Generated {len(combos)} combinations")
    print(f"Categories: {' x '.join(str(len(cat['options'])) for cat in CATEGORIES)} = {len(combos)}")
    print(f"Wrote to {output_path}")


if __name__ == "__main__":
    main()
