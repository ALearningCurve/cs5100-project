from typing import List, Optional

from langchain.tools import tool

from src.env import RAPIDAPI_API_KEY
from src.tools.external.api import safe_get
from src.tools.external.external_typing import (
  Params,
  TastyGetTrendingResponse,
  UnifiedRecipe,
)

RAPIDAPI_HOST = "tasty.p.rapidapi.com"


class TastyWrapper:
  """Wrapper class to reference Tasty endpoints if needed."""

  @staticmethod
  @tool
  def get_trending_recipes(tool_input: str = "") -> Optional[List[UnifiedRecipe]]:
    """Calls Tasty API to get trending recipes and converts them to UnifiedRecipe type.

    Use this tool to get trending recipes.

    Args:
      tool_input: LangChain required argument, but ignored/unused here

    Returns:
      List of UnifiedRecipe, where each represents a Tasty trending recipe.
    """
    get_trending_recipes_url = f"https://{RAPIDAPI_HOST}/feeds/list"
    headers = {"x-rapidapi-host": RAPIDAPI_HOST, "x-rapidapi-key": RAPIDAPI_API_KEY}
    params: Params = {"from": 0, "size": 5, "vegetarian": False, "timezone": "-0500"}

    response = safe_get(
      get_trending_recipes_url,
      headers=headers,
      params=params,
      model=TastyGetTrendingResponse,
    )
    results = response.results if response else []
    trending_result = [
      result for result in results if result.name and result.name.lower() == "trending"
    ]
    if trending_result:
      tasty_trending_recipes = trending_result[0].items
      return [
        UnifiedRecipe.from_tasty(tasty_recipe=recipe)
        for recipe in tasty_trending_recipes
      ]
    return []
