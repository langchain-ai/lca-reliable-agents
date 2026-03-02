import OpenAI from "openai";
import { wrapOpenAI } from "langsmith/wrappers";
import { traceable } from "langsmith/traceable";
import { uuid7 } from "langsmith";
import "dotenv/config";

// Initialize clients
const client = wrapOpenAI(new OpenAI());

// Configuration
const THREAD_ID = uuid7();

// Conversation history store (use a database in production)
const threadStore: Record<string, any[]> = {};

function getThreadHistory(threadId: string): any[] {
  return threadStore[threadId] || [];
}

function saveThreadHistory(threadId: string, messages: any[]): void {
  threadStore[threadId] = messages;
}

const chatPipeline = traceable(
  async (messages: OpenAI.ChatCompletionMessageParam[]) => {
    // Automatically fetch history if it exists
    const historyMessages = getThreadHistory(THREAD_ID);

    // Combine history with new messages
    const allMessages = [...historyMessages, ...messages];

    // Invoke the model
    const chatCompletion = await client.chat.completions.create({
      model: "gpt-5-nano",
      messages: allMessages,
    });

    // Save and return the complete conversation including input and response
    const responseMessage = chatCompletion.choices[0].message;
    const fullConversation = [
      ...allMessages,
      { role: responseMessage.role, content: responseMessage.content },
    ];
    saveThreadHistory(THREAD_ID, fullConversation);

    return {
      messages: fullConversation,
    };
  },
  { name: "Name Agent", metadata: { thread_id: THREAD_ID } }
);

(async () => {
  // First message
  let messages: any[] = [{ content: "Hi, my name is Sally", role: "user" }];
  let result = await chatPipeline(messages);
  console.log(result.messages[result.messages.length - 1]);

  // Follow up message - agent should remember the name
  messages = [{ content: "What's my name?", role: "user" }];
  result = await chatPipeline(messages);
  console.log(result.messages[result.messages.length - 1]);
})();
