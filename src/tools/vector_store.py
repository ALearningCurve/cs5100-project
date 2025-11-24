from typing import Any, List, Optional

from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.tools import Tool, retriever
from langchain_core.vectorstores import VectorStoreRetriever
from pydantic import BaseModel

from src.paprika.vectorstore import VectorStore


class VectorStoreTools(BaseModel):
  """Wrapper around the custom-made vector store to provide lookup tools
  for agents to use.

  Assumes that the vectorstore already has data!
  """

  vectorstore: VectorStore
  full_recipe_vectorstore: VectorStore
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
      retriever=HybridRetriever(
        vectorstore=self.vectorstore,
        full_recipe_vectorstore=self.full_recipe_vectorstore,
      ),
      name="recipe_retriever",
      description="Useful for searching for recipes relevant to a user's query.",
      document_prompt=prompt_template,
    )


class HybridRetriever(BaseRetriever):
  """Hybrid retriever to utilize both keyword search and semantic vector search."""

  # define class vars for pydantic
  vectorstore: VectorStore
  full_recipe_vectorstore: VectorStore

  # defaulted vars
  k: int = 5
  rrf_k: int = 60  # smoothing constant of RRF
  bm25_weight: float = 0.4
  vector_weight: float = 0.6

  # defined in __init__
  bm25: Optional[BM25Retriever] = None
  vector_retriever: Optional[VectorStoreRetriever] = None

  def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401, need kwargs for BaseRetriever Pydantic
    """Creates an instance of HybridRetriever with the given vectorstore.

    Args:
      kwargs: Keyword args to pass into the BaseRetriever
    """
    super().__init__(**kwargs)

    # 1. create BM25 retriever
    num_docs = self.vectorstore._collection.count()
    chunks = self.vectorstore.similarity_search("", k=num_docs)
    self.bm25 = BM25Retriever.from_documents(chunks)
    self.bm25.k = self.k

    # 2. create vector retriever
    self.vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.k})

  def _get_relevant_documents(
    self, query: str, *, run_manager: CallbackManagerForRetrieverRun
  ) -> List[Document]:
    """Implements hybrid search using RRF to determine the most relevant documents
    for the given query.

    More information about RRF here:
    https://medium.com/@shubhamsarkar996/hybrid-search-in-rag-concept-of-weighted-reciprocal-rank-fusion-rrf-part-1-ae570d9c1879

    Args:
      query: Query to get relevant documents for
      run_manager: Manager that handles callbacks and traces

    Returns:
      List of complete documents relevant to the given query.
    """
    if self.bm25 is None or self.vector_retriever is None:
      err_msg = "HybridRetriever not fully initialized."
      raise ValueError(err_msg)

    # 1. get results from both retrievers
    bm25_results = self.bm25._get_relevant_documents(query, run_manager=run_manager)
    vector_results = self.vector_retriever._get_relevant_documents(
      query, run_manager=run_manager
    )

    # 2. calculated weighted RRF scores
    rrf_scores: dict[str, tuple[Document, float]] = {}
    for rank, doc in enumerate(bm25_results):
      uuid = doc.metadata["full_doc_uuid"]
      doc_score = self.bm25_weight / (self.rrf_k + rank + 1)
      rrf_scores[uuid] = (doc, doc_score)

    for rank, doc in enumerate(vector_results):
      uuid = doc.metadata["full_doc_uuid"]
      doc_score = self.bm25_weight / (self.rrf_k + rank + 1)

      if uuid in rrf_scores:
        rrf_scores[uuid] = (doc, rrf_scores[uuid][1] + doc_score)
      else:
        rrf_scores[uuid] = (doc, doc_score)

    # 3. return the top k scored docs by sorting by score desc
    sorted_docs = sorted(rrf_scores.values(), key=lambda x: x[1], reverse=True)
    docs_to_return = [doc[0] for doc in sorted_docs[: self.k]]
    return self._get_complete_documents(docs_to_return)

  def _get_complete_documents(self, chunks: List[Document]) -> List[Document]:
    """Querying function that gets the full documents for relevant chunks.

    Args:
      chunks: Checks to get the full document for

    Returns:
      List of complete documents from the chunks given
    """
    # 1. get uuids of relevant documents and store index as measure of relevance
    # (low = more relevant)
    recipe_map: dict[str, int] = {}
    for i, chunk in enumerate(chunks):
      uuid = chunk.metadata.get("full_doc_uuid")
      if uuid and uuid not in recipe_map:
        recipe_map[uuid] = i

    # 2. get full documents
    docs = []
    for uuid, _ in sorted(recipe_map.items(), key=lambda x: x[1]):
      single_doc = self.full_recipe_vectorstore.similarity_search(
        "", k=1, filter={"uuid": uuid}
      )[0]
      docs.append(single_doc)

    return docs
