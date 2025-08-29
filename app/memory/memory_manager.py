from langgraph.graph import StateGraph, MessagesState

class ConversationState(MessagesState):
    summary: str = ""

def build_context(state: ConversationState, last_k: int = 5) -> str:
    parts = []
    if state.summary:
        parts.append(f"Context: {state.summary}")
    recent = state.messages[-last_k:] if state.messages else []
    if recent:
        msg_text = "\n".join(f"{m.get('role','user')}: {m.get('content','')}" for m in recent)
        parts.append(f"Recent:\n{msg_text}")
    return "\n\n".join(parts)