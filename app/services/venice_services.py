import os, requests
from typing import List, Dict, Optional

VENICE_API_KEY = os.getenv("VENICE_API_KEY")
VENICE_MODEL_CHAT = os.getenv("VENICE_MODEL_CHAT", "venice-chat") 
VENICE_MODEL_SUMMARY = os.getenv("VENICE_MODEL_SUMMARY", "venice-summary")

def call_venice_chat(prompt: str) -> str:
    # Thay URL/format theo docs Venice của bạn
    res = requests.post(
        "https://api.venice.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {VENICE_API_KEY}"},
        json={"model": VENICE_MODEL_CHAT, "messages": [{"role":"user","content":prompt}]},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

def summarize_with_venice(messages: List[Dict], prev_summary: Optional[str]) -> str:
    # Build plain-text dialogue from a list of {role, content}
    dialogue_lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        dialogue_lines.append(f"{role}: {content}")
    dialogue = "\n".join(dialogue_lines)
    prompt = f"""
You are a summarization assistant. Update the running summary concisely, preserving facts, intents, and decisions.
Previous summary (if any): {prev_summary or "None"}
New conversation chunk:
{dialogue}
Return the updated summary (<=10 sentences, concise).
"""
    res = requests.post(
        "https://api.venice.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {VENICE_API_KEY}"},
        json={"model": VENICE_MODEL_SUMMARY, "messages": [{"role":"user","content":prompt}]},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]


# client gọi Venice API