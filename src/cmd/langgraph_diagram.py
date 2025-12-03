"""This code is taken from https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/rag/langgraph_agentic_rag.md."""

from pathlib import Path

from src.agent.agentic_rag import AgenticRAG

REPO_ROOT = Path(__file__).parents[2]


def main() -> None:
  """Saves the agentic rag graph as a diagram."""
  with open(f"{REPO_ROOT}/resources/agentic-rag-diagram.png", "wb") as f:
    f.write(AgenticRAG().workflow.get_graph().draw_mermaid_png())


if __name__ == "__main__":
  main()
