import shutil
from typing import Generator

import pytest

from src import env
from src.cmd.paprika_etl import main
from src.paprika import vectorstore

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
