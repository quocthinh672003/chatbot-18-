from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request model for chat API"""

    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat API"""

    session_id: str
    answer: str
    summary: Optional[str] = None
