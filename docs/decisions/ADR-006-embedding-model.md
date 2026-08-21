# ADR-006 — Embedding model: FastEmbed (BAAI/bge-small-en-v1.5) instead of OpenAI text-embedding-3-small

**Status:** Accepted  
**Date:** 2026-07-10  
**Author:** Maria Imran  
**Phase:** 4 — RAG

---

## Context

Phase 4 requires an embedding model to convert document chunks and query strings into vectors for storage and similarity search in pgvector. The brief specifies two options:

- `OpenAIEmbeddings` with `text-embedding-3-small` (1536-dimensional vectors, API-based)
- `BedrockEmbeddings` with an equivalent model (API-based, requires AWS credentials)

The brief also notes: *"The dimension of the embedding column is 1536, which matches the OpenAI `text-embedding-3-small` model. If you are using a different embedding model, the dimension must match exactly — document this in an ADR."*

This ADR documents the decision to use a different embedding model and records the consequent schema change.

---

## Decision

**FastEmbed** (`fastembed==0.4.2`) with the **BAAI/bge-small-en-v1.5** model is used for all embedding operations. This model produces **384-dimensional** vectors. The `embedding` column in `document_chunks` was changed from `VECTOR(1536)` to `VECTOR(384)` accordingly.

---

## Reasoning

### No per-call cost

`OpenAIEmbeddings` and `BedrockEmbeddings` bill per token embedded. During development, every document upload and every retrieval query generates an API call. For a platform where document uploads are tested repeatedly, this cost accumulates quickly. FastEmbed runs the model locally inside the Docker container — there is no per-call cost and no API key required for the embedding step.

### No external API dependency at inference time

With `OpenAIEmbeddings`, the upload endpoint fails if the OpenAI API is unreachable, even if the Anthropic API and Postgres are healthy. FastEmbed removes this dependency entirely. The embedding step is now local and deterministic — it produces the same vector for the same input on every run.

### Retrieval quality is sufficient for the use case

BAAI/bge-small-en-v1.5 benchmarks competitively with `text-embedding-3-small` on the MTEB (Massive Text Embedding Benchmark) for English retrieval tasks. For the documents this platform handles — technical writing, programme briefs, project documentation — a 384-dimensional model provides retrieval quality that is indistinguishable from a 1536-dimensional model in manual testing. The gap between the two models is more significant in multilingual and long-document-understanding tasks that are outside this platform's scope.

### Consistent interface via LangChain

`FastEmbedEmbeddings` implements LangChain's `Embeddings` base class. It plugs into `PGVector` and LCEL chains with no interface changes. Switching to `OpenAIEmbeddings` later requires: updating `get_embeddings()` in `app/knowledge/embeddings.py`, dropping and recreating the `document_chunks` table with `VECTOR(1536)`, and re-uploading all documents. No application logic outside `embeddings.py` would need to change.

---

## Schema consequence

The `document_chunks.embedding` column was changed to `VECTOR(384)` to match the model's output dimension. The ivfflat index uses `vector_cosine_ops`, which is dimension-agnostic. The PGVector collection (`ai_doc_knowledge`) stores vectors using this dimension; any change to the embedding model requires dropping the collection and re-ingesting all documents.

**The embedding model used at upload time and at query time must always be the same.** Changing `get_embeddings()` without re-ingesting documents will produce silent retrieval failures — the vectors will be incomparable and similarity search will return nonsense results.

---

## Consequences

**Accepted costs:**

- FastEmbed downloads the BAAI/bge-small-en-v1.5 model on first use (approximately 130 MB). This happens inside the Docker container. The download is cached in a Docker volume and does not repeat on container restarts.
- 384-dimensional vectors produce slightly lower retrieval quality than 1536-dimensional vectors on long or multilingual documents. This trade-off is acceptable for the current document types.
- The brief's default schema assumed 1536 dimensions. Any collaborator following the brief without reading this ADR would create a `VECTOR(1536)` column that is incompatible with this model. The schema comment has been updated to document the actual dimension in use.

**Benefits realised:**

- Document upload and retrieval work with no OpenAI API key and no per-call billing.
- Embedding is fast and deterministic inside the container.
- The platform can run fully offline (useful for demo environments without reliable internet).

---

## How to switch to OpenAIEmbeddings later

1. Set `OPENAI_API_KEY` in the environment.
2. Change `get_embeddings()` in `app/knowledge/embeddings.py` to return `OpenAIEmbeddings(model="text-embedding-3-small")`.
3. Update `schema.sql`: change `VECTOR(384)` to `VECTOR(1536)` on the `embedding` column.
4. Run a fresh schema migration (drop and recreate `document_chunks` table and the PGVector collection tables).
5. Re-upload all documents — existing 384-dim vectors cannot be compared against 1536-dim query vectors.

---

## Review notes

This decision should be revisited if:

- Retrieval quality becomes a bottleneck (users reporting irrelevant answers despite the document containing the answer).
- A phase introduces multilingual documents or very long-form technical specifications where the 384-dim model's limitations become visible.
- OpenAI introduces a free or significantly cheaper embedding tier.

---

*ADR-006 — accepted — embedding model defined in `app/knowledge/embeddings.py`, schema impact in `schema/schema.sql`*
