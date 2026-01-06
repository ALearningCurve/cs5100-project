"""Tests for the authentication module."""

# ruff: noqa: PLR2004, E501, ANN401

from contextlib import contextmanager
from importlib import reload
from typing import Any, Generator
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.app.auth import AUTH_COOKIE_NAME


@contextmanager
def auth_config(**env_patches: Any) -> Generator[Any, None, None]:
  """Context manager to patch auth environment and reload the module.

  Ensures all required auth env variables are present with defaults if needed.
  """
  import os

  # Build patches with defaults for missing variables
  defaults = {
    "SHOULD_AUTHENTICATE": True,
    "AUTHENTICATION_SECRET_KEY": os.getenv("AUTHENTICATION_SECRET_KEY", "test_key"),
    "AUTHENTICATION_USERNAME": os.getenv("AUTHENTICATION_USERNAME", "test_user"),
  }

  # Merge with provided patches (patches override defaults)
  patches = {**defaults, **env_patches}

  with patch.dict("src.env.__dict__", patches):
    import src.app.auth

    reload(src.app.auth)
    yield src.app.auth


@pytest.fixture
def client_with_auth(**env_patches: Any) -> TestClient:
  """Fixture factory to create a test client with specific auth config."""

  def _create_client(**kwargs: Any) -> TestClient:
    with auth_config(**{**env_patches, **kwargs}):
      import src.app.auth

      app = FastAPI()
      app.include_router(src.app.auth.router)
      return TestClient(app)

  return _create_client


def create_request(headers: list[tuple[bytes, bytes]] | None = None) -> Request:
  """Helper to create a test request with optional headers."""
  return Request(
    scope={
      "type": "http",
      "method": "GET",
      "headers": headers or [],
      "path": "/",
      "query_string": b"",
    }
  )


class TestGetAuthenticatedUser:
  """Tests for the get_authenticated_user function."""

  def test_returns_admin_when_skip_authentication(self) -> None:
    """Test that get_authenticated_user returns 'admin' when authentication is skipped."""
    with auth_config(SHOULD_AUTHENTICATE=False):
      import src.app.auth

      request = create_request()
      result = src.app.auth.get_authenticated_user(request)
      assert result == "admin"

  def test_returns_admin_with_valid_cookie(self) -> None:
    """Test that get_authenticated_user returns 'admin' when valid cookie is present."""
    with auth_config(
      SHOULD_AUTHENTICATE=True, AUTHENTICATION_SECRET_KEY="test_secret_key"
    ):
      import src.app.auth

      headers = [(b"cookie", f"{AUTH_COOKIE_NAME}=test_secret_key".encode())]
      request = create_request(headers)
      result = src.app.auth.get_authenticated_user(request)
      assert result == "admin"

  def test_returns_none_with_invalid_cookie(self) -> None:
    """Test that get_authenticated_user returns None when cookie is invalid."""
    with auth_config(
      SHOULD_AUTHENTICATE=True, AUTHENTICATION_SECRET_KEY="test_secret_key"
    ):
      import src.app.auth

      headers = [(b"cookie", f"{AUTH_COOKIE_NAME}=invalid_key".encode())]
      request = create_request(headers)
      result = src.app.auth.get_authenticated_user(request)
      assert result is None

  def test_returns_none_with_no_cookie(self) -> None:
    """Test that get_authenticated_user returns None when no cookie is present."""
    with auth_config(SHOULD_AUTHENTICATE=True):
      import src.app.auth

      request = create_request()
      result = src.app.auth.get_authenticated_user(request)
      assert result is None


class TestLoginEndpoints:
  """Tests for the login page and login submission endpoints."""

  def _get_test_client(self, **env_patches: Any) -> TestClient:
    """Helper to create a test client with auth config."""
    with auth_config(**env_patches):
      import src.app.auth

      app = FastAPI()
      app.include_router(src.app.auth.router)
      return TestClient(app)

  def test_index_redirects_to_chat_when_authenticated(self) -> None:
    """Test that / redirects to /chat when user is authenticated."""
    client = self._get_test_client(SHOULD_AUTHENTICATE=False)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/chat"

  def test_index_redirects_to_login_when_not_authenticated(self) -> None:
    """Test that / redirects to /login when user is not authenticated."""
    client = self._get_test_client(SHOULD_AUTHENTICATE=True)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

  def test_login_page_returns_html(self) -> None:
    """Test that /login returns HTML with a login form."""
    client = self._get_test_client(SHOULD_AUTHENTICATE=True)
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<form" in response.text
    assert 'name="username"' in response.text
    assert 'name="password"' in response.text

  def test_login_page_redirects_to_chat_when_authenticated(self) -> None:
    """Test that /login redirects to /chat when user is already authenticated."""
    client = self._get_test_client(SHOULD_AUTHENTICATE=False)
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/chat"

  def test_login_success(self) -> None:
    """Test that correct credentials set the auth cookie and redirect to /chat."""
    client = self._get_test_client(
      SHOULD_AUTHENTICATE=True,
      AUTHENTICATION_SECRET_KEY="test_secret",
      AUTHENTICATION_USERNAME="testuser",
    )
    response = client.post(
      "/login",
      data={"username": "testuser", "password": "test_secret"},
      follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/chat"
    assert AUTH_COOKIE_NAME in response.cookies

  def test_login_failure_with_wrong_password(self) -> None:
    """Test that incorrect password returns 401 error."""
    client = self._get_test_client(
      SHOULD_AUTHENTICATE=True,
      AUTHENTICATION_SECRET_KEY="test_secret",
      AUTHENTICATION_USERNAME="testuser",
    )
    response = client.post(
      "/login",
      data={"username": "testuser", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert "Incorrect Key" in response.text

  def test_login_failure_with_wrong_username(self) -> None:
    """Test that incorrect username returns 401 error."""
    client = self._get_test_client(
      SHOULD_AUTHENTICATE=True,
      AUTHENTICATION_SECRET_KEY="test_secret",
      AUTHENTICATION_USERNAME="testuser",
    )
    response = client.post(
      "/login",
      data={"username": "wronguser", "password": "test_secret"},
    )
    assert response.status_code == 401
    assert "Incorrect Key" in response.text

  def test_login_success_when_authentication_skipped(self) -> None:
    """Test that login succeeds and redirects to /chat when authentication is skipped."""
    client = self._get_test_client(SHOULD_AUTHENTICATE=False)
    response = client.post(
      "/login",
      data={"username": "anything", "password": "anything"},
      follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/chat"
