from src.tools.mealdb_wrapper import FilterOptionTypes, MealDBWrapper


def test_search_meal_by_name() -> None:
  """Test that MealDB tool search meal by name works as expected."""
  # GIVEN: a MealDB search tool
  tool_wrapper = MealDBWrapper()

  # WHEN: we use the mealdb tool to search for a meal we dont have in the database
  query = "katsu chicken curry"
  result = tool_wrapper.search_meal_by_name.run(query)

  # THEN: we get back relevant results
  assert query in result.lower()


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
    "Brown Stew Chicken",
    "Baked salmon with fennel & tomatoes",
    "BeaverTails",
    "Could not filter with more than one keyword",
  ]
  for index, args in enumerate(query_args):
    result = tool_wrapper.filter_recipes.run(args)

    # THEN: we get back relevant results or error
    assert expected[index].lower() in result.lower()


def test_list_filter_options() -> None:
  """Test that MealDB tool list options for filters (ingredient, category, and area)
  works as expected.
  """
  # GIVEN: a MealDB search tool
  tool_wrapper = MealDBWrapper()

  # WHEN: we use the mealdb tool to list options for filters (ingredient, category,
  # and area)
  expected = ["chicken", "seafood", "canadian"]
  for index, filter_type in enumerate(FilterOptionTypes):
    result = tool_wrapper.list_filter_options.run(filter_type)

    # THEN: we get back relevant results
    assert expected[index] in result.lower()
