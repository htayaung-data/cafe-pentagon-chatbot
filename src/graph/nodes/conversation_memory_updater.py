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
        
        if not conversation_id:
            logger.warning("no_conversation_id_for_memory_update", user_id=user_id)
            return state
        
        try:
            # Add user message to history
            user_metadata = {
                "intent": detected_intent,
                "language": detected_language,
                "conversation_state": "active",
                "confidence": intent_confidence
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
                    "response_quality": state.get("response_quality", "standard")
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
                    "last_intent": detected_intent,
                    "last_language": detected_language,
                    "last_confidence": intent_confidence,
                    "total_messages": len(state.get("conversation_history", [])) + 2  # +2 for user and bot messages
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
            
            # Return state unchanged on error
            return state 