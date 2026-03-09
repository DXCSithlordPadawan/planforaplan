"""File system service for deployment operations.

Security controls:
  CWE-22: validate_deploy_path() prevents directory traversal by resolving
          all paths and confirming they fall within the designated deploy root.
  All path operations use pathlib.Path — no string concatenation.
"""

import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class FileServiceError(Exception):
    """Raised when a file system operation fails or is rejected."""


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


def validate_deploy_path(target: Path, deploy_root: Path) -> None:
    """Raise FileServiceError if target resolves outside deploy_root.

    This is the primary CWE-22 (Path Traversal) control. Call this before
    every file read or write that involves a user-supplied or AI-supplied path.

    Args:
        target: The path to validate.
        deploy_root: The permitted root directory.

    Raises:
        FileServiceError: If target is outside deploy_root.
    """
    try:
        target.resolve().relative_to(deploy_root.resolve())
    except ValueError as exc:
        raise FileServiceError(
            f"Path '{target}' is outside the deployment root '{deploy_root}'"
        ) from exc


# ---------------------------------------------------------------------------
# Template operations
# ---------------------------------------------------------------------------


def copy_base_template(source: Path, destination: Path) -> None:
    """Copy the pre-installed base template to the deployment directory.

    Removes any existing deployment at destination before copying.

    Args:
        source: Path to the base-template directory.
        destination: Target deployment directory.

    Raises:
        FileServiceError: If source does not exist.
    """
    if not source.exists():
        raise FileServiceError(
            f"Base template not found at '{source}'. "
            "Run setup to create and pre-install the base template."
        )
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, symlinks=False)
    logger.info("Base template copied: %s -> %s", source, destination)


# ---------------------------------------------------------------------------
# Generated file operations
# ---------------------------------------------------------------------------


def write_generated_files(files: dict[str, str], deploy_root: Path) -> None:
    """Write AI-generated file contents to the deployment directory.

    Each key in files is a relative path; each value is the file content.
    Path traversal attempts are blocked by validate_deploy_path().

    Args:
        files: Mapping of relative_path -> file_content.
        deploy_root: Root directory for the deployment.
    """
    for relative_path, content in files.items():
        target = deploy_root / relative_path
        validate_deploy_path(target, deploy_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info("Wrote: %s", target)


# ---------------------------------------------------------------------------
# AI response parser
# ---------------------------------------------------------------------------


def parse_generated_files(response: str) -> dict[str, str]:
    """Extract file path/content pairs from an XML-tagged AI response.

    Expects blocks in the form:
        <file path="relative/path/to/file">
        ...content...
        </file>

    Security: Rejects absolute paths and any path containing '..' to prevent
    directory traversal (CWE-22) in AI-generated output.

    Args:
        response: Raw string response from the AI provider.

    Returns:
        Dict mapping relative file paths to their contents.
        Returns an empty dict if no valid file blocks are found.
    """
    pattern = re.compile(
        r'<file\s+path="([^"]+)">(.*?)</file>',
        re.DOTALL,
    )
    files: dict[str, str] = {}
    for match in pattern.finditer(response):
        file_path = match.group(1).strip()
        content = match.group(2).strip()

        # Reject absolute paths and traversal sequences (CWE-22)
        if file_path.startswith(("/", "\\")) or ".." in file_path:
            logger.warning("Rejected suspicious AI-generated path: %s", file_path)
            continue

        files[file_path] = content

    if not files:
        logger.warning("No file blocks found in AI response (length=%d)", len(response))

    return files
