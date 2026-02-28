import "dotenv/config";
import { evaluate } from "langsmith/evaluation";
import {
  chat as chatV4,
  loadKnowledgeBase as loadKbV4,
} from "../../officeflow-agent/agent_v4.js";
import {
  chat as chatV5,
  loadKnowledgeBase as loadKbV5,
} from "../../officeflow-agent/agent_v5.js";
import { concisenessEvaluator } from "./eval_conciseness_pairwise.js";

const DATASET_NAME = "officeflow-dataset";

async function chatWrapperV4(
  inputs: Record<string, any>
): Promise<Record<string, any>> {
  const question = inputs.question ?? "";
  const result = await chatV4(question);
  return { answer: result.output };
}

async function chatWrapperV5(
  inputs: Record<string, any>
): Promise<Record<string, any>> {
  const question = inputs.question ?? "";
  const result = await chatV5(question);
  return { answer: result.output };
}

async function main(): Promise<void> {
  // Load knowledge bases for both agents
  console.log("Loading knowledge bases...");
  await loadKbV4();
  await loadKbV5();

  // Step 1: Run experiment for agent v4
  console.log("\n" + "=".repeat(50));
  console.log("Running experiment for agent_v4...");
  console.log("=".repeat(50));
  const v4Results = await evaluate(chatWrapperV4, {
    data: DATASET_NAME,
    experimentPrefix: "agent-v4",
  });

  // Step 2: Run experiment for agent v5
  console.log("\n" + "=".repeat(50));
  console.log("Running experiment for agent_v5...");
  console.log("=".repeat(50));
  const v5Results = await evaluate(chatWrapperV5, {
    data: DATASET_NAME,
    experimentPrefix: "agent-v5",
  });

  // Get experiment names from results
  const v4Experiment = v4Results.experimentName;
  const v5Experiment = v5Results.experimentName;

  console.log(`\nv4 experiment: ${v4Experiment}`);
  console.log(`v5 experiment: ${v5Experiment}`);

  // Step 3: Run pairwise evaluation
  console.log("\n" + "=".repeat(50));
  console.log("Running pairwise evaluation...");
  console.log("=".repeat(50));
  await evaluate([v4Experiment, v5Experiment], {
    evaluators: [concisenessEvaluator],
    randomizeOrder: true,
  });

  console.log("\n" + "=".repeat(50));
  console.log("Done! Check LangSmith for results.");
  console.log("=".repeat(50));
}

await main();
