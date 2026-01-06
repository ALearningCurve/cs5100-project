import logging
import uuid
from functools import partial
from typing import AsyncIterator, cast

import gradio as gr
from fastapi import FastAPI
from gradio.routes import App as App

from src.agent.agent import setup_agent
from src.agent.agentic_rag import Workflow, do_inference
from src.app.auth import get_authenticated_user
from src.app.langchain_adapter import render

logger = logging.getLogger(__name__)


async def handle_input(
  graph: Workflow,
  input_text: str,
  messages: list[gr.ChatMessage],
  thread_id: int,  # This will be passed from gr.State
) -> AsyncIterator[list[gr.ChatMessage]]:
  """Takes input from user and runs inference.

  Args:
      graph: workflow to use
      input_text: user input
      messages: not used
      thread_id: the conversation id

  Returns:
      messages to render

  Yields:
      messages to render
  """
  # thread_id is now a persistent string for this specific user session
  logger.info(f"Session Thread ID: {thread_id}")

  new_messages = []
  # Pass the thread_id to your agent logic
  async for chunk in do_inference(graph, input_text, thread_id=thread_id):
    for chat_message in render(chunk):
      new_messages.append(chat_message)
      yield new_messages


def mount_chat_interface(app: FastAPI) -> FastAPI:
  """Bootstraps the agentic search chat app.

  Returns:
      tuple of [gradio app, host, port]
  """
  logger.info("Creating chatapp...")

  workflow = setup_agent()

  with gr.Blocks(fill_height=True) as demo:
    session_id = gr.State()
    session_id.value = uuid.uuid4().int

    gr.ChatInterface(
      fn=partial(handle_input, workflow),
      additional_inputs=[session_id],
      type="messages",
      flagging_mode="never",
      title="Agentic Search Chat App: the Cooking Guru",
      description="Hi, I'm Cheffy!\n Ask me anything cooking related - I can help you "
      "search your own cookbook, the web, or even surprise you with new recipes!",
      examples=[
        ["I want to make a chocolate chip cookies."],
        ["How do I cook a perfect steak?"],
        ["Give me a recipe for vegan lasagna."],
      ],
      stop_btn=False,
      fill_height=True,
    )

  return cast(
    FastAPI,
    gr.mount_gradio_app(
      app, demo, path="/chat", auth_dependency=get_authenticated_user
    ),
  )
