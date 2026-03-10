"""Pydantic v2 request and response schemas for all API endpoints.

All user-facing inputs are validated here before any business logic runs.
This satisfies OWASP A03 (Injection) and NIST SP 800-53 SI-10.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self


class ConfigRequest(BaseModel):
    """Request body for POST /api/config.

    Built-in providers (set ``provider`` to one of these):
        ``claude``   — Anthropic Claude (default model overridable via ``model``/``base_url``)
        ``minimax``  — Minimax (default model overridable via ``model``/``base_url``)
        ``gemini``   — Google Gemini (default model overridable via ``model``/``base_url``)

    Custom OpenAI-compatible provider (``provider`` = any other identifier):
        Both ``base_url`` and ``model`` are **required** for custom providers.
    """

    provider: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description=(
            "AI provider name. Built-in values: 'claude', 'minimax', 'gemini'. "
            "Any other value is treated as a custom OpenAI-compatible provider "
            "and requires 'base_url' and 'model' to also be supplied."
        ),
    )
    api_key: str = Field(
        ...,
        min_length=10,
        max_length=512,
        description="Provider API key — held in memory only, never persisted",
    )
    base_url: str | None = Field(
        default=None,
        max_length=2048,
        description=(
            "Optional base URL override for any built-in provider, or the "
            "required endpoint URL for custom providers. "
            "Example: 'https://api.openai.com/v1'"
        ),
    )
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description=(
            "Optional model identifier override for any built-in provider, "
            "or the required model name for custom providers."
        ),
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url_protocol(cls, v: str | None) -> str | None:
        if v is not None and not (
            v.startswith("http://") or v.startswith("https://")
        ):
            raise ValueError("base_url must start with 'http://' or 'https://'")
        return v

    @model_validator(mode="after")
    def custom_provider_requires_base_url_and_model(self) -> Self:
        builtin = {"claude", "minimax", "gemini"}
        if self.provider.lower() not in builtin:
            if not self.base_url:
                raise ValueError(
                    f"'base_url' is required for custom provider '{self.provider}'"
                )
            if not self.model:
                raise ValueError(
                    f"'model' is required for custom provider '{self.provider}'"
                )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"provider": "claude", "api_key": "sk-ant-..."},
                {"provider": "claude", "api_key": "sk-ant-...", "model": "claude-3-5-haiku-20241022"},
                {"provider": "minimax", "api_key": "minimax-key..."},
                {"provider": "minimax", "api_key": "minimax-key...", "model": "abab6.5-chat"},
                {"provider": "gemini", "api_key": "AIza..."},
                {"provider": "gemini", "api_key": "AIza...", "model": "gemini-1.5-flash"},
                {
                    "provider": "my-llm",
                    "api_key": "my-key",
                    "base_url": "https://api.example.com/v1",
                    "model": "my-model-name",
                },
            ]
        }
    }


class PlanRequest(BaseModel):
    """Request body for POST /api/plan."""

    requirement: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="Natural language description of the application to build",
    )
    refine: bool = Field(
        default=False,
        description="If True, send refinement instructions alongside the requirement",
    )


class GenerateRequest(BaseModel):
    """Request body for POST /api/generate."""

    requirement: str = Field(..., min_length=10, max_length=4000)
    plan: str = Field(
        ...,
        min_length=10,
        max_length=16000,
        description="The approved implementation plan from Stage 1",
    )


class PlanResponse(BaseModel):
    """Response body for POST /api/plan."""

    plan: str = Field(..., description="AI-generated implementation plan in markdown")


class StatusResponse(BaseModel):
    """Response body for GET /api/status."""

    phase: str = Field(..., description="idle | planning | generating | deploying | running")
    progress: int = Field(..., ge=0, le=100)
    message: str
    url: str | None = Field(default=None, description="URL of running generated app, when available")


class GenerateResponse(BaseModel):
    """Response body for POST /api/generate."""

    status: str
    message: str


class StopResponse(BaseModel):
    """Response body for POST /api/stop."""

    status: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response body."""

    code: str
    detail: str
