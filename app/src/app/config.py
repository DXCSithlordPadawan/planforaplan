"""Application configuration loaded from environment variables.

Uses pydantic-settings for type-safe env var loading.
API keys are NEVER stored here — they are held only in process memory
via app/state.py after being submitted through the browser UI.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for the AI Application Generator."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    # Deployment paths
    deploy_dir: Path = Path("generated-apps/latest")
    base_template_dir: Path = Path("base-template")

    # Generated app
    generated_app_port: int = 8001

    # Logging
    log_level: str = "INFO"

    # Input validation limits
    max_requirement_length: int = 4000
    min_requirement_length: int = 10
    max_plan_length: int = 16000


# Module-level singleton — import this instance everywhere
settings = Settings()
