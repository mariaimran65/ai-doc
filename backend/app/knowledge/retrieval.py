import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import PGVector
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.knowledge.embeddings import get_embeddings
from app.knowledge.ingest import COLLECTION_NAME

TOP_K = 5

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that answers questions strictly based on the "
            "provided document excerpts. If the answer is not in the excerpts, say so. "
            "Quote relevant parts when helpful. Format your answer clearly using markdown.",
        ),
        ("human", "Question: {question}\n\nDocument excerpts:\n{context}"),
    ]
)


def _vectorstore() -> PGVector:
    return PGVector(
        connection_string=settings.pg_dsn,
        embedding_function=get_embeddings(),
        collection_name=COLLECTION_NAME,
    )


def _format_docs(docs) -> str:
    if not docs:
        return ""
    return "\n\n---\n\n".join(
        f"[Excerpt {i + 1}]\n{doc.page_content}" for i, doc in enumerate(docs)
    )


async def answer_question(
    db: AsyncSession,
    question: str,
    document_id: str | None = None,
) -> str:
    """Retrieve relevant chunks and answer using a LangChain LCEL chain.

    Pipeline:
      1. PGVector.as_retriever()     — cosine similarity search in pgvector
      2. _format_docs()              — format retrieved chunks into context string
      3. ANSWER_PROMPT | llm         — Claude generates an answer grounded in chunks
      4. StrOutputParser()           — extract plain text from the model response

    The retriever is optionally filtered to a specific document_id so Q&A
    can target a single uploaded document.
    """
    vs = _vectorstore()

    search_kwargs: dict = {"k": TOP_K}
    if document_id:
        search_kwargs["filter"] = {"document_id": document_id}

    retriever = vs.as_retriever(search_type="similarity", search_kwargs=search_kwargs)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=settings.google_api_key,
    )

    # LCEL retrieval chain: retrieve → format → prompt → llm → parse
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | ANSWER_PROMPT
        | llm
        | StrOutputParser()
    )

    result = await asyncio.get_running_loop().run_in_executor(
        None, lambda: chain.invoke(question)
    )

    if not result or not result.strip():
        return "No documents found. Please upload a document first."

    return result
