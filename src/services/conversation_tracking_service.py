"""
Conversation Tracking Service for Admin Panel Integration
Handles saving conversations and messages to Supabase for real-time monitoring
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from supabase import create_client, Client
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger("conversation_tracking")


class ConversationTrackingService:
    """
    Service for tracking conversations and messages in Supabase
    """
    
    def __init__(self):
        """Initialize conversation tracking service"""
        self.settings = get_settings()
        
        # Initialize Supabase client with service role key for admin operations
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_role_key
        )
        
        # Simple in-memory cache for conversation status
        # Cache structure: {conversation_id: {"status": str, "human_handling": bool, "rag_enabled": bool, "timestamp": datetime}}
        self._conversation_status_cache = {}
        
        logger.info("conversation_tracking_service_initialized")

    def _get_cached_conversation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation status from cache
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Cached conversation status or None if not cached
        """
        if conversation_id in self._conversation_status_cache:
            cached_data = self._conversation_status_cache[conversation_id]
            logger.info("conversation_status_cache_hit", conversation_id=conversation_id)
            return cached_data
        return None

    def _cache_conversation_status(self, conversation_id: str, conversation_data: Dict[str, Any]) -> None:
        """
        Cache conversation status
        
        Args:
            conversation_id: Conversation identifier
            conversation_data: Conversation data from database
        """
        cache_data = {
            "status": conversation_data.get("status", "active"),
            "human_handling": conversation_data.get("human_handling", False),
            "rag_enabled": conversation_data.get("rag_enabled", True),
            "priority": conversation_data.get("priority", 1),
            "timestamp": datetime.now(timezone.utc)
        }
        
        self._conversation_status_cache[conversation_id] = cache_data
        logger.info("conversation_status_cached", conversation_id=conversation_id, status=cache_data["status"])

    def _invalidate_conversation_cache(self, conversation_id: str) -> None:
        """
        Invalidate cache for a specific conversation
        
        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self._conversation_status_cache:
            del self._conversation_status_cache[conversation_id]
            logger.info("conversation_status_cache_invalidated", conversation_id=conversation_id)

    def get_conversation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation status with caching
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation status with human_handling, rag_enabled, etc.
        """
        try:
            # Try cache first
            cached_status = self._get_cached_conversation_status(conversation_id)
            if cached_status:
                return cached_status
            
            # Cache miss - get from database
            conversation = self.get_conversation_by_id(conversation_id)
            if conversation:
                # Cache the result
                self._cache_conversation_status(conversation_id, conversation)
                return self._get_cached_conversation_status(conversation_id)
            
            return None
            
        except Exception as e:
            logger.error("get_conversation_status_exception", conversation_id=conversation_id, error=str(e))
            return None

    def save_conversation(self, user_id: str, platform: str = 'facebook') -> Optional[Dict[str, Any]]:
        """Save a new conversation to Supabase"""
        try:
            conversation_data = {
                "user_id": user_id,
                "platform": platform,
                "status": "active",
                "priority": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_message_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table("conversations").insert(conversation_data).execute()
            
            if response.data and len(response.data) > 0:
                conversation = response.data[0]
                logger.info("conversation_saved", user_id=user_id, conversation_id=conversation.get('id'))
                return conversation
            else:
                logger.error("conversation_save_failed", user_id=user_id)
                return None
                
        except Exception as e:
            logger.error("conversation_save_exception", user_id=user_id, error=str(e))
            return None

    def save_message(self, conversation_id: str, content: str, sender_type: str = 'user', 
                          confidence_score: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Save a message to Supabase"""
        try:
            # Check if message requires human assistance - ONLY from metadata, NO pattern matching
            requires_human = False
            if metadata:
                # Only check if requires_human is explicitly set in metadata
                requires_human = metadata.get("requires_human", False)
            # No pattern matching - let the LLM decide through the normal workflow
            
            message_data = {
                "conversation_id": conversation_id,
                "sender_type": sender_type,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence_score": confidence_score,
                "requires_human": requires_human,
                "human_replied": False,
                "metadata": metadata or {}
            }
            
            # Log message saving
            logger.info("message_saving", 
                       conversation_id=conversation_id,
                       sender_type=sender_type,
                       requires_human=requires_human,
                       content_preview=content[:50] if content else "")
            
            response = self.supabase.table("messages").insert(message_data).execute()
            
            if response.data and len(response.data) > 0:
                message = response.data[0]
                logger.info("message_saved", 
                           conversation_id=conversation_id, 
                           sender_type=sender_type,
                           requires_human=requires_human)
                
                # Let the LLM workflow decide on escalation - no automatic escalation here
                
                return message
            else:
                logger.error("message_save_failed", conversation_id=conversation_id)
                return None
                
        except Exception as e:
            logger.error("message_save_exception", conversation_id=conversation_id, error=str(e))
            return None



    def _update_conversation_for_human_assistance(self, conversation_id: str) -> bool:
        """
        Update conversation to mark for human handling
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "human_handling": True,
                "rag_enabled": False,
                "status": "escalated",
                "priority": 2,  # Increase priority
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_message_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table("conversations").update(update_data).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info("conversation_updated_for_human_assistance", conversation_id=conversation_id)
                return True
            else:
                logger.error("conversation_update_for_human_assistance_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("conversation_update_for_human_assistance_exception", conversation_id=conversation_id, error=str(e))
            return False

    def update_conversation(self, conversation_id: str, status: str = 'active', 
                                 updates: Optional[Dict[str, Any]] = None) -> bool:
        """Update conversation status and metadata"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_message_at": datetime.now(timezone.utc).isoformat()
            }
            
            if updates:
                update_data.update(updates)
            
            response = self.supabase.table("conversations").update(update_data).eq("id", conversation_id).execute()
            
            if response.data:
                # Automatically invalidate cache when admin updates conversation
                self._invalidate_conversation_cache(conversation_id)
                logger.info("conversation_updated_and_cache_invalidated", conversation_id=conversation_id, status=status)
                return True
            else:
                logger.error("conversation_update_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("conversation_update_exception", conversation_id=conversation_id, error=str(e))
            return False

    def get_or_create_conversation(self, user_id: str, platform: str = 'facebook', conversation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get existing active conversation or create new one"""
        try:
            # If conversation_id is provided, try to get that specific conversation first
            if conversation_id:
                logger.info("attempting_to_find_specific_conversation", user_id=user_id, conversation_id=conversation_id)
                try:
                    # Use limit(1) instead of single() to avoid 406 error when no conversation found
                    response = self.supabase.table("conversations").select("*").eq("id", conversation_id).limit(1).execute()
                    if response.data and len(response.data) > 0:
                        conversation = response.data[0]
                        logger.info("specific_conversation_found", user_id=user_id, conversation_id=conversation.get('id'))
                        return conversation
                    else:
                        logger.info("specific_conversation_not_found", user_id=user_id, conversation_id=conversation_id)
                        # Create the conversation with the specific ID
                        conversation_data = {
                            "id": conversation_id,
                            "user_id": user_id,
                            "platform": platform,
                            "status": "active",
                            "priority": 1,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "last_message_at": datetime.now(timezone.utc).isoformat()
                        }
                        response = self.supabase.table("conversations").insert(conversation_data).execute()
                        if response.data and len(response.data) > 0:
                            conversation = response.data[0]
                            logger.info("conversation_created_with_specific_id", user_id=user_id, conversation_id=conversation.get('id'))
                            return conversation
                except Exception as e:
                    logger.error("error_finding_specific_conversation", user_id=user_id, conversation_id=conversation_id, error=str(e))
            
            # Try to find existing active or escalated conversation
            response = self.supabase.table("conversations").select("*").eq("user_id", user_id).in_("status", ["active", "escalated"]).order("created_at", desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                conversation = response.data[0]
                logger.info("existing_conversation_found", user_id=user_id, conversation_id=conversation.get('id'))
                return conversation
            
            # Create new conversation if none exists
            logger.info("creating_new_conversation", user_id=user_id)
            return self.save_conversation(user_id, platform)
            
        except Exception as e:
            logger.error("get_or_create_conversation_exception", user_id=user_id, error=str(e))
            # Fallback: create new conversation
            return self.save_conversation(user_id, platform)

    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        try:
            response = self.supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("timestamp", desc=False).limit(limit).execute()
            
            if response.data:
                logger.info("messages_retrieved", conversation_id=conversation_id, count=len(response.data))
                return response.data
            else:
                logger.info("no_messages_found", conversation_id=conversation_id)
                return []
                
        except Exception as e:
            logger.error("messages_retrieval_exception", conversation_id=conversation_id, error=str(e))
            return []

    def get_active_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all active conversations for admin panel"""
        try:
            response = self.supabase.table("conversations").select("*").eq("status", "active").order("last_message_at", desc=True).limit(limit).execute()
            
            if response.data:
                logger.info("active_conversations_retrieved", count=len(response.data))
                return response.data
            else:
                logger.info("no_active_conversations_found")
                return []
                
        except Exception as e:
            logger.error("active_conversations_retrieval_exception", error=str(e))
            return []

    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            # Use limit(1) instead of single() to avoid 406 error when no conversation found
            response = self.supabase.table("conversations").select("*").eq("id", conversation_id).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                conversation = response.data[0]
                # Cache the conversation status for future use
                self._cache_conversation_status(conversation_id, conversation)
                logger.info("conversation_retrieved_and_cached", conversation_id=conversation_id)
                return conversation
            else:
                logger.info("conversation_not_found", conversation_id=conversation_id)
                return None
                
        except Exception as e:
            logger.error("conversation_retrieval_exception", conversation_id=conversation_id, error=str(e))
            return None

    def is_conversation_escalated(self, conversation_id: str) -> bool:
        """
        Check if conversation is escalated and should be blocked from AI processing
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if conversation is escalated and AI should not respond
        """
        try:
            status = self.get_conversation_status(conversation_id)
            if status:
                # Check if conversation is escalated and RAG is disabled
                is_escalated = (
                    status.get("status") == "escalated" or 
                    (status.get("human_handling", False) and not status.get("rag_enabled", True))
                )
                
                logger.info("conversation_escalation_check", 
                           conversation_id=conversation_id,
                           is_escalated=is_escalated,
                           status=status.get("status"),
                           human_handling=status.get("human_handling"),
                           rag_enabled=status.get("rag_enabled"))
                
                return is_escalated
            
            return False
            
        except Exception as e:
            logger.error("conversation_escalation_check_exception", conversation_id=conversation_id, error=str(e))
            return False

    def close_conversation(self, conversation_id: str) -> bool:
        """Close a conversation"""
        try:
            response = self.supabase.table("conversations").update({
                "status": "closed",
                "updated_at": datetime.now().isoformat()
            }).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info("conversation_closed", conversation_id=conversation_id)
                return True
            else:
                logger.error("conversation_close_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("conversation_close_exception", conversation_id=conversation_id, error=str(e))
            return False

    def mark_message_requires_human(self, message_id: str) -> bool:
        """Mark a message as requiring human intervention"""
        try:
            response = self.supabase.table("messages").update({
                "requires_human": True,
                "updated_at": datetime.now().isoformat()
            }).eq("id", message_id).execute()
            
            if response.data:
                logger.info("message_marked_requires_human", message_id=message_id)
                return True
            else:
                logger.error("message_mark_human_failed", message_id=message_id)
                return False
                
        except Exception as e:
            logger.error("message_mark_human_exception", message_id=message_id, error=str(e))
            return False

    def mark_message_human_replied(self, message_id: str) -> bool:
        """Mark a message as having received human reply"""
        try:
            response = self.supabase.table("messages").update({
                "human_replied": True,
                "updated_at": datetime.now().isoformat()
            }).eq("id", message_id).execute()
            
            if response.data:
                logger.info("message_marked_human_replied", message_id=message_id)
                return True
            else:
                logger.error("message_mark_human_replied_failed", message_id=message_id)
                return False
                
        except Exception as e:
            logger.error("message_mark_human_replied_exception", message_id=message_id, error=str(e))
            return False

    def clear_conversation_cache(self) -> None:
        """
        Clear all conversation status cache
        Useful for debugging and maintenance
        """
        cache_size = len(self._conversation_status_cache)
        self._conversation_status_cache.clear()
        logger.info("conversation_cache_cleared", cache_size=cache_size)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring
        
        Returns:
            Cache statistics including size and keys
        """
        return {
            "cache_size": len(self._conversation_status_cache),
            "cached_conversations": list(self._conversation_status_cache.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics for admin dashboard"""
        try:
            # Get total conversations
            total_response = self.supabase.table("conversations").select("id", count="exact").execute()
            total_conversations = total_response.count if total_response.count else 0
            
            # Get active conversations
            active_response = self.supabase.table("conversations").select("id", count="exact").eq("status", "active").execute()
            active_conversations = active_response.count if active_response.count else 0
            
            # Get total messages
            messages_response = self.supabase.table("messages").select("id", count="exact").execute()
            total_messages = messages_response.count if messages_response.count else 0
            
            # Get messages requiring human intervention
            human_response = self.supabase.table("messages").select("id", count="exact").eq("requires_human", True).execute()
            messages_requiring_human = human_response.count if human_response.count else 0
            
            stats = {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "total_messages": total_messages,
                "messages_requiring_human": messages_requiring_human,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("conversation_stats_retrieved", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("conversation_stats_retrieval_exception", error=str(e))
            return {
                "total_conversations": 0,
                "active_conversations": 0,
                "total_messages": 0,
                "messages_requiring_human": 0,
                "timestamp": datetime.now().isoformat()
            }


# Global instance
_conversation_tracking_service = None

def get_conversation_tracking_service() -> ConversationTrackingService:
    """Get conversation tracking service instance"""
    global _conversation_tracking_service
    if _conversation_tracking_service is None:
        _conversation_tracking_service = ConversationTrackingService()
    return _conversation_tracking_service 