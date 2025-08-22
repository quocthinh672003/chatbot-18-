"""
Stable Horde Image Generation Backend
Free, crowdsourced image generation
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
from .base import BaseImageBackend
from ..constants import IMAGE_CONFIG, API_ENDPOINTS

class StableHordeBackend(BaseImageBackend):
    """Stable Horde image generation backend"""
    
    def __init__(self, api_key: str = ""):
        # Use anonymous key if none provided (lower priority but works)
        self.api_key = api_key or "0000000000"
        self.base_url = API_ENDPOINTS["stable_horde"]
        self.client = httpx.AsyncClient(timeout=IMAGE_CONFIG["TIMEOUT_SECONDS"])
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image using Stable Horde"""
        try:
            # Prepare request - Simplified format for Stable Horde
            negative_prompt: Optional[str] = kwargs.get("negative_prompt")
            width: int = kwargs.get("width", 512)
            height: int = kwargs.get("height", 512)
            steps: int = kwargs.get("steps", 34)
            cfg_scale: float = kwargs.get("cfg_scale", 6.5)
            sampler_name: str = kwargs.get("sampler_name", "k_dpmpp_2m")

            payload = {
                "prompt": prompt,
                "params": {
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler_name": sampler_name,
                    "n": 1
                },
                "nsfw": True,
                "trusted_workers": False,
                "censor_nsfw": False,
                "r2": True
            }

            if negative_prompt:
                payload["params"]["negative_prompt"] = negative_prompt
            
            # Headers per Stable Horde spec
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Client-Agent": "lucid-dreams-bot:0.1:github.com/yourname/lucid-dreams-bot"
            }
            headers["apikey"] = self.api_key
            
            # Submit generation request
            response = await self.client.post(
                f"{self.base_url}/generate/async",
                json=payload,
                headers=headers
            )
            if response.status_code >= 400:
                # Return body for better debugging
                try:
                    err = response.json()
                except Exception:
                    err = {"text": response.text}
                raise httpx.HTTPStatusError(f"{response.status_code} {err}", request=response.request, response=response)
            
            
            generation_data = response.json()
            generation_id = generation_data["id"]
            
            # Poll for completion
            image_url = await self._poll_generation(generation_id)
            
            if image_url:
                return {
                    "success": True,
                    "image_url": image_url,
                    "prompt": prompt,
                    "backend": "stable_horde"
                }
            else:
                return {
                    "success": False,
                    "error": "Image generation failed or timed out",
                    "backend": "stable_horde"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Stable Horde error: {str(e)}",
                "backend": "stable_horde"
            }
    
    async def _poll_generation(self, generation_id: str) -> Optional[str]:
        """Poll for generation completion"""
        max_attempts = IMAGE_CONFIG["MAX_POLLING_ATTEMPTS"]
        poll_interval = IMAGE_CONFIG["POLLING_INTERVAL"]
        
        for attempt in range(max_attempts):
            try:
                response = await self.client.get(
                    f"{self.base_url}/generate/check/{generation_id}"
                )
                response.raise_for_status()
                
                check_data = response.json()
                
                if check_data["done"]:
                    # Get generated image
                    result_response = await self.client.get(
                        f"{self.base_url}/generate/status/{generation_id}"
                    )
                    result_response.raise_for_status()
                    
                    result_data = result_response.json()
                    if result_data["generations"]:
                        return result_data["generations"][0]["img"]
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        return None
    
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
