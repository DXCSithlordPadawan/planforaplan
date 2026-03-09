"""Pydantic v2 request and response schemas for all API endpoints.

All user-facing inputs are validated here before any business logic runs.
This satisfies OWASP A03 (Injection) and NIST SP 800-53 SI-10.
"""

from pydantic import BaseModel, Field


class ConfigRequest(BaseModel):
    """Request body for POST /api/config."""

    provider: str = Field(
        ...,
        pattern="^(claude|minimax)$",
        description="AI provider name: 'claude' or 'minimax'",
    )
    api_key: str = Field(
        ...,
        min_length=10,
        max_length=512,
        description="Provider API key — held in memory only, never persisted",
    )

    model_config = {"json_schema_extra": {"example": {"provider": "claude", "api_key": "sk-ant-..."}}}


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
