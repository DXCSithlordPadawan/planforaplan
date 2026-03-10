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
        # Timeout breakdown:
        #   connect=10s  — TCP handshake to Anthropic API
        #   read=480s    — max gap between streamed tokens (8 minutes covers
        #                  the largest 32K-token responses at typical speeds)
        #   write=30s    — time to upload the request body
        #   pool=10s     — wait for a connection slot
        self._http_client = httpx.AsyncClient(
            verify=_ssl_context(),
            timeout=httpx.Timeout(connect=10.0, read=480.0, write=30.0, pool=10.0),
        )
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
        """Call the Claude Messages API via streaming and return the full text.

        Streaming is required by the Anthropic SDK when max_tokens is large
        enough that the request could exceed the 10-minute non-streaming
        timeout threshold.  We collect all streamed text_delta events and
        return the concatenated result, which is functionally identical to a
        non-streaming call from the caller's perspective.
        """
        # Build kwargs conditionally: the Anthropic SDK rejects an empty string
        # for the system parameter on some versions.
        stream_kwargs: dict[str, object] = {
            "model": self._model,
            "max_tokens": 32768,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            stream_kwargs["system"] = system_prompt

        try:
            text_parts: list[str] = []
            async with self._client.messages.stream(**stream_kwargs) as stream:
                async for text in stream.text_stream:
                    text_parts.append(text)

            full_text = "".join(text_parts)

            # Guard: an empty response indicates a safety block or truncation.
            if not full_text.strip():
                final_msg = await stream.get_final_message()
                stop_reason = getattr(final_msg, "stop_reason", "unknown")
                logger.warning(
                    "Claude stream produced empty text. stop_reason=%s", stop_reason
                )
                raise AIProviderError(
                    f"Claude returned no content (stop_reason: {stop_reason!r}). "
                    "The response may have been blocked or truncated. Please retry."
                )

            return full_text

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
    """Minimax AI provider using async httpx HTTP client.

    Uses the native Minimax chat completion endpoint (v2), which is the
    endpoint issued keys from platform.minimax.io are authorised against.
    The OpenAI-compatible /v1/chat/completions path requires a separately
    provisioned key and is NOT used here.
    """

    # Native endpoint — keys from platform.minimax.io work here.
    API_BASE = "https://api.minimax.io"
    API_PATH = "/v1/text/chatcompletion_v2"
    MODEL = "MiniMax-Text-01"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        # Key held in memory only; never logged.
        self._api_key = api_key
        self._model = model or self.MODEL
        # If the caller supplies a base_url override (e.g. regional host),
        # append the native path. Otherwise use the default full URL.
        base = base_url.rstrip("/") if base_url else self.API_BASE
        self._api_url = f"{base}{self.API_PATH}"

    async def generate(self, user_prompt: str, system_prompt: str) -> str:
        """Call the Minimax chat completion API and return the response text."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload = {
            "model": self._model,
            "messages": messages,
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
                logger.debug("Minimax raw response: %s", data)
                # Minimax returns API-level errors in base_resp even on HTTP 200.
                base_resp = data.get("base_resp", {})
                if base_resp.get("status_code", 0) != 0:
                    logger.warning(
                        "Minimax base_resp error: code=%s msg=%s",
                        base_resp.get("status_code"),
                        base_resp.get("status_msg"),
                    )
                    raise AIProviderError(
                        f"Minimax API error: {base_resp.get('status_msg', 'unknown error')}"
                    )
                # Native endpoint uses choices[0].message.content
                # Fall back to reply field used by some legacy response shapes.
                try:
                    content = (
                        data["choices"][0]["message"]["content"]
                        if "choices" in data
                        else data["reply"]
                    )
                    return content
                except (KeyError, IndexError) as exc:
                    logger.error("Minimax unexpected response shape: %s", data)
                    raise AIProviderError(
                        f"Unexpected Minimax response format: {data}"
                    ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            # Log the response body to help diagnose unexpected errors.
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.warning("Minimax HTTP %d response: %s", status, body)
            if status == 401:
                raise AIProviderError(
                    "Invalid Minimax API key or wrong API endpoint. "
                    "Ensure your key was issued for api.minimax.io and not a regional variant."
                ) from exc
            if status == 429:
                raise AIRateLimitError(
                    "Minimax rate limit exceeded. Please wait and retry."
                ) from exc
            raise AIProviderError(
                f"Minimax HTTP error: {status} — {body}"
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
                verify=_ssl_context(), timeout=180.0
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                # Guard against safety blocks / MAX_TOKENS where content is absent.
                candidate = data.get("candidates", [{}])[0]
                finish_reason = candidate.get("finishReason", "")
                if "content" not in candidate:
                    logger.warning(
                        "Gemini candidate missing 'content'. finishReason=%s full=%s",
                        finish_reason,
                        data,
                    )
                    raise AIProviderError(
                        f"Gemini returned no content (finishReason: {finish_reason!r}). "
                        "This may be a safety block or token-limit truncation. "
                        "Try a shorter or simpler prompt."
                    )
                try:
                    return candidate["content"]["parts"][0]["text"]
                except (KeyError, IndexError) as exc:
                    logger.error("Gemini unexpected candidate structure: %s", candidate)
                    raise AIProviderError(
                        f"Unexpected Gemini response structure: {candidate}"
                    ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403):
                raise AIProviderError(
                    "Invalid or unauthorized Gemini API key."
                ) from exc
            if status == 400:
                try:
                    detail = exc.response.json()
                except Exception:
                    detail = exc.response.text
                logger.warning("Gemini 400 response: %s", detail)
                raise AIProviderError(f"Invalid Gemini API request: {detail}") from exc
            if status == 429:
                # Surface retry-delay hint if Google includes it in the response.
                try:
                    retry_info = exc.response.json()
                    retry_msg = str(retry_info)
                except Exception:
                    retry_msg = exc.response.text
                logger.warning("Gemini rate limit response: %s", retry_msg)
                raise AIRateLimitError(
                    "Gemini rate limit exceeded. The free tier allows 15 requests/min "
                    "and 1,500 requests/day. Please wait a minute and retry, or "
                    "switch to a paid API key with higher quotas."
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
