"""Tests for AI provider factory and error handling."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.ai_provider import (
    AIProviderError,
    ClaudeProvider,
    MinimaxProvider,
    create_provider,
)


class TestCreateProviderFactory:
    def test_creates_claude_provider(self) -> None:
        provider = create_provider("claude", "sk-ant-test1234567890")
        assert isinstance(provider, ClaudeProvider)

    def test_creates_minimax_provider(self) -> None:
        provider = create_provider("minimax", "minimax-test-key-1234")
        assert isinstance(provider, MinimaxProvider)

    def test_case_insensitive(self) -> None:
        provider = create_provider("CLAUDE", "sk-ant-test1234567890")
        assert isinstance(provider, ClaudeProvider)

    def test_raises_for_unknown_provider(self) -> None:
        with pytest.raises(AIProviderError, match="Unknown provider"):
            create_provider("openai", "some-key-1234567890")
