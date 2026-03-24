"""
tests/test_auth_routes.py — Unit tests for auth session management routes.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.mark.unit
class TestAuthRefresh:
    def test_refresh_requires_cookie(self) -> None:
        response = client.post("/auth/refresh")
        assert response.status_code == 401
        assert response.json()["detail"] == "Session expired. Sign in again."

    def test_refresh_returns_new_session_and_sets_cookies(self) -> None:
        mock_session = SimpleNamespace(access_token="new-access", refresh_token="new-refresh")
        mock_user = SimpleNamespace(id="user-123", email="user@example.com")
        mock_auth_response = SimpleNamespace(session=mock_session, user=mock_user)

        mock_supabase = MagicMock()
        mock_supabase.auth.refresh_session.return_value = mock_auth_response

        with patch("src.api.routes.auth.create_client", return_value=mock_supabase):
            client.cookies.set("session_refresh", "stale-refresh")
            response = client.post("/auth/refresh")
            client.cookies.clear()

        assert response.status_code == 200
        assert response.json() == {"user_id": "user-123", "email": "user@example.com"}
        set_cookie_headers = response.headers.get_list("set-cookie")
        assert any("session=new-access" in header for header in set_cookie_headers)
        assert any("session_refresh=new-refresh" in header for header in set_cookie_headers)

    def test_refresh_failure_clears_cookies(self) -> None:
        mock_supabase = MagicMock()
        mock_supabase.auth.refresh_session.side_effect = RuntimeError("expired")

        with patch("src.api.routes.auth.create_client", return_value=mock_supabase):
            client.cookies.set("session_refresh", "stale-refresh")
            response = client.post("/auth/refresh")
            client.cookies.clear()

        assert response.status_code == 401
        set_cookie_headers = response.headers.get_list("set-cookie")
        assert any(
            'session=""' in header or ("session=" in header and "Max-Age=0" in header)
            for header in set_cookie_headers
        )
        assert any(
            'session_refresh=""' in header
            or ("session_refresh=" in header and "Max-Age=0" in header)
            for header in set_cookie_headers
        )


@pytest.mark.unit
class TestAuthCallback:
    def test_callback_dispatches_calendar_sync_after_login(self) -> None:
        token_response = MagicMock(status_code=200)
        token_response.json.return_value = {
            "id_token": "google-id-token",
            "access_token": "google-access-token",
            "refresh_token": "google-refresh-token",
        }

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__.return_value.post = AsyncMock(return_value=token_response)
        mock_http_client.__aexit__.return_value = None

        mock_session = SimpleNamespace(
            access_token="supabase-access-token",
            refresh_token="supabase-refresh-token",
        )
        mock_user = SimpleNamespace(id="user-123", email="user@example.com")
        mock_auth_response = SimpleNamespace(session=mock_session, user=mock_user)

        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_id_token.return_value = mock_auth_response
        mock_user_db = MagicMock()

        with (
            patch("src.api.routes.auth.httpx.AsyncClient", return_value=mock_http_client),
            patch("src.api.routes.auth.create_client", return_value=mock_supabase),
            patch("src.api.routes.auth.get_client", return_value=mock_user_db),
            patch("src.api.routes.auth.sync_calendar_artifacts.delay") as mock_sync_delay,
        ):
            client.cookies.set("oauth_state", "expected-state")
            response = client.get(
                "/auth/callback?code=test-code&state=expected-state",
                follow_redirects=False,
            )
            client.cookies.clear()

        assert response.status_code == 307
        mock_sync_delay.assert_called_once_with(
            user_id="user-123",
            user_jwt="supabase-access-token",
            google_refresh_token="google-refresh-token",
        )
