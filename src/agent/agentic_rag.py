"""This module defines the Agentic RAG state graph that determines
the logic flow of our Chatbot's responses.

Much of this file is adapted from LangChain docs.

- https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/rag/langgraph_agentic_rag.md
"""

import logging
from typing import Any, AsyncIterator, List, Optional, Type, TypeAlias

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.agent import setup_agent, setup_model
from src.paprika.vectorstore import connect
from src.tools.external.mealdb_wrapper import MealDBWrapper
from src.tools.external.recipe_api import RecipeAPI
from src.tools.external.tasty_wrapper import TastyWrapper
from src.tools.vector_store import VectorStoreTools

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """
Look at the user's query and try to reason about the underlying semantic intent/meaning.
Here is the user query: {question}
From this query and its underlying semantic intent/meaning,
formulate an improved question.
Respond with ONLY the improved question, nothing else.
"""

GRADE_PROMPT = """
You are a grader assessing the relevance of a potential answer to a user's question.
Here is the potential answer: {answer}
Here is the user's question: {question}

If the answer contains sufficient information to fully answer the user's question,
respond with: final_answer
If more information is needed, suggest ONE of the following tools:
- vectorstore (for searching recipe vector database)
- search_meal_by_name (for searching meals by name)
- get_trending (for trending recipes)
- get_random (for random recipe suggestions)
- rewrite_question (to improve the query)
- filter_recipes (to filter recipes)
- list_filter_options (to list options to filter by)

Respond with ONLY the node name, nothing else.
"""

Workflow: TypeAlias = Runnable[Any, Any]

SUGGESTED_ACTION_STR = "Suggested next action:"

TOOL_NAMES = [
  "vectorstore",
  "search_meal_by_name",
  "get_random",
  "get_trending",
  "filter_recipes",
  "list_filter_options",
]


