from src.tools.external.external_typing import UnifiedRecipe
from src.tools.external.tasty_wrapper import TastyWrapper


def test_get_trending_recipes() -> None:
  """Test that Tasty tool get trending recipes works as expected."""
  # GIVEN: a Tasty get trending recipes tool
  tool_wrapper = TastyWrapper()

  # WHEN: we use the Tasty get trending recipes tool to get trending recipes
  result = tool_wrapper.get_trending_recipes.run("")

  # THEN: we get back relevant results from Tasty API
  assert all([isinstance(r, UnifiedRecipe) and r.title for r in result])
