"""
Human Escalation Service for Cafe Pentagon Chatbot
Manages conversation escalation to human staff
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger

logger = get_logger("escalation_service")


class EscalationService:
    """
    Service for managing human escalation
    Handles escalation detection, assignment, and management
    """
    
    def __init__(self):
        """Initialize escalation service"""
        self.conversation_tracking = get_conversation_tracking_service()
        logger.info("escalation_service_initialized")
    
    def escalate_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        reason: str,
        admin_id: Optional[str] = None
    ) -> bool:
        """
        Escalate a conversation to human handling
        
        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            reason: Reason for escalation
            admin_id: Optional admin to assign
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "rag_enabled": False,
                "human_handling": True,
                "status": "escalated",
                "priority": 2,  # Increase priority
                "escalation_reason": reason,
                "escalation_timestamp": datetime.now().isoformat(),
                "last_message_at": datetime.now().isoformat()
            }
            
            if admin_id:
                update_data["assigned_admin_id"] = admin_id
            
            response = self.conversation_tracking.supabase.table("conversations").update(
                update_data
            ).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info(
                    "conversation_escalated",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    reason=reason,
                    admin_id=admin_id
                )
                return True
            else:
                logger.error("escalation_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("escalation_error", conversation_id=conversation_id, error=str(e))
            return False
    
    def deescalate_conversation(self, conversation_id: str, admin_id: str) -> bool:
        """
        De-escalate a conversation back to bot handling
        
        Args:
            conversation_id: Conversation identifier
            admin_id: Admin who is releasing the conversation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "rag_enabled": True,
                "human_handling": False,
                "status": "active",
                "priority": 1,  # Reset priority
                "escalation_reason": None,
                "escalation_timestamp": None,
                "assigned_admin_id": None,
                "last_message_at": datetime.now().isoformat()
            }
            
            response = self.conversation_tracking.supabase.table("conversations").update(
                update_data
            ).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info(
                    "conversation_deescalated",
                    conversation_id=conversation_id,
                    admin_id=admin_id
                )
                return True
            else:
                logger.error("deescalation_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("deescalation_error", conversation_id=conversation_id, error=str(e))
            return False
    
    def assign_conversation(self, conversation_id: str, admin_id: str) -> bool:
        """
        Assign a conversation to a specific admin
        
        Args:
            conversation_id: Conversation identifier
            admin_id: Admin to assign
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "assigned_admin_id": admin_id,
                "last_message_at": datetime.now().isoformat()
            }
            
            response = self.conversation_tracking.supabase.table("conversations").update(
                update_data
            ).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info(
                    "conversation_assigned",
                    conversation_id=conversation_id,
                    admin_id=admin_id
                )
                return True
            else:
                logger.error("assignment_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("assignment_error", conversation_id=conversation_id, error=str(e))
            return False
    
    def get_escalated_conversations(self, admin_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all escalated conversations
        
        Args:
            admin_id: Optional admin filter
            
        Returns:
            List of escalated conversations
        """
        try:
            query = self.conversation_tracking.supabase.table("conversations").select(
                "id, user_id, platform, status, priority, assigned_admin_id, "
                "escalation_reason, escalation_timestamp, created_at, last_message_at"
            ).eq("human_handling", True)
            
            if admin_id:
                query = query.eq("assigned_admin_id", admin_id)
            
            response = query.order("escalation_timestamp", desc=True).execute()
            
            if response.data:
                logger.info("escalated_conversations_retrieved", count=len(response.data))
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error("escalated_conversations_error", error=str(e))
            return []
    
    def get_conversation_escalation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get escalation status of a conversation
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Escalation status or None if not found
        """
        try:
            response = self.conversation_tracking.supabase.table("conversations").select(
                "rag_enabled, human_handling, status, priority, assigned_admin_id, "
                "escalation_reason, escalation_timestamp"
            ).eq("id", conversation_id).single().execute()
            
            if response.data:
                return response.data
            else:
                return None
                
        except Exception as e:
            logger.error("escalation_status_error", conversation_id=conversation_id, error=str(e))
            return None
    
    def mark_message_for_human(self, message_id: str, conversation_id: str) -> bool:
        """
        Mark a specific message as requiring human attention
        
        Args:
            message_id: Message identifier
            conversation_id: Conversation identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "requires_human": True,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.conversation_tracking.supabase.table("messages").update(
                update_data
            ).eq("id", message_id).execute()
            
            if response.data:
                logger.info(
                    "message_marked_for_human",
                    message_id=message_id,
                    conversation_id=conversation_id
                )
                return True
            else:
                logger.error("message_mark_failed", message_id=message_id)
                return False
                
        except Exception as e:
            logger.error("message_mark_error", message_id=message_id, error=str(e))
            return False
    
    def mark_human_replied(self, message_id: str, admin_id: str) -> bool:
        """
        Mark that a human has replied to a message
        
        Args:
            message_id: Message identifier
            admin_id: Admin who replied
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "human_replied": True,
                "metadata": {"replied_by": admin_id, "replied_at": datetime.now().isoformat()}
            }
            
            response = self.conversation_tracking.supabase.table("messages").update(
                update_data
            ).eq("id", message_id).execute()
            
            if response.data:
                logger.info(
                    "human_reply_marked",
                    message_id=message_id,
                    admin_id=admin_id
                )
                return True
            else:
                logger.error("human_reply_mark_failed", message_id=message_id)
                return False
                
        except Exception as e:
            logger.error("human_reply_mark_error", message_id=message_id, error=str(e))
            return False


# Global escalation service instance
_escalation_service: Optional[EscalationService] = None


def get_escalation_service() -> EscalationService:
    """Get or create escalation service instance"""
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = EscalationService()
    return _escalation_service 