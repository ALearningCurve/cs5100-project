from pathlib import Path
from src.paprika.parser import Recipe as RawRecipe
from pydantic import TypeAdapter, BaseModel
from datetime import datetime
from typing import Optional, Any, cast
import io

import pandas as pd
import numpy as np
import logging


logger = logging.getLogger(__name__)


class Recipe(BaseModel):
  """Represents a cleaned recipe."""

  created: datetime

  name: str
  name_cleaned: str

  description: Optional[str]

  ingredients: Optional[str]
  """List of ingredients separated by \n"""
  directions: Optional[str]
  """List of directions separated by \n"""
  notes: Optional[str]
  """List of notes separated by \n"""
  nutritional_info: Optional[str]
  """List of nutritional info separated by \n"""

  prep_time: Optional[str]
  prep_time_min: Optional[int]
  cook_time: Optional[str]
  cook_time_min: Optional[int]
  total_time: Optional[str]
  total_time_min: Optional[int]

  difficulty: Optional[str]

  servings: Optional[str]
  rating: int
  been_tried: bool
  source: Optional[str]
  source_url: Optional[str]

  categories: list[str]
  categories_cleaned: list[str]


def _2d_unique(series: pd.Series) -> pd.Series:
  # TODO @ALearningCurve add comment
  # inspired by method in https://stackoverflow.com/a/55189967
  return np.unique(np.concatenate(series.values))


def _print_summary_stats(df: pd.DataFrame) -> None:
  # TODO @ALearningCurve add comment
  info = io.StringIO()
  df.info(buf=info)
  logger.debug(f"Summary Stats: {df.shape=}\n\n{df.columns=}\ninfo={info.getvalue()}")


def _parse_categories(s: list[str]) -> list[str]:
  # TODO @ALearningCurve add comment
  cleaned = []
  for tag in s:
    tag = tag.strip()

    # remove numeric prefix like 1' or 2'
    tag = tag.replace("’", "'")
    if "'" in tag and tag[0].isnumeric():
      tag = tag.split("'", 1)[1].strip()
    # remove leading underscore used for internal tags
    if tag.startswith("_"):
      tag = tag[1:]

    if len(tag) == 0:
      continue

    cleaned.append(tag)
  return cleaned


def _to_pydantic(df: pd.DataFrame) -> list[Recipe]:
  recipes: list[Recipe] = []
  for _, recipe in df.iterrows():
    recipes.append(Recipe(**recipe.to_dict()))

  return recipes


def transform(recipes: list[RawRecipe]) -> list[Recipe]:
  """Given a list of parsed recipes from the paprike export,
  does basic ETL on them.

  Args:
      recipes: the recipes to parse/clean

  Returns:
      the cleaned recipes
  """
  # convert JSON format into pandas dataframe
  df = pd.read_json(
    io.StringIO(TypeAdapter(list[RawRecipe]).dump_json(recipes).decode())
  )
  df = df.replace(r"^\s*$", pd.NA, regex=True)  # replace blanks with NA

  # 1. show brief overview of data that will be transformed
  _print_summary_stats(df)

  # 2. do transforms
  # 2.1. drop useless columns
  df = df.drop(
    columns=[
      "photo_hash",
      "photos",
      "photo",
      "image_url",
      "photo_large",
      "photo_data",
      "hash",
      "uid",
    ]
  )

  # 2.2. add column for "been tried"
  df["been_tried"] = df["rating"].apply(
    lambda x: False if x is None or x == "0" else True
  )

  # 2.3. correct the datatype for datetimes
  df["created"] = df["created"].apply(
    lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
  )

  # 2.4. drop rows of df[name] where starts with "_" since these are
  # categories or labels in the given dataset
  mask = df["name"].str.startswith("_")
  logger.info(f"dropping {mask.sum()} placeholder recipes (start with '_')")
  df = df.loc[~mask].reset_index(drop=True)

  # 2.5. clean some common non-ascii patterns in titles
  df["name_cleaned"] = df["name"]
  non_ascii_subsitutions = {
    "’": "'",
    "‘": "'",
    "🦃": "(Thanksgiving)",
    "😋": " ",
    "🍪": " ",
    ",": ",",
    "!!!*THE*": "The",
  }
  for src, dst in non_ascii_subsitutions.items():
    df["name_cleaned"] = df["name_cleaned"].str.replace(src, dst, regex=False)

  # 2.6. Harmonize categories to be correct
  # for example: categories is array of "["1\'Drinks + Cocktails", \'_Try these\']",

  # create a new column with parsed category lists
  df["categories_cleaned"] = df["categories"].apply(_parse_categories)
  logger.debug(
    f"starting_tags={_2d_unique(df['categories'])},\n "
    f"ending_tags={_2d_unique(df['categories_cleaned'])}"
  )

  # 2.7. Harmonize the minutes of prep, cook, and overall time
  # For example: '30 min' -> 30, "1hrs 2min" -> 62
  time_columns = ["prep_time", "cook_time", "total_time"]

  for time_column in time_columns:
    logger.debug(f"\ncreating duration in minutes column for '{time_column}'")

    # try to convert disparate time formats
    temp = df[time_column].str.replace("mins", "minutes")
    temp = temp.str.replace("hrs", "hours")

    # remove bad formats
    temp = temp.mask(
      temp.str.contains(r"\b(?:or|chilling)\b", case=False, na=False), pd.NA
    )
    temp = temp.mask(temp.str.contains(r"[-–—\\\/:]", na=False), pd.NA)

    # show the amount of rows which could not be converted
    logger.debug(
      f"ignoring {temp.isna().sum() - df[time_column].isna().sum()}"
      " rows due to poor formatting"
    )

    # do basic time conversion
    temp = (pd.to_timedelta(temp).dt.total_seconds() // 60).astype(pd.Int64Dtype())
    df[f"{time_column}_min"] = temp

  # 2.8. drop any recipes which have no notes, directions, descriptions,
  # ingredients, or usable names!
  dropped = df.dropna(
    subset=["notes", "directions", "description", "ingredients", "name_cleaned"],
    how="all",
  )  # pyright: ignore[reportCallIssue], this is a false positive!
  logger.info(
    f"dropping {len(df) - len(dropped)} recipes due to having no indexable information"
  )
  df = dropped

  # 2.9. optimize type representation
  df = df.convert_dtypes()
  _print_summary_stats(df)

  return _to_pydantic(df)
