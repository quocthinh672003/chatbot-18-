import uuid
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationSummaryBufferMemory
from src.config.settings import (
    REDIS_URL,
    VENICE_BASE_URL,
    VENICE_API_KEY,
    VENICE_MODEL,
    MAX_TOKEN_LIMIT,
    TEMPERATURE,
    MEMORY_K,
)


class ChatService:
    """Service xử lý chat với Venice LLM và memory management"""

    def __init__(self):
        """Khởi tạo LLM Venice"""
        self.llm = ChatOpenAI(
            model=VENICE_MODEL,
            temperature=TEMPERATURE,
            base_url=VENICE_BASE_URL,
            api_key=VENICE_API_KEY,
        )

    def get_memory_for_session(self, session_id: str):
        """
        Tạo memory cho session cụ thể

        Returns:
            ConversationSummaryBufferMemory: Memory với auto-summarization
        """
        # RedisChatMessageHistory → lưu raw messages (không mất khi restart app)
        history = RedisChatMessageHistory(
            session_id=session_id,
            url=REDIS_URL,
            ttl=86400,  # 24 hours
        )

        # ConversationSummaryBufferMemory → tự động decide: giữ k message mới + summary cũ
        memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            chat_memory=history,
            max_token_limit=MAX_TOKEN_LIMIT,
            return_messages=True,
            k=MEMORY_K,  # giữ k tin gần nhất, cũ hơn thì tóm tắt
        )

        return memory

    def process_chat(self, message: str, session_id: Optional[str] = None):
        """
        Xử lý chat request theo workflow:

        User ↔️ AI (Venice API):
        - Mỗi khi user gửi tin → hệ thống append cả user + AI message vào Redis
        - Redis chính là nguồn dữ liệu thật (state) cho short-term memory
        - Nếu hội thoại > 5 message → tóm tắt cũ + giữ 5 tin gần nhất
        - Khi gọi Venice API: prompt = summary + 5 messages gần nhất

        Args:
            message (str): Message từ user
            session_id (Optional[str]): Session ID, tạo mới nếu None

        Returns:
            dict: Kết quả với session_id, answer, summary
        """

        # Step 1: Tạo session_id nếu chưa có
        if not session_id:
            session_id = str(uuid.uuid4())

        # Step 2: Tạo memory từ session_id
        # RedisChatMessageHistory → lưu raw messages (không mất khi restart app)
        # ConversationSummaryBufferMemory → tự động decide: giữ k message mới + summary cũ
        memory = self.get_memory_for_session(session_id)

        # Step 3: Ghi message user vào memory
        memory.chat_memory.add_user_message(message)

        # Step 4: Lấy context đã được memory quản lý
        # Nếu >5 message → prompt gửi đi gồm summary toàn bộ cũ + 5 message gần nhất
        past_messages = memory.chat_memory.messages

        # Step 5: Gọi LLM với context
        # Venice vừa hiểu toàn bộ ngữ cảnh trước đó (qua summary),
        # vừa có chi tiết gần nhất (qua 5 message mới)
        messages = past_messages + [{"role": "user", "content": message}]
        response = self.llm.invoke(messages)
        answer = response.content

        # Step 6: Ghi lại kết quả
        memory.chat_memory.add_ai_message(answer)

        # Step 7: Trả về kết quả
        return {
            "session_id": session_id,
            "answer": answer,
            "summary": getattr(memory, "moving_summary_buffer", None),
        }
