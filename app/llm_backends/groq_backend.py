import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..constants import LLM_CONFIG, GROQ_MODELS, RESPONSE_TEMPLATES
from ..utils.helpers import safe_json_parse, extract_meta_from_text, get_error_message, retry_with_backoff

class GroqBackend:
    """Groq API backend for LLM operations"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.client = httpx.AsyncClient(
            timeout=LLM_CONFIG["TIMEOUT_SECONDS"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        
        # Use constants for configuration
        self.default_temperature = LLM_CONFIG["DEFAULT_TEMPERATURE"]
        self.max_tokens = LLM_CONFIG["MAX_TOKENS"]
        self.retry_attempts = LLM_CONFIG["RETRY_ATTEMPTS"]
    
    async def chat(self, messages: List[Dict[str, str]], 
                  model: str = "llama3.1-8b", 
                  temperature: float = None,
                  max_tokens: int = None) -> Dict[str, Any]:
        """Send chat completion request to Groq"""
        
        try:
            # Use default values if not provided
            temperature = temperature or self.default_temperature
            max_tokens = max_tokens or self.max_tokens
            
            # Get model name from constants
            model_name = GROQ_MODELS.get(model, GROQ_MODELS["llama3.1-8b"])
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = await self._make_request("/chat/completions", payload)
            
            if response.get("choices") and len(response["choices"]) > 0 and "message" in response["choices"][0]:
                choice = response["choices"][0]
                content = choice["message"].get("content", "")
                
                # Extract meta information if present
                clean_content, meta = extract_meta_from_text(content)
                
                return {
                    "content": clean_content,
                    "meta": meta,
                    "model": model_name,
                    "usage": response.get("usage", {}),
                    "finish_reason": choice.get("finish_reason")
                }
            else:
                # Log unexpected schema for debugging
                import logging
                logging.getLogger(__name__).error(f"Unexpected Groq response schema: {response}")
                raise Exception("No response content received")
                
        except Exception as e:
            return {
                "error": get_error_message("api_timeout", error=str(e)),
                "content": RESPONSE_TEMPLATES["error"]
            }
    
    async def create_character_card(self, character_type: str, 
                                  user_preferences: str = "") -> Dict[str, Any]:
        """Create character card using Groq"""
        
        try:
            # Get character template from constants
            from ..constants import CHARACTER_TEMPLATES
            template = CHARACTER_TEMPLATES.get(character_type, CHARACTER_TEMPLATES["seductive"])
            
            system_prompt = f"""Create a detailed character card for a {character_type} character.
            
Base template:
- Name: {template['name']}
- Persona: {template['persona']}
- Boundaries: {template['boundaries']}
- Scenario: {template['scenario']}
- Greeting: {template['greeting']}

User preferences: {user_preferences}

Create a JSON response with:
{{
    "name": "character name",
    "persona": "detailed persona description",
    "boundaries": "character boundaries",
    "scenario": "current scenario",
    "greeting": "character greeting",
    "style": "{character_type}",
    "nsfw_level": 1-5,
    "tags": ["tag1", "tag2"]
}}

Keep it engaging but appropriate for 18+ audience."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a {character_type} character card"}
            ]
            
            result = await self.chat(messages, model="llama3.1-70b")
            
            if "error" in result:
                return result
            
            # Parse character card from response
            character_data = safe_json_parse(result["content"])
            if character_data:
                return {
                    "success": True,
                    "character": character_data,
                    "model": result["model"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to parse character card",
                    "raw_response": result["content"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": get_error_message("api_timeout", error=str(e))
            }
    
    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize conversation using Groq"""
        
        try:
            # Create conversation text
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in messages[-10:]  # Last 10 messages
            ])
            
            system_prompt = """Summarize the conversation in 1-2 sentences. 
Focus on the main topics and any important details mentioned."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize this conversation:\n\n{conversation_text}"}
            ]
            
            result = await self.chat(messages, model="llama3.1-8b", max_tokens=150)
            
            if "error" in result:
                return "Conversation summary unavailable."
            
            return result["content"]
            
        except Exception as e:
            return "Conversation summary unavailable."
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify user intent using Groq"""
        
        try:
            system_prompt = """Classify the user's intent into one of these categories:
- chat: general conversation
- roleplay: character roleplay request
- image: image generation request
- help: help or support request
- settings: settings or configuration request

Respond with JSON:
{
    "intent": "category",
    "confidence": 0.0-1.0,
    "details": "explanation"
}"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            result = await self.chat(messages, model="llama3.1-8b", max_tokens=100)
            
            if "error" in result:
                return {"intent": "chat", "confidence": 0.3, "details": "Classification failed"}
            
            # Parse intent from response
            intent_data = safe_json_parse(result["content"])
            if intent_data:
                return intent_data
            else:
                return {"intent": "chat", "confidence": 0.3, "details": "Failed to parse intent"}
                
        except Exception as e:
            return {"intent": "chat", "confidence": 0.3, "details": f"Error: {str(e)}"}
    
    @retry_with_backoff
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Groq API with retry logic"""
        
        url = f"{self.base_url}{endpoint}"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return {
            "backend": "groq",
            "models_available": list(GROQ_MODELS.keys()),
            "default_temperature": self.default_temperature,
            "max_tokens": self.max_tokens,
            "retry_attempts": self.retry_attempts
        }
