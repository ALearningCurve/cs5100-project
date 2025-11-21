from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


# ========== MEALDB ========== #
class MealDBMeal(BaseModel):
  """Data class to represent a meal from MealDB."""

  id_meal: str = Field(alias="idMeal")
  str_meal: str = Field(alias="strMeal")
  str_meal_alteranate: Optional[str] = Field(None, alias="strMealAlternate")
  str_category: str = Field(alias="strCategory")
  str_area: str = Field(alias="strArea")
  str_instructions: str = Field(alias="strInstructions")
  str_meal_thumb: str = Field(alias="strMealThumb")
  str_tags: Optional[str] = Field(None, alias="strTags")
  str_youtube: Optional[str] = Field(None, alias="strYouTube")

  class Config:
    """Config class for MealDBMeal."""

    extra = "allow"

  @property
  def ingredients(self) -> List[str]:
    """Property that parses ingredients and their measurements from MealDB.
    This is because it comes in as "strIngredient1" ... "strIngredient20"
    and "strMeasure1" ... "strMeasure20".

    Returns:
      List of strings representing ingredients and their measurements if they exist.
    """
    result: List[str] = []
    for i in range(1, 21):
      ingredient = getattr(self, f"strIngredient{i}", None)
      measure = getattr(self, f"strMeasure{i}", None)
      if ingredient and ingredient.strip():
        result.append(
          f"{measure.strip()} {ingredient.strip()}" if measure else ingredient.strip()
        )
    return result


class MealDBSearchResponse(BaseModel):
  """Data class to represent response from MealDB search API."""

  meals: Optional[List[MealDBMeal]]


class MealDBFilterOptionTypes(str, Enum):
  """Represents types of filter options that the agent can input to
  list_filter_options to get options to use to filter the recipes.
  """

  INGREDIENT = "i"
  CATEGORY = "c"
  AREA = "a"


class MealDBFilterMeal(BaseModel):
  """Data class to represent a filtered meal."""

  id_meal: str = Field(alias="idMeal")
  str_meal: str = Field(alias="strMeal")
  str_meal_thumb: str = Field(alias="strMealThumb")


class MealDBFilterResponse(BaseModel):
  """Data class to represent a response for MealDB filter API."""

  meals: Optional[List[MealDBFilterMeal]]


class MealDBFilterOption(BaseModel):
  """Data class to represent filter options results for MealDB filter API."""

  id_ingredient: Optional[int] = Field(None, alias="idIngredient")
  str_ingredient: Optional[str] = Field(None, alias="strCategory")
  str_description: Optional[str] = Field(None, alias="strDescription")
  str_category: Optional[str] = Field(None, alias="strCategory")
  str_area: Optional[str] = Field(None, alias="strArea")


class MealDBFilterOptionResponse(BaseModel):
  """Data class to represent a response for MealDB filter options API."""

  meals: List[MealDBFilterOption]


# ========== SPOONACULAR ========== #
class SpoonacularSearchResult(BaseModel):
  """Data class to represent a result from Spoonacular search API."""

  id: int
  title: str
  image: Optional[HttpUrl] = None
  image_type: Optional[str] = Field(None, alias="imageType")


class SpoonacularIngredient(BaseModel):
  """Data class to represent an ingredient and its details from Spoonacular."""

  id: Optional[int] = None
  name: str
  amount: Optional[float] = None
  unit: Optional[str] = None
  original: Optional[str] = None


class SpoonacularRecipeDetailed(BaseModel):
  """Data class to represent a detailed recipe from Spoonacular GET recipe API."""

  id: int
  title: str
  image: Optional[HttpUrl] = None
  source_url: Optional[HttpUrl] = Field(None, alias="sourceUrl")

  servings: Optional[int] = None
  ready_in_minutes: Optional[int] = Field(None, alias="readyInMinutes")
  cuisines: List[str] = []
  dish_types: List[str] = Field([], alias="dishTypes")

  instructions: Optional[str] = None
  extended_ingredients: List[SpoonacularIngredient] = Field(
    [], alias="extendedIngredients"
  )


class SpoonacularRandomRecipeResponse(BaseModel):
  """Data class to represent a response from Spoonacular random recipe API."""

  recipes: List[SpoonacularRecipeDetailed] = []


class SpoonacularSearchResponse(BaseModel):
  """Data class to represent a response from Spoonacular search API."""

  results: List[SpoonacularSearchResult] = []
  offset: Optional[int] = None
  number: Optional[int] = None
  total_results: Optional[int] = Field(None, alias="totalResults")


class SpoonacularSimilarResponse(BaseModel):
  """Data class to represent a response from Spoonacular similar recipes API."""

  results: List[SpoonacularSearchResult] = []


# ========== TASTY ========== #


class TastyComponent(BaseModel):
  """Data class to represent a Tasty component or ingredient."""

  raw_text: str
  extra_comment: Optional[str] = None


class TastySection(BaseModel):
  """Data class to represent a Tasty section, or list of ingredients."""

  name: Optional[str] = None
  components: List[TastyComponent]


class TastyTag(BaseModel):
  """Data class to represent a Tasty tag."""

  name: str
  id: int
  display_name: str
  type: str


