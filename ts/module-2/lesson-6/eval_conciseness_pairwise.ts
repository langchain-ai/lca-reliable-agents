import OpenAI from "openai";
import { evaluate } from "langsmith/evaluation";
import type { Run } from "langsmith/schemas";

const openai = new OpenAI();

const CONCISENESS_PROMPT = `You are evaluating two responses to the same customer question.
Determine which response is MORE CONCISE while still providing all crucial information.

**Conciseness** means getting straight to the point, avoiding filler, and not repeating information.
**Crucial information** includes direct answers, necessary context, and required next steps.

A shorter response is NOT automatically better if it omits crucial information.

**Question:** {question}

**Response A:**
{response_a}

**Response B:**
{response_b}

Output your verdict as a single number:
1 if Response A is more concise while preserving crucial information
2 if Response B is more concise while preserving crucial information
0 if they are roughly equal`;

export async function concisenessEvaluator({
  inputs,
  runs,
}: {
  inputs: Record<string, any>;
  runs: Run[];
}) {
  const [runA, runB] = runs;
  const scores: Record<string, number> = {};

  const response = await openai.chat.completions.create({
    model: "gpt-5-nano",
    messages: [
      {
        role: "system",
        content:
          "You are a conciseness evaluator. Respond with only a single number: 0, 1, or 2.",
      },
      {
        role: "user",
        content: CONCISENESS_PROMPT.replace("{question}", inputs.question)
          .replace("{response_a}", runA?.outputs?.answer ?? "N/A")
          .replace("{response_b}", runB?.outputs?.answer ?? "N/A"),
      },
    ],
  });

  const preference = parseInt(
    response.choices[0].message.content?.trim() ?? "0"
  );

  if (preference === 1) {
    scores[runA.id] = 1;
    scores[runB.id] = 0;
  } else if (preference === 2) {
    scores[runA.id] = 0;
    scores[runB.id] = 1;
  } else {
    scores[runA.id] = 0;
    scores[runB.id] = 0;
  }

  return { key: "conciseness", scores };
}

// When run directly as a script
const isMainModule = process.argv[1]?.endsWith("eval_conciseness_pairwise");
if (isMainModule) {
  await evaluate(["agent-v4-experiment", "agent-v5-experiment"], {
    evaluators: [concisenessEvaluator],
    randomizeOrder: true,
  });
}
