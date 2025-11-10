import json

import requests

from src.tools.api_cache import ApiCache


def safe_get(url: str, params: dict[str, str] | None = None) -> str:
  """Sends a GET request to the given URL with the given params, with try except to
  handle errors.

  Args:
      url: url of endpoint to hit
      params: dict of params to append to the request

  Returns:
      string of json response from the endpoint
  """
  # get API cache and get response for call if cached
  api_cache = ApiCache()
  cached_response = api_cache.get_response(url, params)

  # return if cached
  if cached_response:
    return cached_response

  # try API call since response was not cached
  try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return json.dumps(data)
  except Exception as e:
    return f"Unexpected error when sending GET req: {e}"
