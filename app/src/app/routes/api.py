"""REST API routes for the AI Application Generator.

Endpoints:
  POST /api/config   — configure AI provider + API key
  POST /api/plan     — Stage 1: generate implementation plan
  POST /api/generate — Stage 2: generate code, deploy, launch browser
  GET  /api/status   — query current execution status
  POST /api/stop     — terminate the running generated application
  GET  /api/health   — liveness check
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app import state
from app.config import settings
from app.models import (
    ConfigRequest,
    GenerateRequest,
    GenerateResponse,
    PlanRequest,
    PlanResponse,
    StatusResponse,
    StopResponse,
)
from app.prompts import CODE_SYSTEM_PROMPT, PLAN_SYSTEM_PROMPT
from app.services.ai_provider import AIProviderError, create_provider
from app.services.file_service import (
    FileServiceError,
    copy_base_template,
    parse_generated_files,
    write_generated_files,
)
from app.services.process_service import (
    ProcessServiceError,
    kill_process_on_port,
    kill_process_tree,
    launch_browser,
    start_generated_app,
    wait_for_ready,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@router.post("/config")
async def configure(request: ConfigRequest) -> dict[str, str]:
    """Validate and store AI provider credentials in process memory.

    The API key is validated with a minimal test call before being stored.
    It is never written to disk or included in any log output.
    """
    try:
        provider = create_provider(
            request.provider,
            request.api_key,
            base_url=request.base_url,
            model=request.model,
        )
        # Validate credentials with a low-cost probe call
        await provider.generate("Hello", "Reply with the single word: ok")
    except AIProviderError as exc:
        logger.warning("Provider configuration failed: %s", exc)
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    # Close the previous provider's HTTP client if it exposes aclose()
    old_provider = state.get_provider()
    if old_provider is not None and hasattr(old_provider, "aclose"):
        await old_provider.aclose()

    state.set_provider(provider)
    state.set_status("idle", 0, "Provider configured. Ready to generate.")
    return {"status": "configured"}


# ---------------------------------------------------------------------------
# Stage 1: Plan generation
# ---------------------------------------------------------------------------


@router.post("/plan", response_model=PlanResponse)
async def generate_plan(request: PlanRequest) -> PlanResponse:
    """Generate an implementation plan from a natural language requirement."""
    provider = state.get_provider()
    if provider is None:
        raise HTTPException(status_code=400, detail="Provider not configured.")

    state.set_status("planning", 10, "Generating implementation plan...")
    await state.broadcast("info", "Sending requirement to AI provider...")

    refine_prefix = (
        "Refine and improve the following plan based on the requirement:\n\n"
        if request.refine
        else ""
    )
    user_prompt = f"{refine_prefix}{request.requirement}"

    try:
        plan = await provider.generate(user_prompt, PLAN_SYSTEM_PROMPT)
    except AIProviderError as exc:
        state.set_status("idle", 0, f"Plan generation failed: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    state.set_status("idle", 0, "Plan ready for review.")
    await state.broadcast("success", "Plan generated. Please review and approve.")
    return PlanResponse(plan=plan)


# ---------------------------------------------------------------------------
# Stage 2: Code generation + deployment (background task)
# ---------------------------------------------------------------------------


async def _generate_and_deploy(requirement: str, plan: str) -> None:
    """Background task: generate code, deploy, and launch browser."""
    provider = state.get_provider()
    if provider is None:
        state.set_status("idle", 0, "Provider not configured.")
        return

    try:
        # --- Code generation -------------------------------------------------
        state.set_status("generating", 20, "Generating application code...")
        await state.broadcast("info", "Sending requirement + plan to AI for code generation...")

        user_prompt = CODE_SYSTEM_PROMPT.format(
            requirement=requirement,
            plan=plan,
        )
        response = await provider.generate(user_prompt, "")

        await state.broadcast("info", "Code generation complete. Parsing files...")
        state.set_status("generating", 50, "Parsing generated files...")

        files = parse_generated_files(response)
        if not files:
            raise FileServiceError(
                "No files were extracted from the AI response. "
                "The AI may not have followed the XML format. Please retry."
            )

        await state.broadcast("info", f"Found {len(files)} generated file(s).")

        # --- Deployment ------------------------------------------------------
        state.set_status("deploying", 60, "Copying base template...")
        await state.broadcast("info", "Copying base template to deployment directory...")

        deploy_dir = settings.deploy_dir
        base_template = settings.base_template_dir

        copy_base_template(base_template, deploy_dir)
        await state.broadcast("info", "Writing generated files...")

        state.set_status("deploying", 70, "Writing generated files...")
        write_generated_files(files, deploy_dir)

        # --- Process startup -------------------------------------------------
        state.set_status("deploying", 80, "Starting application server...")
        await state.broadcast("info", f"Starting uvicorn on port {settings.generated_app_port}...")

        kill_process_on_port(settings.generated_app_port)

        async def log_cb(level: str, message: str) -> None:
            await state.broadcast(level, message)

        # start_generated_app is synchronous; run it in a thread executor
        loop = asyncio.get_running_loop()
        process = await loop.run_in_executor(
            None,
            lambda: start_generated_app(
                deploy_dir,
                settings.generated_app_port,
                lambda lvl, msg: None,  # Sync placeholder; WS broadcast below
            ),
        )
        state.set_process(process)

        # wait_for_ready reads stdout — run in thread executor
        url = await loop.run_in_executor(
            None,
            lambda: wait_for_ready(process, settings.generated_app_port, timeout=30),
        )

        # --- Success ---------------------------------------------------------
        state.set_status("running", 100, "Application is running.", url=url)
        await state.broadcast("success", f"Application started at {url}")

        launch_browser(url)
        await state.broadcast("info", f"Browser launched: {url}")

    except (AIProviderError, FileServiceError, ProcessServiceError) as exc:
        logger.error("Generation/deployment failed: %s", exc)
        state.set_status("idle", 0, f"Error: {exc}")
        await state.broadcast("error", str(exc))


@router.post("/generate", response_model=GenerateResponse)
async def generate_app(
    request: GenerateRequest, background_tasks: BackgroundTasks
) -> GenerateResponse:
    """Stage 2: Generate application code and deploy it.

    Returns immediately with status 'deploying'.
    Progress is streamed via WebSocket /ws/logs.
    """
    if state.get_provider() is None:
        raise HTTPException(status_code=400, detail="Provider not configured.")

    current = state.get_status()
    if current["phase"] in ("generating", "deploying"):
        raise HTTPException(
            status_code=409,
            detail="A generation is already in progress. Stop it first.",
        )

    background_tasks.add_task(_generate_and_deploy, request.requirement, request.plan)
    return GenerateResponse(status="deploying", message="Generation started.")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Return the current execution phase, progress, and URL."""
    s = state.get_status()
    return StatusResponse(**s)


# ---------------------------------------------------------------------------
# Stop
# ---------------------------------------------------------------------------


@router.post("/stop", response_model=StopResponse)
async def stop_app() -> StopResponse:
    """Terminate the running generated application."""
    process = state.get_process()
    if process is not None:
        kill_process_tree(process)
        state.set_process(None)

    state.set_status("idle", 0, "Application stopped.")
    await state.broadcast("info", "Generated application stopped.")
    return StopResponse(status="idle", message="Application stopped.")
