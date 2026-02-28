"""
Evaluator: Schema-Before-Query Check

Checks that whenever the agent uses query_database, it first inspects
the database schema (via PRAGMA table_info or sqlite_master) before
running a data query. This ensures the agent doesn't blindly guess
column names.
"""
import re


SCHEMA_PATTERNS = [
    r"PRAGMA\s+table_info",
    r"SELECT\s+.*FROM\s+sqlite_master",
    r"PRAGMA\s+database_list",
    r"\.schema",
]


def _is_schema_query(sql: str) -> bool:
    """Return True if the SQL is a schema-inspection query."""
    for pattern in SCHEMA_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            return True
    return False


def _extract_tool_calls(run) -> list[dict]:
    """Extract tool calls from run output messages."""
    run_outputs = run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}
    messages = run_outputs.get("messages", [])

    tool_calls = []
    for msg in messages:
        if isinstance(msg, dict):
            for tc in msg.get("tool_calls", []):
                func = tc.get("function", {})
                tool_calls.append({
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", ""),
                })
    return tool_calls


def schema_before_query(run, example) -> dict:
    """Score 1 if the agent checks DB schema before querying data, 0 otherwise.

    If the agent never calls query_database, scores 1 (not applicable).
    """
    tool_calls = _extract_tool_calls(run)

    db_calls = [tc for tc in tool_calls if tc["name"] == "query_database"]

    # No database calls — nothing to check
    if not db_calls:
        return {"score": 1, "comment": "No query_database calls — schema check not applicable"}

    # Check if any schema query appears before the first non-schema data query
    seen_schema_check = False
    for tc in db_calls:
        sql = tc.get("arguments", "")
        if _is_schema_query(sql):
            seen_schema_check = True
        else:
            # First real data query — was there a schema check before it?
            if not seen_schema_check:
                return {
                    "score": 0,
                    "comment": f"Agent queried data without checking schema first. First query: {sql[:200]}",
                }
            break  # Schema was checked before first data query — pass

    if seen_schema_check:
        return {"score": 1, "comment": "Agent checked schema before querying data"}

    return {"score": 1, "comment": "All query_database calls were schema inspections"}
