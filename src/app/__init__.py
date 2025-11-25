import logging
from functools import partial
from typing import AsyncIterator

import gradio as gr
from gradio.routes import App as App

from src.agent.agent import setup_agent
from src.agent.agentic_rag import Workflow, do_inference
from src.app.langchain_adapter import render

logger = logging.getLogger(__name__)


async def handle_input(
  graph: Workflow, input_text: str, messages: list[gr.ChatMessage]
) -> AsyncIterator[list[gr.ChatMessage]]:
  """Gradio chat callback to handle user input + agent response.

  Args:
      graph: the workflow to use for inference
      input_text: prompt from the user
      messages: previous chat messages

  Yields:
      workflow generated messages (yields as they are made)
  """
  new_messages = []
  # approach inspired by docs:
  # https://www.gradio.app/guides/agents-and-tool-usage#a-real-example-using-langchain-agents
  # messages.append(gr.ChatMessage(content=input_text, role="user"))
  async for chunk in do_inference(graph, input_text):
    for chat_message in render(chunk):
      new_messages.append(chat_message)
      yield new_messages


def launch() -> tuple[App, str, str]:
  """Bootstraps the agentic search chat app.

  Returns:
      tuple of [gradio app, host, port]
  """
  logger.info("Starting app...")

  workflow = setup_agent()
  demo = gr.ChatInterface(
    partial(handle_input, workflow),
    type="messages",
    flagging_mode="never",
    title="Agentic Search Chat App: the Cooking Guru",
    description="Hi, I'm Cheffy!\n Ask me anything cooking related - I can help you "
    "search your own cookbook, the web, or even surprise you with new recipes!",
    examples=[
      ["I want to make a chocolate chip cookies.", ""],
      ["How do I cook a perfect steak?", ""],
      ["Give me a recipe for vegan lasagna.", ""],
    ],
    stop_btn=False,
  )

  return demo.launch()
