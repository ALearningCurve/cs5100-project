from enum import Enum
from typing import Optional

from langchain.tools import tool

from src.tools.api import safe_get

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
SEARCH_MEAL_BY_NAME_URL = f"{MEALDB_BASE_URL}/search.php"
FILTER_BY_X_URL = f"{MEALDB_BASE_URL}/filter.php"
LIST_OPTIONS_URL = f"{MEALDB_BASE_URL}/list.php"


class FilterOptionTypes(str, Enum):
  """Represents types of filter options that the agent can input to
  list_filter_options to get options to use to filter the recipes.
  """

  INGREDIENT = "i"
  CATEGORY = "c"
  AREA = "a"


class MealDBWrapper:
  """Wrapper class for LangChain tools to reference MealDB endpoints if needed."""

  @staticmethod
  @tool
  def search_meal_by_name(meal_name: str) -> str:
    """Calls MealDB search meal by name endpoint with the given meal_name.

    Use this tool to search for a recipe for a meal with a specific name.

    Args:
        meal_name: name of meal to query MealDB for a recipe for

    Returns:
        string of json response from MealDB
    """
    return safe_get(SEARCH_MEAL_BY_NAME_URL, {"s": meal_name})

  @staticmethod
  @tool
  def filter_recipes(
    ingredient: Optional[str] = None,
    category: Optional[str] = None,
    area: Optional[str] = None,
  ) -> str:
    """Calls MealDB filter by one of ingredient, category, or area.

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
    params = {
      key: value
      for key, value in {"i": ingredient, "c": category, "a": area}.items()
      if value is not None
    }

    # verify only one param is passed in
    if len(params) > 1:
      return "Could not filter with more than one keyword"

    return safe_get(FILTER_BY_X_URL, params)

  @staticmethod
  @tool
  def list_filter_options(filter_option_type: FilterOptionTypes) -> str:
    """Calls MealDB endpoint to get a list of filter options for the given type.

    Use this tool when the user asks for options for ingredients, categories, and areas
    to filter by.

    Example calls:
    - filter_recipes(FilterOptionTypes.INGREDIENT)
    - filter_recipes(FilterOptionTypes.CATEGORY)
    - filter_recipes(FilterOptionTypes.AREA)

    Args:
        filter_option_type: types of filters to get options for

    Returns:
        string of json response from MealDB containing options of things to filter by
        for the given type
    """
    return safe_get(LIST_OPTIONS_URL, {filter_option_type.value: "list"})
