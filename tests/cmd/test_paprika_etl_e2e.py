"""Does E2E tests for paprika ETL command. This allows use to treat the ETL
as a black box and just make sure that the end result is as expected for
testing simiplicity.

The main think we care about is that the vectorstore search works as expected.
"""

import shutil
from collections import defaultdict
from typing import Generator

import pytest

from src import env
from src.cmd.paprika_etl import main
from src.paprika import vectorstore
from src.paprika.chunker import SECTIONS_TO_CHUNK

REPO_ROOT = env.REPO_ROOT


@pytest.fixture(scope="session")
def setup_vectorstore(
  tmp_path_factory: pytest.TempPathFactory,
) -> Generator[vectorstore.Chroma, None, None]:
  """Creates and yields a vectorstore populated by the ETL process
  (for use in e2e test).

  Cleans up self after test is done.

  Args:
      tmp_path_factory: pytest tmp path factory fixture

  Yields:
      the connected vectorstore
  """
  # GIVEN: vectorstore location and paprika export
  vectorstore.CHROMA_ROOT = tmp_path_factory.mktemp("chroma")
  env.PAPRIKA_EXPORT_PATH = tmp_path_factory.mktemp("export") / "export.paprikarecipes"
  shutil.copyfile(
    REPO_ROOT / "tests" / "fixtures" / "paprika" / "export.paprikarecipes",
    env.PAPRIKA_EXPORT_PATH,
  )

  # WHEN: we run the ETL
  main()

  # THEN: we can connect to the vectorstore
  yield vectorstore.connect()

  # FINALLY: cleanup
  if vectorstore.CHROMA_ROOT.exists():
    shutil.rmtree(vectorstore.CHROMA_ROOT)


def test_all_chunks_in_db(setup_vectorstore: vectorstore.Chroma) -> None:
  """Make sure the command runs end to end for simple case."""
  # GIVEN the vectorstore setup by the ETL
  chroma = setup_vectorstore

  # WHEN we query for all items
  recipes = chroma.get(limit=1000)

  # THEN make sure we got the correct # of responses
  assert len(recipes["ids"]) == 18  # noqa: PLR2004, we know that there should be 18 chunks
  assert set(recipes["included"]) == set(["documents", "metadatas"]), (
    "these fields are always included"
  )
  assert len(recipes["documents"]) == len(recipes["ids"])
  assert len(recipes["metadatas"]) == len(recipes["ids"])

  # AND make sure all recipes are represented
  recipes_found = set()
  wanted_names = {
    "!!!*THE* Chocolate Chip Cookie Recipe (Lauren's)",
    "Air Fryer Chicken Breast",
  }
  for metadata in recipes["metadatas"]:
    recipes_found.add(metadata["name"])
  assert recipes_found == wanted_names

  # AND make sure sections are represented
  sections_found = defaultdict(set)
  for metadata in recipes["metadatas"]:
    sections_found[metadata["name"]].add(metadata["section"])
  assert all(
    len(sections_found[recipe_name]) >= len(SECTIONS_TO_CHUNK) // 2
    for recipe_name in wanted_names
  )

  # AND make sure that the content is non-empty
  for document in recipes["documents"]:
    assert len(document) > 0


@pytest.mark.parametrize(
  "query, expected_recipe",
  [
    ("chocolate", "!!!*THE* Chocolate Chip Cookie Recipe (Lauren's)"),
    ("air fryer", "Air Fryer Chicken Breast"),
  ],
)
def test_vectorstore_search(
  query: str, expected_recipe: str, setup_vectorstore: vectorstore.Chroma
) -> None:
  """Make sure semantic search works in vectorstore."""
  # GIVEN the vectorstore setup by the ETL
  chroma = setup_vectorstore

  # WHEN we search
  results = chroma.similarity_search(
    query,
    k=3,
  )

  # THEN make sure we got results
  assert len(results) > 0

  # AND make sure the expected recipe is in the results
  assert all(result.metadata["name"] == expected_recipe for result in results)
