import logging
from functools import partial
from typing import AsyncIterator, Iterator

import gradio as gr
from gradio.routes import App
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage

from src.agent.agent import Agent, do_inference, setup_agent

logger = logging.getLogger(__name__)


def _render_ai_message(message: AIMessage) -> Iterator[gr.ChatMessage]:
  """Renders AIMessage into gradio message format.

  Args:
      message: the messag to render

  Returns:
      iterator of gradio chat messages
  """
  # If the AIMessage has content, then it is a message from LLM -> user
  if len(message.content) != 0:
    content_blocks = (
      [message.content] if isinstance(message.content, str) else message.content
    )
    # render each block as a seperate message, accounting for
    # text and document (dict format) response mix
    for block in content_blocks:
      txt = block["text"] if isinstance(block, dict) else block
      yield gr.ChatMessage(role="assistant", content=txt)

  # If there are tool calls, then render them as truncated 'calling tool' messages
  if message.tool_calls is not None and len(message.tool_calls) > 0:
    for tool_call in message.tool_calls:
      yield gr.ChatMessage(
        role="assistant",
        content=f"Calling tool {tool_call['name']} with args {tool_call['args']}",
        metadata={"title": f"Using tool '{tool_call['name']}' (#{tool_call['id']})"},
      )


def _render_tool_message(message: ToolMessage) -> Iterator[gr.ChatMessage]:
  """Renders ToolMessage into gradio message format.

  Args:
      message: the messag to render

  Returns:
      iterator of gradio chat messages
  """
  assert type(message.content) is str, f"str, got {type(message.content)}"
  yield gr.ChatMessage(
    role="assistant",
    content=f"{message.content}",
    metadata={"title": f"Done with tool '{message.name}' (#{message.tool_call_id})"},
  )


def _render_message(message: AnyMessage) -> Iterator[gr.ChatMessage]:
  """Renders message from chunk from stream into gradio message format."""
  if isinstance(message, AIMessage):
    yield from _render_ai_message(message)
  elif isinstance(message, ToolMessage):
    yield from _render_tool_message(message)
  else:
    err_msg = f"Unknown message type: {type(message)}"
    raise TypeError(err_msg)


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
    for chat_message in _render_message(chunk):
      new_messages.append(chat_message)
      yield new_messages


def main() -> tuple[App, str, str]:
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


if __name__ == "__main__":
  main()
