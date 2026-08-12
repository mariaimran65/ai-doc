import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.auth_utils import get_current_user
from app.chat.chain import build_chain

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@router.post("/")
async def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Stream a chat response as Server-Sent Events.

    Conversation history is stored in Redis keyed by user ID, so it persists
    across server restarts. The client sends the full message list so the UI
    can render history, but the LLM reads history from Redis — not the payload.

    Tokens are streamed back as SSE data events. A final [DONE] event signals
    the end of the stream.
    """
    if not body.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    user_input = body.messages[-1].content
    user_id = current_user["sub"]

    chain = build_chain(user_id=user_id, email=current_user["email"])

    async def event_generator():
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                lambda: chain.invoke(
                    {"input": user_input},
                    config={"configurable": {"session_id": user_id}},
                ),
            )
            output = result.get("output", "")
            chunk_size = 4
            for i in range(0, len(output), chunk_size):
                yield {"data": json.dumps({"token": output[i : i + chunk_size]})}
                await asyncio.sleep(0.01)
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}

        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
