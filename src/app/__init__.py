import logging
from functools import partial
from typing import AsyncIterator

import gradio as gr
from gradio.routes import App as App

from src.agent.agent import Agent, do_inference, setup_agent
from src.app.langchain_adapter import render

logger = logging.getLogger(__name__)


async def handle_input(
  agent: Agent, input_text: str, messages: list[gr.ChatMessage]
) -> AsyncIterator[list[gr.ChatMessage]]:
  """Gradio chat callback to handle user input + agent response.

  Args:
      agent: the agent to use for inference
      input_text: prompt from the user
      messages: previous chat messages

  Yields:
      agent generated messages (yields as they are made)
  """
  new_messages = []
  # approach inspired by docs:
  # https://www.gradio.app/guides/agents-and-tool-usage#a-real-example-using-langchain-agents
  # messages.append(gr.ChatMessage(content=input_text, role="user"))
  async for chunk in do_inference(agent, input_text):
    for chat_message in render(chunk):
      new_messages.append(chat_message)
      yield new_messages


def launch() -> tuple[App, str, str]:
  """Bootstraps the agentic search chat app.

  Returns:
      tuple of [gradio app, host, port]
  """
  logger.info("Starting app...")

  demo = gr.ChatInterface(
    partial(handle_input, setup_agent()),
    type="messages",
    flagging_mode="never",
    title="Agentic Search Chat App: the Cooking Guru",
    description="An agentic search chat app that helps you find "
    "cooking recipes from both your own cookbook and the web.",
    examples=[
      ["I want to make a chocolate chip cookies.", ""],
      ["How do I cook a perfect steak?", ""],
      ["Give me a recipe for vegan lasagna.", ""],
    ],
    stop_btn=False,
  )

  return demo.launch()
