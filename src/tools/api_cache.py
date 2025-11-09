import sqlite3
from typing import Optional
from urllib.parse import urlencode

from src.env import API_CACHE_DB_PATH

CREATE_API_CACHE_STR = """
    CREATE TABLE IF NOT EXISTS api_cache (
        key TEXT PRIMARY KEY,
        response TEXT
    )
"""


class ApiCache:
  """A persistent cache that stores API calls and responses."""

  _instance: Optional["ApiCache"] = None  # class level instance

  def __new__(cls, *args: object, **kwargs: object) -> "ApiCache":
    """Create singleton for persistent API cache.

    Args:
        *args: args for the constructor
        **kwargs: keyword args for the constructor

    Returns:
        singleton of ApiCache
    """
    if not cls._instance:
      cls._instance = super(ApiCache, cls).__new__(cls, *args, **kwargs)
    return cls._instance

  def __init__(self) -> None:
    """Returns singleton of ApiCache with initialized SQLite database if exists.
    Else initializes an SQLite database and table for the API cache.
    """
    # if initialized don't initialize
    if hasattr(self, "_initialized") and self._initialized:
      return

    # create database and table
    API_CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    self.conn = sqlite3.connect(str(API_CACHE_DB_PATH))
    self.cursor = self.conn.cursor()
    self.cursor.execute(CREATE_API_CACHE_STR)
    self.conn.commit()

  def make_cache_key(self, url: str, params: dict[str, str] | None) -> str:
    """Takes in URL and params for the API call and turns it into key for cache.

    Args:
        url: the URL of the API call
        params: queries to include in the API call

    Returns:
        the complete URL string the API call is to, including queries
    """
    url_postfix = ""
    if params is not None:
      sorted_params = dict(sorted(params.items()))
      url_postfix = f"?{urlencode(sorted_params)}"

    return url + url_postfix

  def get_response(self, url: str, params: dict[str, str] | None) -> str:
    """Tries to get the response for the API call if it exists in the database.
    Else returns empty string.

    Args:
        url: the URL of the API call
        params: queries to include in the API call

    Returns:
        either the response from the API call or None
    """
    key = self.make_cache_key(url, params)
    return (
      self.cursor.execute(
        "SELECT response FROM api_cache WHERE key=?", (key,)
      ).fetchone()
      or ""
    )

  def set_response(self, key: str, response: str) -> None:
    """Tries to get the response for the API call if it exists in the database.
    Else returns None.

    Args:
        key: the key to set within the database
        response: the response to store within the database with the given key

    Returns:
        either the response from the API call or None
    """
    self.cursor.execute(
      "INSERT OR REPLACE INTO api_cache (key, response) VALUES (?, ?)", (key, response)
    )
    self.conn.commit()
