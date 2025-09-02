from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request model cho chat API"""

    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model cho chat API"""

    session_id: str
    answer: str
    summary: Optional[str] = None
