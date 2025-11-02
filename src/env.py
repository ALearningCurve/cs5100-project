import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).parents[1]
load_dotenv(REPO_ROOT / ".env")


def _get_or_fail(key: str) -> str:
  """Gets environment variable with name corresponding to key. If
  not defined, then panic.

  Args:
      key: environment variable to access

  Returns:
      value of environment variable
  """
  val = os.environ.get(key)
  assert val is not None and len(val.strip()) != 0, (
    f"wanted value for {key=}, instead got {val=}"
  )
  return val


# GOOGLE_API_KEY = _get_or_fail("GOOGLE_API_KEY")

PAPRIKA_EXPORT_PATH = Path(
  os.environ.get(
    "PAPRIKA_EXPORT_PATH", str(REPO_ROOT / "resources/paprika/export.paprikarecipes")
  )
)
