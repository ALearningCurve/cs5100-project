"""This module contains functions and datatypes to parse a paprika export."""

import json
import zipfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Recipe(BaseModel):
  """Represents a recipe in the archive with various attributes."""

  uid: Optional[str] = None
  created: Optional[str] = None
  hash: Optional[str] = None
  name: Optional[str] = None
  description: Optional[str] = None
  ingredients: Optional[str] = None
  directions: Optional[str] = None
  notes: Optional[str] = None
  nutritional_info: Optional[str] = None
  prep_time: Optional[str] = None
  cook_time: Optional[str] = None
  total_time: Optional[str] = None
  difficulty: Optional[str] = None
  servings: Optional[str] = None
  rating: Optional[float] = None
  source: Optional[str] = None
  source_url: Optional[str] = None
  photo: Optional[str] = None
  photo_large: Optional[str] = None
  photo_hash: Optional[str] = None
  image_url: Optional[str] = None
  photo_data: Optional[str] = None
  photos: Optional[str] = None
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
    # 2. extract each archive from the namelist
    for recipe_name in archive.namelist():
      with archive.open(recipe_name) as recipe_fp:
        recipes.append(Recipe(**json.load(recipe_fp)))
  return recipes
