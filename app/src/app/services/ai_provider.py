"""AI provider abstraction layer.

Defines the AIProvider Protocol and concrete implementations for Claude,
Minimax, Gemini, and any OpenAI-compatible custom endpoint. All
provider-specific details are encapsulated here so that routes and services
interact only with the Protocol interface.

Security:
  - API keys are accepted as constructor arguments only; they are never
    written to disk or included in log output.
  - All exceptions are mapped to AIProviderError before propagating,
    preventing internal SDK details from leaking to callers.
  - All outbound HTTPS connections use the certifi CA bundle so that the
    correct root certificates are available regardless of the host OS trust
    store (fixes SSL: CERTIFICATE_VERIFY_FAILED on some environments).
"""

import logging
import ssl
from typing import Protocol, runtime_checkable

import anthropic
import certifi
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
# Shared SSL helper
# ---------------------------------------------------------------------------


def _ssl_context() -> ssl.SSLContext:
    """Return an SSLContext loaded with the certifi CA bundle.

    Using certifi ensures that the Mozilla root certificates are available
    regardless of the host OS trust store configuration, which fixes
    SSL: CERTIFICATE_VERIFY_FAILED errors seen on some Linux and macOS
    environments.
    """
    ctx = ssl.create_default_context(cafile=certifi.where())
    return ctx


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------


class ClaudeProvider:
    """Claude AI provider using the official anthropic async SDK."""

    # Pin to the current production model; update here when upgrading.
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str) -> None:
        # Keep a reference to the httpx client so it can be closed when this
        # provider instance is no longer needed (e.g. replaced by a new
        # configuration). The Anthropic SDK does not close an externally
        # supplied client, so we manage its lifecycle here.
        self._http_client = httpx.AsyncClient(verify=_ssl_context())
        # Client holds the key in memory only; never logged.
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key, http_client=self._http_client
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Call when discarding this provider."""
        await self._http_client.aclose()

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
            async with httpx.AsyncClient(
                verify=_ssl_context(), timeout=120.0
            ) as client:
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
# Gemini (Google)
# ---------------------------------------------------------------------------


class GeminiProvider:
    """Google Gemini AI provider using async httpx HTTP client."""

    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemini-1.5-pro"

    def __init__(self, api_key: str) -> None:
        # Key held in memory only; never logged.
        self._api_key = api_key

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Gemini generateContent API and return the response text."""
        url = f"{self.API_BASE}/{self.MODEL}:generateContent"
        # API key is passed via a request header to avoid it appearing in
        # server access logs (which record the request URL).
        headers = {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
        try:
            async with httpx.AsyncClient(
                verify=_ssl_context(), timeout=120.0
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403):
                raise AIProviderError(
                    "Invalid or unauthorized Gemini API key."
                ) from exc
            if status == 400:
                raise AIProviderError("Invalid Gemini API request.") from exc
            raise AIProviderError(f"Gemini HTTP error: {status}") from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                f"Network error calling Gemini: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Custom (OpenAI-compatible)
# ---------------------------------------------------------------------------


class CustomProvider:
    """Generic OpenAI-compatible provider using async httpx HTTP client.

    Use this for any provider that exposes the OpenAI chat completions API
    (e.g. Ollama, Mistral, LM Studio, Azure OpenAI, OpenRouter, etc.).

    Args:
        api_key:  Bearer token for the remote API.
        base_url: Base URL of the OpenAI-compatible service, e.g.
                  ``https://api.openai.com/v1`` or
                  ``http://localhost:11434/v1``.
        model:    Model identifier as expected by the remote service.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        # Keys held in memory only; never logged.
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the OpenAI-compatible chat completions endpoint."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload = {"model": self._model, "messages": messages}
        try:
            async with httpx.AsyncClient(
                verify=_ssl_context(), timeout=120.0
            ) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AIProviderError(
                    "Invalid API key for custom provider."
                ) from exc
            raise AIProviderError(
                f"Custom provider HTTP error: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                f"Network error calling custom provider: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_provider(
    provider_name: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> AIProvider:
    """Return the correct AIProvider instance for the given provider name.

    Built-in providers (case-insensitive):
        ``claude``   — Anthropic Claude (claude-sonnet-4-20250514)
        ``minimax``  — Minimax (abab6.5s-chat)
        ``gemini``   — Google Gemini (gemini-1.5-pro)

    Custom provider:
        Any other name is treated as a custom OpenAI-compatible provider.
        Both ``base_url`` and ``model`` must be supplied in that case.

    Args:
        provider_name: Provider identifier (case-insensitive).
        api_key:       Provider API key — held in memory only.
        base_url:      Required for custom providers. Base URL of the
                       OpenAI-compatible endpoint.
        model:         Required for custom providers. Model identifier.

    Raises:
        AIProviderError: If the provider is not recognised and
                         ``base_url``/``model`` are not provided.
    """
    match provider_name.lower():
        case "claude":
            return ClaudeProvider(api_key)
        case "minimax":
            return MinimaxProvider(api_key)
        case "gemini":
            return GeminiProvider(api_key)
        case _:
            if base_url and model:
                return CustomProvider(api_key, base_url, model)
            raise AIProviderError(
                f"Unknown provider '{provider_name}'. "
                "Use 'claude', 'minimax', or 'gemini', "
                "or supply 'base_url' and 'model' for a custom "
                "OpenAI-compatible provider."
            )
