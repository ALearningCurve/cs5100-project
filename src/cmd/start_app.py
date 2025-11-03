import logging

from src.paprika.vectorstore import connect

logger = logging.getLogger(__name__)


def main() -> None:
  """Bootstraps the agentic search chat app."""
  logger.info("Starting app...")

  vector_store = connect()

  q = "dish with chicken"
  results = vector_store.similarity_search(q, k=10)
  print(f"RAG vector search for: '{q}'")
  for result in results:
    print(result.metadata["name"])


if __name__ == "__main__":
  main()
