/**
 * Evaluator: Schema-Before-Query Check
 *
 * Checks that whenever the agent uses query_database, it first inspects
 * the database schema (via PRAGMA table_info or sqlite_master) before
 * running a data query. This ensures the agent doesn't blindly guess
 * column names.
 */
import type { Run } from "langsmith/schemas";

const SCHEMA_PATTERNS = [
  /PRAGMA\s+table_info/i,
  /SELECT\s+.*FROM\s+sqlite_master/i,
  /PRAGMA\s+database_list/i,
  /\.schema/i,
];

function isSchemaQuery(sql: string): boolean {
  /** Return true if the SQL is a schema-inspection query. */
  return SCHEMA_PATTERNS.some((pattern) => pattern.test(sql));
}

interface ToolCall {
  name: string;
  arguments: string;
}

function extractToolCalls(run: Run): ToolCall[] {
  /** Extract tool calls from run output messages. */
  const runOutputs = run.outputs ?? {};
  const messages: any[] = runOutputs.messages ?? [];

  const toolCalls: ToolCall[] = [];
  for (const msg of messages) {
    if (typeof msg === "object" && msg !== null) {
      for (const tc of msg.tool_calls ?? []) {
        const func = tc.function ?? {};
        toolCalls.push({
          name: func.name ?? "",
          arguments: func.arguments ?? "",
        });
      }
    }
  }
  return toolCalls;
}

export function schemaBeforeQuery(
  run: Run,
): { key: string; score: number; comment: string } {
  /**
   * Score 1 if the agent checks DB schema before querying data, 0 otherwise.
   *
   * If the agent never calls query_database, scores 1 (not applicable).
   */
  const toolCalls = extractToolCalls(run);

  const dbCalls = toolCalls.filter((tc) => tc.name === "query_database");

  // No database calls -- nothing to check
  if (dbCalls.length === 0) {
    return {
      key: "schema_before_query",
      score: 1,
      comment: "No query_database calls -- schema check not applicable",
    };
  }

  // Check if any schema query appears before the first non-schema data query
  let seenSchemaCheck = false;
  for (const tc of dbCalls) {
    const sql = tc.arguments ?? "";
    if (isSchemaQuery(sql)) {
      seenSchemaCheck = true;
    } else {
      // First real data query -- was there a schema check before it?
      if (!seenSchemaCheck) {
        return {
          key: "schema_before_query",
          score: 0,
          comment: `Agent queried data without checking schema first. First query: ${sql.slice(0, 200)}`,
        };
      }
      break; // Schema was checked before first data query -- pass
    }
  }

  if (seenSchemaCheck) {
    return { key: "schema_before_query", score: 1, comment: "Agent checked schema before querying data" };
  }

  return {
    key: "schema_before_query",
    score: 1,
    comment: "All query_database calls were schema inspections",
  };
}
