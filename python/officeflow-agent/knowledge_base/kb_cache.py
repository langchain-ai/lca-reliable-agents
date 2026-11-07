"""Shared helpers for the knowledge-base embedding cache (used by the agents and generate_embeddings.py)."""
import hashlib
import os
from pathlib import Path

from openai import AsyncOpenAI
from langsmith.wrappers import wrap_openai

# Embeddings are served by the LangSmith gateway's OpenAI direct-access path. The unified /v1 endpoints
# have no embeddings route, and the model ID must be bare ("text-embedding-3-small", no "openai/" prefix).
GATEWAY_OPENAI_URL = "https://gateway.smith.langchain.com/openai/v1"
EMBEDDING_MODEL = "text-embedding-3-small"
_SKIPPED_DOCS = {"CHUNKING_NOTES.md"}


def docs_fingerprint(docs_dir: Path) -> str:
    """Hash of every knowledge-base document's name and content.

    File mtimes can't be trusted: git checkouts and CI give every file the same mtime, which made the old
    mtime check report a stale cache as fresh.
    """
    h = hashlib.sha256()
    for path in sorted(Path(docs_dir).glob("*.md")):
        if path.name in _SKIPPED_DOCS:
            continue
        h.update(path.name.encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def make_embedding_client(fallback: AsyncOpenAI):
    """Gateway client when LANGSMITH_API_KEY is set, otherwise the given direct OpenAI client."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        return fallback
    return wrap_openai(AsyncOpenAI(base_url=GATEWAY_OPENAI_URL, api_key=api_key))
