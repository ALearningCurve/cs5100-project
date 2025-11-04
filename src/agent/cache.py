import json
from typing import Optional, Sequence

from langchain_community.cache import SQLiteCache
from langchain_core.outputs import Generation


class IDStrippingCache(SQLiteCache):
  """A cache that ignores message IDs when caching into the DB."""

  def __init__(self, db_path: str) -> None:
    """Creates a new cache instance, passing args to `SQLiteCache`.

    Args:
        db_path: path to the SQLite database file
    """
    super().__init__(db_path)

  def remove_id_from_prompt(self, prompt: str) -> str:
    """Remove the UUID from the prompt string which
    is added during serialization.

    Args:
        prompt: the prompt string

    Returns:
        prompt string without message ids
    """
    messages = json.loads(prompt)
    for message in messages:
      if "kwargs" in message and "id" in message["kwargs"]:
        del message["kwargs"]["id"]
    return json.dumps(messages)

  def lookup(self, prompt: str, llm_string: str) -> Optional[Sequence[Generation]]:
    """Look up from the cache using prompt and llm_string."""
    return super().lookup(
      prompt=self.remove_id_from_prompt(prompt),
      llm_string=llm_string,
    )

  def update(
    self, prompt: str, llm_string: str, return_val: Sequence[Generation]
  ) -> None:
    """Update the cache using the prompt, llm_string, and return value."""
    return super().update(
      prompt=self.remove_id_from_prompt(prompt),
      llm_string=llm_string,
      return_val=return_val,
    )
