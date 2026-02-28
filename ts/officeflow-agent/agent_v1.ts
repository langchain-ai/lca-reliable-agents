import dotenv from "dotenv";
import OpenAI from "openai";
import { traceable } from "langsmith/traceable";
import { wrapOpenAI } from "langsmith/wrappers";
import { uuid7 } from "langsmith";
import Database from "better-sqlite3";
import * as path from "path";
import * as fs from "fs";
import * as readline from "readline";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, "../.env") });

// Initialize clients
const client = wrapOpenAI(new OpenAI({ apiKey: process.env.OPENAI_API_KEY }));

// Configuration
const threadId = String(uuid7());

// Conversation history store (use a database in production)
const threadStore: Record<string, any[]> = {};

// Knowledge base storage (loaded on startup)
let knowledgeBaseDocs: [string, string][] = []; // List of [filename, content] tuples
let knowledgeBaseEmbeddings: number[][] = []; // Corresponding embeddings

const systemPrompt = `You are Emma, a customer support specialist for OfficeFlow Supply Co., a paper and office supplies distribution company serving small-to-medium businesses across North America.

ABOUT YOUR ROLE:
You're part of the Customer Experience team and have been with OfficeFlow for 3 years. You're known for being helpful, efficient, and genuinely caring about solving customer problems. Your manager emphasizes that every interaction is an opportunity to build trust and loyalty.

WHAT YOU CAN HELP WITH:
✓ Product Information - Answer questions about our catalog of office supplies, paper products, writing instruments, organizational tools, and desk accessories
✓ Inventory & Availability - Check current stock levels and help customers find what they need
✓ Product Recommendations - Suggest products based on customer needs, usage patterns, and budget
✓ General Inquiries - Handle questions about our company, product lines, and services

WHAT YOU CANNOT DIRECTLY HANDLE:
✗ Order Placement - While you can provide product info, actual ordering is done through our web portal or by contacting our sales team at sales@officeflow.com
✗ Order Status & Tracking - Direct customers to check their account portal or contact fulfillment@officeflow.com
✗ Returns & Refunds - These require approval from our Returns Department at returns@officeflow.com
✗ Account Changes - Billing, payment methods, and account settings must go through accounts@officeflow.com
✗ Technical Support - For website issues, direct to support@officeflow.com

YOUR COMMUNICATION STYLE:
- Warm and professional, never robotic or overly formal
- Use natural language - "I'd be happy to help" instead of "I will assist you"
- Show empathy when customers are frustrated
- Be specific and accurate with information
- If you don't know something, be honest and direct them to the right resource
- Use the customer's name if they provide it
- Keep responses concise but thorough

IMPORTANT - CHECK DATABASE FIRST:
When customers ask about products or inventory, ALWAYS check the database FIRST before asking clarifying questions. Give them useful information about what you find, rather than asking for more details upfront. For example, if a customer asks "do you have any paper?" - check what paper products are in stock and tell them what's available, don't ask "what type of paper are you looking for?"

INTERACTION GUIDELINES:
1. Always greet customers warmly and acknowledge their question
2. Ask clarifying questions only if truly necessary AFTER checking available information
3. Provide complete, accurate information about products and availability
4. If recommending products, explain why they're a good fit
5. End conversations by checking if they need anything else
6. When you can't help directly, provide the specific contact or resource they need
7. Never make up information - if you're unsure, say so and offer to connect them with someone who knows

YOUR TOOLS:
You have access to two powerful tools to help customers:

1. query_database - Use this for product-related questions:
   - Product availability and stock levels
   - Product prices and pricing information
   - Product details and specifications
   - Searching for specific items in inventory

2. search_knowledge_base - Use this for company policies and information:
   - Returns and refunds policies
   - Shipping and delivery information
   - Ordering process and payment methods
   - Store locations and contact information
   - Company background and general info
   - Business hours and holiday closures

Choose the right tool based on what the customer is asking about. For questions about specific products, use the database. For questions about policies, processes, or company information, use the knowledge base.

EXAMPLE INTERACTIONS:

Customer: "Do you have copy paper?"
You: "Yes, we do! We carry several types of copy paper. Are you looking for standard 8.5x11 inch letter size, or do you need a specific weight or finish? I can check what we have in stock."

Customer: "I need to return an order"
You: "I understand you need to process a return. While I can't handle returns directly, our Returns Department will be happy to help you. You can reach them at returns@officeflow.com or call 1-800-OFFICE-1 ext. 3. They typically respond within 4 business hours. Do you need any other information I can help with?"

Customer: "What's the best pen for signing documents?"
You: "For document signing, I'd recommend a pen with archival-quality ink that won't fade over time. Let me check what we have available that would work well for that purpose."

Remember: You represent OfficeFlow's commitment to excellent customer service. Be helpful, honest, and human in every interaction.`;

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

