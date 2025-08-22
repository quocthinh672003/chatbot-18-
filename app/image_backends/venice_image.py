"""
Venice AI Image Backend - Core Image Generation
Primary image generation backend using Venice AI
"""

import httpx
import logging
from typing import Dict, Any, Optional
from .base import BaseImageBackend
from ..constants import IMAGE_CONFIG, API_ENDPOINTS
from ..utils.helpers import get_error_message, retry_with_backoff

logger = logging.getLogger(__name__)

class VeniceImageBackend(BaseImageBackend):
    """Venice AI backend for image generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.venice.ai"
        self.client = httpx.AsyncClient(
            timeout=IMAGE_CONFIG["TIMEOUT_SECONDS"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image using Venice AI"""
        try:
            model = kwargs.get("model", "venice-image-xl")
            size = kwargs.get("size", IMAGE_CONFIG["DEFAULT_SIZE"])
            style = kwargs.get("style", IMAGE_CONFIG["DEFAULT_STYLE"])
            
            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "style": style,
                "quality": "high",
                "n": 1
            }
            
            response = await self._make_request("/v1/images/generations", payload)
            
            if "error" in response:
                return response
            
            # Get image URL from response
            image_url = response["data"][0]["url"]
            
            # Download image
            image_data = await self._download_image(image_url)
            
            return {
                "image_data": image_data,
                "image_url": image_url,
                "prompt": prompt,
                "model": model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Venice image generation error: {e}")
            return {
                "error": get_error_message("api_error", details=str(e)),
                "success": False
            }
    
    async def _download_image(self, image_url: str) -> bytes:
        """Download image from URL"""
        try:
            async with self.client as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Image download error: {e}")
            raise Exception(f"Failed to download image: {str(e)}")
    
    @retry_with_backoff
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Venice API with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.client as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise Exception("Request timeout")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid API key")
            elif e.response.status_code == 429:
                raise Exception("Rate limit exceeded")
            else:
                raise Exception(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def check_safety(self, prompt: str) -> bool:
        """Check if prompt is safe for generation"""
        try:
            # Basic safety check - can be enhanced
            unsafe_keywords = ["child", "minor", "underage", "illegal"]
            prompt_lower = prompt.lower()
            
            for keyword in unsafe_keywords:
                if keyword in prompt_lower:
                    return False
            
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
