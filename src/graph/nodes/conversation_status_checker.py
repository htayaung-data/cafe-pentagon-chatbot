"""
Conversation Status Checker Node for LangGraph
Checks conversation status before any LLM processing to prevent escalated conversations from being processed
"""

from typing import Dict, Any
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger

logger = get_logger("conversation_status_checker_node")


class ConversationStatusCheckerNode:
    """
    LangGraph node for checking conversation status before LLM processing
    Prevents escalated conversations from being processed by LLMs
    """
    
    def __init__(self):
        """Initialize conversation status checker node"""
        self.conversation_tracking = get_conversation_tracking_service()
        logger.info("conversation_status_checker_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check conversation status and block escalated conversations
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with escalation check results
        """
        conversation_id = state.get("conversation_id", "")
        user_id = state.get("user_id", "")
        user_message = state.get("user_message", "")
        
        if not conversation_id:
            logger.warning("no_conversation_id_for_status_check", user_id=user_id)
            return state
        
        try:
            # Check if conversation is escalated
            is_escalated = self.conversation_tracking.is_conversation_escalated(conversation_id)
            
            if is_escalated:
                logger.info("conversation_escalated_blocking_llm_processing", 
                           conversation_id=conversation_id,
                           user_id=user_id)
                
                # Return state with escalation flags to prevent LLM processing
                updated_state = state.copy()
                updated_state.update({
                    "conversation_escalated": True,
                    "escalation_blocked": True,
                    "action_type": "escalated_conversation",
                    "rag_enabled": False,
                    "human_handling": True,
                    "requires_human": True,
                    "response": "This conversation has been escalated to human assistance. Please wait for a staff member to assist you.",
                    "response_generated": True,
                    "escalation_reason": "Conversation already escalated by admin"
                })
                
                return updated_state
            
            else:
                logger.info("conversation_status_check_passed", 
                           conversation_id=conversation_id,
                           user_id=user_id)
                
                # Mark conversation as not escalated and allow processing
                updated_state = state.copy()
                updated_state.update({
                    "conversation_escalated": False,
                    "escalation_blocked": False
                })
                
                return updated_state
                
        except Exception as e:
            logger.error("conversation_status_check_failed",
                        conversation_id=conversation_id,
                        error=str(e))
            
            # On error, allow processing to continue (fail-safe)
            updated_state = state.copy()
            updated_state.update({
                "conversation_escalated": False,
                "escalation_blocked": False
            })
            
            return updated_state