const queryDatabase = traceable(
  (query: string, dbPath: string): string => {
    try {
      const db = new Database(dbPath);
      const results = db.prepare(query).all();
      db.close();
      return JSON.stringify(results);
    } catch (e: any) {
      return `Error: ${e.message}`;
    }
  },
  { name: "query_database", run_type: "tool" }
);

function chunkText(text: string, chunkSize: number = 200, overlap: number = 20): string[] {
  const chunks: string[] = [];
  let start = 0;
  while (start < text.length) {
    const end = start + chunkSize;
    const chunk = text.slice(start, end);
    if (chunk.trim()) {
      chunks.push(chunk);
    }
    start = end - overlap;
  }
  return chunks;
}

async function loadKnowledgeBase(kbDir: string = "./knowledge_base"): Promise<void> {
  const kbPath = path.join(kbDir, "documents");
  const cachePath = path.join(kbDir, "embeddings", "embeddings.json");

  // Try to load from cache first
  if (fs.existsSync(cachePath)) {
    const cacheData = JSON.parse(fs.readFileSync(cachePath, "utf-8"));
    knowledgeBaseDocs = cacheData.docs.map((doc: [string, string]) => [doc[0], doc[1]] as [string, string]);
    knowledgeBaseEmbeddings = cacheData.embeddings;
    console.log(`Knowledge base loaded from cache: ${knowledgeBaseDocs.length} chunks`);
    return;
  }

  // Fall back to generating embeddings
  if (!fs.existsSync(kbPath)) {
    console.log(`Warning: Knowledge base directory '${kbDir}' not found`);
    return;
  }

  const chunks: [string, string][] = [];
  const files = fs.readdirSync(kbPath).filter(f => f.endsWith(".md"));
  for (const file of files) {
    if (file === "CHUNKING_NOTES.md") continue;
    const content = fs.readFileSync(path.join(kbPath, file), "utf-8");
    const fileChunks = chunkText(content);
    for (let i = 0; i < fileChunks.length; i++) {
      chunks.push([`${file}:chunk_${i}`, fileChunks[i]]);
    }
  }

  if (chunks.length === 0) {
    console.log(`Warning: No documents found in '${kbDir}'`);
    return;
  }

  knowledgeBaseDocs = chunks;

  console.log(`Generating embeddings for ${chunks.length} chunks...`);
  const embeddings: number[][] = [];
  for (const [chunkName, content] of chunks) {
    const response = await client.embeddings.create({
      model: "text-embedding-3-small",
      input: content,
    });
    embeddings.push(response.data[0].embedding);
  }

  knowledgeBaseEmbeddings = embeddings;
  console.log(`Knowledge base loaded: ${chunks.length} chunks indexed`);
}

const searchKnowledgeBase = traceable(
  async (query: string, topK: number = 2): Promise<string> => {
    if (knowledgeBaseDocs.length === 0 || knowledgeBaseEmbeddings.length === 0) {
      return "Error: Knowledge base not loaded";
    }

    // Generate embedding for query
    const response = await client.embeddings.create({
      model: "text-embedding-3-small",
      input: query,
    });
    const queryEmbedding = response.data[0].embedding;

    // Calculate cosine similarity with all documents
    const similarities: [number, number][] = [];
    for (let i = 0; i < knowledgeBaseEmbeddings.length; i++) {
      const similarity = cosineSimilarity(queryEmbedding, knowledgeBaseEmbeddings[i]);
      similarities.push([i, similarity]);
    }

    // Sort by similarity and get top k
    similarities.sort((a, b) => b[1] - a[1]);
    const topResults = similarities.slice(0, topK);

    // Format results
    const results: string[] = [];
    for (const [idx, score] of topResults) {
      const [filename, content] = knowledgeBaseDocs[idx];
      results.push(`=== ${filename} (relevance: ${score.toFixed(3)}) ===\n${content}\n`);
    }

    return results.join("\n");
  },
  { name: "search_knowledge_base", run_type: "tool" }
);

