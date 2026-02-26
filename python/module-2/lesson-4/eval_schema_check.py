import json
from langsmith.schemas import Run, Example


def sql_starts_with_schema_check(run: Run, example: Example) -> dict:
    """Check that the first SQL query starts by discovering the DB schema.

    Only applies to examples where expected_tools includes 'query_database'.
    The first SQL tool call should be a schema discovery query
    (e.g. SELECT name FROM sqlite_master) before any data queries.
    """
    expected_tools = example.metadata.get("expected_tools", "")

    # Only evaluate examples that expect a database query
    if "query_database" not in expected_tools:
        return {
            "key": "sql_starts_with_schema_check",
            "score": None,
            "comment": f"Not applicable — expected_tools is '{expected_tools}'.",
        }

    messages = run.outputs.get("messages", [])

    # Collect all query_database calls in order
    sql_queries = []
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            if fn.get("name") == "query_database":
                try:
                    args = json.loads(fn["arguments"])
                    sql_queries.append(args.get("query", ""))
                except (json.JSONDecodeError, KeyError):
                    continue

    if not sql_queries:
        return {
            "key": "sql_starts_with_schema_check",
            "score": 0,
            "comment": "Expected query_database but no SQL queries were made.",
        }

    first_query = sql_queries[0].strip().lower()
    is_schema_check = "sqlite_master" in first_query or "pragma table_info" in first_query

    return {
        "key": "sql_starts_with_schema_check",
        "score": 1 if is_schema_check else 0,
        "comment": (
            f"First SQL query: {sql_queries[0]!r} — "
            + ("starts with schema discovery." if is_schema_check else "does NOT start with schema discovery.")
        ),
    }
