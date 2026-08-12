import os
import tempfile
import uuid

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio

from app.config import settings
from app.knowledge.embeddings import get_embeddings

COLLECTION_NAME = "ai_doc_knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def _vectorstore() -> PGVector:
    """Return a LangChain PGVector store connected to our Postgres instance.

    PGVector manages its own tables (langchain_pg_collection,
    langchain_pg_embedding) alongside our documents table.
    """
    return PGVector(
        connection_string=settings.pg_dsn,
        embedding_function=get_embeddings(),
        collection_name=COLLECTION_NAME,
    )


async def ingest_document(
    db: AsyncSession,
    user_id: str,
    filename: str,
    content: bytes,
) -> dict:
    """Load, split, embed and store a document using LangChain tooling.

    Pipeline:
      1. PyPDFLoader / TextLoader  — LangChain document loader
      2. RecursiveCharacterTextSplitter — splits on natural boundaries
         (paragraphs → sentences → words) so chunks stay semantically coherent
      3. PGVector.add_documents()  — embeds + stores in pgvector
      4. INSERT into documents     — records metadata for the UI listing

    Returns a summary dict with document_id, chunk count, and filename.
    """
    suffix = ".pdf" if filename.lower().endswith(".pdf") else ".txt"

    # Write bytes to a temp file — LangChain loaders require a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path, encoding="utf-8")

        docs = loader.load()
        if not docs or not any(d.page_content.strip() for d in docs):
            raise ValueError("Could not extract text from file.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            raise ValueError("No content chunks generated.")

        # Insert document row first so we have the ID for metadata
        doc_id = str(uuid.uuid4())
        await db.execute(
            text(
                "INSERT INTO documents (id, user_id, title, source_name, raw_text) "
                "VALUES (:id, :user_id, :title, :source_name, :raw_text)"
            ),
            {
                "id": doc_id,
                "user_id": user_id,
                "title": filename,
                "source_name": filename,
                "raw_text": docs[0].page_content[:4000],
            },
        )
        await db.commit()

        # Tag each chunk with document_id so we can filter on retrieval
        for chunk in chunks:
            chunk.metadata["document_id"] = doc_id
            chunk.metadata["user_id"] = user_id

        # Embed + store — run sync PGVector call in a thread
        vs = _vectorstore()
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: vs.add_documents(chunks)
        )

        return {"document_id": doc_id, "chunks": len(chunks), "filename": filename}

    finally:
        os.unlink(tmp_path)