class TastyInstruction(BaseModel):
  """Data class to represent a Tasty instruction."""

  display_text: str


class TastyTrendingRecipe(BaseModel):
  """Data class to represent a Tasty recipe."""

  id: int
  name: Optional[str] = ""
  slug: Optional[str] = ""
  seo_title: Optional[str] = ""
  instructions: Optional[List[TastyInstruction]] = []
  sections: List[TastySection] = []
  tags: Optional[List[TastyTag]] = []
  thumbnail_url: Optional[HttpUrl] = None
  video_url: Optional[HttpUrl] = None


class TastyGetTrendingResult(BaseModel):
  """Data class to represent a Tasty trending result."""

  name: Optional[str] = None
  items: List[TastyTrendingRecipe] = []


class TastyGetTrendingResponse(BaseModel):
  """Data class to represent a Tasty response from trending feed API."""

  results: List[TastyGetTrendingResult]


# ========== CUSTOM ========== #
class UnifiedRecipe(BaseModel):
  """Data class to represent a structured LLM-understandable recipe from
  either MealDB or Spoonacular.
  """

  id: str
  title: str
  category: Optional[str]
  area: Optional[str]
  instructions: Optional[str]
  ingredients: List[str]
  image_url: Optional[str] = None
  source_url: Optional[str] = None
  similar_recipes: Optional[List[SpoonacularSearchResult]] = None

  @classmethod
  def from_mealdbmeal(cls, mealdb_recipe: MealDBMeal) -> "UnifiedRecipe":
    """Initializes instance of UnifiedRecipe using MealDBMeal.

    Args:
      mealdb_recipe: MealDBMeal to convert to UnifiedRecipe

    Returns:
      Given MealDBMeal as UnifiedRecipe
    """
    ingredients = [
      value
      for key, value in mealdb_recipe.model_dump().items()
      if key.startswith("strIngredient") and value
    ]
    return cls(
      id=mealdb_recipe.id_meal,
      title=mealdb_recipe.str_meal,
      category=mealdb_recipe.str_category,
      area=mealdb_recipe.str_area,
      instructions=mealdb_recipe.str_instructions,
      ingredients=ingredients,
      image_url=mealdb_recipe.str_meal_thumb,
      source_url=mealdb_recipe.str_youtube,
    )

  @classmethod
  def from_spoonacular_recipe_detailed(
    cls,
    spoonacular_recipe: SpoonacularRecipeDetailed,
    similar_recipes: Optional[List[SpoonacularSearchResult]],
  ) -> "UnifiedRecipe":
    """Initializes instance of UnifiedRecipe using SpoonacularRecipeDetailed.

    Args:
      spoonacular_recipe: SpoonacularRecipeDetailed to convert to UnifiedRecipe
      similar_recipes: List of SpoonacularSearchResult that are similar to this recipe

    Returns:
      Given SpoonacularRecipeDetailed as UnifiedRecipe
    """
    return cls(
      id=str(spoonacular_recipe.id),
      title=spoonacular_recipe.title,
      category=(
        spoonacular_recipe.dish_types[0] if spoonacular_recipe.dish_types else None
      ),
      area=(spoonacular_recipe.cuisines[0] if spoonacular_recipe.cuisines else None),
      instructions=spoonacular_recipe.instructions,
      ingredients=[
        ingredient.original or ingredient.name
        for ingredient in spoonacular_recipe.extended_ingredients
      ],
      image_url=str(spoonacular_recipe.image),
      source_url=str(spoonacular_recipe.source_url),
      similar_recipes=similar_recipes,
    )

  @classmethod
  def from_tasty(cls, tasty_recipe: TastyTrendingRecipe) -> "UnifiedRecipe":
    """Initializes instance of UnifiedRecipe using TastyTrendingRecipe.

    Args:
      tasty_recipe: TastyTrendingRecipe to convert to UnifiedRecipe

    Returns:
      Given TastyTrendingRecipe as UnifiedRecipe
    """
    # ingredients is a list nested down, so
    ingredients = (
      [
        (
          component.raw_text
          + (component.extra_comment if component.extra_comment else "")
        )
        for component in tasty_recipe.sections[0].components
      ]
      if tasty_recipe.sections
      else []
    )

    # parse tags for cuisine type and category type
    cuisine: Optional[str] = None
    category: Optional[str] = None
    if tasty_recipe.tags:
      for tag in tasty_recipe.tags:
        if tag.type == "cuisine" and cuisine is None:
          cuisine = tag.display_name
        elif tag.type in ["dietary", "meal"] and category is None:
          category = tag.display_name

        if tag and category:
          break

    return cls(
      id=str(tasty_recipe.id),
      title=tasty_recipe.name or tasty_recipe.slug or tasty_recipe.seo_title or "",
      category=category,
      area=cuisine,
      instructions="\n".join(
        [instruction.display_text.strip() for instruction in tasty_recipe.instructions]
        if tasty_recipe.instructions
        else []
      ),
      ingredients=ingredients,
      image_url=str(tasty_recipe.thumbnail_url),
      source_url=str(tasty_recipe.video_url),
    )


Params = Dict[str, Union[str, int]]
