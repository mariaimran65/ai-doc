from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from duckduckgo_search import DDGS

from app.config import settings


def _llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=settings.google_api_key,
    )


def _search(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
        return (
            "\n\n".join(f"{r['title']}\n{r['body']}" for r in results) or "No results."
        )
    except Exception as e:
        return f"Search failed: {e}"


def researcher_node(state: dict) -> dict:
    task = state["task"]
    search_results = _search(task)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a research agent. Summarise the following search results "
                "as they relate to the task. Be factual and concise.",
            ),
            ("human", "Task: {task}\n\nSearch results:\n{results}"),
        ]
    )
    chain = prompt | _llm()
    response = chain.invoke({"task": task, "results": search_results})
    output = response.content

    return {
        "research_output": output,
        "steps": [{"node": "researcher", "output": output}],
    }


def coder_node(state: dict) -> dict:
    task = state["task"]
    research = state.get("research_output", "")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a coding agent. Based on the task and any research provided, "
                "produce a concise, well-commented code example in Python. "
                "Use markdown code blocks.",
            ),
            ("human", "Task: {task}\n\nResearch context:\n{research}"),
        ]
    )
    chain = prompt | _llm()
    response = chain.invoke({"task": task, "research": research})
    output = response.content

    return {
        "code_output": output,
        "steps": [{"node": "coder", "output": output}],
    }


def summariser_node(state: dict) -> dict:
    task = state["task"]
    research = state.get("research_output", "")
    code = state.get("code_output", "")

    parts = [
        f"Research:\n{research}" if research else "",
        f"Code:\n{code}" if code else "",
    ]
    context = "\n\n".join(p for p in parts if p)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a synthesis agent. Combine the worker outputs into a "
                "clear, structured final answer for the user. Use markdown headings.",
            ),
            ("human", "Task: {task}\n\n{context}"),
        ]
    )
    chain = prompt | _llm()
    response = chain.invoke({"task": task, "context": context})
    output = response.content

    return {
        "final_output": output,
        "steps": [{"node": "summariser", "output": output}],
    }
