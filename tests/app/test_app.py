import pytest
from gradio import ChatMessage

from src.agent.agentic_rag import AgenticRAG
from src.app import handle_input


@pytest.mark.asyncio
async def test_happy_path() -> None:
  """Make sure the `handle_input` callback correctly streams the response."""
  # GIVEN: initialize the AgenticRAG workflow
  workflow = AgenticRAG().workflow

  # AND a simple prompt that's in the vectorstore
  prompt = "How do I make chocolate chip cookies?"
  initial_messages = []

  # WHEN: stream output from handle_input
  async for message_list in handle_input(workflow, prompt, initial_messages):
    # THEN: verify we get a list of valid chat messages
    assert isinstance(message_list, list) and len(message_list) > 0, (
      "Expected non-empty message list"
    )

    for msg in message_list:
      assert isinstance(msg, ChatMessage), f"Expected ChatMessage but got {type(msg)}"
      assert (
        hasattr(msg, "role") and msg.role in ["user", "assistant", "system"]
      ) and (
        hasattr(msg, "content") and isinstance(msg.content, str) and len(msg.content)
      ), "ChatMessage does not have valid role and content"
