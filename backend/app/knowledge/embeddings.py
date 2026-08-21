from functools import lru_cache

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIM = 384


@lru_cache(maxsize=1)
def get_embeddings() -> FastEmbedEmbeddings:
    """Return a cached LangChain-compatible embedding model backed by fastembed.

    fastembed runs locally (no API key needed) using ONNX runtime.
    Wrapping it in LangChain's FastEmbedEmbeddings makes it compatible with
    LangChain's PGVector vectorstore and retrieval chains.
    """
    return FastEmbedEmbeddings(model_name=MODEL_NAME)
