"""
Base agent class for Cafe Pentagon Chatbot
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from src.config.settings import get_settings
from src.utils.logger import LoggerMixin, log_performance
from src.utils.cache import SimpleCacheManager


class BaseAgent(LoggerMixin, ABC):
    """
    Base agent class providing common functionality for all agents
    """
    
    def __init__(self, name: str):
        """Initialize base agent"""
        super().__init__()
        self.name = name
        self.settings = get_settings()
        self.cache = SimpleCacheManager()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.openai_max_tokens,
            api_key=self.settings.openai_api_key
        )
        
        self.logger.info("agent_initialized", agent_name=name)
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and return updated state
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state
        """
        pass
    
    def get_user_language(self, state: Dict[str, Any]) -> str:
        """Get user's preferred language from state"""
        return state.get("user_language", self.settings.default_language)
    
    def get_conversation_history(self, state: Dict[str, Any]) -> List[BaseMessage]:
        """Get conversation history as LangChain messages"""
        history = state.get("conversation_history", [])
        messages = []
        
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    def add_message_to_history(self, state: Dict[str, Any], role: str, content: str) -> Dict[str, Any]:
        """Add a message to conversation history with enhanced context"""
        history = state.get("conversation_history", [])
        message = {
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp(),
            "intent": state.get("primary_intent", "unknown"),
            "language": state.get("user_language", "en"),
            "conversation_state": state.get("conversation_state", "unknown")
        }
        
        history.append(message)
        
        # Keep only last 10 messages for context (increased from 8 for better memory)
        max_length = min(self.settings.max_conversation_length, 10)
        if len(history) > max_length:
            history = history[-max_length:]
        
        state["conversation_history"] = history
        
        # Save to cache immediately
        user_id = state.get("user_id")
        if user_id:
            try:
                self.cache.set_conversation(user_id, history)
                self.logger.debug("conversation_history_saved_to_cache", user_id=user_id, history_length=len(history))
            except Exception as e:
                self.logger.error("failed_to_save_conversation_to_cache", error=str(e))
        
        return state
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_user_profile(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get user profile from state or cache"""
        user_id = state.get("user_id")
        if not user_id:
            return {}
        
        profile = self.cache.get_user_profile(user_id)
        if not profile:
            profile = {
                "user_id": user_id,
                "language": self.get_user_language(state),
                "preferences": {},
                "dietary_restrictions": [],
                "allergies": [],
                "created_at": self._get_timestamp()
            }
            self.cache.set_user_profile(user_id, profile)
        
        return profile
    
    def update_user_profile(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        user_id = state.get("user_id")
        if not user_id:
            return state
        
        profile = self.get_user_profile(state)
        profile.update(updates)
        profile["updated_at"] = self._get_timestamp()
        
        self.cache.set_user_profile(user_id, profile)
        return state
    
    @log_performance
    def generate_response(self, messages: List[BaseMessage], system_prompt: str = "") -> str:
        """Generate response using LLM"""
        try:
            if system_prompt:
                from langchain_core.messages import SystemMessage
                messages = [SystemMessage(content=system_prompt)] + messages
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            self.logger.error("llm_generation_failed", error=str(e))
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    def should_continue(self, state: Dict[str, Any]) -> bool:
        """Check if conversation should continue"""
        return not state.get("conversation_ended", False)
    
    def end_conversation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mark conversation as ended"""
        state["conversation_ended"] = True
        return state 
