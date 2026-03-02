import "dotenv/config";
import type { EvaluationResult } from "langsmith/evaluation";
import { evaluate } from "langsmith/evaluation";

// Dummy "app" that always returns a response mentioning OfficeFlow
const dummyApp = async (): Promise<Record<string, any>> => {
  return { response: "Sure! In OfficeFlow, you can reset your password from the settings page." };
}

// Code-based Eval — check if the response mentions "officeflow"
const mentionsOfficeflow = async ({ outputs }: {
  outputs: Record<string, any>;
}): Promise<EvaluationResult> => {
  const score = outputs?.response?.toLowerCase().includes("officeflow");
  return { key: "mentions_officeflow", score };
}

// Experiment
await evaluate(dummyApp, {
  data: "officeflow-dataset",
  evaluators: [mentionsOfficeflow],
});
