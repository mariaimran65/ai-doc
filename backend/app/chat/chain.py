from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import RedisChatMessageHistory

from app.config import settings

_SYSTEM_PROMPT = """You are an AI assistant embedded in the AI-Doc platform — a training \
programme that teaches production AI engineering. You help the signed-in user with \
questions about LangChain, LangGraph, RAG pipelines, FastAPI, Docker, and AI \
engineering in general.

Always be concise and technical. When showing code, use markdown code blocks.

Signed-in user: {email} (ID: {user_id})"""

_HISTORY_TTL = 60 * 60 * 24 * 7


def _get_session_history(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(
        session_id,
        url=settings.redis_url,
        ttl=_HISTORY_TTL,
    )


def build_chain(user_id: str, email: str) -> RunnableWithMessageHistory:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0.3,
        google_api_key=settings.google_api_key,
    )

    system_message = _SYSTEM_PROMPT.format(email=email, user_id=user_id)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    return RunnableWithMessageHistory(
        chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
