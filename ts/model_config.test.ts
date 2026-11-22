import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import dotenv from "dotenv";
import OpenAI from "openai";
import { embeddingClient, gatewayURL, openAIChatOptions, requiredAPIKeys } from "./model_config.js";

test("direct flags use only the OpenAI credential for chat", () => {
  for (const flag of [undefined, "", "false", "FALSE", "0", "no"]) {
    const env = { LANGSMITH_GATEWAY: flag, OPENAI_API_KEY: "provider-key" };
    assert.equal(gatewayURL(env), undefined);
    assert.deepEqual(openAIChatOptions(env), { apiKey: "provider-key" });
    assert.deepEqual(requiredAPIKeys(env), ["OPENAI_API_KEY"]);
  }
});

test("Gateway flags, custom URLs, overrides, and tracing are independent", () => {
  for (const flag of ["true", "TRUE", "1", "yes", "YeS"]) {
    const env = { LANGSMITH_GATEWAY: flag, LANGSMITH_API_KEY: "ls-key" };
    assert.deepEqual(openAIChatOptions(env), {
      apiKey: "ls-key", baseURL: "https://gateway.smith.langchain.com/openai/v1",
    });
    assert.deepEqual(requiredAPIKeys(env), ["LANGSMITH_API_KEY"]);
  }
  const env = {
    LANGSMITH_GATEWAY: "http://localhost:8080/custom/",
    LANGSMITH_GATEWAY_API_KEY: "inference-key", LANGSMITH_API_KEY: "tracing-key",
    LANGSMITH_TRACING: "false",
  };
  assert.deepEqual(openAIChatOptions(env), {
    apiKey: "inference-key", baseURL: "http://localhost:8080/custom/openai/v1",
  });
  assert.deepEqual(requiredAPIKeys(env), ["LANGSMITH_GATEWAY_API_KEY"]);
  env.LANGSMITH_TRACING = "true";
  assert.deepEqual(requiredAPIKeys(env), ["LANGSMITH_GATEWAY_API_KEY", "LANGSMITH_API_KEY"]);
  env.LANGSMITH_GATEWAY_API_KEY = "";
  assert.equal(openAIChatOptions(env).apiKey, "tracing-key");
});

test("missing, blank, and placeholder credentials fail without provider fallback", () => {
  for (const [flag, key] of [["false", "OPENAI_API_KEY"], ["true", "LANGSMITH_API_KEY"]]) {
    for (const value of [undefined, "", " ", "your_api_key_here", "sk-proj-...", "lsv2_pt_...", "your-openai-api-key", "your-langsmith-key", "****", "<api-key>", "changeme", "placeholder"]) {
      assert.throws(() => openAIChatOptions({ LANGSMITH_GATEWAY: flag, [key]: value }), new RegExp(key));
    }
  }
  assert.throws(() => openAIChatOptions({
    LANGSMITH_GATEWAY: "true", LANGSMITH_GATEWAY_API_KEY: "your_key_here", LANGSMITH_API_KEY: "valid-key",
  }), /LANGSMITH_GATEWAY_API_KEY/);
});

test("dotenv loads Gateway configuration but does not overwrite shell values", () => {
  const saved = { ...process.env };
  const folder = mkdtempSync(path.join(tmpdir(), "course-gateway-"));
  try {
    for (const key of Object.keys(process.env)) delete process.env[key];
    const file = path.join(folder, ".env");
    writeFileSync(file, "LANGSMITH_GATEWAY=true\nLANGSMITH_API_KEY=file-key\nLANGSMITH_TRACING=false\n");
    dotenv.config({ path: file });
    assert.equal(openAIChatOptions().apiKey, "file-key");
    process.env.LANGSMITH_GATEWAY = "false";
    process.env.OPENAI_API_KEY = "shell-key";
    dotenv.config({ path: file });
    assert.deepEqual(openAIChatOptions(), { apiKey: "shell-key" });
    process.env.LANGSMITH_GATEWAY = "true";
    const client = embeddingClient(false);
    assert.equal(client.apiKey, "shell-key");
    assert.equal(client.baseURL, "https://api.openai.com/v1");
  } finally {
    for (const key of Object.keys(process.env)) delete process.env[key];
    Object.assign(process.env, saved);
    rmSync(folder, { recursive: true });
  }
});

test("installed raw SDK sends chat to the provider Gateway path with its credential", async () => {
  const client = new OpenAI({
    ...openAIChatOptions({ LANGSMITH_GATEWAY: "true", LANGSMITH_API_KEY: "ls-key" }),
    fetch: async (url, options) => {
      assert.equal(String(url), "https://gateway.smith.langchain.com/openai/v1/chat/completions");
      assert.equal(new Headers(options?.headers).get("Authorization"), "Bearer ls-key");
      return new Response(JSON.stringify({ id: "test", choices: [], object: "chat.completion", created: 0, model: "gpt-5-nano" }), { headers: { "Content-Type": "application/json" } });
    },
  });
  await client.chat.completions.create({ model: "gpt-5-nano", messages: [{ role: "user", content: "hello" }] });
});

test("all raw chat entrypoints use the helper and keep embeddings separate", () => {
  const files = [
    "module-1/lesson-2/thread_agent.ts", "module-1/lesson-2/third_party_agent.ts",
    "module-2/lesson-6/eval_conciseness_pairwise.ts", "eval_conciseness_pairwise.ts",
    ...Array.from({ length: 6 }, (_, i) => `officeflow-agent/agent_v${i}.ts`),
  ];
  for (const file of files) {
    const source = readFileSync(new URL(file, import.meta.url), "utf8");
    assert.ok(source.includes("new OpenAI(openAIChatOptions())"), file);
    assert.ok(!source.includes("client.embeddings.create("), file);
  }
});
