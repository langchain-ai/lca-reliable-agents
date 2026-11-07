"""Pre-generate embeddings for the knowledge base to speed up agent startup.

Run from the knowledge_base directory:  python generate_embeddings.py
"""
import asyncio
import json
import os
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

from kb_cache import docs_fingerprint, make_embedding_client, EMBEDDING_MODEL

load_dotenv()

# LangSmith gateway when LANGSMITH_API_KEY is set, otherwise OpenAI directly
client = make_embedding_client(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

DOCS_DIR = "./documents"
EMBEDDINGS_DIR = "./embeddings"


async def generate_embeddings():
    """Generate embeddings for whole documents."""
    docs_path = Path(DOCS_DIR)
    embeddings_path = Path(EMBEDDINGS_DIR)

    docs_hash = docs_fingerprint(docs_path)
    docs = []
    for file_path in docs_path.glob("*.md"):
        if file_path.name == "CHUNKING_NOTES.md":
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            docs.append((file_path.name, content))

    print(f"Generating embeddings for {len(docs)} documents...")
    embeddings = []
    for filename, content in docs:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=content
        )
        embeddings.append(response.data[0].embedding)
        print(f"  {filename}")

    cache_data = {
        "docs": docs,
        "embeddings": embeddings,
        # The agents compare this against the current documents to detect a stale cache
        "docs_hash": docs_hash,
    }
    embeddings_path.mkdir(parents=True, exist_ok=True)
    cache_path = embeddings_path / "embeddings.json"
    with open(cache_path, 'w') as f:
        json.dump(cache_data, f)
    print(f"\nSaved embeddings to {cache_path}")


async def main():
    await generate_embeddings()
    print("\nDone! Agents will now load embeddings from cache.")


if __name__ == "__main__":
    asyncio.run(main())
