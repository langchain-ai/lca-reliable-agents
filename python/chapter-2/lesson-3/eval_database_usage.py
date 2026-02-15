"""
Database Query Usage Evaluator for LangSmith

Evaluates whether the agent correctly queried the database.
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
    Evaluate whether the agent queried the database when appropriate.
    """

    # Extract all database queries from the trace
    queries = extract_database_queries(run)

    if not queries:
        return {
            "key": "database_query_usage",
            "score": 0,
            "comment": "Agent did not query the database"
        }

    # Build comment
    comment_parts = []
    comment_parts.append(f"Executed {len(queries)} database queries")

    comment_parts.append("\n\nQueries executed:")
    for i, q in enumerate(queries, 1):
        comment_parts.append(f"  {i}. {q}")

    return {
        "key": "database_query_usage",
        "score": 1,
        "comment": "\n".join(comment_parts)
    }




if __name__ == "__main__":
    # Example usage
    print("Database Query Usage Evaluator")
    print("=" * 50)
    print("\nThis evaluator checks:")
    print("1. Whether the agent queried the database")
    print("\nTo use with LangSmith:")
    print("  from eval_database_usage import evaluate_database_usage")
    print("  results = evaluate(dataset_name, evaluators=[evaluate_database_usage])")
