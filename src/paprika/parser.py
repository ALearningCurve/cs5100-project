"""This module contains functions and datatypes to parse a paprika export."""

import gzip
import json
import zipfile
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel


class Recipe(BaseModel):
  """Represents a recipe in the archive with various attributes."""

  uid: str
  created: str
  hash: str
  name: str
  description: str
  ingredients: str
  directions: str
  notes: str
  nutritional_info: str
  prep_time: str
  cook_time: str
  total_time: str
  difficulty: str
  servings: str
  rating: float
  source: str
  source_url: str
  photo: Optional[str] = None
  photo_large: Optional[str] = None
  photo_hash: Optional[str] = None
  image_url: Optional[str] = None
  photo_data: Optional[str] = None
  photos: list[Any]
  categories: list[str] = []


def parse(path: Path) -> list[Recipe]:
  """Given path to exported archive from paprika, extracts each recipe!

  Args:
      path: path to archive

  Returns:
      list of all recipes in the archive as-is
  """
  # Per https://paprikaapp.zendesk.com/hc/en-us/articles/360051324613-What-export-formats-do-you-support
  # we know that this archive is a zip!

  recipes: list[Recipe] = []
  # 1. parse as zip
  with zipfile.ZipFile(path, "r") as archive:
    # 2. extract each compressed recipe from the zip
    for recipe_name in archive.namelist():
      with (
        archive.open(recipe_name, "r") as zipped_fp,
        gzip.open(zipped_fp) as unzipped_fp,
      ):
        recipes.append(Recipe(**json.load(unzipped_fp)))
  return recipes
