import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.auth_utils import get_current_user
from app.agents.graph import build_graph

router = APIRouter()


class RunRequest(BaseModel):
    task: str


@router.post("/run")
async def run_agent(
    body: RunRequest,
    current_user: dict = Depends(get_current_user),
):
    """Stream LangGraph execution steps as SSE.

    Each node execution emits one or more step events so the UI can show
    live agent activity. A final event carries the complete output.
    """
    if not body.task.strip():
        raise HTTPException(status_code=400, detail="Task must not be empty")

    graph = build_graph()

    async def event_generator():
        loop = asyncio.get_running_loop()

        initial_state = {
            "task": body.task,
            "research_output": "",
            "code_output": "",
            "final_output": "",
            "steps": [],
            "next": "",
            "iteration": 0,
        }

        try:
            # Run graph in thread to avoid blocking the event loop
            all_steps = []
            final_output = ""

            def run_graph():
                nonlocal final_output
                result = None
                for chunk in graph.stream(initial_state):
                    for node_name, node_output in chunk.items():
                        steps = node_output.get("steps", [])
                        all_steps.extend(steps)
                        result = node_output
                if result:
                    final_output = result.get("final_output", "")
                return all_steps, final_output

            steps, final = await loop.run_in_executor(None, run_graph)

            for step in steps:
                yield {"data": json.dumps({"step": step})}
                await asyncio.sleep(0.05)

            yield {"data": json.dumps({"final": final})}

        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}

        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
