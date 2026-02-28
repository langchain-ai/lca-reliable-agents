/**
 * Pre-generate embeddings for the knowledge base to speed up agent startup.
 */
import dotenv from "dotenv";
import OpenAI from "openai";
import * as path from "path";
import * as fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const DOCS_DIR = path.join(__dirname, "documents");
const EMBEDDINGS_DIR = path.join(__dirname, "embeddings");

async function generateEmbeddings(): Promise<void> {
  const docs: [string, string][] = [];
  const files = fs.readdirSync(DOCS_DIR).filter(f => f.endsWith(".md"));
  for (const file of files) {
    if (file === "CHUNKING_NOTES.md") continue;
    const content = fs.readFileSync(path.join(DOCS_DIR, file), "utf-8");
    docs.push([file, content]);
  }

  console.log(`Generating embeddings for ${docs.length} documents...`);
  const embeddings: number[][] = [];
  for (const [filename, content] of docs) {
    const response = await client.embeddings.create({
      model: "text-embedding-3-small",
      input: content,
    });
    embeddings.push(response.data[0].embedding);
    console.log(`  ${filename}`);
  }

  const cacheData = {
    docs,
    embeddings,
  };
  const cachePath = path.join(EMBEDDINGS_DIR, "embeddings.json");
  fs.writeFileSync(cachePath, JSON.stringify(cacheData));
  console.log(`\nSaved embeddings to ${cachePath}`);
}

async function main(): Promise<void> {
  await generateEmbeddings();
  console.log("\nDone! Agents will now load embeddings from cache.");
}

main().catch(console.error);
