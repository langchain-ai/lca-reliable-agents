"""
Tool Usage Evaluator for OfficeFlow Agent

Evaluates:
1. Did the agent call the correct tool based on expected_tools metadata?
2. If query_database was called, was the first SQL query a schema discovery?
"""

import json
import re
from langsmith.schemas import Run, Example


def extract_tool_calls(run: Run) -> list[dict]:
    """Extract tool calls from the run outputs messages."""
    messages = run.outputs.get("messages", [])
    tool_calls = []

    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg.get("tool_calls", []):
                if isinstance(tc, dict):
                    tool_calls.append({
                        "name": tc.get("function", {}).get("name"),
                        "arguments": tc.get("function", {}).get("arguments", "{}")
                    })

    return tool_calls


def is_schema_discovery_query(sql: str) -> bool:
    """Check if a SQL query is discovering the database schema."""
    sql_lower = sql.lower().strip()

    # Common schema discovery patterns
    patterns = [
        r"select\s+.*\s+from\s+sqlite_master",
        r"pragma\s+table_info",
        r"pragma\s+schema",
        r"select\s+name\s+from\s+sqlite_master",
        r"\.schema",
        r"\.tables",
    ]

    for pattern in patterns:
        if re.search(pattern, sql_lower):
            return True

    return False


def correct_tool_used(run: Run, example: Example) -> dict:
    """
    Evaluate if the agent called the correct tool based on expected_tools metadata.

    Returns:
        dict with key, score (0 or 1), and comment
    """
    expected_tools = example.metadata.get("expected_tools", "")
    tool_calls = extract_tool_calls(run)
    tools_called = [tc["name"] for tc in tool_calls]

    # Determine if correct tool was used
    if expected_tools == "no_tools":
        # Should not have called any tools
        score = 1 if len(tools_called) == 0 else 0
        comment = f"Expected no tools. Called: {tools_called if tools_called else 'none'}"

    elif expected_tools == "query_database":
        score = 1 if "query_database" in tools_called else 0
        comment = f"Expected query_database. Called: {tools_called if tools_called else 'none'}"

    elif expected_tools == "search_knowledge_base":
        score = 1 if "search_knowledge_base" in tools_called else 0
        comment = f"Expected search_knowledge_base. Called: {tools_called if tools_called else 'none'}"

    else:
        # Unknown expected_tools value
        score = 0
        comment = f"Unknown expected_tools value: {expected_tools}"

    return {
        "key": "correct_tool_used",
        "score": score,
        "comment": comment
    }


def schema_discovery_first(run: Run, example: Example) -> dict:
    """
    Evaluate if the first SQL query was a schema discovery query.

    Only applicable when query_database was expected and called.

    Returns:
        dict with key, score (0, 1, or None), and comment
    """
    expected_tools = example.metadata.get("expected_tools", "")
    tool_calls = extract_tool_calls(run)

    # Only evaluate if query_database was expected
    if expected_tools != "query_database":
        return {
            "key": "schema_discovery_first",
            "score": None,  # Not applicable
            "comment": "N/A - query_database not expected"
        }

    # Find all query_database calls
    db_calls = [tc for tc in tool_calls if tc["name"] == "query_database"]

    if not db_calls:
        return {
            "key": "schema_discovery_first",
            "score": 0,
            "comment": "query_database was expected but not called"
        }

    # Check if the first query was schema discovery
    first_call = db_calls[0]
    try:
        args = json.loads(first_call["arguments"])
        query = args.get("query", "")
    except json.JSONDecodeError:
        return {
            "key": "schema_discovery_first",
            "score": 0,
            "comment": "Could not parse query arguments"
        }

    is_schema = is_schema_discovery_query(query)

    return {
        "key": "schema_discovery_first",
        "score": 1 if is_schema else 0,
        "comment": f"First query: {query[:100]}{'...' if len(query) > 100 else ''}"
    }


# List of evaluators to use with evaluate()
evaluators = [correct_tool_used, schema_discovery_first]
