"""This module defines the LangChain agent.

Much of this file is adapted from LangChain docs.

- https://docs.langchain.com/oss/python/langchain/quickstart
- https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/rag/langgraph_agentic_rag.md
"""

import logging
from typing import Any, TypeAlias

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import utils

from src.agent.cache import IDStrippingCache
from src.env import AGENT_CACHE_DB_PATH, GEMINI_API_KEY
from src.paprika.vectorstore import connect
from src.tools.external.mealdb_wrapper import MealDBWrapper
from src.tools.external.recipe_api import RecipeAPI
from src.tools.external.tasty_wrapper import TastyWrapper
from src.tools.vector_store import VectorStoreTools

logger = logging.getLogger(__name__)

Agent: TypeAlias = Runnable[Any, Any]
SEARCH_AGENT_SYSTEM_PROMPT = """You are "Cheffy", an AI cooking assistant that helps users find recipes from 
their personal cookbook and the web, answer cooking-related questions, and
provide cooking tips and advice.

You have access to useful tools for retrieving recipes. If these tools are
relevant to the user query, synthesize tools calls to create
wholistic and helpful response for the user.

RULES:
1. Use tools when relevant to the user query, and include multiple calls if needed.
2. Synthesize the outcome of tool calls and don't include irrelevant information. If a tool call has no relevant result, inform user of what you tried. 
3. When calling a tool, summarize and only include relevant parts.
4. Always be encouraging, positive, and friendly - you are here to help!
5. If you don't know the answer or can't find it using tools, admit it and refer the user to do their own research.
6. MOST IMPORTANTLY: you MUST conclude your turn with a final answer to the user. Final answer must always be provided.
7. Ask user if they want to search their own recipe book or online (or both) before using recipe search tools. 
   INTERNAL tools search user's own recipes whereas EXTERNAL tools search online.
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
  full_recipe_vectorstore = connect(True)
  vectorstore_tools = VectorStoreTools(
    vectorstore=vectorstore, full_recipe_vectorstore=full_recipe_vectorstore, k=5
  )
  recipe_api_tool = RecipeAPI()
  recipe_api_tool = RecipeAPI()
  mealdb_tool = MealDBWrapper()
  tasty_tool = TastyWrapper()

  return create_agent(
    model=setup_model(),
    tools=[
      vectorstore_tools.recipe_retriever,
      recipe_api_tool.search_meal_by_name,
      mealdb_tool.filter_recipes,
      mealdb_tool.list_filter_options,
      recipe_api_tool.get_random_recipe,
      tasty_tool.get_trending_recipes,
    ],
    debug=True,
    system_prompt=SEARCH_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
  )
