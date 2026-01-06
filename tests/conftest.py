import os

import pytest

pytest_plugins = [
  "fixtures.paprika_etl",
]


@pytest.fixture(autouse=True)
def disable_rate_limit_for_tests() -> None:
  """Disable rate limiting for all tests by default."""
  os.environ["DISABLE_RATE_LIMIT"] = "true"

  # Reload the rate_limit module to pick up the env variable
  import importlib

  import src.app.rate_limit

  importlib.reload(src.app.rate_limit)
