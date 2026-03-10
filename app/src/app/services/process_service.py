"""Process management service.

Handles port detection, uvicorn subprocess launch, stdout readiness
monitoring, browser launch, and clean shutdown.

Security controls:
  CWE-78: All subprocess.Popen calls use list-form arguments.
          shell=True is never used.
          User-supplied values (port numbers) are validated as integers
          before being included in command lists.
"""

import logging
import os
import platform
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Callable

import psutil

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ProcessServiceError(Exception):
    """Raised when a process management operation fails."""


# ---------------------------------------------------------------------------
# Port management
# ---------------------------------------------------------------------------


def kill_process_on_port(port: int) -> None:
    """Terminate any process currently listening on the given port.

    Uses psutil for cross-platform port detection and clean termination.

    Args:
        port: TCP port number to check (validated integer).
    """
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                try:
                    proc = psutil.Process(conn.pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                    logger.info(
                        "Terminated process on port %d (PID %d)", port, conn.pid
                    )
                except psutil.NoSuchProcess:
                    pass  # Already gone
                except psutil.TimeoutExpired:
                    proc.kill()  # Force kill if graceful terminate timed out
                    logger.warning("Force-killed PID %d on port %d", conn.pid, port)
    except psutil.AccessDenied:
        logger.warning("Access denied when scanning port %d — continuing", port)


def kill_process_tree(process: subprocess.Popen) -> None:
    """Terminate a process and all its children using psutil.

    Args:
        process: The subprocess.Popen object to terminate.
    """
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        parent.terminate()
        # Wait for all to exit
        gone, alive = psutil.wait_procs(children + [parent], timeout=5)
        for proc in alive:
            proc.kill()
        logger.info("Process tree terminated (PID %d)", process.pid)
    except psutil.NoSuchProcess:
        pass  # Already exited


# ---------------------------------------------------------------------------
# Uvicorn path resolution
# ---------------------------------------------------------------------------


def _uvicorn_executable(deploy_dir: Path) -> str:
    """Return the absolute path to a usable uvicorn executable.

    Resolution order (first found wins):
      1. deploy_dir/.venv  — dedicated venv created by a prior install step.
      2. The venv that is currently running this process (sys.executable).
         This is always correct because uvicorn is a dependency of planforaplan
         and is therefore guaranteed to exist alongside the running interpreter.

    We never fall back to a bare 'uvicorn' string because on Windows that
    requires uvicorn to be on the system PATH, which is not guaranteed and
    causes [WinError 2] when it is absent.
    """
    # --- 1. Deploy-dir venv --------------------------------------------------
    if platform.system() == "Windows":
        deploy_uvicorn = deploy_dir / ".venv" / "Scripts" / "uvicorn.exe"
    else:
        deploy_uvicorn = deploy_dir / ".venv" / "bin" / "uvicorn"

    if deploy_uvicorn.exists():
        logger.info("Using deploy-dir uvicorn: %s", deploy_uvicorn)
        return str(deploy_uvicorn)

    # --- 2. Running-interpreter venv -----------------------------------------
    # sys.executable is e.g. C:\planforaplan\.venv\Scripts\python.exe
    # uvicorn sits alongside it in the same Scripts / bin directory.
    scripts_dir = Path(sys.executable).parent
    if platform.system() == "Windows":
        host_uvicorn = scripts_dir / "uvicorn.exe"
    else:
        host_uvicorn = scripts_dir / "uvicorn"

    if host_uvicorn.exists():
        logger.info(
            "Deploy-dir venv not found at %s — using host venv uvicorn: %s",
            deploy_uvicorn,
            host_uvicorn,
        )
        return str(host_uvicorn)

    # --- No uvicorn found anywhere -------------------------------------------
    raise ProcessServiceError(
        f"Cannot locate uvicorn. Checked:\n"
        f"  {deploy_uvicorn}\n"
        f"  {host_uvicorn}\n"
        "Ensure uvicorn is installed in the planforaplan virtual environment."
    )


# ---------------------------------------------------------------------------
# Dependency installation
# ---------------------------------------------------------------------------


# Packages always present in the planforaplan venv.  We never ask pip to
# install or upgrade these because on Windows pip cannot overwrite executable
# files (.exe) that are held open by the running process ([WinError 32]).
_BASE_PACKAGES: frozenset[str] = frozenset({
    "fastapi",
    "uvicorn",
    "jinja2",
    "python-multipart",
    "starlette",
    "pydantic",
    "anyio",
    "httptools",
    "watchfiles",
    "websockets",
    "click",
    "h11",
})


def _extra_requirements(req_file: Path) -> list[str]:
    """Return only the lines from req_file whose package name is not in
    _BASE_PACKAGES.

    Handles common requirement line formats:
      - bare name:              ``requests``
      - name with version:      ``requests==2.31.0``  ``requests>=2.28``
      - name with extras:       ``uvicorn[standard]``
      - comment / blank lines:  skipped silently
    """
    import re
    extras: list[str] = []
    for raw in req_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        # Skip blank lines, comments, and -r/-c/-f directives
        if not line or line.startswith(("#", "-")):
            continue
        # Extract the bare package name (before any [extra], ==, >=, etc.)
        match = re.match(r"^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)", line)
        if not match:
            continue
        pkg_name = match.group(1).lower().replace("-", "-").replace("_", "-")
        if pkg_name not in _BASE_PACKAGES:
            extras.append(line)
    return extras


def install_requirements(
    deploy_dir: Path,
    log_callback: Callable[[str, str], None] | None = None,
) -> None:
    """Pip-install any *extra* packages from the generated app's requirements.

    Packages already present in the planforaplan venv (fastapi, uvicorn,
    jinja2, etc.) are skipped.  This avoids the Windows [WinError 32] error
    that occurs when pip tries to overwrite an in-use executable such as
    uvicorn.exe.

    Only genuinely new packages (e.g. sqlalchemy, httpx, pandas) are
    installed into the running venv so uvicorn can import them.

    Args:
        deploy_dir:   Directory containing the generated app's requirements.txt.
        log_callback: Optional callable(level, message) for progress output.

    Raises:
        ProcessServiceError: If pip exits with a non-zero return code.
    """
    req_file = deploy_dir / "requirements.txt"
    if not req_file.exists():
        logger.info("No requirements.txt in %s — skipping install", deploy_dir)
        return

    extra_pkgs = _extra_requirements(req_file)
    if not extra_pkgs:
        logger.info("No extra packages to install (all are base packages).")
        if log_callback:
            log_callback("info", "All dependencies already satisfied.")
        return

    logger.info("Extra packages to install: %s", extra_pkgs)
    if log_callback:
        log_callback("info", f"Installing {len(extra_pkgs)} extra package(s): {', '.join(extra_pkgs)}")

    # Always invoke pip via the running interpreter to guarantee we install
    # into the correct venv regardless of PATH.
    cmd = [
        sys.executable, "-m", "pip",
        "install",
        "--quiet",
        "--disable-pip-version-check",
        *extra_pkgs,
    ]

    logger.info("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProcessServiceError(
            "pip install timed out after 120 seconds."
        ) from exc
    except OSError as exc:
        raise ProcessServiceError(f"Failed to run pip: {exc}") from exc

    if result.returncode != 0:
        logger.error("pip install failed:\n%s", result.stderr)
        raise ProcessServiceError(
            f"pip install failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )

    logger.info("Extra requirements installed successfully.")
    if log_callback:
        log_callback("info", "Extra dependencies installed.")


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------


def start_generated_app(
    deploy_dir: Path,
    port: int,
    log_callback: Callable[[str, str], None],
) -> subprocess.Popen:
    """Start the generated FastAPI application with uvicorn.

    Args:
        deploy_dir: Directory containing the generated app (with main.py).
        port: Port number to run the app on (validated integer).
        log_callback: Callable(level, message) for broadcasting log lines.

    Returns:
        The running subprocess.Popen object.

    Raises:
        ProcessServiceError: If the subprocess fails to start.
    """
    uvicorn_path = _uvicorn_executable(deploy_dir)

    # CWE-78: list-form args only — no shell=True, no string interpolation
    cmd = [
        uvicorn_path,
        "main:app",
        "--host", "127.0.0.1",
        "--port", str(int(port)),  # Explicit int cast before str
    ]

    log_callback("info", f"Starting uvicorn on port {port}...")
    logger.info("Launching: %s", " ".join(cmd))

    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(deploy_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ},  # Inherit env; no untrusted values injected
        )
    except OSError as exc:
        raise ProcessServiceError(f"Failed to start uvicorn: {exc}") from exc

    return process


def wait_for_ready(
    process: subprocess.Popen,
    port: int,
    timeout: int = 30,
    log_callback: Callable[[str, str], None] | None = None,
) -> str:
    """Monitor subprocess stdout for the uvicorn readiness signal.

    Args:
        process: The running uvicorn subprocess.
        port: Expected port number.
        timeout: Maximum seconds to wait before raising an error.
        log_callback: Optional callable for forwarding stdout lines.

    Returns:
        The application URL (e.g. 'http://127.0.0.1:8001').

    Raises:
        ProcessServiceError: If the process exits or times out before ready.
    """
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + timeout

    if process.stdout is None:
        raise ProcessServiceError("No stdout pipe available on process.")

    for line in process.stdout:
        line = line.rstrip()
        if log_callback:
            log_callback("info", line)
        logger.debug("uvicorn: %s", line)

        if time.monotonic() > deadline:
            raise ProcessServiceError(
                f"Server startup timed out after {timeout} seconds."
            )

        if "Application startup complete" in line or "Uvicorn running on" in line:
            logger.info("Server ready at %s", url)
            return url

        if process.poll() is not None:
            raise ProcessServiceError(
                "Process exited before signalling readiness."
            )

    raise ProcessServiceError("Process stdout closed before signalling readiness.")


# ---------------------------------------------------------------------------
# Browser launch
# ---------------------------------------------------------------------------


def launch_browser(url: str) -> None:
    """Open the default system browser at the given URL.

    Uses Python stdlib webbrowser — no external dependencies.

    Args:
        url: URL to open (e.g. 'http://127.0.0.1:8001').
    """
    webbrowser.open(url)
    logger.info("Browser launched: %s", url)
