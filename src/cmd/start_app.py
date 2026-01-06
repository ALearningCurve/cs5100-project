import logging

from src.app import launch

logger = logging.getLogger(__name__)


def main() -> None:
  """Bootstraps the agentic search chat app."""
  logger.info("Starting app...")

  return launch()


if __name__ == "__main__":
  main()
