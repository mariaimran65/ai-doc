from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.config import settings
from app.chat.tools import make_user_tools

SYSTEM_PROMPT = """You are an AI assistant embedded in the AI-Doc platform — a training \
programme that teaches production AI engineering. You help the signed-in user with \
questions about LangChain, LangGraph, RAG pipelines, FastAPI, Docker, and AI \
engineering in general.

You have access to a web search tool for current information. Use it when the question \
requires facts you may not have, or when the user asks about recent developments.

Always be concise and technical. When showing code, use markdown code blocks."""


def build_executor(user_id: str, email: str) -> AgentExecutor:
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0.3,
        streaming=True,
        api_key=settings.anthropic_api_key,
    )
    tools = make_user_tools(user_id, email)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def history_from_messages(messages: list[dict]) -> list:
    """Convert frontend message list to LangChain message objects."""
    result = []
    for m in messages:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result
