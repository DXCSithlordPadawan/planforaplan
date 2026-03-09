"""Integration tests for the REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app import state


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestConfigEndpoint:
    def test_rejects_invalid_provider(self, client: TestClient) -> None:
        response = client.post(
            "/api/config",
            json={"provider": "openai", "api_key": "sk-test-1234567890"},
        )
        assert response.status_code == 422  # Pydantic pattern validation

    def test_rejects_short_api_key(self, client: TestClient) -> None:
        response = client.post(
            "/api/config",
            json={"provider": "claude", "api_key": "short"},
        )
        assert response.status_code == 422  # min_length=10

    def test_rejects_missing_fields(self, client: TestClient) -> None:
        response = client.post("/api/config", json={})
        assert response.status_code == 422


class TestPlanEndpoint:
    def test_rejects_unconfigured_provider(self, client: TestClient) -> None:
        # Reset state
        state._provider = None
        response = client.post(
            "/api/plan",
            json={"requirement": "Build a todo list app"},
        )
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"].lower()

    def test_rejects_short_requirement(self, client: TestClient) -> None:
        response = client.post(
            "/api/plan",
            json={"requirement": "too short"},
        )
        assert response.status_code == 422


class TestStatusEndpoint:
    def test_returns_status_structure(self, client: TestClient) -> None:
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "phase" in data
        assert "progress" in data
        assert "message" in data


class TestStopEndpoint:
    def test_stop_when_idle_returns_idle(self, client: TestClient) -> None:
        response = client.post("/api/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "idle"


class TestIndexPage:
    def test_index_returns_html(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "AI Application Generator" in response.text

    def test_security_headers_present(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert "content-security-policy" in response.headers
