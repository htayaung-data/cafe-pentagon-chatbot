"""
RAG Controller Node for LangGraph
Controls whether RAG processing is enabled for the conversation
"""

from typing import Dict, Any, Optional
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger

logger = get_logger("rag_controller_node")


class RAGControllerNode:
    """
    LangGraph node for RAG control
    Checks if RAG is enabled and routes conversation flow accordingly
    """
    
    def __init__(self):
        """Initialize RAG controller node"""
        self.conversation_tracking = get_conversation_tracking_service()
        logger.info("rag_controller_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state and check RAG control
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with RAG control information
        """
        conversation_id = state.get("conversation_id")
        user_id = state.get("user_id")
        
        if not conversation_id:
            logger.warning("no_conversation_id_provided", user_id=user_id)
            # Default to RAG enabled if no conversation ID
            state.update({
                "rag_enabled": True,
                "human_handling": False
            })
            return state
        
        try:
            # Get conversation from Supabase to check RAG status
            conversation = self._get_conversation_status(conversation_id)
            
            if conversation:
                # Use status from database
                rag_enabled = conversation.get("rag_enabled", True)
                human_handling = conversation.get("human_handling", False)
                escalation_reason = conversation.get("escalation_reason")
                escalation_timestamp = conversation.get("escalation_timestamp")
                
                logger.info(
                    "rag_status_retrieved",
                    conversation_id=conversation_id,
                    rag_enabled=rag_enabled,
                    human_handling=human_handling
                )
            else:
                # Default values if conversation not found
                rag_enabled = True
                human_handling = False
                escalation_reason = None
                escalation_timestamp = None
                logger.warning("conversation_not_found", conversation_id=conversation_id)
            
            # Update state with RAG control information
            state.update({
                "rag_enabled": rag_enabled,
                "human_handling": human_handling,
                "escalation_reason": escalation_reason,
                "escalation_timestamp": escalation_timestamp
            })
            
            # Check if escalation is requested in pattern matching
            if state.get("is_escalation_request", False):
                # If user explicitly requests human help, disable RAG
                state["rag_enabled"] = False
                state["requires_human"] = True
                state["escalation_reason"] = "explicit_human_request"
                
                # Update conversation in database
                self._update_conversation_escalation(conversation_id, user_id)
                
                logger.info(
                    "escalation_requested",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    reason="explicit_human_request"
                )
            
            # Log final RAG status
            logger.info(
                "rag_control_processed",
                conversation_id=conversation_id,
                rag_enabled=state["rag_enabled"],
                human_handling=state["human_handling"],
                requires_human=state.get("requires_human", False)
            )
            
        except Exception as e:
            logger.error(
                "rag_control_error",
                conversation_id=conversation_id,
                error=str(e)
            )
            # Default to RAG enabled on error
            state.update({
                "rag_enabled": True,
                "human_handling": False
            })
        
        return state
    
    def _get_conversation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation status from Supabase
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation data or None if not found
        """
        try:
            # Query conversations table for RAG status and escalation info
            response = self.conversation_tracking.supabase.table("conversations").select(
                "rag_enabled, human_handling, status, assigned_admin_id, escalation_reason, escalation_timestamp"
            ).eq("id", conversation_id).single().execute()
            
            if response.data:
                return response.data
            else:
                return None
                
        except Exception as e:
            logger.error("conversation_status_query_error", conversation_id=conversation_id, error=str(e))
            return None
    
    def _update_conversation_escalation(self, conversation_id: str, user_id: str) -> bool:
        """
        Update conversation for escalation
        
        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update conversation to mark for human handling
            from datetime import datetime
            
            update_data = {
                "rag_enabled": False,
                "human_handling": True,
                "status": "escalated",
                "priority": 2,  # Increase priority for escalated conversations
                "escalation_reason": "explicit_human_request",
                "escalation_timestamp": datetime.now().isoformat()
            }
            
            response = self.conversation_tracking.supabase.table("conversations").update(
                update_data
            ).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info(
                    "conversation_escalated",
                    conversation_id=conversation_id,
                    user_id=user_id
                )
                return True
            else:
                logger.error("conversation_escalation_failed", conversation_id=conversation_id)
                return False
                
        except Exception as e:
            logger.error("conversation_escalation_error", conversation_id=conversation_id, error=str(e))
            return False
    
    def should_skip_rag(self, state: Dict[str, Any]) -> bool:
        """
        Determine if RAG processing should be skipped
        
        Args:
            state: Current conversation state
            
        Returns:
            True if RAG should be skipped, False otherwise
        """
        # Skip RAG if:
        # 1. RAG is disabled for this conversation
        # 2. Human is handling the conversation
        # 3. User requested human help
        # 4. It's a simple greeting/goodbye
        
        skip_conditions = [
            not state.get("rag_enabled", True),
            state.get("human_handling", False),
            state.get("requires_human", False),
            state.get("is_greeting", False),
            state.get("is_goodbye", False)
        ]
        
        return any(skip_conditions)
    
    def get_rag_route(self, state: Dict[str, Any]) -> str:
        """
        Determine the next route based on RAG status
        
        Args:
            state: Current conversation state
            
        Returns:
            Route name: "rag_processing", "human_response", or "pattern_response"
        """
        if self.should_skip_rag(state):
            if state.get("is_greeting", False):
                return "pattern_response"
            elif state.get("is_goodbye", False):
                return "pattern_response"
            elif state.get("requires_human", False):
                return "human_response"
            else:
                return "human_response"
        else:
            return "rag_processing" 