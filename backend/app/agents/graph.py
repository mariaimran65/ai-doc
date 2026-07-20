import operator
from typing import TypedDict, Annotated, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.config import settings
from app.agents.workers import researcher_node, coder_node, summariser_node


class AgentState(TypedDict):
    task: str
    research_output: str
    code_output: str
    final_output: str
    # steps accumulate across all nodes
    steps: Annotated[list, operator.add]
    next: str
    iteration: int


class SupervisorDecision(BaseModel):
    next: Literal["researcher", "coder", "summariser", "FINISH"]
    reasoning: str


def supervisor_node(state: AgentState) -> dict:
    task = state["task"]
    iteration = state.get("iteration", 0)
    research_done = bool(state.get("research_output"))
    code_done = bool(state.get("code_output"))

    # After 3 iterations or when both research and code are done, summarise
    if iteration >= 3 or (research_done and code_done):
        decision = SupervisorDecision(
            next="summariser", reasoning="All workers complete."
        )
    else:
        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            temperature=0,
            api_key=settings.anthropic_api_key,
        ).with_structured_output(SupervisorDecision)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a supervisor coordinating worker agents. "
                    "Available workers:\n"
                    "- researcher: searches the web and summarises findings\n"
                    "- coder: writes Python code examples\n"
                    "- summariser: synthesises all outputs into a final answer (call last)\n\n"
                    "Workers already done: {done}\n"
                    "Choose the most useful next worker for this task, or FINISH if done.",
                ),
                ("human", "Task: {task}"),
            ]
        )
        done = []
        if research_done:
            done.append("researcher")
        if code_done:
            done.append("coder")

        decision = (prompt | llm).invoke(
            {
                "task": task,
                "done": ", ".join(done) if done else "none",
            }
        )

    return {
        "next": decision.next,
        "steps": [
            {
                "node": "supervisor",
                "output": f"→ routing to {decision.next}: {decision.reasoning}",
            }
        ],
        "iteration": iteration + 1,
    }


def route(state: AgentState) -> str:
    return state["next"]


def build_graph() -> StateGraph:
    wf = StateGraph(AgentState)

    wf.add_node("supervisor", supervisor_node)
    wf.add_node("researcher", researcher_node)
    wf.add_node("coder", coder_node)
    wf.add_node("summariser", summariser_node)

    wf.set_entry_point("supervisor")

    wf.add_conditional_edges(
        "supervisor",
        route,
        {
            "researcher": "researcher",
            "coder": "coder",
            "summariser": "summariser",
            "FINISH": END,
        },
    )

    wf.add_edge("researcher", "supervisor")
    wf.add_edge("coder", "supervisor")
    wf.add_edge("summariser", END)

    return wf.compile()
