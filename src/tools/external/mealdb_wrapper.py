import logging
from typing import List, Optional

from langchain.tools import tool

from src.tools.external.api import safe_get
from src.tools.external.external_typing import (
  MealDBFilterMeal,
  MealDBFilterOption,
  MealDBFilterOptionResponse,
  MealDBFilterOptionTypes,
  MealDBFilterResponse,
  MealDBMeal,
  MealDBSearchResponse,
  Params,
)

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
SEARCH_MEAL_BY_NAME_URL = f"{MEALDB_BASE_URL}/search.php"
FILTER_BY_X_URL = f"{MEALDB_BASE_URL}/filter.php"
LIST_OPTIONS_URL = f"{MEALDB_BASE_URL}/list.php"

logger = logging.getLogger(__name__)


class MealDBWrapper:
  """Wrapper class to reference MealDB endpoints if needed."""

  _instance: Optional["MealDBWrapper"] = None

  def __new__(cls) -> "MealDBWrapper":
    """Creates a new instance of SpoonacularWrapper if one does not exist.
    Else, returns the existing instance.

    Returns:
      Singleton instance of SpoonacularWrapper.
    """
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  @staticmethod
  def search_meal_by_name(meal_name: str) -> Optional[List[MealDBMeal]]:
    """Calls MealDB search meal by name endpoint with the given meal_name.

    Args:
        meal_name: name of meal to query MealDB for a recipe for

    Returns:
        string of json response from MealDB representing info about the meal
    """
    response = safe_get(
      SEARCH_MEAL_BY_NAME_URL, params={"s": meal_name}, model=MealDBSearchResponse
    )
    return response.meals if response else None

  @staticmethod
  @tool
  def filter_recipes(
    ingredient: Optional[str] = None,
    category: Optional[str] = None,
    area: Optional[str] = None,
  ) -> Optional[List[MealDBFilterMeal]]:
    """EXTERNAL TOOL: Find external recipes, calls MealDB filter by one of ingredient,
    category, or area.

    Use this tool when the user asks for recipes "with ingredient", "from area", and
    "within category". Only include one parameters at a time, you cannot call this
    function with multiple parameters like ingredient and cateogry.

    Example calls:
    - filter_recipes(ingredient="chicken")
    - filter_recipes(category="Seafood")
    - filter_recipes(area="Canada")

    Args:
        ingredient: main ingredient to filter meals for (i.e. Chicken)
        category: category to filter meals for (i.e. Seafood)
        area: area to filter meals for (i.e. Canada)

    Returns:
        string of json response from MealDB containing meals with main ingredient
    """
    # only include in params if the function is called with it
    params: Params = {
      key: value
      for key, value in {"i": ingredient, "c": category, "a": area}.items()
      if value is not None
    }

    # verify only one param is passed in
    if len(params) > 1:
      logger.warning("Could not filter with more than one keyword")
      return None

    response = safe_get(FILTER_BY_X_URL, params=params, model=MealDBFilterResponse)
    return response.meals if response else None

  @staticmethod
  @tool
  def list_filter_options(
    filter_option_type: MealDBFilterOptionTypes,
  ) -> Optional[List[MealDBFilterOption]]:
    """EXTERNAL TOOL: Find external recipes, calls MealDB endpoint to get a list of
    filter options for the given type.

    Use this tool when the user asks for options for ingredients, categories, and areas
    to filter by or before attempting to use 'filter_recipes' tool.

    Example calls:
    - filter_recipes(MealDBFilterOptionTypes.INGREDIENT)
    - filter_recipes(MealDBFilterOptionTypes.CATEGORY)
    - filter_recipes(MealDBFilterOptionTypes.AREA)

    Args:
        filter_option_type: types of filters to get options for

    Returns:
        string of json response from MealDB containing options of things to filter by
        for the given type
    """
    response = safe_get(
      LIST_OPTIONS_URL,
      params={filter_option_type.value: "list"},
      model=MealDBFilterOptionResponse,
    )
    return response.meals if response else None
