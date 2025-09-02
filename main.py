from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.models.models import ChatRequest, ChatResponse
from src.services.service import ChatService

app = FastAPI(title="AI Chat System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
try:
    chat_service = ChatService()
except Exception as e:
    print(f"Failed to initialize ChatService: {e}")
    chat_service = None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - handle conversation with AI

    Workflow:
    1. Receive {message, session_id?}
    2. Create memory from session_id
    3. Add message to memory
    4. Get context managed by memory
    5. Call Venice LLM with context
    6. Save response
    7. Return {session_id, answer}
    """

    # Check if service is available
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service is not available")

    # Validate request
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = chat_service.process_chat(
            message=request.message, session_id=request.session_id
        )

        return ChatResponse(
            session_id=result["session_id"],
            answer=result["answer"],
            summary=result["summary"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from src.database.redis_client import redis_client

    try:
        redis_info = redis_client.get_connection_info()
        service_status = "healthy" if chat_service else "unhealthy"

        return {
            "status": service_status,
            "service": "AI Chat System",
            "redis": redis_info,
            "venice_llm": "available" if chat_service else "unavailable",
        }
    except Exception as e:
        return {"status": "unhealthy", "service": "AI Chat System", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    from src.config.settings import APP_HOST, APP_PORT, DEBUG

    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=DEBUG)
