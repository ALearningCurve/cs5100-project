import logging
from typing import Iterator

import gradio as gr
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage

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


def render(message: AnyMessage) -> Iterator[gr.ChatMessage]:
  """Renders message from chunk from stream into gradio message format."""
  if isinstance(message, AIMessage):
    yield from _render_ai_message(message)
  elif isinstance(message, ToolMessage):
    yield from _render_tool_message(message)
  else:
    err_msg = f"Unknown message type: {type(message)}"
    raise TypeError(err_msg)
