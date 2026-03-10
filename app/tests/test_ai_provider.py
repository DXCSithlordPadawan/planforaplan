"""Tests for AI provider factory and error handling."""

import ssl

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_provider import (
    AIProviderError,
    AIRateLimitError,
    ClaudeProvider,
    CustomProvider,
    GeminiProvider,
    MinimaxProvider,
    _ssl_context,
    create_provider,
)


class TestSslContext:
    def test_returns_ssl_context(self) -> None:
        ctx = _ssl_context()
        assert isinstance(ctx, ssl.SSLContext)

    def test_calls_create_default_context_with_certifi_cafile(self) -> None:
        import certifi

        with patch("ssl.create_default_context") as mock_create:
            mock_create.return_value = MagicMock(spec=ssl.SSLContext)
            _ssl_context()
            mock_create.assert_called_once_with(cafile=certifi.where())


class TestCreateProviderFactory:
    def test_creates_claude_provider(self) -> None:
        provider = create_provider("claude", "sk-ant-test1234567890")
        assert isinstance(provider, ClaudeProvider)

    def test_creates_minimax_provider(self) -> None:
        provider = create_provider("minimax", "minimax-test-key-1234")
        assert isinstance(provider, MinimaxProvider)

    def test_creates_gemini_provider(self) -> None:
        provider = create_provider("gemini", "AIzaSy-test-key-1234567")
        assert isinstance(provider, GeminiProvider)

    def test_creates_gemini_provider_with_custom_model(self) -> None:
        provider = create_provider("gemini", "AIzaSy-test-key-1234567", model="gemini-1.5-flash")
        assert isinstance(provider, GeminiProvider)
        assert provider._model == "gemini-1.5-flash"

    def test_creates_gemini_provider_with_custom_base_url(self) -> None:
        provider = create_provider(
            "gemini",
            "AIzaSy-test-key-1234567",
            base_url="https://generativelanguage.googleapis.com/v1/models",
        )
        assert isinstance(provider, GeminiProvider)
        assert provider._api_base == "https://generativelanguage.googleapis.com/v1/models"

    def test_gemini_provider_defaults(self) -> None:
        provider = GeminiProvider("AIzaSy-test-key-1234567")
        assert provider._model == GeminiProvider.MODEL
        assert provider._api_base == GeminiProvider.API_BASE

    def test_gemini_default_model_is_current(self) -> None:
        """Default model must not be the deprecated gemini-1.5-pro."""
        assert GeminiProvider.MODEL != "gemini-1.5-pro"

    def test_creates_custom_provider(self) -> None:
        provider = create_provider(
            "my-llm",
            "test-key-1234567890",
            base_url="https://api.example.com/v1",
            model="my-model",
        )
        assert isinstance(provider, CustomProvider)

    def test_case_insensitive(self) -> None:
        provider = create_provider("CLAUDE", "sk-ant-test1234567890")
        assert isinstance(provider, ClaudeProvider)

    def test_case_insensitive_gemini(self) -> None:
        provider = create_provider("GEMINI", "AIzaSy-test-key-1234567")
        assert isinstance(provider, GeminiProvider)

    def test_raises_for_unknown_provider_without_base_url(self) -> None:
        with pytest.raises(AIProviderError, match="Unknown provider"):
            create_provider("openai", "some-key-1234567890")

    def test_raises_for_unknown_provider_without_model(self) -> None:
        with pytest.raises(AIProviderError, match="Unknown provider"):
            create_provider(
                "openai",
                "some-key-1234567890",
                base_url="https://api.openai.com/v1",
            )

    def test_raises_for_unknown_provider_without_base_url_only(self) -> None:
        with pytest.raises(AIProviderError, match="Unknown provider"):
            create_provider(
                "openai",
                "some-key-1234567890",
                model="gpt-4o",
            )


