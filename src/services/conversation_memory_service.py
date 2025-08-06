"""
Conversation Memory Service for Cafe Pentagon Chatbot
Handles conversation history loading, updating, and context management for LangGraph workflow
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger
from src.utils.cache import get_cache_manager

logger = get_logger("conversation_memory")


class ConversationMemoryService:
    """
    Service for managing conversation memory and context
    Handles loading, updating, and caching conversation history
    """
    
    def __init__(self):
        """Initialize conversation memory service"""
        self.conversation_tracking = get_conversation_tracking_service()
        self.cache = get_cache_manager()
        logger.info("conversation_memory_service_initialized")
    
    def load_conversation_history(self, conversation_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Load conversation history from database and cache
        
        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            limit: Maximum number of messages to load
            
        Returns:
            List of conversation messages in LangGraph format
        """
        try:
            # Try to get from cache first
            cache_key = f"conversation_history:{conversation_id}"
            cached_history = self.cache.get(cache_key)
            
            if cached_history:
                logger.info("conversation_history_loaded_from_cache", 
                           conversation_id=conversation_id,
                           message_count=len(cached_history))
                return cached_history[:limit]
            
            # Load from database
            db_messages = self.conversation_tracking.get_conversation_messages(conversation_id, limit=limit)
            
            if not db_messages:
                logger.info("no_conversation_history_found", conversation_id=conversation_id)
                return []
            
            # Convert to LangGraph format
            conversation_history = []
            for msg in db_messages:
                # Map sender_type to role
                role = "user" if msg.get("sender_type") == "user" else "assistant"
                
                # Extract metadata
                metadata = msg.get("metadata", {})
                
                conversation_history.append({
                    "role": role,
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp"),
                    "intent": metadata.get("intent", "unknown"),
                    "language": metadata.get("user_language", "en"),
                    "conversation_state": metadata.get("conversation_state", "active"),
                    "confidence": msg.get("confidence_score"),
                    "message_id": msg.get("id")
                })
            
            # Cache the history
            self.cache.set(cache_key, conversation_history, ttl=3600)  # 1 hour cache
            
            logger.info("conversation_history_loaded_from_database", 
                       conversation_id=conversation_id,
                       message_count=len(conversation_history))
            
            return conversation_history
            
        except Exception as e:
            logger.error("conversation_history_loading_failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            return []
    
    def add_message_to_history(self, conversation_id: str, role: str, content: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to conversation history and update cache
        
        Args:
            conversation_id: Conversation identifier
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional message metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message entry
            message_entry = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "intent": metadata.get("intent", "unknown") if metadata else "unknown",
                "language": metadata.get("language", "en") if metadata else "en",
                "conversation_state": metadata.get("conversation_state", "active") if metadata else "active",
                "confidence": metadata.get("confidence", 0.0) if metadata else 0.0
            }
            
            # Update cache
            cache_key = f"conversation_history:{conversation_id}"
            cached_history = self.cache.get(cache_key) or []
            
            # Add new message
            cached_history.append(message_entry)
            
            # Keep only last 20 messages in cache
            if len(cached_history) > 20:
                cached_history = cached_history[-20:]
            
            # Update cache
            self.cache.set(cache_key, cached_history, ttl=3600)
            
            logger.info("message_added_to_conversation_history", 
                       conversation_id=conversation_id,
                       role=role,
                       content_length=len(content))
            
            return True
            
        except Exception as e:
            logger.error("failed_to_add_message_to_history", 
                        conversation_id=conversation_id,
                        error=str(e))
            return False
    
    def update_conversation_context(self, conversation_id: str, context_updates: Dict[str, Any]) -> bool:
        """
        Update conversation context metadata
        
        Args:
            conversation_id: Conversation identifier
            context_updates: Context updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update conversation in database
            success = self.conversation_tracking.update_conversation(
                conversation_id, 
                updates=context_updates
            )
            
            if success:
                logger.info("conversation_context_updated", 
                           conversation_id=conversation_id,
                           updates=context_updates)
            
            return success
            
        except Exception as e:
            logger.error("failed_to_update_conversation_context", 
                        conversation_id=conversation_id,
                        error=str(e))
            return False
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the conversation for context
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation summary or None
        """
        try:
            history = self.load_conversation_history(conversation_id, "", limit=5)
            
            if not history:
                return None
            
            # Create summary
            summary = {
                "total_messages": len(history),
                "last_user_message": None,
                "last_bot_message": None,
                "primary_language": "en",
                "common_intents": [],
                "conversation_tone": "neutral"
            }
            
            # Find last messages
            for msg in reversed(history):
                if msg["role"] == "user" and not summary["last_user_message"]:
                    summary["last_user_message"] = msg["content"]
                elif msg["role"] == "assistant" and not summary["last_bot_message"]:
                    summary["last_bot_message"] = msg["content"]
            
            # Analyze language and intents
            languages = [msg.get("language", "en") for msg in history]
            intents = [msg.get("intent", "unknown") for msg in history]
            
            if languages:
                summary["primary_language"] = max(set(languages), key=languages.count)
            
            if intents:
                intent_counts = {}
                for intent in intents:
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
                summary["common_intents"] = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return summary
            
        except Exception as e:
            logger.error("failed_to_get_conversation_summary", 
                        conversation_id=conversation_id,
                        error=str(e))
            return None
    
    def clear_conversation_history(self, conversation_id: str) -> bool:
        """
        Clear conversation history from cache
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = f"conversation_history:{conversation_id}"
            self.cache.delete(cache_key)
            
            logger.info("conversation_history_cleared_from_cache", conversation_id=conversation_id)
            return True
            
        except Exception as e:
            logger.error("failed_to_clear_conversation_history", 
                        conversation_id=conversation_id,
                        error=str(e))
            return False


def get_conversation_memory_service() -> ConversationMemoryService:
    """Get conversation memory service instance"""
    return ConversationMemoryService() 