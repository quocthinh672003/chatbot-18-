import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from sqlmodel import select
from ..db import get_session
from ..models import User, AuditLog
from ..config import settings
from ..constants import SAFETY_CONFIG
from ..utils.helpers import is_safe_content, calculate_risk_level, validate_input

logger = logging.getLogger(__name__)

@dataclass
class SafetyResult:
    blocked: bool
    reason: Optional[str] = None
    risk_level: int = 0  # 0-5 scale

class SafetyService:
    """Content safety and moderation service"""
    
    def __init__(self):
        # Use constants instead of hard-coded values
        self.unsafe_keywords = SAFETY_CONFIG["UNSAFE_KEYWORDS"]
        self.age_verification_required = SAFETY_CONFIG["AGE_VERIFICATION_REQUIRED"]
        self.min_age = SAFETY_CONFIG["MIN_AGE"]
        self.max_risk_level = SAFETY_CONFIG["MAX_RISK_LEVEL"]
        
        # User age verification cache
        self.verified_users = {}
    
    def check_message_safety(self, message: str, user_id: int = None) -> Dict[str, Any]:
        """Check if message is safe to process"""
        
        # Validate input first
        is_valid, error_msg = validate_input(message)
        if not is_valid:
            return {
                "safe": False,
                "reason": error_msg,
                "risk_level": 3,
                "blocked": True
            }
        
        # Check for unsafe content
        if not is_safe_content(message, self.unsafe_keywords):
            return {
                "safe": False,
                "reason": "Contains unsafe keywords",
                "risk_level": 3,
                "blocked": True
            }
        
        # Calculate risk level
        risk_level = calculate_risk_level(message, self.unsafe_keywords)
        
        # Check if risk level exceeds threshold
        if risk_level > self.max_risk_level:
            return {
                "safe": False,
                "reason": f"Risk level too high ({risk_level})",
                "risk_level": risk_level,
                "blocked": True
            }
        
        return {
            "safe": True,
            "reason": "Message passed safety checks",
            "risk_level": risk_level,
            "blocked": False
        }
    
    def check_age_verification(self, user_id: int, user_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if user meets age requirements"""
        
        # If age verification not required, allow
        if not self.age_verification_required:
            return {
                "verified": True,
                "reason": "Age verification not required"
            }
        
        # Check cache first
        if user_id in self.verified_users:
            return {
                "verified": True,
                "reason": "Previously verified"
            }
        
        # Check user info if provided
        if user_info:
            # Check if user has verified age in Telegram
            if user_info.get("is_premium") or user_info.get("verified"):
                self.verified_users[user_id] = datetime.utcnow()
                return {
                    "verified": True,
                    "reason": "Premium/verified user"
                }
        
        # For now, assume users are adults (in production, implement proper age verification)
        # This is a simplified implementation
        self.verified_users[user_id] = datetime.utcnow()
        return {
            "verified": True,
            "reason": "Age verification passed",
            "warning": "Please ensure you are 18+ to use this bot"
        }
    
    def check_image_safety(self, prompt: str) -> Dict[str, Any]:
        """Check if image generation prompt is safe"""
        
        # Check for unsafe content in prompt
        if not is_safe_content(prompt, self.unsafe_keywords):
            return {
                "safe": False,
                "reason": "Image prompt contains unsafe content",
                "risk_level": 3,
                "blocked": True
            }
        
        # Calculate risk level
        risk_level = calculate_risk_level(prompt, self.unsafe_keywords)
        
        # Check if risk level exceeds threshold
        if risk_level > self.max_risk_level:
            return {
                "safe": False,
                "reason": f"Image prompt risk level too high ({risk_level})",
                "risk_level": risk_level,
                "blocked": True
            }
        
        return {
            "safe": True,
            "reason": "Image prompt passed safety checks",
            "risk_level": risk_level,
            "blocked": False
        }
    
    def audit_log(self, user_id: int, action: str, content: str, result: Dict[str, Any]):
        """Log safety check results for audit"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "result": result
        }
        
        # In production, store this in database
        print(f"SAFETY_AUDIT: {log_entry}")
    
    def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety service statistics"""
        
        return {
            "verified_users_count": len(self.verified_users),
            "unsafe_keywords_count": len(self.unsafe_keywords),
            "age_verification_required": self.age_verification_required,
            "min_age": self.min_age,
            "max_risk_level": self.max_risk_level
        }
    
    def cleanup_old_verifications(self, days: int = 30):
        """Clean up old age verifications"""
        
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 3600)
        
        to_remove = []
        for user_id, timestamp in self.verified_users.items():
            if timestamp.timestamp() < cutoff:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.verified_users[user_id]
        
        print(f"Cleaned up {len(to_remove)} old age verifications")
