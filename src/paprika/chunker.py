from pydantic import BaseModel

from src.paprika.cleanse_and_enrich import Recipe

SECTIONS_TO_CHUNK = {
  "description",
  "name_cleaned",
  "ingredients",
  "directions",
  "notes",
  "nutritional_info",
  "difficulty",
  "categories_cleaned",
}
"""These are fields in the recipe which we want to embed."""


class FullRecipeMetadata(BaseModel):
  """This represents the metadata columns for the full recipe."""

  uuid: str
  section: str
  name: str
  tags: str


class ChunkMetadata(BaseModel):
  """This represents the metadata columns for each chunk."""

  full_doc_uuid: str
  section: str
  name: str
  tags: str

  def to_full_recipe_metadata(self) -> FullRecipeMetadata:
    """Converts chunk metadata to full recipe metadata.

    Returns:
      Converted chunk metadata to full recipe metadata.
    """
    data = self.model_dump()
    data["uuid"] = data.pop("full_doc_uuid")  # rename for full recipe metadata
    data["section"] = "Full Recipe"
    return FullRecipeMetadata(**data)


class Chunk(BaseModel):
  """Represents a chunk content which will be embedded in RAG system."""

  content: str
  metadata: ChunkMetadata


class Chunker:
  """Container class used to do basic chunking of recipe into different sections
  which can then be embedded in vector db.
  """

  @staticmethod
  def make_chunks(recipes: list[Recipe]) -> list[Chunk]:
    """Given recipes, chunks each recipe into multiple chunks
    which can then be encoded in vector db for good semantic search.

    Args:
        recipes: the recipes to chunk

    Returns:
        the chunks of all the recipes in no particular order
    """
    chunks = []
    for recipe in recipes:
      chunks.extend(Chunker._chunk_generator(recipe))
    return chunks

  @staticmethod
  def _chunk_generator(recipe: Recipe) -> list[Chunk]:
    """Create chunks for a single recipe. See :py:func:`Chunker.make_chunks`.

    Args:
        recipe: recipe to create chunks for

    Returns:
        the section level chunks for this recipe
    """
    chunks = []
    recipe_obj = recipe.model_dump()

    # create chunks for each section
    for section in SECTIONS_TO_CHUNK:
      # only make chunk if there is something to chunk
      if recipe_obj[section] is None:
        continue
      # create the chunk!
      chunks.append(
        Chunk(
          content=f"{section}: {recipe_obj[section]}",
          metadata=ChunkMetadata(
            full_doc_uuid=recipe.uuid,
            name=recipe.name,
            tags=str(recipe.categories_cleaned),
            section=section,
          ),
        )
      )

    return chunks
