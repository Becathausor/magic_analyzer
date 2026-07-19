"""LangChain model factories, pointing to DeepInfra like llm.py."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

DEEPINFRA_BASE_URL = os.environ.get("DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai")
DEFAULT_MODEL = os.environ.get("MODEL", "Qwen/Qwen3.6-35B-A3B")
DEFAULT_EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")


def _api_key() -> str:
    api_key = os.environ.get("DEEPINFRA_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPINFRA_API_KEY missing. Fill it in .env file.")
    return api_key


def get_chat_model(model: str = DEFAULT_MODEL) -> ChatOpenAI:
    """Return a LangChain chat model pointing to DeepInfra."""
    return ChatOpenAI(model=model, api_key=_api_key(), base_url=DEEPINFRA_BASE_URL)


def get_embeddings(model: str = DEFAULT_EMBEDDING_MODEL) -> OpenAIEmbeddings:
    """Return a LangChain embeddings client pointing to DeepInfra.

    DeepInfra's embeddings endpoint expects raw text, unlike OpenAI's API which
    accepts pre-tokenized input — tiktoken pre-tokenization must stay disabled.
    """
    return OpenAIEmbeddings(
        model=model,
        api_key=_api_key(),
        base_url=DEEPINFRA_BASE_URL,
        tiktoken_enabled=False,
        check_embedding_ctx_length=False,
    )
