from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.chat_message_histories import RedisChatMessageHistory

from app.config import settings
from app.chat.tools import make_user_tools

SYSTEM_PROMPT = """You are an AI assistant embedded in the AI-Doc platform — a training \
programme that teaches production AI engineering. You help the signed-in user with \
questions about LangChain, LangGraph, RAG pipelines, FastAPI, Docker, and AI \
engineering in general.

You have access to a web search tool for current information. Use it when the question \
requires facts you may not have, or when the user asks about recent developments.

Always be concise and technical. When showing code, use markdown code blocks."""

# Redis TTL for chat history: 7 days
_HISTORY_TTL = 60 * 60 * 24 * 7


def _get_session_history(session_id: str) -> RedisChatMessageHistory:
    """Return a Redis-backed message history for the given session/user ID.

    History is keyed by session_id so each user has their own persistent
    conversation that survives server restarts.
    """
    return RedisChatMessageHistory(
        session_id,
        url=settings.redis_url,
        ttl=_HISTORY_TTL,
    )


def build_chain(user_id: str, email: str) -> RunnableWithMessageHistory:
    """Build an AgentExecutor wrapped with Redis-backed conversation history.

    The returned chain is invoked with {"input": <text>} and a configurable
    session_id, which is used to load/save history from Redis automatically.
    History persists across server restarts — solving the 'restart wipes memory'
    problem by storing it in Redis rather than in process memory.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.3,
        google_api_key=settings.google_api_key,
    )
    tools = make_user_tools(user_id, email)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    return RunnableWithMessageHistory(
        executor,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
