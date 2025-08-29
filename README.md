User (Web/App)
    |
    v
[API Gateway - FastAPI]  -- validates, routes -->
    |
    v
[Orchestrator - LangGraph StateGraph]
    |
    +--> (RouterNode) --should_summarize?--> [Yes] ----+
    |                                                 |
    |                                             [SummarizationNode]
    |                                             - read N messages
    |                                             - create/update running summary (Venice)
    |                                             - trim to last_k
    |                                                 |
    +------------------------------ No ---------------+
    |
    v
[LLMNode - Venice Chat]
  - build prompt = system + summary + last_k + user_msg
  - get AI response
    |
    v
[PersistNode - Redis]
  - LPUSH user/ai messages
  - LTRIM to last_k
  - SET summary (if updated)
    |
    v
Response -> User

Component table
Component	Tech	Main task	Core funcs/vars	Data/Key	Docs
API Gateway	FastAPI	Endpoints /chat, /session/{id}, lightweight auth, forward to Orchestrator	POST /chat, GET /session, DELETE /session	n/a	FastAPI docs: https://fastapi.tiangolo.com/
Orchestrator	LangGraph StateGraph + MessagesState	Coordinate node flow, pass state, thread_id	graph.invoke(input, config={'thread_id': session_id})	thread_id=session	LangGraph memory (short-term): link
RouterNode	Python fn in graph	Decide whether to summarize	should_summarize(session_id) based on LLEN/token	Redis LLEN chat:{sid}:messages	Manage memory: link
SummarizationNode	Venice (summarize), Redis	Create/update running summary, trim	summarize_with_venice(messages, prev_summary) -> new_summary; set_summary(); ltrim_last_k()	GET/SET chat:{sid}:summary; LRANGE/LTRIM chat:{sid}:messages	Long/short-term mem: link
LLMNode	Venice Chat API	Generate reply from context	build_prompt(summary,last_k,user_msg); call_venice_chat(prompt)	n/a	Venice docs: https://docs.venice.ai
PersistNode	Redis	Store user/AI messages; enforce last_k window	store_message(role, content); ltrim_last_k()	LPUSH chat:{sid}:messages; LTRIM ... 0 k-1	Redis Lists: link
Session API	FastAPI + Redis	Query/delete session	get_recent_messages(k), get_summary(), clear_session()	keys by sid	FastAPI; Redis links above
Mechanism “summary + last_k” (brief)
Config variables:
K_LAST_MESSAGES (e.g., 5), SUMMARY_THRESHOLD_N (e.g., 10), TOKEN_BUDGET (per model).
For each message:
1) PersistNode: LPUSH user message → optional LTRIM.
2) RouterNode: if LLEN ≥ SUMMARY_THRESHOLD_N or token estimate exceeds budget → go SummarizationNode.
3) SummarizationNode:
Take a recent chunk (e.g., latest 20) + prev_summary.
Running summary prompt: “concise, keep facts/intents/decisions, avoid redundant details”.
Venice returns summary_new → SET chat:{sid}:summary = summary_new.
LTRIM chat:{sid}:messages 0..K_LAST_MESSAGES-1.
4) LLMNode:
Build prompt: system + [Summary] + last_k messages + current_user_message.
Venice returns reply.
5) PersistNode: save AI message, LTRIM to keep last_k.
Results:
Multi-user: isolated by `session_id`.
On app kill: state persists in Redis.
Compact context: only summary + last_k sent to Venice each call.
References:
Short-term memory & checkpointing: LangGraph Add memory
Short-term memory management: Manage short-term memory
Long-term memory: Add long-term memory
Redis Lists: Redis Lists
Venice API: https://docs.venice.ai
Recommended defaults: K_LAST_MESSAGES=5, SUMMARY_THRESHOLD_N=10.

Quick demo

1) Configure `.env`:
```
REDIS_URL=redis://localhost:6379/0
VENICE_API_KEY=sk-...
K_LAST_MESSAGES=5
SUMMARY_THRESHOLD_N=10
```

2) Install deps and run API:
```
pip install -r requirements.txt
uvicorn main:app --reload
```

3) Call the chat API:
```
POST /api/chat {"session_id":"u1","message":"hello"}
GET  /api/session/u1
DELETE /api/session/u1
```