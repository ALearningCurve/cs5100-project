import logging

from langchain.agents import create_agent
from langchain.messages import AnyMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import utils

from src.agent.cache import IDStrippingCache
from src.env import AGENT_CACHE_DB_PATH, GEMINI_API_KEY


def _log_tracing_info() -> None:
  """Logs langsmith tracing information for debugging purposes."""
  logger = logging.getLogger(__name__)
  if utils.tracing_is_enabled():
    logger.info("Langsmith tracing is ENABLED")
  else:
    logger.info("Langsmith tracing is DISABLED")


# has type ignore since langchain type is generic!
def setup_agent() -> Runnable:  # type: ignore
  """Creates and configures a LangChain agent using Google Gemini model
  and all required tools.

  Returns:
      the agent as a Runnable
  """
  #  inspired by https://docs.langchain.com/oss/python/langchain/quickstart
  _log_tracing_info()

  # 1. create the model
  cache = IDStrippingCache(str(AGENT_CACHE_DB_PATH))

  model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GEMINI_API_KEY,
    max_tokens=4000,
    timeout=30,
    cache=cache,
  )

  # 2. create the agent
  AGENT_CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
  return create_agent(
    model=model,
    tools=[],
    debug=True,
    system_prompt="you are a helpful assistant",
    checkpointer=InMemorySaver(),
  )


# has type ignore since langchain type is generic!
def do_inference(agent: Runnable) -> dict[str, AnyMessage]:  # type: ignore
  """Given some agent, perform inference with it.

  Args:
      agent (Runnable): the agent to use for inference
  """
  # our current app only has single-thread, so we
  # just set thread_id to 1
  config = {"configurable": {"thread_id": 1}}

  # perform inference
  message = HumanMessage(content="Hey - hows it going?").model_dump()

  # has type ignore since langchain type is generic!
  res = agent.invoke(
    {
      "messages": [
        message,
      ]
    },
    config,  # type: ignore
  )
  return {"messages": res}


do_inference(setup_agent())
