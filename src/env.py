import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).parents[1]

env_file = REPO_ROOT / ".env"
if env_file.exists():
  load_dotenv(env_file)
else:
  logger.warning(".env file not found at %s", env_file)

get = os.environ.get


def _get_or_fail(key: str) -> str:
  """Gets environment variable with name corresponding to key. If
  not defined, then panic.

  Args:
      key: environment variable to access

  Returns:
      value of environment variable
  """
  val = get(key)
  assert val is not None and len(val.strip()) != 0, (
    f"wanted value for {key=}, instead got {val=}"
  )
  return val


def disable_gradio_tracking() -> None:
  """Disables gradio telemetry."""
  os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")


disable_gradio_tracking()

# 1. setup env vars for the ETL/Agent persistent storage

PAPRIKA_EXPORT_PATH = Path(
  get("PAPRIKA_EXPORT_PATH", str(REPO_ROOT / "resources/paprika/export.paprikarecipes"))
)

AGENT_CACHE_DB_PATH = Path(
  get("AGENT_CACHE_DB_PATH", str(REPO_ROOT / "resources/agent/langchain_cache.db"))
)

API_CACHE_DB_PATH = Path(
  get("API_CACHE_DB_PATH", str(REPO_ROOT / "resources/tools/api_cache.db"))
)

# 2. setup env vars for API keys

GEMINI_API_KEY = _get_or_fail("GEMINI_API_KEY")
SPOONACULAR_API_KEY = _get_or_fail("SPOONACULAR_API_KEY")
RAPIDAPI_API_KEY = _get_or_fail("RAPIDAPI_API_KEY")


# 3. setup env vars for the authentication
AUTHENTICATION_SECRET_KEY = get("AUTHENTICATION_SECRET_KEY")
AUTHENTICATION_USERNAME = get("AUTHENTICATION_USERNAME")
assert (AUTHENTICATION_SECRET_KEY is None) == (AUTHENTICATION_USERNAME is None), (
  "Partial authentication provided (key or username) but not the other"
)
SHOULD_AUTHENTICATE = AUTHENTICATION_SECRET_KEY is not None
if not SHOULD_AUTHENTICATE:
  logger.critical("authentication disabled!")