class TestClaudeProviderSsl:
    def test_uses_certifi_ssl_context(self) -> None:
        """ClaudeProvider must inject a certifi-backed httpx client."""
        import httpx

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            mock_cls.return_value = MagicMock()
            ClaudeProvider("sk-ant-test1234567890")
            _, kwargs = mock_cls.call_args
            http_client = kwargs.get("http_client")
            assert isinstance(http_client, httpx.AsyncClient)


class TestMinimaxProviderSsl:
    @pytest.mark.asyncio
    async def test_uses_certifi_ssl_context(self) -> None:
        """MinimaxProvider must pass verify=<SSLContext> to httpx."""
        provider = MinimaxProvider("minimax-test-key-1234")
        captured: list[dict] = []

        original_init = __import__("httpx").AsyncClient.__init__

        def patched_init(self, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(kwargs)
            # Don't actually create the client; just record kwargs
            raise RuntimeError("stop")

        with patch("httpx.AsyncClient.__init__", patched_init):
            try:
                await provider.generate("hi", "sys")
            except RuntimeError:
                pass

        assert captured, "httpx.AsyncClient was not instantiated"
        verify = captured[0].get("verify")
        assert isinstance(verify, ssl.SSLContext)


class TestGeminiProviderSsl:
    @pytest.mark.asyncio
    async def test_uses_certifi_ssl_context(self) -> None:
        """GeminiProvider must pass verify=<SSLContext> to httpx."""
        provider = GeminiProvider("AIzaSy-test-key")
        captured: list[dict] = []

        def patched_init(self, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(kwargs)
            raise RuntimeError("stop")

        with patch("httpx.AsyncClient.__init__", patched_init):
            try:
                await provider.generate("hi", "sys")
            except RuntimeError:
                pass

        assert captured
        assert isinstance(captured[0].get("verify"), ssl.SSLContext)


class TestGeminiProviderRateLimit:
    @pytest.mark.asyncio
    async def test_raises_ai_rate_limit_error_on_429(self) -> None:
        """GeminiProvider must raise AIRateLimitError for HTTP 429 responses."""
        import httpx

        provider = GeminiProvider("AIzaSy-test-key")
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_exc = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=mock_exc)
        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(AIRateLimitError, match="rate limit exceeded"):
                await provider.generate("hi", "sys")

    def test_rate_limit_error_is_subclass_of_ai_provider_error(self) -> None:
        """AIRateLimitError must be a subclass of AIProviderError."""
        assert issubclass(AIRateLimitError, AIProviderError)


class TestMinimaxProviderRateLimit:
    @pytest.mark.asyncio
    async def test_raises_ai_rate_limit_error_on_429(self) -> None:
        """MinimaxProvider must raise AIRateLimitError for HTTP 429 responses."""
        import httpx

        provider = MinimaxProvider("minimax-test-key-1234")
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_exc = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=mock_exc)
        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(AIRateLimitError, match="rate limit exceeded"):
                await provider.generate("hi", "sys")


class TestCustomProviderRateLimit:
    @pytest.mark.asyncio
    async def test_raises_ai_rate_limit_error_on_429(self) -> None:
        """CustomProvider must raise AIRateLimitError for HTTP 429 responses."""
        import httpx

        provider = CustomProvider(
            "key-1234567890",
            "https://api.example.com/v1",
            "my-model",
        )
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_exc = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=mock_exc)
        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(AIRateLimitError, match="rate limit exceeded"):
                await provider.generate("hi", "sys")
    @pytest.mark.asyncio
    async def test_uses_certifi_ssl_context(self) -> None:
        """CustomProvider must pass verify=<SSLContext> to httpx."""
        provider = CustomProvider(
            "key-1234567890",
            "https://api.example.com/v1",
            "my-model",
        )
        captured: list[dict] = []

        def patched_init(self, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(kwargs)
            raise RuntimeError("stop")

        with patch("httpx.AsyncClient.__init__", patched_init):
            try:
                await provider.generate("hi", "sys")
            except RuntimeError:
                pass

        assert captured
        assert isinstance(captured[0].get("verify"), ssl.SSLContext)
