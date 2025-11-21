from typing import List, Optional

from src.env import SPOONACULAR_API_KEY
from src.tools.external.api import safe_get
from src.tools.external.external_typing import (
  Params,
  SpoonacularRandomRecipeResponse,
  SpoonacularRecipeDetailed,
  SpoonacularSearchResponse,
  SpoonacularSearchResult,
  SpoonacularSimilarResponse,
)

SPOONACULAR_BASE_URL = "https://api.spoonacular.com/recipes"
SPOONACULAR_SEARCH_URL = f"{SPOONACULAR_BASE_URL}/complexSearch"
SPOONACULAR_GET_RECIPE_POSTFIX = "information"
SPOONACULAR_RANDOM_URL = f"{SPOONACULAR_BASE_URL}/random"
SPOONACULAR_SIMILAR_POSTFIX = "similar"


class SpoonacularWrapper:
  """Wrapper class to reference Spoonacular endpoints if needed."""

  _instance: Optional["SpoonacularWrapper"] = None

  def __new__(cls) -> "SpoonacularWrapper":
    """Creates a new instance of SpoonacularWrapper if one does not exist.
    Else, returns the existing instance.

    Returns:
      Singleton instance of SpoonacularWrapper.
    """
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def _attach_api_key(self, params: Optional[Params] = None) -> Params:
    """Attaches this instance's API key to the given params, or creates new params
    with the API key if no params given.

    Args:
        params: Params to use in the request to Spoonacular. Defaults to None.

    Returns:
        Params with this instance's API key.
    """
    if not params:
      params = {}

    params["apiKey"] = SPOONACULAR_API_KEY
    return params

  def search_meal_by_name(self, meal_name: str) -> List[SpoonacularSearchResult]:
    """Calls Spoonacular search endpoint with the given meal_name.

    Returns:
        List of search results for the given meal name. Since we use {"number": 1}
        in the params, only returns one result. If no relevant meals, returns [].
    """
    response = safe_get(
      SPOONACULAR_SEARCH_URL,
      params=self._attach_api_key({"query": meal_name, "number": 1}),
      model=SpoonacularSearchResponse,
    )
    return response.results if response else []

  def get_recipe_by_id(self, recipe_id: int) -> Optional[SpoonacularRecipeDetailed]:
    """Calls Spoonacular get information about recipe from recipe id.

    Args:
        recipe_id: The id of the recipe to get more recipe information for

    Returns:
        Detailed recipe for the given recipe id or None if invalid or not found
    """
    get_recipe_url = (
      SPOONACULAR_BASE_URL + "/" + str(recipe_id) + "/" + SPOONACULAR_GET_RECIPE_POSTFIX
    )
    return (
      safe_get(
        get_recipe_url, params=self._attach_api_key(), model=SpoonacularRecipeDetailed
      )
      or None
    )

  def get_random_recipe(self) -> Optional[SpoonacularRecipeDetailed]:
    """Calls Spoonacular to get a random recipe.

    Returns:
        Detailed recipe or None if failed.
    """
    response = safe_get(
      SPOONACULAR_RANDOM_URL,
      params=self._attach_api_key({"number": 1}),
      model=SpoonacularRandomRecipeResponse,
    )
    return response.recipes[0] if (response and response.recipes) else None

  def get_similar_recipes(
    self, recipe_id: int
  ) -> Optional[List[SpoonacularSearchResult]]:
    """Calls Spoonacular to get similar recipes to the given recipe id.

    Args:
      recipe_id: Id of the recipe to get similar recipes for

    Returns:
      List of Spoonacular search results that are similar to the given recipe id.
    """
    get_similar_recipes_url = (
      SPOONACULAR_BASE_URL + "/" + str(recipe_id) + "/" + SPOONACULAR_SIMILAR_POSTFIX
    )
    response = safe_get(
      get_similar_recipes_url,
      params=self._attach_api_key({"number": 3}),
      model=SpoonacularSimilarResponse,
    )
    return response.results if (response and response.results) else None
