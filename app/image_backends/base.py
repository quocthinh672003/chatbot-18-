"""
Base Image Backend Interface
Abstract base class for image generation backends
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseImageBackend(ABC):
    """Abstract base class for image generation backends"""
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image from prompt"""
        pass
    
    @abstractmethod
    async def check_safety(self, prompt: str) -> bool:
        """Check if prompt is safe for generation"""
        pass
