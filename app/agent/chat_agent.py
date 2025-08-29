from typing import Dict, List, Optional

from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState

from app.config import K_LAST_MESSAGES, SUMMARY_THRESHOLD_N
from app.memory.redis_checkpointer import r, key_messages, key_summary
from app.services.venice_services import call_venice_chat, summarize_with_venice


class ChatState(MessagesState):
    summary: str = ""


def _read_last_k(session_id: str, k: int) -> List[Dict]:
    items = r().lrange(key_messages(session_id), 0, k - 1)
    result: List[Dict] = []
    for raw in reversed(items):
        try:
            role, content = raw.split("|", 1)
        except ValueError:
            role, content = "user", raw
        result.append({"role": role, "content": content})
    return result


def _push(session_id: str, role: str, content: str) -> None:
    r().lpush(key_messages(session_id), f"{role}|{content}")
    r().ltrim(key_messages(session_id), 0, K_LAST_MESSAGES - 1)


def router_node(state: ChatState, *, session_id: str) -> str:
    # Decide whether to summarize
    list_len = r().llen(key_messages(session_id))
    return "summarize" if list_len >= SUMMARY_THRESHOLD_N else "llm"


def summarize_node(state: ChatState, *, session_id: str) -> ChatState:
    recent = _read_last_k(session_id, SUMMARY_THRESHOLD_N)
    prev = r().get(key_summary(session_id))
    new_summary = summarize_with_venice(recent, prev)
    r().set(key_summary(session_id), new_summary)
    state.summary = new_summary
    return state


def llm_node(state: ChatState, *, session_id: str) -> ChatState:
    last_k = _read_last_k(session_id, K_LAST_MESSAGES)
    summary_text = r().get(key_summary(session_id)) or ""
    parts: List[str] = []
    if summary_text:
        parts.append(f"[Summary]\n{summary_text}")
    if last_k:
        dialogue = "\n".join(f"{m['role']}: {m['content']}" for m in last_k)
        parts.append(f"[Recent]\n{dialogue}")
    context = "\n\n".join(parts)
    user_msg = state.messages[-1]["content"] if state.messages else ""
    prompt = f"Answer briefly and helpfully. Here is the context.\n{context}\n\nUser: {user_msg}"

    reply = call_venice_chat(prompt)

    # Persist
    _push(session_id, "assistant", reply)
    state.messages.append({"role": "assistant", "content": reply})
    return state


def persist_user_node(state: ChatState, *, session_id: str) -> ChatState:
    # Persist the latest user message that came with the request
    if state.messages:
        last = state.messages[-1]
        if last.get("role") == "user":
            _push(session_id, "user", last.get("content", ""))
    return state


def build_graph() -> StateGraph:
    g = StateGraph(ChatState)

    g.add_node("persist_user", persist_user_node)
    g.add_node("summarize", summarize_node)
    g.add_node("llm", llm_node)

    g.set_entry_point("persist_user")
    g.add_conditional_edges("persist_user", router_node, {"summarize": "summarize", "llm": "llm"})
    g.add_edge("summarize", "llm")
    g.add_edge("llm", END)
    return g


graph = build_graph()