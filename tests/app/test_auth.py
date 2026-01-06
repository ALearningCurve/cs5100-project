"""Tests for the authentication module."""

# ruff: noqa: PLR2004, E501

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.auth import (
  AUTH_COOKIE_NAME,
  AUTHENTICATION_SECRET_KEY,
  get_authenticated_user,
  router,
)


@pytest.fixture
def client() -> TestClient:
  """Create a test client for the FastAPI app."""
  app = FastAPI()
  app.include_router(router)
  return TestClient(app)


class TestGetAuthenticatedUser:
  """Tests for the get_authenticated_user function."""

  def test_returns_admin_when_skip_authentication(self) -> None:
    """Test that get_authenticated_user returns 'admin' when authentication is skipped."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", True):
      from starlette.requests import Request as StarletteRequest

      # Create a mock request with no cookies
      request = StarletteRequest(
        scope={
          "type": "http",
          "method": "GET",
          "headers": [],
          "path": "/",
          "query_string": b"",
        }
      )
      result = get_authenticated_user(request)
      assert result == "admin"

  def test_returns_admin_with_valid_cookie(self) -> None:
    """Test that get_authenticated_user returns 'admin' when valid cookie is present."""
    from starlette.requests import Request

    request = Request(
      scope={
        "type": "http",
        "method": "GET",
        "headers": [
          (b"cookie", f"{AUTH_COOKIE_NAME}={AUTHENTICATION_SECRET_KEY}".encode())
        ],
        "path": "/",
        "query_string": b"",
      }
    )
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      # Need to import after patching
      from src.app.auth import get_authenticated_user as gau

      result = gau(request)
      assert result == "admin"

  def test_returns_none_with_invalid_cookie(self) -> None:
    """Test that get_authenticated_user returns None when cookie is invalid."""
    from starlette.requests import Request

    request = Request(
      scope={
        "type": "http",
        "method": "GET",
        "headers": [(b"cookie", f"{AUTH_COOKIE_NAME}=invalid_key".encode())],
        "path": "/",
        "query_string": b"",
      }
    )
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      from src.app.auth import get_authenticated_user as gau

      result = gau(request)
      assert result is None

  def test_returns_none_with_no_cookie(self) -> None:
    """Test that get_authenticated_user returns None when no cookie is present."""
    from starlette.requests import Request

    request = Request(
      scope={
        "type": "http",
        "method": "GET",
        "headers": [],
        "path": "/",
        "query_string": b"",
      }
    )
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      from src.app.auth import get_authenticated_user as gau

      result = gau(request)
      assert result is None


class TestLoginEndpoints:
  """Tests for the login page and login submission endpoints."""

  def test_index_redirects_to_chat_when_authenticated(self, client: TestClient) -> None:
    """Test that / redirects to /chat when user is authenticated."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", True):
      response = client.get("/", follow_redirects=False)
      assert response.status_code == 307
      assert response.headers["location"] == "/chat"

  def test_index_redirects_to_login_when_not_authenticated(
    self, client: TestClient
  ) -> None:
    """Test that / redirects to /login when user is not authenticated."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      response = client.get("/", follow_redirects=False)
      assert response.status_code == 307
      assert response.headers["location"] == "/login"

  def test_login_page_returns_html(self, client: TestClient) -> None:
    """Test that /login returns HTML with a login form."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      response = client.get("/login")
      assert response.status_code == 200
      assert "text/html" in response.headers["content-type"]
      assert "<form" in response.text
      assert 'name="username"' in response.text
      assert 'name="password"' in response.text

  def test_login_page_redirects_to_chat_when_authenticated(
    self, client: TestClient
  ) -> None:
    """Test that /login redirects to /chat when user is already authenticated."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", True):
      response = client.get("/login", follow_redirects=False)
      assert response.status_code == 307
      assert response.headers["location"] == "/chat"

  def test_login_success(self, client: TestClient) -> None:
    """Test that correct credentials set the auth cookie and redirect to /chat."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      with patch("src.app.auth.AUTHENTICATION_SECRET_KEY", "test_secret"):
        with patch("src.app.auth.AUTHENTICATION_USERNAME", "testuser"):
          response = client.post(
            "/login",
            data={"username": "testuser", "password": "test_secret"},
            follow_redirects=False,
          )
          assert response.status_code == 303
          assert response.headers["location"] == "/chat"
          assert AUTH_COOKIE_NAME in response.cookies

  def test_login_failure_with_wrong_password(self, client: TestClient) -> None:
    """Test that incorrect password returns 401 error."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      with patch("src.app.auth.AUTHENTICATION_SECRET_KEY", "test_secret"):
        with patch("src.app.auth.AUTHENTICATION_USERNAME", "testuser"):
          response = client.post(
            "/login",
            data={"username": "testuser", "password": "wrong_password"},
          )
          assert response.status_code == 401
          assert "Incorrect Key" in response.text

  def test_login_failure_with_wrong_username(self, client: TestClient) -> None:
    """Test that incorrect username returns 401 error."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", False):
      with patch("src.app.auth.AUTHENTICATION_SECRET_KEY", "test_secret"):
        with patch("src.app.auth.AUTHENTICATION_USERNAME", "testuser"):
          response = client.post(
            "/login",
            data={"username": "wronguser", "password": "test_secret"},
          )
          assert response.status_code == 401
          assert "Incorrect Key" in response.text

  def test_login_success_when_authentication_skipped(self, client: TestClient) -> None:
    """Test that login succeeds and redirects to /chat when authentication is skipped."""
    with patch("src.app.auth.SKIP_AUTHENTICATION", True):
      response = client.post(
        "/login",
        data={"username": "anything", "password": "anything"},
        follow_redirects=False,
      )
      assert response.status_code == 303
      assert response.headers["location"] == "/chat"
