import argparse
import gzip
import json
import zipfile
from pathlib import Path


def main() -> None:
  """Converts paprika cookbook JSON to paprika export format."""
  parser = argparse.ArgumentParser(
    "Converts paprika cookbook JSON to paprika export format"
  )
  parser.add_argument("input", type=Path)
  parser.add_argument("output", type=Path)
  args = parser.parse_args()

  with open(args.input, "r") as fd:
    recipes = json.load(fd)

  with zipfile.ZipFile(args.output, "w") as archive:
    for recipe in recipes:
      archive.writestr(
        f"{recipe['uid']}.json", gzip.compress(json.dumps(recipe).encode())
      )


if __name__ == "__main__":
  main()
