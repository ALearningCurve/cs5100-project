from typing import Optional

from langchain.tools import tool

from src.tools.external.external_typing import UnifiedRecipe
from src.tools.external.mealdb_wrapper import MealDBWrapper
from src.tools.external.spoonacular_wrapper import SpoonacularWrapper


class RecipeAPI:
  """External API wrapper that searches for recipes using MealDB and Spoonacular."""

  @staticmethod
  @tool
  def search_meal_by_name(meal_name: str) -> Optional[UnifiedRecipe]:
    """Searches for a recipe by a given meal name.
    Tries MealDB then BigOven.

    Args:
      meal_name: The name of the meal to search for

    Returns:
      string response of relevant information to the meal queried
    """
    # get singleton instances of MealDB and Spoonacular Wrappers
    mealdb = MealDBWrapper()
    spoonacular = SpoonacularWrapper()

    # try MealDB
    mealdb_meals = mealdb.search_meal_by_name(meal_name)
    if mealdb_meals:
      mealdb_recipe = mealdb_meals[0]
      return UnifiedRecipe.from_mealdbmeal(mealdb_recipe=mealdb_recipe)

    # if couldn't find use spoonacular
    spoonacular_meals = spoonacular.search_meal_by_name(meal_name)
    if spoonacular_meals:
      recipe_id = spoonacular_meals[0].id
      spoonacular_recipe = spoonacular.get_recipe_by_id(recipe_id)
      if spoonacular_recipe:
        similar_recipes = spoonacular.get_similar_recipes(recipe_id)
        return UnifiedRecipe.from_spoonacular_recipe_detailed(
          spoonacular_recipe=spoonacular_recipe, similar_recipes=similar_recipes
        )

    return None

  @staticmethod
  @tool
  def get_random_recipe(tool_input: str = "") -> Optional[UnifiedRecipe]:
    """Gets a random recipe from Spoonacular.

    Use this tool to get a random recipe.

    Args:
      tool_input: LangChain required argument, but ignored/unused here

    Returns:
      Random UnifiedRecipe or None if failed.
    """
    spoonacular = SpoonacularWrapper()
    recipe = spoonacular.get_random_recipe()
    if recipe:
      similar_recipes = spoonacular.get_similar_recipes(recipe.id)
      return UnifiedRecipe.from_spoonacular_recipe_detailed(
        spoonacular_recipe=recipe, similar_recipes=similar_recipes
      )

    return None
