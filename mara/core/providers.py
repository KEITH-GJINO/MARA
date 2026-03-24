"""Model-agnostic LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompletionResponse:
    """Standardized response from any LLM provider."""

    content: str
    model: str
    token_usage: dict[str, int] = field(default_factory=dict)
    raw_response: Any = None

    def __str__(self) -> str:
        return self.content


class LLMProvider(ABC):
    """Abstract interface for LLM providers.

    MARA is model-agnostic. Implement this interface to add support
    for any LLM backend — cloud APIs, local models, or custom endpoints.
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """Generate a completion from the model.

        Args:
            prompt: The primary prompt content.
            context: Optional memory/context to prepend.
            temperature: Sampling temperature.
            max_tokens: Maximum response length.

        Returns:
            The model's response as a string.
        """
        ...

    @abstractmethod
    async def complete_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a structured (JSON) response conforming to a schema.

        Args:
            prompt: The primary prompt content.
            schema: JSON schema the response must conform to.

        Returns:
            Parsed dictionary matching the provided schema.
        """
        ...


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._client: Any = None

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def complete(
        self,
        prompt: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        client = await self._get_client()

        messages = []
        if context:
            messages.append({"role": "user", "content": context})
            messages.append({
                "role": "assistant",
                "content": "Understood. I have this context available.",
            })
        messages.append({"role": "user", "content": prompt})

        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        return response.content[0].text

    async def complete_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        import json

        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        raw = await self.complete(structured_prompt, **kwargs)
        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._client: Any = None

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                )
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def complete(
        self,
        prompt: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        client = await self._get_client()

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def complete_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        import json

        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        raw = await self.complete(structured_prompt, **kwargs)
        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)
