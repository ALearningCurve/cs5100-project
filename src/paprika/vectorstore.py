import shutil
from functools import lru_cache

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.env import REPO_ROOT
from src.paprika.chunker import Chunk

# NOTE: most of this code is adapted from LangChain docs
# article "Build a semantic search engine with LangChain"
# https://docs.langchain.com/oss/python/langchain/knowledge-base

CHROMA_ROOT = REPO_ROOT / "resources" / "chroma"


@lru_cache(1)
def _embeddings() -> Embeddings:
  return HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    show_progress=True,
  )


# TODO @ALearningCurve fine-tuning?


def connect() -> Chroma:
  # TODO @ALearningCurve
  CHROMA_ROOT.mkdir(parents=True, exist_ok=True)
  return Chroma(
    collection_name="recipes",
    embedding_function=_embeddings(),
    client_settings=Settings(anonymized_telemetry=False),
    persist_directory=str(CHROMA_ROOT),
  )


def load_chunks(chunks: list[Chunk]) -> None:
  # TODO @ALearningCurve
  if CHROMA_ROOT.exists():
    shutil.rmtree(CHROMA_ROOT)
  docs = [
    Document(page_content=chunk.content, metadata=chunk.metadata.model_dump())
    for chunk in chunks
  ]  # @ALearningCurve add metadata!

  text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=200, add_start_index=True
  )
  docs = text_splitter.split_documents(docs)

  vector_store = connect()
  vector_store.add_documents(documents=docs)