class AgenticRAG:
  """Wrapper class to create a workflow for agentic RAG to handle user queries."""

  def __init__(self) -> None:
    """Initializes the wrapper class with all models, all tools,
    and the workflow.
    """
    # initialize models
    self.cheffy_agent = setup_agent()
    self.rewrite_llm = setup_model()
    self.grading_llm = setup_model()

    # initialize tools
    self.vectorstore = connect()
    self.full_recipe_vectorstore = connect(True)
    self.vectorstore_tools = VectorStoreTools(
      vectorstore=self.vectorstore,
      full_recipe_vectorstore=self.full_recipe_vectorstore,
      k=5,
    )
    self.recipe_api_tool = RecipeAPI()
    self.mealdb_tool = MealDBWrapper()
    self.tasty_tool = TastyWrapper()

    # initialize workflow
    self.workflow = self._setup_agentic_graph()

  def _setup_agentic_graph(self) -> Workflow:
    """Creates the agentic RAG workflow by adding nodes and edges to the graph.

    Returns:
        The workflow as a runnable
    """
    agentic_workflow = StateGraph(MessagesState)

    # add LLM nodes
    agentic_workflow.add_node("cheffy_agent", self._cheffy_agent_node)
    agentic_workflow.add_node("rewrite_question", self._rewrite_question_node)
    agentic_workflow.add_node("grading_llm", self._grading_node)
    agentic_workflow.add_node("final_answer", self._final_answer_node)

    # wrap and add Tool nodes
    for tool_name, tool_node in zip(
      TOOL_NAMES, self._generate_tool_nodes(), strict=False
    ):
      agentic_workflow.add_node(tool_name, tool_node)

    # establish start of the graph
    agentic_workflow.add_edge(START, "cheffy_agent")
    agentic_workflow.add_edge("cheffy_agent", "grading_llm")
    agentic_workflow.add_conditional_edges("grading_llm", self._grading_router_node)

    # connect tools to grading
    for name in TOOL_NAMES:
      agentic_workflow.add_edge(name, "grading_llm")

    # after rewriting, make sure Cheffy responds to new prompt
    agentic_workflow.add_edge("rewrite_question", "cheffy_agent")

    # final answer is end
    agentic_workflow.add_edge("final_answer", END)

    return agentic_workflow.compile()

  def _generate_tool_nodes(self) -> List[ToolNode]:
    """Generates ToolNodes to be used in the agentic workflow.

    Returns:
        List of ToolNodes for the agentic workflow
    """
    tools = [
      self.vectorstore_tools.recipe_retriever,
      self.recipe_api_tool.search_meal_by_name,
      self.recipe_api_tool.get_random_recipe,
      self.tasty_tool.get_trending_recipes,
      self.mealdb_tool.filter_recipes,
      self.mealdb_tool.list_filter_options,
    ]

    return [
      ToolNode(tools=[tool], name=name)
      for tool, name in zip(tools, TOOL_NAMES, strict=False)
    ]

  def _cheffy_agent_node(self, state: MessagesState) -> MessagesState:
    """Node that harnesses the Cheffy agent to respond to a user query.

    Args:
        state: current state of the conversation, including all past messages.

    Returns:
        State with the Cheffy agent output appended to it.
    """
    response = self.cheffy_agent.invoke({"messages": state["messages"]})
    return self._structure_llm_response(response)

  def _rewrite_question_node(self, state: MessagesState) -> MessagesState:
    """Node that harnesses an LLM to rewrite a user's query.

    Args:
        state: current state of the conversation, including all past messages.

    Returns:
        State with the rewritten user query appended to it.
    """
    # get last question
    last_question = self._get_most_recent_msg(state, HumanMessage)

    if not last_question:  # if no user question, return no messags
      return {"messages": []}

    # call LLM to rewrite user prompt
    prompt = REWRITE_PROMPT.format(question=last_question)
    rewritten_prompt = self.rewrite_llm.invoke([{"role": "user", "content": prompt}])

    return {"messages": [HumanMessage(content=rewritten_prompt.content)]}

  def _grading_node(self, state: MessagesState) -> MessagesState:
    """Node that harnesses an LLM to grade an answer and suggest a next action.

    Args:
        state: current state of the conversation, including all past messages.

    Returns:
        State with the suggested next action appended to it.
    """
    # get last question and last answer
    last_question = self._get_most_recent_msg(state, HumanMessage)
    if not last_question:
      return {"messages": [AIMessage(content=f"{SUGGESTED_ACTION_STR} final_answer")]}

    last_answer = self._get_most_recent_msg(state, AIMessage)
    if not last_answer:
      return {"messages": [AIMessage(content=f"{SUGGESTED_ACTION_STR} vectorstore")]}

    # generate grading prompt and call LLM for suggestion
    prompt = GRADE_PROMPT.format(answer=last_answer, question=last_question)
    suggestion = self.grading_llm.invoke(prompt)
    suggestion_text = self._extract_text(
      self._structure_llm_response(suggestion)["messages"][0]
    )

    return {
      "messages": [AIMessage(content=f"{SUGGESTED_ACTION_STR} {suggestion_text}")]
    }

  def _final_answer_node(self, state: MessagesState) -> MessagesState:
    """Node that harnesses the Cheffy agent to produce a final answer.

    Args:
        state: current state of the conversation, including all past messages.

    Returns:
        State with just the Cheffy agent final output
    """
    # filter out suggestion messages
    filtered_messages = [
      msg
      for msg in state["messages"]
      if not self._extract_text(msg).startswith(SUGGESTED_ACTION_STR)
    ]

    # generate final prompt and call LLM for final answer
    final_instruction = (
      "Based on all the information gathered above, make a comprehensive answer to the"
      + " user's question. Make sure this answer is helpful, complete, and friendly!"
      + " If you believe an existing AI response is sufficient, you may use that."
    )
    prompt_messages = filtered_messages + [HumanMessage(content=final_instruction)]
    final_answer = self.cheffy_agent.invoke({"messages": prompt_messages})
    structured_final_messages= self._structure_llm_response(final_answer)["messages"]
    return {"messages": [structured_final_messages[-1]]}

  def _grading_router_node(self, state: MessagesState) -> str:
    """Node that determines which node is the next to use based on state.

    Args:
        state: current state of the conversation, including all past messages.

    Returns:
        Name of the node to use next
    """
    suggestion = self._extract_text(state["messages"][-1]).lower()

    for name in TOOL_NAMES:
      if name in suggestion:
        return name

    return "final_answer"

  def _extract_text(self, message: AnyMessage) -> str:  # noqa: ANN401
    """Helper function to parse content from a message as a string.

    Args:
        message: Message to parse string content from

    Returns:
        Content of message as a string
    """
    content = message.content

    if isinstance(content, str):
      return content

    string_parts: List[str] = []
    for item in content:  # could be list of strings or dict
      if isinstance(item, str):
        string_parts.append(item)
      elif isinstance(item, dict):
        string_values = [value for value in item.values() if isinstance(value, str)]
        string_parts += string_values
    return " ".join(string_parts)

  def _structure_llm_response(self, llm_response: Any) -> MessagesState:  # noqa: ANN401
    """Helper function to structure the LLM response as a MessagesState.

    Args:
        llm_response: Response from the LLM to be structured

    Returns:
        MessagesState representing the LLM's response
    """
    # if state returned
    if isinstance(llm_response, dict) and "messages" in llm_response:
      return {"messages": llm_response["messages"]}
    if isinstance(llm_response, list):  # if messages returned
      return {"messages": llm_response}
    return {"messages": [llm_response]}  # if single message returned

  def _get_most_recent_msg(
    self, state: MessagesState, msg_type: Type[AnyMessage]
  ) -> Optional[AnyMessage]:
    """Helper function that goes through the messages of the MessagesState
    and returns the most recent message of the given message type.

    Args:
        state: current state of the conversation, including all past messages.
        msg_type: the message type to filter for.

    Returns:
        The most recent message of given message type (AnyMessage)
    """
    # search for messages of msg_type
    target_msgs = [msg for msg in state["messages"] if isinstance(msg, msg_type)]

    if not target_msgs:
      logger.warning(f"No message of type {msg_type} found in MessagesState")
      return None

    # return most recent
    return target_msgs[-1]


async def do_inference(graph: Workflow, prompt: str) -> AsyncIterator[AnyMessage]:
  """Given some workflow and prompt, perform inference and yield the chunks
  as they come in.

  Args:
      graph: the workflow to use for inference
      prompt: the prompt to give to the workflow

  Yields:
      Messages as they come in from the workflow
  """
  config = RunnableConfig({"configurable": {"thread_id": 1}})
  initial_state = {"messages": [HumanMessage(content=prompt)]}

  async for chunk in graph.astream(initial_state, config, stream_mode="updates"):
    logger.info(f"Received chunk: {chunk} ({type(chunk)})")

    # stream_mode="updates" returns {node_name: {messages: [...]}}
    if isinstance(chunk, dict):
      for node_name, node_output in chunk.items():
        if node_name in (TOOL_NAMES + ["final_answer"]): # only keep tool + final
          if isinstance(node_output, dict) and "messages" in node_output:
            for msg in node_output["messages"]:
              yield msg
          else:
            logger.warning(f"Node {node_name} returned invalid response")
    else:
      err_msg = f"Unexpected graph chunk type: {type(chunk)}"
      raise TypeError(err_msg)
