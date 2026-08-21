from langchain_core.tools import tool
from duckduckgo_search import DDGS


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use for questions about recent events,
    facts, or anything that requires up-to-date information."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"**{r['title']}**\n{r['body']}\nSource: {r['href']}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"


def make_user_tools(user_id: str, email: str) -> list:
    """Return tools bound to the current authenticated user."""

    @tool
    def get_current_user() -> dict:
        """Return the profile of the currently signed-in user."""
        return {"user_id": user_id, "email": email}

    return [get_current_user, web_search]
