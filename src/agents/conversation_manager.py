"""
Conversation management for Cafe Pentagon Chatbot
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.base import BaseAgent
from src.utils.language import detect_language, translate_text
from src.utils.cache import get_cache_manager


class ConversationManager(BaseAgent):
    """
    Manages conversation state, history, and flow control
    """
    
    def __init__(self):
        """Initialize conversation manager"""
        super().__init__("conversation_manager")
        self.cache_manager = get_cache_manager()
        
        # Conversation flow states
        self.conversation_states = {
            "greeting": "Initial greeting and welcome",
            "menu_browsing": "User is browsing menu",
            "menu_searching": "User is searching for specific items",
            "ordering": "User is placing an order",
            "reservation_making": "User is making a reservation",
            "faq_answering": "Answering FAQ questions",
            "complaint_handling": "Handling complaints",
            "clarification": "Asking for clarification",
            "goodbye": "Ending conversation"
        }
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Manage conversation state and flow"""
        user_message = state.get("user_message", "")
        if not user_message:
            return state
        
        # Initialize conversation if needed
        if "conversation_state" not in state:
            state = self._initialize_conversation(state)
        
        # Add user message to history
        state = self.add_message_to_history(state, "user", user_message)
        
        # Detect language if not set
        if "user_language" not in state:
            detected_lang = detect_language(user_message)
            state["user_language"] = detected_lang
        
        # Update conversation state based on intents
        state = await self._update_conversation_state(state)
        
        # Handle conversation flow
        state = await self._handle_conversation_flow(state)
        
        return state
    
    def _initialize_conversation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize new conversation"""
        state.update({
            "conversation_state": "greeting",
            "conversation_history": [],
            "session_start_time": self._get_timestamp(),
            "turn_count": 0,
            "context": {},
            "pending_actions": []
        })
        
        self.logger.info("conversation_initialized", user_id=state.get("user_id"))
        return state
    
    async def _update_conversation_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation state based on detected intents"""
        intents = state.get("detected_intents", [])
        current_state = state.get("conversation_state", "greeting")
        
        # Determine new state based on primary intent
        primary_intent = state.get("primary_intent", "unknown")
        
        new_state = self._map_intent_to_state(primary_intent, current_state)
        
        if new_state != current_state:
            state["conversation_state"] = new_state
            state["context"] = {}  # Clear context for new state
            
            self.logger.info(
                "conversation_state_changed",
                from_state=current_state,
                to_state=new_state,
                primary_intent=primary_intent
            )
        
        return state
    
    def _map_intent_to_state(self, intent: str, current_state: str) -> str:
        """Map intent to conversation state"""
        intent_state_mapping = {
            "greeting": "greeting",
            "menu_browse": "menu_browsing",
            "menu_search": "menu_searching",
            "order_place": "ordering",
            "reservation": "reservation_making",
            "faq": "faq_answering",
            "complaint": "complaint_handling",
            "events": "faq_answering",
            "jobs": "faq_answering",
            "goodbye": "goodbye",
            "unknown": "clarification"
        }
        
        return intent_state_mapping.get(intent, current_state)
    
    async def _handle_conversation_flow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation flow based on current state"""
        conversation_state = state.get("conversation_state", "greeting")
        
        # Increment turn count
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        # Handle different conversation states
        if conversation_state == "greeting":
            state = await self._handle_greeting(state)
        elif conversation_state == "menu_browsing":
            state = await self._handle_menu_browsing(state)
        elif conversation_state == "menu_searching":
            state = await self._handle_menu_searching(state)
        elif conversation_state == "ordering":
            state = await self._handle_ordering(state)
        elif conversation_state == "reservation_making":
            state = await self._handle_reservation_making(state)
        elif conversation_state == "faq_answering":
            state = await self._handle_faq_answering(state)
        elif conversation_state == "complaint_handling":
            state = await self._handle_complaint_handling(state)
        elif conversation_state == "clarification":
            state = await self._handle_clarification(state)
        elif conversation_state == "goodbye":
            state = await self._handle_goodbye(state)
        
        return state
    
    async def _handle_greeting(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle greeting state"""
        language = self.get_user_language(state)
        
        if language == "my":
            greeting = "မင်္ဂလာပါ! Cafe Pentagon မှ ကြိုဆိုပါတယ်။ ကျွန်တော် ဘယ်လိုကူညီပေးနိုင်မလဲ?"
        else:
            greeting = "Hello! Welcome to Cafe Pentagon. How can I help you today?"
        
        state["assistant_response"] = greeting
        state = self.add_message_to_history(state, "assistant", greeting)
        
        return state
    
    async def _handle_menu_browsing(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle menu browsing state"""
        # This will be handled by MenuAgent
        state["next_agent"] = "menu_agent"
        return state
    
    async def _handle_menu_searching(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle menu searching state"""
        # This will be handled by MenuAgent
        state["next_agent"] = "menu_agent"
        return state
    
    async def _handle_ordering(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ordering state"""
        # This will be handled by OrderAgent (Phase 2)
        state["next_agent"] = "order_agent"
        return state
    
    async def _handle_reservation_making(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reservation making state"""
        # This will be handled by ReservationAgent (Phase 2)
        state["next_agent"] = "reservation_agent"
        return state
    
    async def _handle_faq_answering(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle FAQ answering state"""
        # This will be handled by RAGAgent
        state["next_agent"] = "rag_agent"
        return state
    
    async def _handle_complaint_handling(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complaint handling state"""
        # This will be handled by ComplaintAgent (Phase 3)
        state["next_agent"] = "complaint_agent"
        return state
    
    async def _handle_clarification(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clarification state"""
        language = self.get_user_language(state)
        
        if language == "my":
            clarification = "ကျေးဇူးပြု၍ ပိုရှင်းရှင်းလင်းလင်း ပြောပြပေးပါ။ ကျွန်တော် ဘယ်လိုကူညီပေးနိုင်မလဲ?"
        else:
            clarification = "Could you please clarify? How can I help you?"
        
        state["assistant_response"] = clarification
        state = self.add_message_to_history(state, "assistant", clarification)
        
        return state
    
    async def _handle_goodbye(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle goodbye state"""
        language = self.get_user_language(state)
        
        if language == "my":
            goodbye = "ကျေးဇူးတင်ပါတယ်! ပြန်လည်လာရောက်လည်ပတ်ပေးပါ။ နေကောင်းပါစေ!"
        else:
            goodbye = "Thank you for visiting Cafe Pentagon! Please come back again. Have a great day!"
        
        state["assistant_response"] = goodbye
        state = self.add_message_to_history(state, "assistant", goodbye)
        state = self.end_conversation(state)
        
        return state
    
    def get_conversation_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation context"""
        return state.get("context", {})
    
    def update_conversation_context(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation context"""
        context = state.get("context", {})
        context.update(updates)
        state["context"] = context
        return state
    
    def add_pending_action(self, state: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        """Add pending action to conversation"""
        pending_actions = state.get("pending_actions", [])
        pending_actions.append(action)
        state["pending_actions"] = pending_actions
        return state
    
    def clear_pending_actions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Clear pending actions"""
        state["pending_actions"] = []
        return state
    
    def get_conversation_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation summary"""
        return {
            "user_id": state.get("user_id"),
            "conversation_state": state.get("conversation_state"),
            "user_language": state.get("user_language"),
            "turn_count": state.get("turn_count", 0),
            "session_start_time": state.get("session_start_time"),
            "conversation_ended": state.get("conversation_ended", False)
        }
    
    async def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        try:
            # Clear from cache
            success = self.cache_manager.clear_conversation(user_id)
            
            # Clear from memory if cache failed
            if not success:
                self.logger.warning("cache_clear_failed_using_memory", user_id=user_id)
            
            self.logger.info("conversation_cleared", user_id=user_id)
            return True
            
        except Exception as e:
            self.logger.error("conversation_clear_failed", error=str(e))
            return False
    
    async def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        try:
            # Try to get from cache first
            history = self.cache_manager.get_conversation(user_id)
            
            if history is None:
                # If not in cache, return empty list
                self.logger.info("no_conversation_history_found", user_id=user_id)
                return []
            
            # Ensure history is a list
            if isinstance(history, list):
                return history
            else:
                self.logger.warning("invalid_conversation_history_format", user_id=user_id)
                return []
                
        except Exception as e:
            self.logger.error("conversation_history_retrieval_failed", error=str(e))
            return []
    
    async def save_conversation_history(self, user_id: str, history: List[Dict[str, Any]]) -> bool:
        """Save conversation history for user"""
        try:
            success = self.cache_manager.set_conversation(user_id, history)
            if success:
                self.logger.info("conversation_history_saved", user_id=user_id, history_length=len(history))
            else:
                self.logger.warning("conversation_history_save_failed", user_id=user_id)
            return success
            
        except Exception as e:
            self.logger.error("conversation_history_save_error", error=str(e))
            return False 