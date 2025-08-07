"""
Conversation Memory Updater Node for LangGraph
Updates conversation history and context after response generation
"""

from typing import Dict, Any
from src.services.conversation_memory_service import get_conversation_memory_service
from src.utils.logger import get_logger

logger = get_logger("conversation_memory_updater_node")


class ConversationMemoryUpdaterNode:
    """
    LangGraph node for updating conversation memory
    Adds user message and bot response to conversation history
    """
    
    def __init__(self):
        """Initialize conversation memory updater node"""
        self.memory_service = get_conversation_memory_service()
        logger.info("conversation_memory_updater_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
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
        detected_language = state.get("detected_language", "en")
        detected_intent = state.get("detected_intent", "unknown")
        intent_confidence = state.get("intent_confidence", 0.0)
        response_generated = state.get("response_generated", False)
        human_handling = state.get("human_handling", False)
        requires_human = state.get("requires_human", False)
        
        if not conversation_id:
            logger.warning("no_conversation_id_for_memory_update", user_id=user_id)
            return state
        
        try:
            # Ensure conversation exists in Supabase
            from src.services.conversation_tracking_service import get_conversation_tracking_service
            conversation_tracking = get_conversation_tracking_service()
            
            # Check if conversation was already escalated and blocked from LLM processing
            conversation_escalated = state.get("conversation_escalated", False)
            escalation_blocked = state.get("escalation_blocked", False)
            
            if conversation_escalated and escalation_blocked:
                logger.info("conversation_escalated_skipping_processing", 
                           conversation_id=conversation_id,
                           user_id=user_id)
                # Return state unchanged - don't process escalated conversations
                return state
            
            # Get or create conversation
            conversation = conversation_tracking.get_or_create_conversation(
                user_id=user_id,
                platform="streamlit",
                conversation_id=conversation_id
            )
            
            if not conversation:
                logger.error("failed_to_get_or_create_conversation", 
                           conversation_id=conversation_id,
                           user_id=user_id)
                return state
            
            # Add user message to history
            user_metadata = {
                "intent": detected_intent,
                "language": detected_language,
                "conversation_state": "active",
                "confidence": intent_confidence,
                "requires_human": requires_human
            }
            
            self.memory_service.add_message_to_history(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                metadata=user_metadata
            )
            
            # Add bot response to history if generated
            if response_generated and response:
                bot_metadata = {
                    "intent": detected_intent,
                    "language": detected_language,
                    "conversation_state": "active",
                    "confidence": intent_confidence,
                    "response_quality": state.get("response_quality", "standard"),
                    "human_handling": human_handling,
                    "requires_human": requires_human
                }
                
                self.memory_service.add_message_to_history(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response,
                    metadata=bot_metadata
                )
            
            # Update conversation context with human assistance flags
            context_updates = {
                "last_message_at": "now()",
                "metadata": {
                    "last_intent": detected_intent,
                    "last_language": detected_language,
                    "last_confidence": intent_confidence,
                    "total_messages": len(state.get("conversation_history", [])) + 2,  # +2 for user and bot messages
                    "human_handling": human_handling,
                    "requires_human": requires_human
                }
            }
            
            self.memory_service.update_conversation_context(conversation_id, context_updates)
            
            # Update conversation tracking service with human assistance flags
            if human_handling or requires_human:
                from src.services.conversation_tracking_service import get_conversation_tracking_service
                conversation_tracking = get_conversation_tracking_service()
                
                conversation_updates = {
                    "human_handling": human_handling,
                    "rag_enabled": not human_handling,
                    "priority": 2 if human_handling else 1
                }
                
                # Use the correct status based on human handling
                status = "escalated" if human_handling else "active"
                conversation_tracking.update_conversation(conversation_id, status, conversation_updates)
                
                logger.info("conversation_updated_for_human_assistance", 
                           conversation_id=conversation_id,
                           human_handling=human_handling,
                           requires_human=requires_human)
            
            # Reload conversation history to include new messages
            updated_history = self.memory_service.load_conversation_history(conversation_id, user_id, limit=10)
            
            logger.info("conversation_memory_updated", 
                       conversation_id=conversation_id,
                       user_message_length=len(user_message),
                       bot_response_length=len(response),
                       updated_history_length=len(updated_history),
                       human_handling=human_handling,
                       requires_human=requires_human)
            
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
            
            # Return state unchanged on error
            return state 