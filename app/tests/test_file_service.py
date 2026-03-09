"""Unit tests for file_service — especially path traversal (CWE-22) guards."""

import pytest
from pathlib import Path

from app.services.file_service import (
    FileServiceError,
    parse_generated_files,
    validate_deploy_path,
)


class TestValidateDeployPath:
    """Tests for the CWE-22 path traversal guard."""

    def test_valid_path_within_root(self, tmp_path: Path) -> None:
        """Paths inside the deploy root must be accepted without error."""
        target = tmp_path / "subdir" / "file.py"
        # Should not raise
        validate_deploy_path(target, tmp_path)

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        """Paths using .. to escape the deploy root must be rejected."""
        target = tmp_path / ".." / "etc" / "passwd"
        with pytest.raises(FileServiceError, match="outside the deployment root"):
            validate_deploy_path(target.resolve(), tmp_path)

    def test_rejects_absolute_outside_root(self) -> None:
        """Absolute paths that resolve outside the deploy root must be rejected."""
        deploy_root = Path("/tmp/deploy")
        target = Path("/etc/passwd")
        with pytest.raises(FileServiceError):
            validate_deploy_path(target, deploy_root)

    def test_exact_root_accepted(self, tmp_path: Path) -> None:
        """The deploy root itself is a valid target."""
        validate_deploy_path(tmp_path, tmp_path)


class TestParseGeneratedFiles:
    """Tests for XML file block parser."""

    def test_parses_single_file(self) -> None:
        response = '<file path="main.py">print("hello")</file>'
        result = parse_generated_files(response)
        assert result == {"main.py": 'print("hello")'}

    def test_parses_multiple_files(self) -> None:
        response = (
            '<file path="main.py">app = 1</file>'
            '<file path="templates/index.html"><html></html></file>'
        )
        result = parse_generated_files(response)
        assert len(result) == 2
        assert "main.py" in result
        assert "templates/index.html" in result

    def test_parses_multiline_content(self) -> None:
        response = '<file path="app.py">line1\nline2\nline3</file>'
        result = parse_generated_files(response)
        assert "line2" in result["app.py"]

    def test_rejects_path_traversal(self) -> None:
        response = '<file path="../../../etc/passwd">evil</file>'
        result = parse_generated_files(response)
        assert result == {}

    def test_rejects_absolute_unix_path(self) -> None:
        response = '<file path="/etc/passwd">evil</file>'
        result = parse_generated_files(response)
        assert result == {}

    def test_rejects_absolute_windows_path(self) -> None:
        response = '<file path="\\windows\\system32\\evil.exe">evil</file>'
        result = parse_generated_files(response)
        assert result == {}

    def test_returns_empty_dict_for_no_blocks(self) -> None:
        result = parse_generated_files("No XML file tags here at all.")
        assert result == {}

    def test_content_is_stripped(self) -> None:
        response = '<file path="x.py">  \n  content  \n  </file>'
        result = parse_generated_files(response)
        assert result["x.py"] == "content"
