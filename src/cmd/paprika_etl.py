# from src.paprika.parser import parse
import argparse
import logging
from pathlib import Path

from pydantic import TypeAdapter

from src.paprika.parser import Recipe, parse

logger = logging.getLogger(__name__)


def main() -> None:
  """Bootstraps the vector DB by importing paprika data and creating DB."""
  logger.info("Importing paprika data...")

  # 1. get CLI args
  parser = argparse.ArgumentParser(
    description="Script to populate vector db with paprika information."
  )
  parser.add_argument(
    "path",
    help="path to the paprika export archive",
    type=Path,
    default=Path("resources/paprika/export.paprikarecipes"),
    nargs="?",
  )
  args = parser.parse_args()

  # 2. parse and save parsed json
  archive: Path = args.path
  recipes = parse(archive)
  save_path = archive.parent / f".{archive.name}.parsed.json"
  print(recipes[0])
  with open(save_path, "wb") as output:
    output.write(TypeAdapter(list[Recipe]).dump_json(recipes, indent=2))

  # 3. do basic data cleaning


if __name__ == "__main__":
  main()
