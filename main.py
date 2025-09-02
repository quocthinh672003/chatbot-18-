from fastapi import FastAPI, HTTPException
from src.models.models import ChatRequest, ChatResponse
from src.services.service import ChatService

app = FastAPI(title="AI Chat System", version="1.0.0")

# Khởi tạo service
chat_service = ChatService()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - xử lý conversation với AI

    Workflow:
    1. Nhận {message, session_id?}
    2. Tạo memory từ session_id
    3. Ghi message vào memory
    4. Lấy context đã được memory quản lý
    5. Gọi LLM Venice với context
    6. Lưu response
    7. Trả về {session_id, answer}
    """
    try:
        result = chat_service.process_chat(
            message=request.message, session_id=request.session_id
        )

        return ChatResponse(
            session_id=result["session_id"],
            answer=result["answer"],
            summary=result["summary"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from src.database.redis_client import redis_client

    redis_info = redis_client.get_connection_info()

    return {"status": "healthy", "service": "AI Chat System", "redis": redis_info}


if __name__ == "__main__":
    import uvicorn
    from src.config.settings import APP_HOST, APP_PORT, DEBUG

    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=DEBUG)
