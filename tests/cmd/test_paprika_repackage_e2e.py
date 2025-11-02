"""Does E2E tests for paprika rapacke command.

We mainly just want to make sure that the repackaging
of paprika export json to paprika binary format
stays consistent across changes, not necessarily
that the repackaging logic is perfect.
"""

import sys
from pathlib import Path
from shutil import copyfile

import pytest

from src.cmd.paprika_repackage import main
from src.env import REPO_ROOT
from src.paprika.parser import parse


def test_happy_path(tmp_path: Path) -> None:
  """Make sure the command runs end to end for simple case."""
  # GIVEN: input and expected output files
  wanted_input = REPO_ROOT / "tests" / "fixtures" / "paprika" / "export.json"
  wanted_output = REPO_ROOT / "tests" / "fixtures" / "paprika" / "export.paprikarecipes"

  # AND: temp input and output files
  temp_input = tmp_path / "export.json"
  temp_output = tmp_path / "export.paprikarecipes"
  copyfile(wanted_input, temp_input)

  # WHEN: we run the command
  sys.argv = [
    "fake_prog",
    str(temp_input),
    str(temp_output),
  ]
  main()

  # THEN: the output file is as expected
  assert temp_output.exists()
  assert parse(temp_output) == parse(wanted_output)


@pytest.mark.parametrize(
  "argv",
  [
    [],
    ["foo"],
  ],
)
def test_missing_inputs(capsys: pytest.CaptureFixture[str], argv: list[str]) -> None:
  """Tests that missing required inputs
  raises SystemExit & has helpful error message.

  Args:
      capsys: pytest capture fixture
      argv: the argv to pass to the main function
  """
  # GIVEN: missing required inputs
  sys.argv = ["fake_prog", *argv]

  # WHEN/THEN: running the command raises SystemExit with helpful message
  with pytest.raises(SystemExit) as sysexit:
    main()
  assert sysexit.value.code == 2  # noqa: PLR2004
  assert "required" in capsys.readouterr().err
