import logging
from functools import partial
from typing import Any, AsyncIterator

import gradio as gr
from gradio.routes import App
from langchain_core.messages import AIMessage

from src.agent.agent import Agent, do_inference, setup_agent

logger = logging.getLogger(__name__)


async def handle_input(
  agent: Agent, input_text: str, messages: list[Any]
) -> AsyncIterator[gr.ChatMessage]:
  """Gradio chat callback to handle user input + agent response.

  Args:
      agent: the agent to use for inference
      input_text: prompt from the user
      messages: previous chat messages

  Yields:
      agent generated messages (yields as they are made)
  """
  # approach inspireed by docs:
  # https://www.gradio.app/guides/agents-and-tool-usage#a-real-example-using-langchain-agents
  async for chunk in do_inference(agent, input_text):
    assert isinstance(chunk, AIMessage)

    if len(chunk.content) != 0:
      yield gr.ChatMessage(role="assistant", content=chunk.content)

    if chunk.tool_calls is not None and len(chunk.tool_calls) > 0:
      for tool_call in chunk.tool_calls:
        yield gr.ChatMessage(
          role="assistant",
          content=f"Calling tool {tool_call['name']} with args {tool_call['args']}",
          metadata={"title": f"Tool Call: {tool_call['name']}"},
        )


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
      ["I want to make a chocolate cake.", ""],
      ["How do I cook a perfect steak?", ""],
      ["Give me a recipe for vegan lasagna.", ""],
    ],
    stop_btn=False,
  )

  return demo.launch()


if __name__ == "__main__":
  main()
