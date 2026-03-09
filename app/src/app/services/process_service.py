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
    """Return the absolute path to uvicorn inside the deploy_dir venv.

    Handles Windows vs. POSIX path differences.
    """
    if platform.system() == "Windows":
        uvicorn = deploy_dir / ".venv" / "Scripts" / "uvicorn.exe"
    else:
        uvicorn = deploy_dir / ".venv" / "bin" / "uvicorn"

    if not uvicorn.exists():
        # Fall back to the system uvicorn if venv not present
        logger.warning(
            "Venv uvicorn not found at %s — falling back to system uvicorn", uvicorn
        )
        return "uvicorn"

    return str(uvicorn)


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
