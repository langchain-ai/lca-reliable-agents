"""
Database Query Usage Evaluator for LangSmith

Evaluates whether the agent correctly queried the database according to tool description rules.
"""

from langsmith.schemas import Run, Example


def extract_database_queries(run: Run) -> list[str]:
    """Extract all database queries from a trace."""
    queries = []

    def traverse_run(r: Run):
        # Check if this run called query_database
        if r.name == "query_database" and r.inputs:
            query = r.inputs.get("query", "")
            if query:
                queries.append(query)

        # Traverse child runs
        if hasattr(r, 'child_runs') and r.child_runs:
            for child in r.child_runs:
                traverse_run(child)

    traverse_run(run)
    return queries


def evaluate_database_usage(run: Run, example: Example) -> dict:
    """
    Evaluate whether the agent:
    1. Queried the database when appropriate
    2. Followed tool description rules for schema discovery and search patterns
    """

    # Extract all database queries from the trace
    queries = extract_database_queries(run)

    if not queries:
        return {
            "key": "database_query_usage",
            "score": 0,
            "comment": "Agent did not query the database"
        }

    # Check rules
    issues = []
    good_practices = []

    # Check if schema discovery happened
    has_schema_discovery = False
    has_table_query = any("sqlite_master" in q.lower() for q in queries)
    has_pragma = any("pragma" in q.lower() for q in queries)

    if has_table_query or has_pragma:
        has_schema_discovery = True
        good_practices.append("Performed schema discovery")

    # Check for proper wildcard usage in LIKE clauses
    for i, query in enumerate(queries, 1):
        query_lower = query.lower()

        if "like" in query_lower:
            # Check for improper patterns (keyword% without leading %)
            if "like '" in query_lower or 'like "' in query_lower:
                # Extract the pattern after LIKE
                import re
                # Find LIKE patterns
                patterns = re.findall(r"like\s+['\"]([^'\"]+)['\"]", query_lower)

                for pattern in patterns:
                    # Skip schema discovery queries
                    if pattern == "table" or "sqlite" in query_lower:
                        continue

                    # Check if it has wildcards on both sides
                    if pattern.startswith("%") and pattern.endswith("%"):
                        good_practices.append(f"Query {i}: Used wildcards on both sides: {pattern}")
                    elif pattern.endswith("%") and not pattern.startswith("%"):
                        issues.append(f"Query {i}: Used only trailing wildcard: {pattern} (should be %keyword%)")
                    elif not "%" in pattern:
                        issues.append(f"Query {i}: No wildcards used: {pattern}")

        # Check for case-insensitive search using LOWER()
        if "like" in query_lower and "lower(" in query_lower:
            good_practices.append(f"Query {i}: Used LOWER() for case-insensitive search")
        elif "like" in query_lower and "lower(" not in query_lower and "sqlite_master" not in query_lower:
            # Only flag if it's a text search, not schema discovery
            if any(keyword in query_lower for keyword in ["paper", "pen", "stapler", "folder", "notebook", "cartridge"]):
                issues.append(f"Query {i}: Did not use LOWER() for case-insensitive text search")

    # Calculate score
    score = 1 if len(issues) == 0 else 0

    # Build comment
    comment_parts = []
    comment_parts.append(f"Executed {len(queries)} database queries")

    if has_schema_discovery:
        comment_parts.append("✓ Performed schema discovery")
    else:
        comment_parts.append("✗ Did not perform schema discovery")

    if good_practices:
        comment_parts.append("\n\nGood practices:")
        comment_parts.extend([f"  ✓ {p}" for p in good_practices])

    if issues:
        comment_parts.append("\n\nIssues found:")
        comment_parts.extend([f"  ✗ {i}" for i in issues])

    comment_parts.append("\n\nQueries executed:")
    for i, q in enumerate(queries, 1):
        comment_parts.append(f"  {i}. {q}")

    return {
        "key": "database_query_usage",
        "score": score,
        "comment": "\n".join(comment_parts)
    }




if __name__ == "__main__":
    # Example usage
    print("Database Query Usage Evaluator")
    print("=" * 50)
    print("\nThis evaluator checks:")
    print("1. Whether the agent queried the database")
    print("2. Whether they followed tool description rules:")
    print("   - Schema discovery first")
    print("   - Wildcards on BOTH sides: LIKE '%keyword%'")
    print("   - Case-insensitive search: LOWER(column)")
    print("\nTo use with LangSmith:")
    print("  from eval_database_usage import evaluate_database_usage")
    print("  results = evaluate(dataset_name, evaluators=[evaluate_database_usage])")
