import OpenAI from "openai";
import { wrapOpenAI } from "langsmith/wrappers";

type Environment = Record<string, string | undefined>;

export function gatewayURL(env: Environment = process.env): string | undefined {
  const value = env.LANGSMITH_GATEWAY;
  if (!value || ["false", "0", "no"].includes(value.toLowerCase())) return;
  const base = ["true", "1", "yes"].includes(value.toLowerCase())
    ? "https://gateway.smith.langchain.com"
    : value.replace(/\/+$/, "");
  return `${base}/openai/v1`;
}

export function validKey(value: string | undefined): boolean {
  return Boolean(value?.trim() && !/your_|your-|_here|\.\.\.|…|\*{4}|[<>]|changeme|placeholder/i.test(value));
}

export function requiredAPIKeys(env: Environment = process.env): string[] {
  const keys = [gatewayURL(env)
    ? (env.LANGSMITH_GATEWAY_API_KEY ? "LANGSMITH_GATEWAY_API_KEY" : "LANGSMITH_API_KEY")
    : "OPENAI_API_KEY"];
  if (env.LANGSMITH_TRACING?.toLowerCase() === "true") keys.push("LANGSMITH_API_KEY");
  return [...new Set(keys)];
}

export function openAIChatOptions(env: Environment = process.env) {
  const baseURL = gatewayURL(env);
  const keyName = baseURL
    ? (env.LANGSMITH_GATEWAY_API_KEY ? "LANGSMITH_GATEWAY_API_KEY" : "LANGSMITH_API_KEY")
    : "OPENAI_API_KEY";
  if (!validKey(env[keyName])) {
    throw new Error(`Set ${keyName} to a non-empty API key, not a template placeholder`);
  }
  return { apiKey: env[keyName], ...(baseURL ? { baseURL } : {}) };
}

const embeddingClients = new Map<boolean, OpenAI>();

export function embeddingClient(traced = true): OpenAI {
  if (!validKey(process.env.OPENAI_API_KEY)) {
    throw new Error("Knowledge-base embeddings require a direct OPENAI_API_KEY");
  }
  let client = embeddingClients.get(traced);
  if (!client) {
    client = new OpenAI();
    if (traced) client = wrapOpenAI(client);
    embeddingClients.set(traced, client);
  }
  return client;
}
