import os

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# Disable rate limiter during testing
RATE_LIMIT_ENABLED = os.getenv("DISABLE_RATE_LIMIT", "false").lower() != "true"

limiter = Limiter(
  key_func=get_remote_address,
  default_limits=["60/minute"],
  enabled=RATE_LIMIT_ENABLED,
)


def mount(app: FastAPI) -> None:
  """Adds rate limiter."""
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
  app.add_middleware(SlowAPIMiddleware)
