import json
import logging
from typing import Mapping, Optional, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from src.tools.external.api_cache import ApiCache
from src.tools.external.external_typing import Params

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def safe_get(
  url: str,
  model: Type[T],
  headers: Optional[Mapping[str, str]] = None,
  params: Optional[Params] = None,
) -> Optional[T]:
  """Sends a GET request to the given URL with the given headers and params, with try
  except to handle errors. The response is converted to type Pydantic model class T.

  Args:
    url: URL of endpoint to hit
    headers: dict of headers to append to the request
    params: dict of params to append to the request
    model: Pydantic class to parse into

  Returns:
    Pydantic model class or None
  """
  # get API cache and get response for call if cached
  api_cache = ApiCache()
  cached_response = api_cache.get_response(url, headers, params)

  # get raw json from cache or from response
  raw_json: str
  if cached_response:
    raw_json = cached_response
  else:
    # try API call since response was not cached
    try:
      response = requests.get(url, headers=headers, params=params)
      response.raise_for_status()
      data = response.json()
      raw_json = json.dumps(data)
      api_cache.set_response(api_cache.make_cache_key(url, headers, params), raw_json)
    except Exception:
      logger.exception("Unexpected error when sending GET req")
      return None

  # parse to pydantic model
  try:
    return model.model_validate_json(raw_json)
  except ValidationError:
    logger.exception(f"Validation failed for model {model.__name__}")
    return None
