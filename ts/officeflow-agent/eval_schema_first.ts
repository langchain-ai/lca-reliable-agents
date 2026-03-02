interface RunOutputs {
  messages?: any[];
  [key: string]: any;
}

interface Run {
  outputs?: RunOutputs;
}

export function schemaFirstEvaluator(run: Run): { score: number | null; comment: string } {
  const runOutputs: RunOutputs = (run as any).outputs ?? (run as any)?.get?.("outputs") ?? {};
  const messages: any[] = runOutputs.messages ?? [];

  // Extract all query_database SQL queries in order
  const sqlQueries: string[] = [];
  for (const msg of messages) {
    if (msg.role !== "assistant") continue;
    for (const tc of msg.tool_calls ?? []) {
      const fn = tc.function ?? {};
      if (fn.name === "query_database") {
        try {
          const args = JSON.parse(fn.arguments);
          if (args.query) {
            sqlQueries.push(args.query);
          }
        } catch {
          continue;
        }
      }
    }
  }

  // No SQL queries made - not applicable
  if (sqlQueries.length === 0) {
    return { score: null, comment: "No query_database calls were made." };
  }

  const firstQuery = sqlQueries[0].trim().toLowerCase();
  const isSchema = firstQuery.includes("sqlite_master") || firstQuery.includes("pragma table_info");

  return {
    score: isSchema ? 1 : 0,
    comment:
      `First SQL query: ${JSON.stringify(sqlQueries[0])} — ` +
      (isSchema ? "starts with schema discovery." : "does NOT start with schema discovery."),
  };
}
