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


class AIRateLimitError(AIProviderError):
    """Raised when an AI provider returns HTTP 429 (rate limit exceeded)."""


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
    """Return an SSLContext that trusts both the OS certificate store and certifi.

    Two-step approach:
    1. ``ssl.create_default_context()`` (no cafile) loads the platform's default
       CA store — Windows Certificate Store on Windows, Keychain on macOS, and
       the system CA bundle on Linux.  Passing cafile= would *replace* the system
       store entirely, which discards Windows trust anchors and causes
       ``SSL: CERTIFICATE_VERIFY_FAILED`` errors for providers (e.g. Minimax)
       whose intermediate CA is present in the Windows store but absent from the
       certifi bundle.
    2. ``ctx.load_verify_locations(cafile=certifi.where())`` *adds* the Mozilla
       root certificates from certifi on top of whatever the OS already loaded,
       ensuring good coverage on all platforms.
    """
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=certifi.where())
    return ctx


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------


class ClaudeProvider:
    """Claude AI provider using the official anthropic async SDK."""

    # Pin to the current production model; update here when upgrading.
    MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        # Keep a reference to the httpx client so it can be closed when this
        # provider instance is no longer needed (e.g. replaced by a new
        # configuration). The Anthropic SDK does not close an externally
        # supplied client, so we manage its lifecycle here.
        self._http_client = httpx.AsyncClient(verify=_ssl_context())
        self._model = model or self.MODEL
        # Client holds the key in memory only; never logged.
        kwargs: dict[str, object] = {
            "api_key": api_key,
            "http_client": self._http_client,
        }
        if base_url:
            kwargs["base_url"] = base_url
        self._client = anthropic.AsyncAnthropic(**kwargs)

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Call when discarding this provider."""
        await self._http_client.aclose()

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Claude Messages API and return the response text."""
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except anthropic.AuthenticationError as exc:
            raise AIProviderError("Invalid Claude API key.") from exc
        except anthropic.RateLimitError as exc:
            raise AIRateLimitError(
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
    MODEL = "abab6.5s-chat"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        # Key held in memory only; never logged.
        self._api_key = api_key
        self._model = model or self.MODEL
        self._api_url = base_url.rstrip("/") if base_url else self.API_URL

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Minimax chat completion API and return the response text."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
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
                    self._api_url, headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                raise AIProviderError("Invalid Minimax API key.") from exc
            if status == 429:
                raise AIRateLimitError(
                    "Minimax rate limit exceeded. Please wait and retry."
                ) from exc
            raise AIProviderError(
                f"Minimax HTTP error: {status}"
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
    MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        # Key held in memory only; never logged.
        self._api_key = api_key
        self._model = model or self.MODEL
        self._api_base = base_url.rstrip("/") if base_url else self.API_BASE

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Gemini generateContent API and return the response text."""
        url = f"{self._api_base}/{self._model}:generateContent"
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
            if status == 429:
                raise AIRateLimitError(
                    "Gemini rate limit exceeded. Please wait and retry."
                ) from exc
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
            status = exc.response.status_code
            if status == 401:
                raise AIProviderError(
                    "Invalid API key for custom provider."
                ) from exc
            if status == 429:
                raise AIRateLimitError(
                    "Custom provider rate limit exceeded. Please wait and retry."
                ) from exc
            raise AIProviderError(
                f"Custom provider HTTP error: {status}"
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
        ``claude``   — Anthropic Claude (claude-sonnet-4-20250514, overridable via model/base_url)
        ``minimax``  — Minimax (abab6.5s-chat, overridable via model/base_url)
        ``gemini``   — Google Gemini (gemini-2.0-flash, overridable via model/base_url)

    Custom provider:
        Any other name is treated as a custom OpenAI-compatible provider.
        Both ``base_url`` and ``model`` must be supplied in that case.

    Args:
        provider_name: Provider identifier (case-insensitive).
        api_key:       Provider API key — held in memory only.
        base_url:      Optional base URL override for built-in providers.
                       Required for custom providers.
        model:         Optional model override for built-in providers.
                       Required for custom providers.

    Raises:
        AIProviderError: If the provider is not recognised and
                         ``base_url``/``model`` are not provided.
    """
    match provider_name.lower():
        case "claude":
            return ClaudeProvider(api_key, model=model, base_url=base_url)
        case "minimax":
            return MinimaxProvider(api_key, model=model, base_url=base_url)
        case "gemini":
            return GeminiProvider(api_key, model=model, base_url=base_url)
        case _:
            if base_url and model:
                return CustomProvider(api_key, base_url, model)
            raise AIProviderError(
                f"Unknown provider '{provider_name}'. "
                "Use 'claude', 'minimax', or 'gemini', "
                "or supply 'base_url' and 'model' for a custom "
                "OpenAI-compatible provider."
            )
