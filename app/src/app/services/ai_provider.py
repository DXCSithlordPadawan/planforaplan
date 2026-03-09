"""AI provider abstraction layer.

Defines the AIProvider Protocol and concrete implementations for Claude
and Minimax. All provider-specific details are encapsulated here so that
routes and services interact only with the Protocol interface.

Security:
  - API keys are accepted as constructor arguments only; they are never
    written to disk or included in log output.
  - All exceptions are mapped to AIProviderError before propagating,
    preventing internal SDK details from leaking to callers.
"""

import logging
from typing import Protocol, runtime_checkable

import anthropic
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AIProviderError(Exception):
    """Raised when an AI provider call fails for any reason."""


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AIProvider(Protocol):
    """Structural interface all AI providers must satisfy."""

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Send a prompt and return the AI response as a plain string."""
        ...


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------


class ClaudeProvider:
    """Claude AI provider using the official anthropic async SDK."""

    # Pin to the current production model; update here when upgrading.
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str) -> None:
        # Client holds the key in memory only; never logged.
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Claude Messages API and return the response text."""
        try:
            message = await self._client.messages.create(
                model=self.MODEL,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except anthropic.AuthenticationError as exc:
            raise AIProviderError("Invalid Claude API key.") from exc
        except anthropic.RateLimitError as exc:
            raise AIProviderError(
                "Claude rate limit exceeded. Please wait and retry."
            ) from exc
        except anthropic.APIError as exc:
            raise AIProviderError(f"Claude API error: {exc}") from exc


# ---------------------------------------------------------------------------
# Minimax
# ---------------------------------------------------------------------------


class MinimaxProvider:
    """Minimax AI provider using async httpx HTTP client."""

    API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    def __init__(self, api_key: str) -> None:
        # Key held in memory only; never logged.
        self._api_key = api_key

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Minimax chat completion API and return the response text."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "abab6.5s-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.API_URL, headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AIProviderError("Invalid Minimax API key.") from exc
            raise AIProviderError(
                f"Minimax HTTP error: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                f"Network error calling Minimax: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_provider(provider_name: str, api_key: str) -> AIProvider:
    """Return the correct AIProvider instance for the given provider name.

    Args:
        provider_name: 'claude' or 'minimax' (case-insensitive).
        api_key: Provider API key — held in memory only.

    Raises:
        AIProviderError: If provider_name is not recognised.
    """
    match provider_name.lower():
        case "claude":
            return ClaudeProvider(api_key)
        case "minimax":
            return MinimaxProvider(api_key)
        case _:
            raise AIProviderError(
                f"Unknown provider '{provider_name}'. Use 'claude' or 'minimax'."
            )
