from typing import List, Dict, Any
import asyncio
from datetime import datetime
import json
from ..constants import MEMORY_CONFIG
from ..utils.helpers import truncate_text, format_timestamp

class MemoryService:
    """Simplified memory service - optimized for performance"""
    
    def __init__(self):
        # Use constants instead of hard-coded values
        self.max_facts_per_user = MEMORY_CONFIG["MAX_FACTS_PER_USER"]
        self.cleanup_days = MEMORY_CONFIG["CLEANUP_DAYS"]
        
        # In-memory storage for speed (no Qdrant dependency)
        self.facts_cache = {}
        self.user_preferences = {}
        
    async def store_fact(self, user_id: int, fact: str, fact_type: str = "message", metadata: Dict = None):
        """Store fact in memory (simplified, no vector search)"""
        try:
            # Simple in-memory storage
            if user_id not in self.facts_cache:
                self.facts_cache[user_id] = []
            
            fact_data = {
                "fact": fact,
                "type": fact_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Keep only last N facts per user (prevent memory bloat)
            self.facts_cache[user_id].append(fact_data)
            if len(self.facts_cache[user_id]) > self.max_facts_per_user:
                self.facts_cache[user_id] = self.facts_cache[user_id][-self.max_facts_per_user:]
                
        except Exception as e:
            # Silent fail - don't block main flow
            print(f"Memory store failed: {e}")
    
    async def search_facts(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword search (no embeddings)"""
        try:
            if user_id not in self.facts_cache:
                return []
            
            # Simple keyword matching
            query_lower = query.lower()
            matches = []
            
            for fact_data in reversed(self.facts_cache[user_id]):  # Recent first
                fact_lower = fact_data["fact"].lower()
                
                # Check if any word in query matches fact
                query_words = query_lower.split()
                fact_words = fact_lower.split()
                
                if any(word in fact_words for word in query_words):
                    matches.append(fact_data)
                    if len(matches) >= limit:
                        break
            
            return matches
            
        except Exception as e:
            # Return empty list on error
            return []
    
    async def store_user_preference(self, user_id: int, preference_type: str, value: str):
        """Store user preference"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}
            
            self.user_preferences[user_id][preference_type] = {
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Preference store failed: {e}")
    
    def get_user_preference(self, user_id: int, preference_type: str) -> str:
        """Get user preference"""
        try:
            return self.user_preferences.get(user_id, {}).get(preference_type, {}).get("value")
        except:
            return None
    
    async def cleanup_old_data(self, days: int = None):
        """Cleanup old data to prevent memory bloat"""
        try:
            cleanup_days = days or self.cleanup_days
            cutoff = datetime.utcnow().timestamp() - (cleanup_days * 24 * 3600)
            
            for user_id in list(self.facts_cache.keys()):
                self.facts_cache[user_id] = [
                    fact for fact in self.facts_cache[user_id]
                    if datetime.fromisoformat(fact["timestamp"]).timestamp() > cutoff
                ]
                
                # Remove user if no facts left
                if not self.facts_cache[user_id]:
                    del self.facts_cache[user_id]
                    
        except Exception as e:
            print(f"Cleanup failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            total_facts = sum(len(facts) for facts in self.facts_cache.values())
            total_users = len(self.facts_cache)
            total_preferences = sum(len(prefs) for prefs in self.user_preferences.values())
            
            return {
                "total_facts": total_facts,
                "total_users": total_users,
                "total_preferences": total_preferences,
                "memory_usage_mb": self._estimate_memory_usage()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            import sys
            
            # Rough estimation
            facts_size = sum(
                len(str(fact)) for facts in self.facts_cache.values() 
                for fact in facts
            )
            prefs_size = sum(
                len(str(pref)) for prefs in self.user_preferences.values() 
                for pref in prefs.values()
            )
            
            total_bytes = facts_size + prefs_size
            return round(total_bytes / (1024 * 1024), 2)
        except:
            return 0.0
