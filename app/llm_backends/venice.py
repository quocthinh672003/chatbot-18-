"""
Venice AI Backend - Core LLM Backend
Primary LLM backend using Venice AI for chat and character creation
"""

import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from .base import BaseLLMBackend
from ..constants import LLM_CONFIG, CHARACTER_TEMPLATES, RESPONSE_TEMPLATES
from ..utils.helpers import safe_json_parse, extract_meta_from_text, get_error_message, retry_with_backoff

logger = logging.getLogger(__name__)

class VeniceBackend(BaseLLMBackend):
    """Venice AI backend for LLM operations"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.venice.ai"
        self.client = httpx.AsyncClient(
            timeout=LLM_CONFIG["TIMEOUT_SECONDS"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        self.default_temperature = LLM_CONFIG["DEFAULT_TEMPERATURE"]
        self.max_tokens = LLM_CONFIG["MAX_TOKENS"]
        self.retry_attempts = LLM_CONFIG["RETRY_ATTEMPTS"]
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Send chat completion request to Venice AI"""
        try:
            model = kwargs.get("model", "venice-uncensored-chat")
            temperature = kwargs.get("temperature", self.default_temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = await self._make_request("/v1/chat/completions", payload)
            
            if "error" in response:
                return response
            
            content = response["choices"][0]["message"]["content"]
            clean_content, meta = extract_meta_from_text(content)
            
            return {
                "content": clean_content,
                "meta": meta,
                "model": model,
                "usage": response.get("usage", {}),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Venice chat error: {e}")
            return {
                "error": get_error_message("api_error", details=str(e)),
                "success": False
            }
    
    async def create_character_card(self, character_type: str) -> Dict[str, Any]:
        """Create character card using Venice AI"""
        try:
            # Get character template
            template = CHARACTER_TEMPLATES.get(character_type, CHARACTER_TEMPLATES["seductive"])
            
            system_prompt = f"""
You are a character creation expert. Create a detailed character card for a {character_type} character.

Base template:
- Name: {template['name']}
- Persona: {template['persona']}
- Boundaries: {template['boundaries']}
- Scenario: {template['scenario']}
- Greeting: {template['greeting']}

Create a unique character based on this template. Return the response in this JSON format:
{{
    "name": "Character Name",
    "persona": "Detailed personality description",
    "boundaries": "Character boundaries and limits",
    "scenario": "Current scenario/setting",
    "greeting": "Character's greeting message",
    "style": "realistic",
    "nsfw_level": 3,
    "image_prompt": "Detailed image prompt for character",
    "tags": ["tag1", "tag2", "tag3"]
}}
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a {character_type} character"}
            ]
            
            response = await self.chat(messages, model="venice-uncensored-chat")
            
            if "error" in response:
                return response
            
            # Parse character data
            character_data = safe_json_parse(response["content"])
            if not character_data:
                return {
                    "error": "Failed to parse character data",
                    "success": False
                }
            
            return {
                "character": character_data,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Venice character creation error: {e}")
            return {
                "error": get_error_message("api_error", details=str(e)),
                "success": False
            }
    
    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize conversation using Venice AI"""
        try:
            if not messages:
                return "No conversation to summarize."
            
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in messages[-10:]  # Last 10 messages
            ])
            
            system_prompt = """
You are a conversation summarizer. Create a brief, engaging summary of the conversation that captures the key points and context.
Keep the summary under 100 words and focus on the main topics, emotions, and any important details.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize this conversation:\n\n{conversation_text}"}
            ]
            
            response = await self.chat(messages, model="venice-uncensored-chat")
            
            if "error" in response:
                return "Failed to summarize conversation."
            
            return response["content"]
            
        except Exception as e:
            logger.error(f"Venice summarization error: {e}")
            return "Failed to summarize conversation."
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify message intent using Venice AI"""
        try:
            system_prompt = """
You are an intent classifier. Analyze the user message and classify it into one of these categories:
- chat: General conversation
- roleplay: Character roleplay requests
- image: Image generation requests
- help: Help or command requests
- settings: Settings or configuration requests

Return the response in this JSON format:
{
    "intent": "category",
    "confidence": 0.95,
    "details": "explanation"
}
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this message: {message}"}
            ]
            
            response = await self.chat(messages, model="venice-uncensored-chat")
            
            if "error" in response:
                return {"intent": "chat", "confidence": 0.5, "details": "Fallback classification"}
            
            # Parse intent data
            intent_data = safe_json_parse(response["content"])
            if not intent_data:
                return {"intent": "chat", "confidence": 0.5, "details": "Failed to parse intent"}
            
            return intent_data
            
        except Exception as e:
            logger.error(f"Venice intent classification error: {e}")
            return {"intent": "chat", "confidence": 0.5, "details": "Error in classification"}
    
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
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
