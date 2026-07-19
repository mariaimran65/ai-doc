from functools import lru_cache
from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIM = 384


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns a list of 384-dim vectors."""
    model = _model()
    return [v.tolist() for v in model.embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]
