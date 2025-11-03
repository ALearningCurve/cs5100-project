from src.agent.tools import VectorStoreTools
from src.paprika.vectorstore import VectorStore


def test_tool_api_works(setup_vectorstore: VectorStore) -> None:
  """Test that the vectorstore tool API works as expected."""
  # GIVEN: a vectorstore populated by the ETL process
  vectorstore = setup_vectorstore

  # AND: a vectorstore tool
  tools = VectorStoreTools(vectorstore=vectorstore)
  tool = tools.recipe_retriever

  # WHEN: we use the tool to search for something we know is in the DB
  query = "How do I make chocolate chip cookies?"
  result = tool.run(query)

  # THEN: we get back relevant results
  assert "cookies" in result.lower()
