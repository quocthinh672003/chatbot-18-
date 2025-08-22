"""
Utility functions and helpers for the chatbot
Reusable functions to avoid code duplication
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..constants import INTENT_PATTERNS, INTENT_KEYWORDS, RESPONSE_TEMPLATES, ERROR_MESSAGES


def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON from text, handling common formatting issues
    """
    try:
        # Find JSON-like content in text
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1:
            return None
            
        json_str = text[start:end + 1]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None


def extract_meta_from_text(text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Extract meta information from LLM response text
    Returns (clean_text, meta_dict)
    """
    meta = {}
    clean_text = text
    
    # Look for META: {...} pattern
    meta_match = re.search(r'META:\s*({.*?})', text, re.DOTALL)
    if meta_match:
        try:
            meta = json.loads(meta_match.group(1))
            clean_text = text.replace(meta_match.group(0), '').strip()
        except json.JSONDecodeError:
            pass
    
    return clean_text, meta


def classify_intent_simple(message: str) -> Tuple[str, float]:
    """
    Simple intent classification using patterns and keywords
    Returns (intent, confidence)
    """
    message_lower = message.lower()
    
    # Check patterns first (highest confidence)
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return intent, 0.9
    
    # Check keywords (medium confidence)
    intent_scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in message_lower:
                score += 1
                # Bonus for exact word matches
                if keyword in message_lower.split():
                    score += 0.5
        
        if score > 0:
            intent_scores[intent] = score
    
    if intent_scores:
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        max_possible = max(len(keywords) for keywords in INTENT_KEYWORDS.values())
        confidence = min(best_score / max_possible, 1.0)
        return best_intent, confidence
    
    return "chat", 0.3


def create_simple_summary(messages: List[Dict[str, str]]) -> str:
    """
    Create a simple conversation summary without LLM
    """
    if not messages:
        return "No conversation history."
    
    topics = []
    for msg in messages:
        content = msg["content"].lower()
        
        # Extract topics using simple rules
        if any(word in content for word in ["hello", "hi", "chào"]):
            topics.append("greeting")
        elif any(word in content for word in ["bye", "goodbye", "tạm biệt"]):
            topics.append("farewell")
        elif any(word in content for word in ["image", "ảnh", "picture"]):
            topics.append("image_request")
        elif any(word in content for word in ["roleplay", "character", "nhân vật"]):
            topics.append("roleplay_request")
        elif any(word in content for word in ["help", "giúp"]):
            topics.append("help_request")
    
    if topics:
        unique_topics = list(set(topics))
        return f"Topics: {', '.join(unique_topics)}"
    
    return "General conversation"


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to specified length with ellipsis
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_response(template_key: str, **kwargs) -> str:
    """
    Format response using templates with safe substitution
    """
    template = RESPONSE_TEMPLATES.get(template_key, template_key)
    try:
        return template.format(**kwargs)
    except KeyError:
        # Fallback if template variables are missing
        return template


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary values
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def validate_input(text: str, max_length: int = 4096) -> Tuple[bool, str]:
    """
    Validate user input
    Returns (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Message cannot be empty"
    
    if len(text) > max_length:
        return False, f"Message too long (max {max_length} characters)"
    
    # Check for excessive whitespace
    if len(text.strip()) < 2:
        return False, "Message too short"
    
    return True, ""


def extract_image_prompt(message: str) -> str:
    """
    Extract image prompt from user message
    """
    # Remove common image request phrases
    prompt = message.lower()
    remove_phrases = [
        "tạo ảnh", "generate image", "vẽ ảnh", "draw picture",
        "ảnh của", "picture of", "photo of", "show me", "cho tôi xem"
    ]
    
    for phrase in remove_phrases:
        prompt = prompt.replace(phrase, "")
    
    prompt = prompt.strip()
    
    # Default prompt if empty
    if not prompt:
        prompt = "beautiful woman, elegant, high quality"
    
    return prompt


def is_safe_content(text: str, unsafe_keywords: List[str]) -> bool:
    """
    Check if content is safe using keyword matching
    """
    text_lower = text.lower()
    return not any(keyword in text_lower for keyword in unsafe_keywords)


def calculate_risk_level(text: str, unsafe_keywords: List[str]) -> int:
    """
    Calculate risk level based on content analysis
    Returns 0-3 (0=safe, 3=high risk)
    """
    text_lower = text.lower()
    risk_score = 0
    
    # Count unsafe keywords
    for keyword in unsafe_keywords:
        if keyword in text_lower:
            risk_score += 1
    
    # Additional risk factors
    if len(re.findall(r'\b(fuck|shit|bitch)\b', text_lower)) > 2:
        risk_score += 1
    
    if len(re.findall(r'[!]{3,}', text)) > 0:
        risk_score += 1
    
    return min(risk_score, 3)


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for display
    """
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "just now"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, dict2 overwrites dict1
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def get_error_message(error_type: str, **kwargs) -> str:
    """
    Get formatted error message
    """
    template = ERROR_MESSAGES.get(error_type, "An error occurred")
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def validate_api_response(response_data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, str]:
    """
    Validate API response structure
    """
    for field in required_fields:
        if field not in response_data:
            return False, f"Missing required field: {field}"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def retry_with_backoff(func=None, *, max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying functions with exponential backoff.
    Supports both sync and async functions.
    """
    import inspect

    def _decorator(f):
        if inspect.iscoroutinefunction(f):
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return await f(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            delay = base_delay * (2 ** attempt)
                            import asyncio
                            await asyncio.sleep(delay)
                raise last_exception
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return f(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            delay = base_delay * (2 ** attempt)
                            import time
                            time.sleep(delay)
                raise last_exception
            return sync_wrapper

    if func is None:
        return _decorator
    return _decorator(func)
