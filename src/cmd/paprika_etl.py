# from src.paprika.parser import parse
import logging

from pydantic import TypeAdapter

from src import env
from src.paprika.chunker import Chunker
from src.paprika.cleanse_and_enrich import clean_and_enrich_recipes
from src.paprika.parser import Recipe, parse
from src.paprika.vectorstore import load_chunks

logger = logging.getLogger(__name__)


def main() -> None:
  """Bootstraps the vector DB by importing paprika data and creating DB."""
  logger.info("Importing paprika data...")

  # 2. parse and save parsed json
  logger.info(f"E - parsing export archive {str(env.PAPRIKA_EXPORT_PATH)}")
  recipes = parse(env.PAPRIKA_EXPORT_PATH)
  save_path = (
    env.PAPRIKA_EXPORT_PATH.parent / f".{env.PAPRIKA_EXPORT_PATH.name}.parsed.json"
  )
  with open(save_path, "wb") as output:
    output.write(TypeAdapter(list[Recipe]).dump_json(recipes, indent=2))

  # 3. do basic data cleaning
  logger.info("T - initial data cleaning & preprocessing (1/2)")
  enriched_recipes = clean_and_enrich_recipes(recipes)

  logger.info("T - user space chunking (2/2)")
  chunks = Chunker.make_chunks(enriched_recipes)

  # 4. load the data to the vector db
  logger.info("L: load to DB")
  load_chunks(chunks)


if __name__ == "__main__":
  main()
