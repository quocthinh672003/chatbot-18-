"""
Base LLM Backend Interface
Abstract base class for LLM backends
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMBackend(ABC):
    """Abstract base class for LLM backends"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Send chat completion request"""
        pass
    
    @abstractmethod
    async def create_character_card(self, character_type: str) -> Dict[str, Any]:
        """Create character card"""
        pass
    
    @abstractmethod
    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize conversation"""
        pass
    
    @abstractmethod
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify message intent"""
        pass
