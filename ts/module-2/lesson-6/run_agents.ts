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

  // Run experiment for agent v4
  console.log("\nRunning experiment for agent_v4...");
  const v4Results = await evaluate(chatWrapperV4, {
    data: DATASET_NAME,
    experimentPrefix: "agent-v4",
  });

  // Run experiment for agent v5
  console.log("\nRunning experiment for agent_v5...");
  const v5Results = await evaluate(chatWrapperV5, {
    data: DATASET_NAME,
    experimentPrefix: "agent-v5",
  });

  console.log(`\nv4 experiment: ${v4Results.experimentName}`);
  console.log(`v5 experiment: ${v5Results.experimentName}`);
  console.log("Done! Use these experiment names in the pairwise evaluation.");
}

await main();
