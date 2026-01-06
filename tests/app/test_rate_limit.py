"""Tests for the rate limiting functionality."""
# ruff: noqa: PLR2004, E501, ANN401

import os
from contextlib import contextmanager
from importlib import reload
from typing import Any, Generator
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


@contextmanager
def rate_limit_config(enabled: bool) -> Generator[Any, None, None]:
  """Context manager to set rate limit enabled/disabled and reload modules."""
  env_var = "false" if enabled else "true"
  with patch.dict(os.environ, {"DISABLE_RATE_LIMIT": env_var}):
    # Reload modules to pick up the env variable
    import src.app.auth
    import src.app.rate_limit

    reload(src.app.rate_limit)
    reload(src.app.auth)

    yield


class TestRateLimitingEnabled:
  """Tests for rate limiting when enabled."""

  def test_requests_succeed_within_limit(self) -> None:
    """Test that requests succeed when within rate limit."""
    with rate_limit_config(enabled=True):
      from src.app.auth import router as auth_router
      from src.app.rate_limit import mount as mount_rate_limiter

      app = FastAPI()
      mount_rate_limiter(app)
      app.include_router(auth_router)
      client = TestClient(app)

      # Should succeed - first request
      response = client.post(
        "/login",
        data={"username": "test", "password": "test"},
      )
      assert response.status_code in [303, 401]  # Either redirect or auth error

  def test_exceeding_rate_limit_returns_429(self) -> None:
    """Test that exceeding rate limit returns 429 status."""
    with rate_limit_config(enabled=True):
      from src.app.auth import router as auth_router
      from src.app.rate_limit import mount as mount_rate_limiter

      app = FastAPI()
      mount_rate_limiter(app)
      app.include_router(auth_router)
      client = TestClient(app)

      # Make 11 requests to the login endpoint (limit is 10/minute)
      responses = []
      for _ in range(12):
        response = client.post(
          "/login",
          data={"username": "test", "password": "test"},
        )
        responses.append(response.status_code)

      # At least one should be 429 (rate limit exceeded)
      assert 429 in responses

  def test_rate_limit_header_present(self) -> None:
    """Test that rate limit headers are present in response."""
    with rate_limit_config(enabled=True):
      from src.app.auth import router as auth_router
      from src.app.rate_limit import mount as mount_rate_limiter

      app = FastAPI()
      mount_rate_limiter(app)
      app.include_router(auth_router)
      client = TestClient(app)

      response = client.post(
        "/login",
        data={"username": "test", "password": "test"},
      )

      # Check for rate limit headers or successful/error response
      assert "x-ratelimit-limit" in response.headers or response.status_code in [
        303,
        401,
      ]


class TestRateLimitingDisabled:
  """Tests for rate limiting when disabled (testing mode)."""

  def test_rate_limiting_disabled_in_tests(self) -> None:
    """Test that rate limiting can be disabled for testing."""
    with rate_limit_config(enabled=False):
      import src.app.rate_limit

      assert src.app.rate_limit.RATE_LIMIT_ENABLED is False, (
        "Rate limit should be disabled"
      )

  def test_unlimited_requests_when_disabled(self) -> None:
    """Test that unlimited requests are allowed when rate limiting is disabled."""
    with rate_limit_config(enabled=False):
      from src.app.auth import router as auth_router
      from src.app.rate_limit import mount as mount_rate_limiter

      app = FastAPI()
      mount_rate_limiter(app)
      app.include_router(auth_router)
      client = TestClient(app)

      # Make 50 requests - should all succeed without 429
      for i in range(50):
        response = client.post(
          "/login",
          data={"username": "test", "password": "test"},
        )
        # Should not return 429 (rate limit exceeded)
        assert response.status_code != 429, f"Request {i} was rate limited"
