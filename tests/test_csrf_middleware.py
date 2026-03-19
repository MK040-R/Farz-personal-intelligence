"""
tests/test_csrf_middleware.py — Unit tests for CSRF Origin validation middleware.

Run:
    pytest tests/test_csrf_middleware.py -v -m unit
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.unit
class TestCSRFOriginMiddleware:
    """CSRF middleware must block mutating requests with unknown origins when a session cookie is present."""

    def test_get_request_always_passes(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code != 403

    def test_post_without_session_cookie_passes(self, client: TestClient) -> None:
        """Bearer-token or unauthenticated POST requests are not CSRF-vulnerable."""
        resp = client.post(
            "/search",
            json={"q": "test"},
            headers={"Authorization": "Bearer fake-token"},
        )
        # Should not be 403 — may be 401/422 depending on auth, but not CSRF-blocked
        assert resp.status_code != 403

    def test_post_with_session_cookie_and_valid_origin_passes(self, client: TestClient) -> None:
        from src.config import settings

        resp = client.post(
            "/search",
            json={"q": "test"},
            headers={"Origin": settings.frontend_origin},
            cookies={"session": "fake-jwt-token"},
        )
        # Should not be 403 — may be 401/422, but not CSRF-blocked
        assert resp.status_code != 403

    def test_post_with_session_cookie_and_bad_origin_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/search",
            json={"q": "test"},
            headers={"Origin": "https://evil.example.com"},
            cookies={"session": "fake-jwt-token"},
        )
        assert resp.status_code == 403
        assert "Origin not allowed" in resp.json()["detail"]

    def test_post_with_session_cookie_and_no_origin_or_referer_rejected(
        self, client: TestClient
    ) -> None:
        # TestClient may add default headers; explicitly clear Origin/Referer
        resp = client.post(
            "/search",
            json={"q": "test"},
            cookies={"session": "fake-jwt-token"},
        )
        assert resp.status_code == 403

    def test_post_with_session_cookie_and_valid_referer_passes(self, client: TestClient) -> None:
        from src.config import settings

        resp = client.post(
            "/search",
            json={"q": "test"},
            headers={"Referer": f"{settings.frontend_origin}/some/page"},
            cookies={"session": "fake-jwt-token"},
        )
        assert resp.status_code != 403

    def test_post_with_session_cookie_and_bad_referer_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/search",
            json={"q": "test"},
            headers={"Referer": "https://evil.example.com/phish"},
            cookies={"session": "fake-jwt-token"},
        )
        assert resp.status_code == 403

    def test_delete_with_session_cookie_and_bad_origin_rejected(self, client: TestClient) -> None:
        resp = client.delete(
            "/chat/sessions/fake-session-id",
            headers={"Origin": "https://evil.example.com"},
            cookies={"session": "fake-jwt-token"},
        )
        assert resp.status_code == 403

    def test_options_request_always_passes(self, client: TestClient) -> None:
        resp = client.options("/search")
        assert resp.status_code != 403

    def test_api_base_url_is_also_allowed(self, client: TestClient) -> None:
        from src.config import settings

        if not settings.API_BASE_URL:
            pytest.skip("API_BASE_URL not set")

        from src.main import _extract_origin

        api_origin = _extract_origin(settings.API_BASE_URL)
        resp = client.post(
            "/search",
            json={"q": "test"},
            headers={"Origin": api_origin},
            cookies={"session": "fake-jwt-token"},
        )
        assert resp.status_code != 403
