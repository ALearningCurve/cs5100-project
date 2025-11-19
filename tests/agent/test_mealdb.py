import json

from src.tools.external.external_typing import MealDBFilterOptionTypes
from src.tools.external.mealdb_wrapper import MealDBWrapper


def test_filter_recipes() -> None:
  """Test that MealDB tool filter recipes by ingredient, category, and area
  works as expected.
  """
  # GIVEN: a MealDB search tool
  tool_wrapper = MealDBWrapper()

  # WHEN: we use the mealdb tool to filter for recipes by ingredient, category,
  # area, and with multiple filters
  query_args = [
    {"ingredient": "chicken", "category": None, "area": None},
    {"ingredient": None, "category": "Seafood", "area": None},
    {"ingredient": None, "category": None, "area": "Canadian"},
    {"ingredient": "filler", "category": "filler", "area": "filler"},
  ]
  expected = [
    "brown stew chicken",
    "baked salmon with fennel & tomatoes",
    "beavertails",
    None,
  ]
  for index, args in enumerate(query_args):
    result = tool_wrapper.filter_recipes.run(args)

    # THEN: we get back relevant results or error
    expected_result = expected[index]
    if expected_result is None:
      assert result is None
    else:
      assert (
        expected_result
        in json.dumps([meal.model_dump_json() for meal in result]).lower()
      )


def test_list_filter_options() -> None:
  """Test that MealDB tool list options for filters (ingredient, category, and area)
  works as expected.
  """
  # GIVEN: a MealDB search tool
  tool_wrapper = MealDBWrapper()

  # WHEN: we use the mealdb tool to list options for filters (ingredient, category,
  # and area)
  expected = ["chicken", "seafood", "canadian"]
  for index, filter_type in enumerate(MealDBFilterOptionTypes):
    result = tool_wrapper.list_filter_options.run(filter_type)

    # THEN: we get back relevant results
    assert (
      expected[index]
      in json.dumps([option.model_dump_json() for option in result]).lower()
    )
