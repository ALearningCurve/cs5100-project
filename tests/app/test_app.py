"""Unit tests for the actual application layer of the start_app command.

Since it is implemented using Gradio, we assume the Gradio framework works as
intended, so we just need to check the 'interface' between our code and
Gradio works (and obeys contract). Therefore, we only test the main callback
`handle_input`.
"""

import pytest
from gradio import ChatMessage
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolCall, ToolMessage

from src import env
from src.app import handle_input

REPO_ROOT = env.REPO_ROOT


@pytest.mark.asyncio
async def test_happy_path() -> None:
  """Make sure the `handle_input` callback correctly streams the response."""
  # GIVEN: a fake agent that returns canned responses
  model = GenericFakeChatModel(
    messages=iter(
      [
        AIMessage(
          content="",
          tool_calls=[
            ToolCall(name="fake_tool1", args={"foo": "bar"}, id="some-id"),
            ToolCall(name="fake_tool2", args={}, id="some-other-id"),
          ],
        ),
        ToolMessage(
          content="something", name="fake_tool2", tool_call_id="some-other-id"
        ),
        "bar",
      ]
    )
  )
  agent = create_agent(model=model, tools=[])

  # AND: expected outputs in Gradio message format (rather than LangChain)
  wanted_outputs = [
    [
      ChatMessage(
        content="Calling tool fake_tool1 with args {'foo': 'bar'}",
        role="assistant",
        metadata={"title": "Using tool 'fake_tool1' (#some-id)"},
        options=[],
      ),
      ChatMessage(
        content="Calling tool fake_tool2 with args {}",
        role="assistant",
        metadata={"title": "Using tool 'fake_tool2' (#some-other-id)"},
        options=[],
      ),
    ],
    [
      ChatMessage(
        content="something",
        role="assistant",
        metadata={"title": "Done with tool 'fake_tool2' (#some-other-id)"},
        options=[],
      )
    ],
    [ChatMessage(content="bar", role="assistant", options=[])],
  ]

  # WHEN + THEN: when the agent is prompted, we get expected
  # output stream in the format Gradio expects
  for wanted_outputs_i in wanted_outputs:
    want_so_far = []
    async for items in handle_input(agent, "foobar", []):
      want_so_far.append(wanted_outputs_i[len(want_so_far)])

      assert want_so_far == items
