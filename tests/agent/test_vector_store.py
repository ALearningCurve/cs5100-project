from src.paprika.vectorstore import VectorStore
from src.tools.vector_store import VectorStoreTools


def test_vector_search_works(
  setup_vectorstores: tuple[VectorStore, VectorStore],
) -> None:
  """Test that the vectorstore tool API works as expected."""
  # GIVEN: a vectorstore populated by the ETL process
  vectorstore, full_recipe_vectorstore = setup_vectorstores

  # AND: a vectorstore tool
  tools = VectorStoreTools(
    vectorstore=vectorstore, full_recipe_vectorstore=full_recipe_vectorstore
  )
  tool = tools.recipe_retriever

  # WHEN: we use the tool to search for something we know is in the DB
  query = "How do I make chocolate chip cookies?"
  result = tool.run(query)

  # THEN: we get back relevant results
  assert "cookies" in result.lower()


def test_keyword_search_works(
  setup_vectorstores: tuple[VectorStore, VectorStore],
) -> None:
  """Test that the vectorstore tool API works as expected."""
  # GIVEN: a vectorstore populated by the ETL process
  vectorstore, full_recipe_vectorstore = setup_vectorstores

  # AND: a vectorstore tool
  tools = VectorStoreTools(
    vectorstore=vectorstore, full_recipe_vectorstore=full_recipe_vectorstore
  )
  tool = tools.recipe_retriever

  # WHEN: we use the tool to search for something we know is in the DB
  query = "chocolate chip cookies"
  result = tool.run(query)

  # THEN: we get back relevant results
  assert "cookies" in result.lower()
