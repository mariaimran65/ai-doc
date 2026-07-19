from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings
from app.knowledge.embeddings import embed_query

TOP_K = 5

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant that answers questions strictly based on the provided document excerpts. "
     "If the answer is not in the excerpts, say so. Quote relevant parts when helpful. "
     "Format your answer clearly using markdown."),
    ("human",
     "Question: {question}\n\n"
     "Document excerpts:\n{context}"),
])


async def retrieve_chunks(db: AsyncSession, query: str, document_id: str | None = None) -> list[str]:
    """Find the top-k most similar chunks to the query using pgvector cosine search."""
    query_vector = embed_query(query)
    vector_str = str(query_vector)

    if document_id:
        rows = await db.execute(
            text(
                "SELECT chunk_text FROM document_chunks "
                "WHERE document_id = :doc_id "
                "ORDER BY embedding <=> :vec "
                "LIMIT :k"
            ),
            {"doc_id": document_id, "vec": vector_str, "k": TOP_K},
        )
    else:
        rows = await db.execute(
            text(
                "SELECT chunk_text FROM document_chunks "
                "ORDER BY embedding <=> :vec "
                "LIMIT :k"
            ),
            {"vec": vector_str, "k": TOP_K},
        )

    return [row[0] for row in rows.fetchall()]


async def answer_question(
    db: AsyncSession,
    question: str,
    document_id: str | None = None,
) -> str:
    """Retrieve relevant chunks and generate an answer with Claude."""
    chunks = await retrieve_chunks(db, question, document_id)

    if not chunks:
        return "No documents found. Please upload a document first."

    context = "\n\n---\n\n".join(
        f"[Excerpt {i + 1}]\n{chunk}" for i, chunk in enumerate(chunks)
    )

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0.1,
        api_key=settings.anthropic_api_key,
    )
    chain = ANSWER_PROMPT | llm
    response = chain.invoke({"question": question, "context": context})
    return response.content
