from langchain_openai import ChatOpenAI
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

_HISTORY_TTL = 60 * 60 * 24 * 7


def _get_session_history(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(
        session_id,
        url=settings.redis_url,
        ttl=_HISTORY_TTL,
    )


def build_chain(user_id: str, email: str) -> RunnableWithMessageHistory:
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.3,
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
