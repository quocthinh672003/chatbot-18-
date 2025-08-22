import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlmodel import select
from ..db import get_session
from ..models import Message, SessionState
from ..services.memory import MemoryService
from ..constants import MEMORY_CONFIG
from ..utils.helpers import create_simple_summary, truncate_text

@dataclass
class MemoryContext:
    """Simplified context information"""
    summary: str
    recent_messages: List[Dict[str, str]]
    character_context: Optional[Dict[str, Any]] = None

class MemoryManager:
    """Simplified memory management - optimized for performance"""
    
    def __init__(self):
        self.memory_service = MemoryService()
        
        # Use constants instead of hard-coded values
        self.max_recent_messages = MEMORY_CONFIG["MAX_RECENT_MESSAGES"]
        self.max_summary_length = MEMORY_CONFIG["MAX_SUMMARY_LENGTH"]
        self.summary_threshold = MEMORY_CONFIG["SUMMARY_THRESHOLD"]
        
    async def get_context(self, user_id: int, session_id: int, current_message: str = None) -> MemoryContext:
        """Get simplified context for user session"""
        
        # Get recent messages only
        recent_messages = await self._get_recent_messages(session_id)
        
        # Get simple summary
        summary = await self._get_or_create_summary(session_id, recent_messages)
        
        # Get character context
        character_context = await self._get_character_context(session_id)
        
        return MemoryContext(
            summary=summary,
            recent_messages=recent_messages,
            character_context=character_context
        )
    
    async def _get_recent_messages(self, session_id: int) -> List[Dict[str, str]]:
        """Get recent messages for context (simplified)"""
        try:
            with get_session() as s:
                messages = s.exec(
                    select(Message)
                    .where(Message.session_id == session_id)
                    .order_by(Message.created_at.desc())
                    .limit(self.max_recent_messages)
                ).all()
                
                # Convert to format expected by LLM
                formatted_messages = []
                for msg in reversed(messages):  # Oldest first
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.text
                    })
                
                return formatted_messages
        except Exception as e:
            # Return empty list on error
            return []
    
    async def _get_or_create_summary(self, session_id: int, recent_messages: List[Dict[str, str]]) -> str:
        """Get existing summary or create simple one"""
        
        # Check if we need to create/update summary
        if len(recent_messages) < self.summary_threshold:
            # Use existing summary from session state
            try:
                with get_session() as s:
                    session = s.exec(
                        select(SessionState).where(SessionState.id == session_id)
                    ).first()
                    
                    if session and session.context_summary:
                        return session.context_summary
            except:
                pass
        
        # Create simple summary using helper function
        if recent_messages:
            summary = create_simple_summary(recent_messages)
            
            # Truncate summary if too long
            summary = truncate_text(summary, self.max_summary_length)
            
            # Update session state
            try:
                with get_session() as s:
                    session = s.exec(
                        select(SessionState).where(SessionState.id == session_id)
                    ).first()
                    
                    if session:
                        session.context_summary = summary
                        session.updated_at = datetime.utcnow()
                        s.commit()
            except:
                pass
            
            return summary
        
        return "No conversation history."
    
    async def _get_character_context(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get current character context"""
        try:
            with get_session() as s:
                session = s.exec(
                    select(SessionState).where(SessionState.id == session_id)
                ).first()
                
                if session and session.character_id:
                    return {
                        "character_id": session.character_id,
                        "character_name": session.character_name,
                        "style": session.style
                    }
        except:
            pass
        
        return None
    
    async def store_message(self, session_id: int, role: str, content: str, 
                          tokens: int = None, meta_data: Dict = None):
        """Store message in database only (no vector store)"""
        
        try:
            # Store in database
            with get_session() as s:
                # Convert meta_data to JSON string for SQLite compatibility
                import json
                meta_data_str = json.dumps(meta_data or {})
                
                message = Message(
                    session_id=session_id,
                    role=role,
                    text=content,
                    tokens=tokens,
                    meta_data=meta_data_str
                )
                s.add(message)
                s.commit()
        except Exception as e:
            # Silent fail - don't block main flow
            print(f"Message store failed: {e}")
    
    async def update_character_context(self, session_id: int, character_id: int, 
                                     character_name: str, style: str = "realistic"):
        """Update character context in session"""
        try:
            with get_session() as s:
                session = s.exec(
                    select(SessionState).where(SessionState.id == session_id)
                ).first()
                
                if session:
                    session.character_id = character_id
                    session.character_name = character_name
                    session.style = style
                    session.updated_at = datetime.utcnow()
                    s.commit()
        except Exception as e:
            print(f"Character context update failed: {e}")
    
    def build_context_prompt(self, context: MemoryContext, current_message: str) -> str:
        """Build simplified context prompt for LLM"""
        
        prompt_parts = []
        
        # Add summary
        if context.summary:
            prompt_parts.append(f"Summary: {context.summary}")
        
        # Add character context
        if context.character_context:
            char = context.character_context
            prompt_parts.append(f"Character: {char['character_name']} ({char['style']})")
        
        # Add recent messages (only last 3)
        if context.recent_messages:
            recent_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context.recent_messages[-3:]  # Only last 3 messages
            ])
            prompt_parts.append(f"Recent:\n{recent_text}")
        
        # Add current message
        prompt_parts.append(f"User: {current_message}")
        
        return "\n\n".join(prompt_parts)
    
    async def cleanup_old_messages(self, days: int = None):
        """Clean up old messages to save storage"""
        try:
            cleanup_days = days or MEMORY_CONFIG["CLEANUP_DAYS"]
            cutoff_date = datetime.utcnow() - timedelta(days=cleanup_days)
            
            with get_session() as s:
                # Delete old messages
                old_messages = s.exec(
                    select(Message).where(Message.created_at < cutoff_date)
                ).all()
                
                for msg in old_messages:
                    s.delete(msg)
                
                s.commit()
                
                print(f"Cleaned up {len(old_messages)} old messages")
        except Exception as e:
            print(f"Cleanup failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        try:
            # Get memory service stats
            memory_stats = self.memory_service.get_memory_stats()
            
            return {
                "memory_service": memory_stats,
                "config": {
                    "max_recent_messages": self.max_recent_messages,
                    "max_summary_length": self.max_summary_length,
                    "summary_threshold": self.summary_threshold
                }
            }
        except Exception as e:
            return {"error": str(e)}
