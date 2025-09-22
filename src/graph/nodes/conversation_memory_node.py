"""
Conversation Memory Node for Simplified LangGraph
Handles conversation history loading and updating for the simplified 3-node workflow
"""

from typing import Dict, Any, List, Optional
from src.services.conversation_memory_service import get_conversation_memory_service
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger

logger = get_logger("conversation_memory_node")


class ConversationMemoryNode:
    """
    LangGraph node for managing conversation memory in simplified workflow
    Loads conversation history and updates it after processing
    """
    
    def __init__(self):
        """Initialize conversation memory node"""
        self.memory_service = get_conversation_memory_service()
        self.conversation_tracking = get_conversation_tracking_service()
        logger.info("conversation_memory_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load conversation history and prepare for processing
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with conversation history loaded
        """
        user_message = state.get("user_message", "")
        user_id = state.get("user_id", "")
        conversation_id = state.get("conversation_id", "")
        platform = state.get("platform", "messenger")
        
        if not conversation_id:
            logger.warning("no_conversation_id_for_memory_load", user_id=user_id)
            return state
        
        try:
            # Ensure conversation exists in Supabase
            conversation = self.conversation_tracking.get_or_create_conversation(
                user_id=user_id,
                platform=platform,
                conversation_id=conversation_id
            )
            
            if not conversation:
                logger.error("failed_to_get_or_create_conversation", 
                           conversation_id=conversation_id,
                           user_id=user_id)
                return state
            
            # Load conversation history
            conversation_history = self.memory_service.load_conversation_history(
                conversation_id=conversation_id,
                user_id=user_id,
                limit=10
            )
            
            # Update state with conversation history
            updated_state = state.copy()
            updated_state.update({
                "conversation_history": conversation_history,
                "memory_loaded": True
            })
            
            logger.info("conversation_memory_loaded", 
                       conversation_id=conversation_id,
                       history_length=len(conversation_history),
                       user_id=user_id)
            
            return updated_state
            
        except Exception as e:
            logger.error("conversation_memory_load_failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            return state
    
    async def update_memory(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update conversation memory with user message and bot response
        
        Args:
            state: Current conversation state with response generated
            
        Returns:
            Updated state with conversation memory updated
        """
        user_message = state.get("user_message", "")
        response = state.get("response", "")
        conversation_id = state.get("conversation_id", "")
        user_id = state.get("user_id", "")
        user_language = state.get("user_language", "en")
        response_strategy = state.get("response_strategy", "polite_fallback")
        analysis_confidence = state.get("analysis_confidence", 0.0)
        response_generated = state.get("response_generated", False)
        data_found = state.get("data_found", False)
        requires_human = state.get("requires_human", False)
        human_handling = state.get("human_handling", False)
        escalation_reason = state.get("escalation_reason", "")
        
        if not conversation_id:
            logger.warning("no_conversation_id_for_memory_update", user_id=user_id)
            return state
        
        try:
            # Add user message to history - preserve original metadata (including attachments)
            user_metadata = {}
            
            # Start with original state metadata (includes attachment data from Facebook)
            original_metadata = state.get("metadata", {})
            if original_metadata:
                user_metadata.update(original_metadata)
            
            # Add/override LangGraph-specific fields
            user_metadata.update({
                "intent": response_strategy,  # Use response strategy as intent
                "language": user_language,
                "conversation_state": "active",
                "confidence": analysis_confidence,
                "requires_human": requires_human
            })
            
            self.memory_service.add_message_to_history(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                metadata=user_metadata
            )
            
            # Add bot response to history if generated
            if response_generated and response:
                bot_metadata = {
                    "intent": response_strategy,
                    "language": user_language,
                    "conversation_state": "active",
                    "confidence": analysis_confidence,
                    "response_quality": "standard" if data_found else "fallback",
                    "requires_human": requires_human,
                    "escalation_reason": escalation_reason
                }
                
                self.memory_service.add_message_to_history(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response,
                    metadata=bot_metadata
                )
            
            # Update conversation context
            context_updates = {
                "last_message_at": "now()",
                "metadata": {
                    "last_intent": response_strategy,
                    "last_language": user_language,
                    "last_confidence": analysis_confidence,
                    "total_messages": len(state.get("conversation_history", [])) + 2,
                    "human_handling": human_handling,
                    "requires_human": requires_human,
                    "escalation_reason": escalation_reason
                }
            }
            
            self.memory_service.update_conversation_context(conversation_id, context_updates)
            
            # Reload conversation history to include new messages
            updated_history = self.memory_service.load_conversation_history(conversation_id, user_id, limit=10)
            
            logger.info("conversation_memory_updated", 
                       conversation_id=conversation_id,
                       user_message_length=len(user_message),
                       bot_response_length=len(response),
                       updated_history_length=len(updated_history))
            
            # Update state with refreshed conversation history
            updated_state = state.copy()
            updated_state.update({
                "conversation_history": updated_history,
                "memory_updated": True
            })
            
            return updated_state
            
        except Exception as e:
            logger.error("conversation_memory_update_failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            return state