// OpenAI function calling schema
const QUERY_DATABASE_TOOL = {
  type: "function" as const,
  function: {
    name: "query_database",
    description: "SQL query to get information about our inventory for customers like products, quantities and prices.",
    parameters: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "SQL query to execute against the inventory database",
        },
      },
      required: ["query"],
    },
  },
};

const SEARCH_KNOWLEDGE_BASE_TOOL = {
  type: "function" as const,
  function: {
    name: "search_knowledge_base",
    description: "Search company knowledge base for information about policies, procedures, company info, shipping, returns, ordering, contact information, store locations, and business hours. Use this for non-product questions.",
    parameters: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Natural language question or search query about company policies or information",
        },
      },
      required: ["query"],
    },
  },
};

function getThreadHistory(threadId: string): any[] {
  return threadStore[threadId] || [];
}

function saveThreadHistory(threadId: string, messages: any[]): void {
  threadStore[threadId] = messages;
}

const chat = traceable(
  async (question: string): Promise<{ messages: any[]; output: string }> => {
    const dbPath = path.join(__dirname, "inventory", "inventory.db");
    const tools = [QUERY_DATABASE_TOOL, SEARCH_KNOWLEDGE_BASE_TOOL];

    // Fetch conversation history from local storage
    const historyMessages = getThreadHistory(threadId);

    // Build messages with history
    const messages: any[] = [
      { role: "system", content: systemPrompt },
      ...historyMessages,
      { role: "user", content: question },
    ];

    // First API call with tools
    let response = await client.chat.completions.create({
      model: "gpt-5-nano",
      messages,
      tools,
      tool_choice: "auto",
    });

    let responseMessage = response.choices[0].message;

    // Handle tool calls if the model wants to use them
    while (responseMessage.tool_calls) {
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
        const functionArgs = JSON.parse(toolCall.function.arguments);

        let result: string;
        if (toolCall.function.name === "query_database") {
          result = await queryDatabase(functionArgs.query, dbPath);
        } else if (toolCall.function.name === "search_knowledge_base") {
          result = await searchKnowledgeBase(functionArgs.query);
        } else {
          result = `Error: Unknown tool ${toolCall.function.name}`;
        }

        // Add tool result to messages
        messages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          name: toolCall.function.name,
          content: result,
        });
      }

      // Make next API call with tool results
      response = await client.chat.completions.create({
        model: "gpt-5-nano",
        messages,
        tools,
        tool_choice: "auto",
      });
      responseMessage = response.choices[0].message;
    }

    // Add final response to messages
    const finalContent = responseMessage.content;
    messages.push({
      role: "assistant",
      content: finalContent,
    });

    // Save conversation history (everything except system prompt)
    saveThreadHistory(threadId, messages.slice(1));

    return { messages, output: finalContent! };
  },
  { name: "Emma", metadata: { thread_id: threadId } }
);

async function main() {
  console.log("Office Supplies Support Chat");
  console.log("=".repeat(50));
  console.log(`Thread ID: ${threadId}`);
  console.log();

  // Load knowledge base on startup
  await loadKnowledgeBase(path.join(__dirname, "knowledge_base"));
  console.log();
  console.log("Type 'quit' or 'exit' to end the conversation\n");

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const askQuestion = (): void => {
    rl.question("You: ", async (userInput) => {
      userInput = userInput.trim();

      if (["quit", "exit", "q"].includes(userInput.toLowerCase())) {
        console.log("Thank you for chatting! Goodbye!");
        rl.close();
        return;
      }

      if (!userInput) {
        askQuestion();
        return;
      }

      const result = await chat(userInput);
      console.log(`\nAgent: ${result.output}\n`);
      askQuestion();
    });
  };

  askQuestion();
}

export { chat, loadKnowledgeBase };

main().catch(console.error);
