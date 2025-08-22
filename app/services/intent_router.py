import re
from typing import Dict, Any, List
from dataclasses import dataclass
from ..constants import INTENT_PATTERNS, INTENT_KEYWORDS
from ..utils.helpers import classify_intent_simple

@dataclass
class IntentResult:
    intent: str
    confidence: float
    details: str
    metadata: Dict[str, Any] = None

class IntentRouter:
    """Rule-based + LLM intent classification for message routing"""
    
    def __init__(self):
        # Use constants instead of hard-coded patterns
        self.patterns = INTENT_PATTERNS
        self.keywords = INTENT_KEYWORDS
    
    async def classify_intent(self, message: str, llm_classifier=None) -> IntentResult:
        """Classify user intent using rules first, then LLM if needed"""
        
        # Use helper function for simple classification
        intent, confidence = classify_intent_simple(message)
        
        # If confidence is high enough, return immediately
        if confidence >= 0.8:
            return IntentResult(
                intent=intent,
                confidence=confidence,
                details=f"Pattern match: {intent}",
                metadata={"method": "pattern"}
            )
        
        # If still low confidence and LLM available, use LLM
        if confidence < 0.6 and llm_classifier:
            try:
                llm_result = await llm_classifier.classify_intent(message)
                if llm_result["confidence"] > confidence:
                    return IntentResult(
                        intent=llm_result["intent"],
                        confidence=llm_result["confidence"],
                        details=llm_result["details"],
                        metadata={"method": "llm"}
                    )
            except Exception as e:
                # Fallback to simple result
                pass
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            details=f"Keyword match: {intent}",
            metadata={"method": "keyword"}
        )
    
    async def route_message(self, message: str, llm_classifier=None) -> Dict[str, Any]:
        """Route message to appropriate handler based on intent"""
        
        intent_result = await self.classify_intent(message, llm_classifier)
        
        routing = {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "handler": self._get_handler(intent_result.intent),
            "details": intent_result.details,
            "metadata": intent_result.metadata
        }
        
        return routing
    
    def _get_handler(self, intent: str) -> str:
        """Get handler name for intent"""
        handlers = {
            "chat": "chat_handler",
            "roleplay": "roleplay_handler", 
            "image": "image_handler",
            "help": "help_handler",
            "settings": "settings_handler"
        }
        return handlers.get(intent, "chat_handler")
    
    def is_image_request(self, message: str) -> bool:
        """Quick check if message is image request"""
        intent, confidence = classify_intent_simple(message)
        return intent == "image" and confidence > 0.7
    
    def is_roleplay_request(self, message: str) -> bool:
        """Quick check if message is roleplay request"""
        intent, confidence = classify_intent_simple(message)
        return intent == "roleplay" and confidence > 0.7
