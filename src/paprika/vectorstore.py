import logging
import shutil
from functools import lru_cache
from typing import TypeAlias

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.env import REPO_ROOT
from src.paprika.chunker import Chunk, ChunkMetadata

logger = logging.getLogger(__name__)

VectorStore: TypeAlias = Chroma

# NOTE: most of this code is adapted from LangChain docs
# article "Build a semantic search engine with LangChain"
# https://docs.langchain.com/oss/python/langchain/knowledge-base

CHROMA_ROOT = REPO_ROOT / "resources" / "chroma"
"""Directory for the chroma vector store to be persisted to"""
EMBEDDINGS_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
"""The model to use for vector/semantic search."""


@lru_cache(1)  # use LRU cache to make this a lazy loaded portion of the application
def _embeddings() -> Embeddings:
  """Get the embedding model which is used for the semanatic search.

  Returns:
      the lang chain embedding wrapper around used model
  """
  # @ALearningCurve 10-30: do we need fine-tuning of the embedding model?
  # > @ALearningCurve 11-1: after experimentation this seems to work well

  cache_path = CHROMA_ROOT / f"models/{EMBEDDINGS_MODEL_NAME}".replace("/", "--")
  if not cache_path.exists():
    logger.warning("cached vectorizer not found!")

  return HuggingFaceEmbeddings(
    model_name=EMBEDDINGS_MODEL_NAME, show_progress=True, cache_folder=str(CHROMA_ROOT)
  )


def connect(full_recipes: bool = False) -> VectorStore:
  """Create langchain connection to ChromaDB.

  Args:
    full_recipes: Flag of whether to connect to the full recipes collection.
                  Defaults to False.

  Returns:
    vectorstore langchain adapter
  """
  CHROMA_ROOT.mkdir(parents=True, exist_ok=True)
  return Chroma(
    collection_name="recipes" if not full_recipes else "full_recipes",
    embedding_function=_embeddings(),
    client_settings=Settings(anonymized_telemetry=False),
    persist_directory=str(CHROMA_ROOT),
  )


def load_chunks(chunks: list[Chunk]) -> None:
  """Given list of recipe chunks, imports those chunks to vector db.

  If a vector db already exists, calling this function REMOVES
  the entire vector db.

  Use the `connect()` function in this module to connect to the db
  populated by this function.

  Args:
      chunks: the chunks to load.
  """
  # 1. remove the db if it already exists
  if CHROMA_ROOT.exists():
    shutil.rmtree(CHROMA_ROOT)

  # 2. create the langchain documents to import
  docs = [
    Document(page_content=chunk.content, metadata=chunk.metadata.model_dump())
    for chunk in chunks
  ]

  # 3. our chunks are already small enough, but for safety
  # do splitting to avoid truncation
  text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=200, add_start_index=True
  )
  docs = text_splitter.split_documents(docs)

  # 4. connect to the db and add all the documents (this triggers embedding)
  vector_store = connect()
  vector_store.add_documents(documents=docs)


def load_full_recipes(chunks: list[Chunk]) -> None:
  """Combines chunks of a document and adds them to the database.

  Args:
    chunks: Chunks of recipes to combine into full recipes and add to the database.
  """
  # 1. merge chunks to create full_recipes
  recipe_chunks_dict: dict[str, tuple[str, ChunkMetadata]] = {}
  for chunk in chunks:
    uuid = chunk.metadata.full_doc_uuid
    full_recipe_tuple = recipe_chunks_dict.get(uuid)
    recipe_chunks_dict[uuid] = (
      (f"{full_recipe_tuple[0]}\n\n" if full_recipe_tuple else "") + chunk.content,
      chunk.metadata,
    )

  full_docs = [
    Document(
      page_content=content, metadata=metadata.to_full_recipe_metadata().model_dump()
    )
    for _, (content, metadata) in recipe_chunks_dict.items()
  ]

  # 2. add to database
  vector_store = connect(True)
  vector_store.add_documents(documents=full_docs)
