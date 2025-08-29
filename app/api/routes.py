from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict

from app.config import K_LAST_MESSAGES, SUMMARY_THRESHOLD_N
from app.memory.redis_checkpointer import r, key_messages, key_summary
from app.services.venice_services import call_venice_chat, summarize_with_venice
from app.agent.chat_agent import graph, ChatState

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    summary: str | None = None


def _get_recent_messages(session_id: str, k: int) -> List[Dict]:
    msgs = r().lrange(key_messages(session_id), 0, k - 1)  # stored newest first
    # convert back to dicts
    result = []
    for raw in reversed(msgs):  # oldest to newest for readability
        try:
            role, content = raw.split("|", 1)
        except ValueError:
            role, content = "user", raw
        result.append({"role": role, "content": content})
    return result


def _push_message(session_id: str, role: str, content: str) -> None:
    r().lpush(key_messages(session_id), f"{role}|{content}")
    r().ltrim(key_messages(session_id), 0, K_LAST_MESSAGES - 1)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.session_id:
        raise HTTPException(400, "session_id is required")

    # Delegate to LangGraph orchestrator (handles persist → route → summarize → llm → persist)
    state = ChatState(messages=[{"role": "user", "content": req.message}], summary=r().get(key_summary(req.session_id)) or "")
    out = graph.invoke(state, config={"thread_id": req.session_id, "configurable": {"session_id": req.session_id}})
    updated_summary = r().get(key_summary(req.session_id)) or None
    reply = out.messages[-1]["content"] if out.messages else ""
    return ChatResponse(session_id=req.session_id, reply=reply, summary=updated_summary)


@router.get("/session/{session_id}")
def get_session(session_id: str):
    return {
        "messages": _get_recent_messages(session_id, K_LAST_MESSAGES),
        "summary": r().get(key_summary(session_id)) or "",
    }


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    r().delete(key_messages(session_id))
    r().delete(key_summary(session_id))
    return {"status": "cleared"}