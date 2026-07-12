"""Mini helper to call LLM with DeepInfra."""

from __future__ import annotations

import os
from typing import TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

DEEPINFRA_BASE_URL = os.environ.get("DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai")
DEFAULT_MODEL = os.environ.get("MODEL", "Qwen/Qwen3.6-35B-A3B")

T = TypeVar("T", bound=BaseModel)

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """
    Return a shared OpenAI client, pointing to DeepInfra and initialized with a DEEPINFRA_API_KEY.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("DEEPINFRA_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DEEPINFRA_API_KEY missing. Fill it in .env file."
            )
        _client = OpenAI(api_key=api_key, base_url=DEEPINFRA_BASE_URL)
    return _client


def call_llm(
    prompt: str,
    output_model: type[T],
    *,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    max_tokens: int = 4096,
) -> T:
    """Call a DeepInfra LLM and return answer.

    Args:
        prompt: user message.
        output_model: Pydantic class describing the expected output scheme.
        model: Model to use, please check available models on deepinfra.com/model
        system: system prompt (optional).
        max_tokens: max token.
    """
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    completion = client.beta.chat.completions.parse(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
        response_format=output_model,
    )
    return completion.choices[0].message.parsed
