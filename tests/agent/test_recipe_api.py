from src.tools.external.external_typing import UnifiedRecipe
from src.tools.external.recipe_api import RecipeAPI


def test_search_meal_by_name_mealdb() -> None:
  """Test that RecipeAPI tool search meal by name works as expected using MealDB API."""
  # GIVEN: a RecipeAPI search tool
  tool_wrapper = RecipeAPI()

  # WHEN: we use the RecipeAPI tool to search for a meal we dont have in the database
  query = "katsu chicken curry"
  result = tool_wrapper.search_meal_by_name.run(query)

  # THEN: we get back relevant results from MealDB API
  assert query in result.model_dump_json().lower()


def test_search_meal_by_name_spoonacular() -> None:
  """Test that RecipeAPI tool search meal by name works as expected
  using Spoonacular.
  """
  # GIVEN: a RecipeAPI search tool
  tool_wrapper = RecipeAPI()

  # WHEN: we use the RecipeAPI tool to search for a meal we dont have in the database
  query = "skirt steak fajitas"
  result = tool_wrapper.search_meal_by_name.run(query)

  # THEN: we get back relevant results from Spoonacular API
  assert query in result.model_dump_json().lower()


def test_get_random_recipe() -> None:
  """Test that RecipeAPI tool get random recipe works as expected."""
  # GIVEN: a RecipeAPI search tool
  tool_wrapper = RecipeAPI()

  # WHEN: we use the RecipeAPI tool to search for a meal we dont have in the database
  result = tool_wrapper.get_random_recipe.run("")

  # THEN: we get back relevant results from Spoonacular API
  assert isinstance(result, UnifiedRecipe) and result.title
