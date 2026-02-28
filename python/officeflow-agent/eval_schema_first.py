import json


def schema_first_evaluator(run, example):
    """Check that the agent's first SQL query is a schema discovery query.

    Extracts all query_database tool calls from the run output messages
    and verifies the first one discovers the DB schema (e.g., sqlite_master
    or PRAGMA table_info) before making data queries.
    """
    run_outputs = run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}
    messages = run_outputs.get("messages", [])

    # Extract all query_database SQL queries in order
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

    # No SQL queries made — not applicable
    if not sql_queries:
        return {"score": None, "comment": "No query_database calls were made."}

    first_query = sql_queries[0].strip().lower()
    is_schema = "sqlite_master" in first_query or "pragma table_info" in first_query

    return {
        "score": 1 if is_schema else 0,
        "comment": (
            f"First SQL query: {sql_queries[0]!r} — "
            + ("starts with schema discovery." if is_schema else "does NOT start with schema discovery.")
        ),
    }
