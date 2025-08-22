import httpx
import json
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseLLMBackend
from ..config import settings

class OpenRouterBackend(BaseLLMBackend):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://lucid-dreams-bot.com",
            "X-Title": "Lucid Dreams Bot"
        }
        self.default_model = "anthropic/claude-3.5-sonnet"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate chat response using OpenRouter"""
        
        # Build system prompt with character info
        character_card = kwargs.get("character_card")
        if character_card:
            system_prompt = f"""You are {character_card.name}, speaking in first person.

PERSONA: {character_card.persona}
BOUNDARIES: {character_card.boundaries}
SCENARIO: {character_card.scenario}

Instructions:
- Stay in character as {character_card.name}
- Be immersive and engaging
- If user requests an image, append: META:{{"make_image": true, "image_prompt": "description"}}
- Keep responses concise but engaging
- Respect boundaries and consent"""
            
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.default_model,
                    "messages": messages,
                    "temperature": 0.9,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            
            return {
                "content": content,
                "usage": data["usage"],
                "model": self.default_model,
                "success": True
            }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def create_character_card(self, character_type: str) -> Dict[str, Any]:
        """Create character card using OpenRouter"""
        
        system = f"""You are an expert character creator for adult roleplay scenarios. 
Create detailed character cards in strict JSON format. Style: realistic, NSFW level: 3/5.
Focus on creating immersive, engaging characters with clear boundaries."""
        
        user = f"""Create a character for adult roleplay. Type: {character_type}

Return JSON matching this exact schema:
{{
  "name": "string (character name)",
  "persona": "detailed personality, traits, speaking style, 100-150 words",
  "boundaries": "consent rules, hard limits, safety guidelines",
  "scenario": "how the story/scene starts, 2-3 sentences",
  "greeting": "first message to user, warm and immersive",
  "style": "realistic",
  "image_prompt": "detailed visual description for image generation",
  "tags": ["keyword1", "keyword2", "keyword3"],
  "nsfw_level": 3
}}"""

        response = await self.chat(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        
        # Extract JSON from response
        content = response["content"]
        start = content.find("{"); end = content.rfind("}")
        if start == -1 or end == -1:
            return {"error": "Model did not return valid JSON", "success": False}
        
        card_data = json.loads(content[start : end + 1])
        return {"character": card_data, "success": True}
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify message intent using OpenRouter"""
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
            
            response = await self.chat(messages)
            
            if "error" in response:
                return {"intent": "chat", "confidence": 0.5, "details": "Fallback classification"}
            
            # Parse intent data
            content = response["content"]
            start = content.find("{"); end = content.rfind("}")
            if start == -1 or end == -1:
                return {"intent": "chat", "confidence": 0.5, "details": "Failed to parse intent"}
            
            intent_data = json.loads(content[start : end + 1])
            return intent_data
            
        except Exception as e:
            return {"intent": "chat", "confidence": 0.5, "details": "Error in classification"}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize conversation using OpenRouter"""
        
        system = "Summarize the key points of this conversation in 2-3 sentences for context retention."
        
        # Combine recent messages
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[-10:]])
        
        response = await self.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": f"Summarize this conversation:\n{conversation_text}"}
        ])
        
        return response["text"]
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models on OpenRouter"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
