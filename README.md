# AI Chat System với LangChain

## 🎯 Mục tiêu

Hệ thống AI chat đáp ứng được nhiều người dùng và hiểu được ngữ cảnh trước đó của cuộc hội thoại, sử dụng LangChain để tối ưu hóa.

## 🏗️ Kiến trúc

### Components chính:

- **RedisChatMessageHistory**: Lưu trữ conversation history per session_id
- **ConversationSummaryBufferMemory**: Auto-summarization + sliding window
- **ChatOpenAI**: Gọi Venice LLM (OpenAI-compatible)
- **FastAPI**: Expose POST /chat endpoint

### Workflow:

1. Nhận request `{message, session_id?}`
2. Tạo memory từ session_id
3. Ghi message vào memory
4. Lấy context đã được memory quản lý
5. Gọi LLM Venice với context
6. Lưu response
7. Trả về `{session_id, answer}`

## 🔄 Luồng hội thoại chi tiết

### User ↔️ AI (Venice API):

**Mỗi khi user gửi tin:**

- Hệ thống append cả user + AI message vào Redis (nhờ RedisChatMessageHistory)
- Redis chính là nguồn dữ liệu thật (state) cho short-term memory → không mất khi restart app

**Nếu hội thoại > 5 message:**

- Thay vì gửi hết lịch sử (tốn token), memory sẽ làm 2 bước:
  1. **Tóm tắt các message cũ** → lưu vào summary (string ngắn gọn)
  2. **Giữ lại N (vd 5) tin gần nhất** để giữ ngữ cảnh gần đây

**Khi gọi Venice API:**

- Bạn gửi vào prompt = summary + 5 messages gần nhất
- Venice vừa hiểu toàn bộ ngữ cảnh trước đó (qua summary), vừa có chi tiết gần nhất (qua 5 message mới)

### RedisChatMessageHistory dùng như nào?

```python
from langchain_community.chat_message_histories import RedisChatMessageHistory

history = RedisChatMessageHistory(
    session_id="user_123",
    url="redis://localhost:6379/0"
)

history.add_user_message("Xin chào")
history.add_ai_message("Chào bạn")

print(history.messages)  # -> [HumanMessage(...), AIMessage(...)]
```

💡 **Điểm chính:** mỗi session_id = 1 cuộc hội thoại riêng biệt.
→ Khi bạn restart app, load lại history = RedisChatMessageHistory(session_id="user_123", ...) thì toàn bộ history vẫn có.

### ConversationSummaryBufferMemory vs ConversationSummaryMemory

**ConversationSummaryMemory:**

- Luôn tóm tắt toàn bộ hội thoại thành 1 bản tóm tắt duy nhất
- Không giữ lại các message gần đây
- Ngữ cảnh gần có thể bị mất chi tiết → thích hợp cho QA dài hạn

**ConversationSummaryBufferMemory ✅ (hay dùng nhất):**

- Kết hợp: giữ lại last_k message gần nhất + summary các tin cũ
- Đây chính là cách bạn nói: "gửi summary + 5 messages gần nhất"
- Dùng trong hầu hết chatbot thực tế → vừa tiết kiệm token, vừa không mất ngữ cảnh gần

👉 **Vậy bạn chỉ cần dùng ConversationSummaryBufferMemory (không cần thêm ConversationSummaryMemory).**

### Cách kết hợp Redis + ConversationSummaryBufferMemory

```python
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="venice-summary")

memory = ConversationSummaryBufferMemory(
    llm=llm,
    chat_memory=RedisChatMessageHistory(
        session_id="user_123",
        url="redis://localhost:6379/0"
    ),
    return_messages=True,
    k=5   # giữ 5 tin gần nhất, cũ hơn thì tóm tắt
)
```

- **RedisChatMessageHistory** → lưu raw messages (không mất khi restart app)
- **ConversationSummaryBufferMemory** → tự động decide: giữ 5 message mới + summary cũ

## 🚀 Cài đặt

### 1. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường:

```bash
cp env.example .env
# Chỉnh sửa .env với thông tin Venice và Redis
```

### 3. Chạy Redis:

```bash
redis-server
```

### 4. Chạy ứng dụng:

```bash
python main.py
```

## 📡 API Usage

### POST /chat

```json
{
  "message": "Xin chào, bạn có thể giúp tôi không?",
  "session_id": null // Tạo mới nếu null
}
```

### Response:

```json
{
  "session_id": "uuid-generated",
  "answer": "Xin chào! Tôi có thể giúp bạn. Bạn cần hỗ trợ gì?",
  "summary": "User greeted and asked for help"
}
```

## 🔧 Cấu hình

### Memory Parameters:

- `MAX_TOKEN_LIMIT`: 1500-2500 (tùy model)
- `TEMPERATURE`: 0.3-0.7
- `MEMORY_K`: 5 (giữ k message gần nhất)
- `REDIS_TTL`: 86400 (24h) - tự động dọn rác

### Venice LLM:

- Base URL: Endpoint Venice server
- Model: Tùy chọn model Venice
- API Key: Authentication

## ✨ Tính năng

### ✅ Đa người dùng:

- Mọi dữ liệu tách theo session_id trong Redis
- Client lưu và gửi lại session_id ở các lượt sau

### ✅ Hiểu ngữ cảnh:

- Auto-summarization khi vượt token limit
- Sliding window giữ cửa sổ gần nhất
- Context được maintain tự động

### ✅ Tối ưu hóa:

- Sử dụng tối đa LangChain components
- Ít code tay, nhiều logic tự động
- Survive khi app restart nhờ Redis

## 🔄 Cách hoạt động

### ConversationSummaryBufferMemory:

1. **Auto-summarization**: Khi conversation vượt max_token_limit
2. **Sliding window**: Luôn giữ cửa sổ gần nhất
3. **Context preservation**: Summary + recent messages

### Mỗi request mới:

1. Load context từ Redis theo session_id
2. Add user message vào history
3. Auto-summarize nếu cần (LangChain tự handle)
4. Generate response với context đã optimize
5. Save AI response vào history
6. Persist tất cả vào Redis

## ✅ Trả lời thắc mắc

**User chat với AI (Venice API).**

**Nếu >5 message** → prompt gửi đi gồm summary toàn bộ cũ + 5 message gần nhất.

**Dùng RedisChatMessageHistory** để lưu state bền.

**Chỉ cần ConversationSummaryBufferMemory** (không cần cả 2).
