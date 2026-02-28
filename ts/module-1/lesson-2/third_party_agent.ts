import OpenAI from "openai";
import { wrapOpenAI } from "langsmith/wrappers";
import { traceable } from "langsmith/traceable";
import "dotenv/config";

const client = wrapOpenAI(new OpenAI());

const weatherRetriever = traceable(
  async () => {
    return "It is sunny today";
  },
  { run_type: "tool", name: "weatherRetriever" }
);

// Define the tool schema for OpenAI
const WEATHER_TOOL: OpenAI.ChatCompletionTool = {
  type: "function",
  function: {
    name: "weather_retriever",
    description: "Get the current weather conditions",
    parameters: {
      type: "object",
      properties: {},
      required: [],
    },
  },
};

const agent = traceable(
  async (question: string): Promise<string | null> => {
    const messages: OpenAI.ChatCompletionMessageParam[] = [
      { role: "user", content: question },
    ];

    // First API call with tool available
    let response = await client.chat.completions.create({
      model: "gpt-5-nano",
      messages,
      tools: [WEATHER_TOOL],
      tool_choice: "auto",
    });

    let responseMessage = response.choices[0].message;

    // Handle tool calls if the model wants to use them
    if (responseMessage.tool_calls) {
      // Add assistant's tool call to messages
      messages.push({
        role: "assistant",
        content: responseMessage.content || "",
        tool_calls: responseMessage.tool_calls.map((tc) => ({
          id: tc.id,
          type: tc.type,
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        })),
      });

      // Execute the tool call(s)
      for (const toolCall of responseMessage.tool_calls) {
        if (toolCall.function.name === "weather_retriever") {
          const result = await weatherRetriever();

          // Add tool result to messages
          messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            content: result,
          });
        }
      }

      // Make second API call with tool results
      response = await client.chat.completions.create({
        model: "gpt-5-nano",
        messages,
        tools: [WEATHER_TOOL],
        tool_choice: "auto",
      });
      responseMessage = response.choices[0].message;
    }

    messages.push({ role: "assistant", content: responseMessage.content || "" });
    return { messages, output: responseMessage.content };
  },
  { name: "agent" }
);

(async () => {
  const result = await agent("What is the weather today?");
  console.log(result.output);
})();
