import os
from collections.abc import Mapping
from functools import lru_cache

GATEWAY_URL = "https://gateway.smith.langchain.com"


def gateway_url(env: Mapping[str, str] | None = None) -> str | None:
    env = os.environ if env is None else env
    value = env.get("LANGSMITH_GATEWAY", "")
    if not value or value.lower() in {"false", "0", "no"}:
        return None
    base = GATEWAY_URL if value.lower() in {"true", "1", "yes"} else value.rstrip("/")
    return f"{base}/openai/v1"


def valid_key(value: str | None) -> bool:
    return bool(
        value
        and value.strip()
        and not any(
            marker in value.lower()
            for marker in (
                "your_",
                "your-",
                "_here",
                "...",
                "…",
                "****",
                "<",
                ">",
                "changeme",
                "placeholder",
            )
        )
    )


def required_api_keys(env: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if env is None else env
    if gateway_url(env):
        keys = [
            "LANGSMITH_GATEWAY_API_KEY"
            if env.get("LANGSMITH_GATEWAY_API_KEY")
            else "LANGSMITH_API_KEY"
        ]
    else:
        keys = ["OPENAI_API_KEY"]
    if env.get("LANGSMITH_TRACING", "").lower() == "true":
        keys.append("LANGSMITH_API_KEY")
    return list(dict.fromkeys(keys))


def openai_chat_options(env: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ if env is None else env
    url = gateway_url(env)
    key_name = (
        (
            "LANGSMITH_GATEWAY_API_KEY"
            if env.get("LANGSMITH_GATEWAY_API_KEY")
            else "LANGSMITH_API_KEY"
        )
        if url
        else "OPENAI_API_KEY"
    )
    if not valid_key(env.get(key_name)):
        raise ValueError(
            f"Set {key_name} to a non-empty API key, not a template placeholder"
        )
    options = {"api_key": env[key_name]}
    if url:
        options["base_url"] = url
    return options


@lru_cache(maxsize=2)
def embedding_client(traced: bool = True):
    from langsmith.wrappers import wrap_openai
    from openai import AsyncOpenAI

    if not valid_key(os.getenv("OPENAI_API_KEY")):
        raise ValueError("Knowledge-base embeddings require a direct OPENAI_API_KEY")
    client = AsyncOpenAI()
    return wrap_openai(client) if traced else client
