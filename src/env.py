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


PAPRIKA_EXPORT_PATH = Path(
  get("PAPRIKA_EXPORT_PATH", str(REPO_ROOT / "resources/paprika/export.paprikarecipes"))
)

AGENT_CACHE_DB_PATH = Path(
  get("AGENT_CACHE_DB_PATH", str(REPO_ROOT / "resources/agent/langchain_cache.db"))
)

API_CACHE_DB_PATH = Path(
  get("API_CACHE_DB_PATH", str(REPO_ROOT / "resources/tools/api_cache.db"))
)

GEMINI_API_KEY = _get_or_fail("GEMINI_API_KEY")
