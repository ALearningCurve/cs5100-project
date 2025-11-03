import logging

from src.app import App, launch

logger = logging.getLogger(__name__)


def main() -> tuple[App, str, str]:
  """Bootstraps the agentic search chat app.

  Returns:
      tuple of [gradio app, host, port]
  """
  logger.info("Starting app...")

  return launch()


if __name__ == "__main__":
  main()
