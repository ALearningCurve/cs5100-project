from pydantic import BaseModel

from src.paprika.cleanse_and_enrich import Recipe

SECTIONS_TO_CHUNK = [
  "description",
  "name_cleaned",
  "ingredients",
  "directions",
  "notes",
  "nutritional_info",
  "difficulty",
  "categories_cleaned",
]
"""These are fields in the recipe which we want to embed."""


class ChunkMetadata(BaseModel):
  section: str
  name: str
  tags: str


class Chunk(BaseModel):
  content: str
  metadata: ChunkMetadata


class Chunker:
  @staticmethod
  def make_chunks(recipes: list[Recipe]) -> list[Chunk]:
    # TODO comment
    chunks = []
    for recipe in recipes:
      chunks.extend(Chunker._chunk_generator(recipe))
    return chunks

  @staticmethod
  def _chunk_generator(recipe: Recipe) -> list[Chunk]:
    # TODO comment
    chunks = []
    recipe_obj = recipe.model_dump()
    for section in SECTIONS_TO_CHUNK:
      if recipe_obj[section] is None:
        continue
      chunks.append(
        Chunk(
          content=f"{section}: {recipe_obj[section]}",
          metadata=ChunkMetadata(
            name=recipe.name, tags=str(recipe.categories_cleaned), section=section
          ),
        )
      )

    return chunks
