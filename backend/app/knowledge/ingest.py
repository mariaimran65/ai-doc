import io
import uuid
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.knowledge.embeddings import embed_texts

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def extract_text(filename: str, content: bytes) -> str:
    """Extract plain text from PDF or txt file."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="replace")


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(chunk)
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


async def ingest_document(
    db: AsyncSession,
    user_id: str,
    filename: str,
    content: bytes,
) -> dict:
    """Extract, chunk, embed and store a document. Returns summary."""
    raw_text = extract_text(filename, content)
    if not raw_text.strip():
        raise ValueError("Could not extract text from file.")

    chunks = chunk_text(raw_text)
    if not chunks:
        raise ValueError("No content chunks generated.")

    # Insert document row
    doc_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO documents (id, user_id, title, source_name, raw_text) "
            "VALUES (:id, :user_id, :title, :source_name, :raw_text)"
        ),
        {"id": doc_id, "user_id": user_id, "title": filename, "source_name": filename, "raw_text": raw_text},
    )

    # Embed all chunks in one batch
    vectors = embed_texts(chunks)

    # Insert chunk rows
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        await db.execute(
            text(
                "INSERT INTO document_chunks (id, document_id, chunk_index, chunk_text, embedding) "
                "VALUES (:id, :doc_id, :idx, :chunk_text, :embedding::vector)"
            ),
            {
                "id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "idx": idx,
                "chunk_text": chunk,
                "embedding": "[" + ",".join(str(v) for v in vector) + "]",
            },
        )

    await db.commit()
    return {"document_id": doc_id, "chunks": len(chunks), "filename": filename}
