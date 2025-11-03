import logging
from typing import AsyncIterator

import gradio as gr

from src.agent.agent import do_inference, setup_agent

logger = logging.getLogger(__name__)

agent = setup_agent()


async def foo(input_text: str, messages: str) -> AsyncIterator[gr.ChatMessage]:
  """Gradio chat callback to handle user input + agent response.

  Args:
      input_text: prompt from the user
      messages: previous chat messages

  Yields:
      agent generated messages (yields as they are made)
  """
  # approach inspireed by docs:
  # https://www.gradio.app/guides/agents-and-tool-usage#a-real-example-using-langchain-agents
  async for chunk in do_inference(agent, input_text):
    yield gr.ChatMessage(role="assistant", content=chunk.content)


def main() -> None:
  """Bootstraps the agentic search chat app."""
  logger.info("Starting app...")

  demo = gr.ChatInterface(
    foo,
    type="messages",
    flagging_mode="never",
    title="Agentic Search Chat App: the Cooking Guru",
    description="An agentic search chat app that helps you find "
    "cooking recipes from both your own cookbook and the web.",
    examples=[
      ["I want to make a chocolate cake.", ""],
      ["How do I cook a perfect steak?", ""],
      ["Give me a recipe for vegan lasagna.", ""],
    ],
    stop_btn=False,
  )

  demo.launch()


if __name__ == "__main__":
  main()
