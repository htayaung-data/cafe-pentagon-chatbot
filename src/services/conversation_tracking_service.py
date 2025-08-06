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
        
        logger.info("conversation_tracking_service_initialized")

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

    def save_message(self, conversation_id: int, content: str, sender_type: str = 'user', 
                          confidence_score: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Save a message to Supabase"""
        try:
            # Check if message requires human assistance
            requires_human = False
            if metadata:
                requires_human = metadata.get("requires_human", False)
                # Also check content for human assistance keywords
                if not requires_human and sender_type == "user":
                    requires_human = self._check_content_for_human_assistance(content)
            
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
            
            response = self.supabase.table("messages").insert(message_data).execute()
            
            if response.data and len(response.data) > 0:
                message = response.data[0]
                logger.info("message_saved", 
                           conversation_id=conversation_id, 
                           sender_type=sender_type,
                           requires_human=requires_human)
                
                # If message requires human assistance, update conversation
                if requires_human:
                    self._update_conversation_for_human_assistance(conversation_id)
                
                return message
            else:
                logger.error("message_save_failed", conversation_id=conversation_id)
                return None
                
        except Exception as e:
            logger.error("message_save_exception", conversation_id=conversation_id, error=str(e))
            return None

    def _check_content_for_human_assistance(self, content: str) -> bool:
        """
        Check if message content indicates need for human assistance
        
        Args:
            content: Message content
            
        Returns:
            True if human assistance is needed, False otherwise
        """
        content_lower = content.lower().strip()
        
        # English patterns
        english_patterns = [
            "talk to a human", "speak to someone", "talk to someone",
            "human help", "real person", "staff member", "employee",
            "manager", "supervisor", "customer service",
            "i need help", "can't help", "not working",
            "complaint", "problem", "issue", "escalate"
        ]
        
        # Burmese patterns
        burmese_patterns = [
            "လူသားနဲ့ပြောချင်ပါတယ်", "အကူအညီလိုပါတယ်",
            "ပိုကောင်းတဲ့အကူအညီလိုပါတယ်", "သူငယ်ချင်းနဲ့ပြောချင်ပါတယ်",
            "လူသားနဲ့ပြောချင်တယ်", "အကူအညီလိုတယ်",
            "မန်နေဂျာ", "အုပ်ချုပ်သူ", "ဝန်ထမ်း",
            "ပြဿနာ", "အခက်အခဲ", "အကူအညီလိုပါတယ်"
        ]
        
        # Check English patterns
        for pattern in english_patterns:
            if pattern in content_lower:
                return True
        
        # Check Burmese patterns
        for pattern in burmese_patterns:
            if pattern in content_lower:
                return True
        
        return False

    def _update_conversation_for_human_assistance(self, conversation_id: int) -> bool:
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

    def update_conversation(self, conversation_id: int, status: str = 'active', 
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
                logger.info("conversation_updated", conversation_id=conversation_id, status=status)
                return True
            else:
                logger.error("conversation_update_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("conversation_update_exception", conversation_id=conversation_id, error=str(e))
            return False

    def get_or_create_conversation(self, user_id: str, platform: str = 'facebook') -> Optional[Dict[str, Any]]:
        """Get existing active conversation or create new one"""
        try:
            # Try to find existing active conversation
            response = self.supabase.table("conversations").select("*").eq("user_id", user_id).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
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

    def get_conversation_messages(self, conversation_id: int, limit: int = 50) -> List[Dict[str, Any]]:
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

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            response = self.supabase.table("conversations").select("*").eq("id", conversation_id).single().execute()
            
            if response.data:
                logger.info("conversation_retrieved", conversation_id=conversation_id)
                return response.data
            else:
                logger.info("conversation_not_found", conversation_id=conversation_id)
                return None
                
        except Exception as e:
            logger.error("conversation_retrieval_exception", conversation_id=conversation_id, error=str(e))
            return None

    def close_conversation(self, conversation_id: int) -> bool:
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

    def mark_message_requires_human(self, message_id: int) -> bool:
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

    def mark_message_human_replied(self, message_id: int) -> bool:
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