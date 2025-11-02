import sys

import pytest

from src.cmd.paprika_repackage import main

# def test_happy_path() -> None:
#   """Does e2e test of the paprika_repackage command."""
#   subprocess.run("uv run ", check=True)
#   time.sleep(100)


@pytest.mark.parametrize(
  "argv",
  [
    [],
    ["foo"],
  ],
)
def test_missing_inputs(capsys: pytest.CaptureFixture[str], argv: list[str]) -> None:
  args = ["foobar"]
  args.extend(argv)
  sys.argv = args
  with pytest.raises(SystemExit) as sysexit:
    main()
  assert sysexit.value.code == 2  # noqa: PLR2004
  assert "required" in capsys.readouterr().err
