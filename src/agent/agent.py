"""This module defines the LangChain agent and state graph.

Much of this file is adapted from LangChain docs.

- https://docs.langchain.com/oss/python/langchain/quickstart
- https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/rag/langgraph_agentic_rag.md
"""

import logging
from typing import Any, AsyncIterator, TypeAlias

from langchain.agents import create_agent
from langchain.messages import AnyMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import utils

from src.agent.cache import IDStrippingCache
from src.env import AGENT_CACHE_DB_PATH, GEMINI_API_KEY
from src.paprika.vectorstore import connect
from src.tools.mealdb_wrapper import MealDBWrapper
from src.tools.vector_store import VectorStoreTools

logger = logging.getLogger(__name__)

Agent: TypeAlias = Runnable[Any, Any]
SEARCH_AGENT_SYSTEM_PROMPT = """You are "Cheffy", an AI cooking assistant that helps users find recipes from 
their personal cookbook and the web, answer cooking-related questions, and
provide cooking tips and advice.

You have access to useful tools for retriving recipes. If these tools are
relevant to the user query, synthesize tools calls to create
wholistic and helpful response for the user.

RULES:
1. Use tools when relevant to the user query, and include multiple calls if needed.
2. Sythensize, don't just call a single tool and return its results verbatim.
3. Always be encouraging, positive, and friendly - you are here to help!
4. If you don't know the answer or can't find it using tools, admit it and refer the user to do their own research.
5. MOST IMPORTANTLY: you MUST conclude your turn with a final answer to the user. Final answer must always be provided.
"""  # noqa: E501


def _log_tracing_info() -> None:
  """Logs langsmith tracing information for debugging purposes."""
  logger = logging.getLogger(__name__)
  if utils.tracing_is_enabled():
    logger.info("Langsmith tracing is ENABLED")
  else:
    logger.info("Langsmith tracing is DISABLED")


_log_tracing_info()


def setup_model() -> ChatGoogleGenerativeAI:
  """Create new LLM model instance used for chatting.

  Returns:
      ChatGoogleGenerativeAI: the model instance
  """
  AGENT_CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
  cache = IDStrippingCache(str(AGENT_CACHE_DB_PATH))

  return ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",  # remove/add -lite when needed
    google_api_key=GEMINI_API_KEY,
    max_tokens=1000,
    timeout=30,
    cache=cache,
  )


def setup_agent() -> Agent:
  """Creates and configures a LangChain agent using Google Gemini model
  and all required tools.

  Returns:
      the agent as a Runnable
  """
  vectorstore = connect()
  vectorstore_tools = VectorStoreTools(vectorstore=vectorstore, k=5)
  mealdb_tool = MealDBWrapper()

  return create_agent(
    model=setup_model(),
    tools=[
      vectorstore_tools.recipe_retriever,
      mealdb_tool.search_meal_by_name,
      mealdb_tool.filter_recipes,
      mealdb_tool.list_filter_options,
    ],
    debug=True,
    system_prompt=SEARCH_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
  )


# has type ignore since langchain type is generic!
async def do_inference(agent: Agent, prompt: str) -> AsyncIterator[AnyMessage]:
  """Given some agent and prompt, perform inference and log/yield the chunks
  as they come in.

  Args:
      agent (Runnable): the agent to use for inference
      prompt (str): the prompt to give to the agent

  Yields:
      dict[str, AnyMessage]: the chunks as they come in
  """
  config = RunnableConfig({"configurable": {"thread_id": 1}})
  message = HumanMessage(content=prompt)

  async for chunk in agent.astream(
    {
      "messages": [
        message,
      ]
    },
    config,
    stream_mode="updates",
  ):
    logger.info(f"\nReceived chunk: {chunk} ({type(chunk)}) \n")
    assert isinstance(chunk, dict), "bad chunk format"

    # now we need to determine which key has the messages
    # which depends on the current state of langchain
    if "model" in chunk:
      messages = chunk["model"]["messages"]
    elif "tools" in chunk:
      messages = chunk["tools"]["messages"]
    else:
      err_msg = f"unexpected chunk: {chunk}"
      raise RuntimeError(err_msg)

    # iteratively yield them out for the caller to process
    for message in messages:
      yield message
