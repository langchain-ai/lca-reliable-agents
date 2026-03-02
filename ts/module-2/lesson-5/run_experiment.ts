import "dotenv/config";

import { fileURLToPath } from "node:url";
import path from "node:path";

import { evaluate } from "langsmith/evaluation";
import { chat, loadKnowledgeBase } from "../../officeflow-agent/agent_v4.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Dataset with bound evaluator in UI
const datasetName = "officeflow-dataset";

async function chatWrapper(
  inputs: Record<string, any>
): Promise<Record<string, any>> {
  /** Wrapper to adapt dataset inputs to chat function signature. */
  const question = inputs.question ?? "";
  const result = await chat(question);
  return { answer: result.output, messages: result.messages };
}

async function main(): Promise<void> {
  // Load knowledge base before running evaluation
  const kbPath = path.resolve(
    __dirname,
    "..",
    "..",
    "officeflow-agent",
    "knowledge_base"
  );
  console.log(`Loading knowledge base from ${kbPath}...`);
  await loadKnowledgeBase(kbPath);
  console.log();

  // Evaluator bound to dataset will run automatically
  const results = await evaluate(chatWrapper, {
    data: datasetName,
  });
  console.log(`Evaluation complete! Results: ${results}`);
  return;
}

await main();
