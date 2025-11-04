from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool, retriever
from pydantic import BaseModel

from src.paprika.vectorstore import VectorStore

VECTORSTORE_PROMPT_TEMPLATE = (
  "-- RECIPE DOCUMENT --\n"
  "Recipe Name: {name}\n"
  "Recipe Section: {section}\n"
  "Content: {page_content}\n"
  "-- END RECIPE DOCUMENT --\n"
)


class VectorStoreTools(BaseModel):
  """Wrapper around the custom-made vector store to provide lookup tools
  for agents to use.

  Assumes that the vectorstore already has data!
  """

  vectorstore: VectorStore
  k: int = 5  # the number of results to return

  model_config = {"arbitrary_types_allowed": True}

  VECTORSTORE_PROMPT_TEMPLATE: str = (
    "-- RECIPE DOCUMENT --\n"
    "Recipe Name: {name}\n"
    "Recipe Section: {section}\n"
    "Content: {page_content}\n"
    "-- END RECIPE DOCUMENT --\n"
  )

  @property
  def recipe_retriever(self) -> Tool:
    """Creates new reciever tool for the vectorstore.

    Returns:
        Tool: the vectorstore retriever tool
    """
    prompt_template = PromptTemplate.from_template(self.VECTORSTORE_PROMPT_TEMPLATE)

    return retriever.create_retriever_tool(
      retriever=self.vectorstore.as_retriever(search_kwargs={"k": self.k}),
      name="recipe_retriever",
      description="Useful for searching for recipes relevant to a user's query.",
      document_prompt=prompt_template,
    )
