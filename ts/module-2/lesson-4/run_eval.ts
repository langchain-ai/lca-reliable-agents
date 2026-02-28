/**
 * Run the schema-before-query evaluator against the officeflow-dataset.
 *
 * Usage:
 *    npx tsx run_eval.ts
 */
import "dotenv/config";
import { evaluate } from "langsmith/evaluation";
import { uuid7 } from "langsmith";
import { chat, loadKnowledgeBase, setThreadId } from "../../officeflow-agent/agent_v5.js";
import { schemaBeforeQuery } from "./eval_schema_check.js";
import { fileURLToPath } from "url";
import * as path from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function setup(): Promise<void> {
  /** Load knowledge base before running evals. */
  const agentDir = path.resolve(__dirname, "..", "..", "officeflow-agent");
  const kbDir = path.join(agentDir, "knowledge_base");
  await loadKnowledgeBase(kbDir);
}

function runAgent(inputs: Record<string, any>): Promise<Record<string, any>> {
  /** Invoke the agent with a fresh thread_id each time. */
  setThreadId(uuid7().toString());
  return chat(inputs.question);
}

await setup();

const results = await evaluate(runAgent, {
  data: "officeflow-dataset",
  evaluators: [schemaBeforeQuery],
  experimentPrefix: "schema-check-v5",
});
