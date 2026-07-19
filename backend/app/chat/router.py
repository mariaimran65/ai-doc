import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.auth_utils import get_current_user
from app.chat.chain import build_executor, history_from_messages

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

    The client sends the full conversation history on every request.
    The last message is the new user input; everything before it is history.
    Tokens are streamed back as SSE data events so the UI can render them live.
    A final [DONE] event signals the end of the stream.
    """
    if not body.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    messages = [m.model_dump() for m in body.messages]
    # Last message is the new user input; preceding messages are history
    user_input = messages[-1]["content"]
    history = history_from_messages(messages[:-1])

    executor = build_executor(
        user_id=current_user["sub"],
        email=current_user["email"],
    )

    async def event_generator():
        loop = asyncio.get_event_loop()

        # Run the blocking AgentExecutor in a thread to avoid blocking the event loop
        async def run_agent():
            return await loop.run_in_executor(
                None,
                lambda: executor.invoke(
                    {"input": user_input, "chat_history": history}
                ),
            )

        try:
            result = await run_agent()
            output = result.get("output", "")
            # Stream the output in chunks so the UI animates
            chunk_size = 4
            for i in range(0, len(output), chunk_size):
                chunk = output[i: i + chunk_size]
                yield {"data": json.dumps({"token": chunk})}
                await asyncio.sleep(0.01)
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}

        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
