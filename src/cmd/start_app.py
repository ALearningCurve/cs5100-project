import logging

from fastapi import FastAPI

from src.app import launch

logger = logging.getLogger(__name__)


def main() -> FastAPI:
  """Bootstraps the agentic search chat app."""
  logger.info("Starting app...")

  return launch()


if __name__ == "__main__":
  main()
