"""
Enhanced Main Agent for Cafe Pentagon Chatbot
Uses AI-driven approach for Burmese and enhanced intent classifier and response generator
"""

import asyncio
from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.agents.intent_classifier import AIIntentClassifier
from src.agents.response_generator import EnhancedResponseGenerator
from src.agents.conversation_manager import ConversationManager
from src.agents.burmese_customer_services_handler import BurmeseCustomerServiceHandler
from src.utils.logger import get_logger

logger = get_logger("enhanced_main_agent")


class EnhancedMainAgent(BaseAgent):
    """
    Enhanced main agent with improved intent classification and response generation
    """
    
    def __init__(self):
        """Initialize enhanced main agent"""
        super().__init__("enhanced_main_agent")
        
        # Initialize components
        self.intent_classifier = AIIntentClassifier()
        self.response_generator = EnhancedResponseGenerator()
        self.conversation_manager = ConversationManager()
        self.burmese_handler = BurmeseCustomerServiceHandler()
        
        logger.info("enhanced_main_agent_initialized")

    async def chat(self, user_message: str, user_id: str, language: str = None) -> Dict[str, Any]:
        """Enhanced chat method with better intent classification and response generation"""
        try:
            # Detect language if not provided
            if not language or language == "Auto-detect":
                from src.utils.language import detect_language
                detected_language = detect_language(user_message)
                logger.info("language_detected_in_chat", 
                           user_message=user_message[:100],
                           detected_language=detected_language)
            else:
                detected_language = language
                logger.info("language_provided_in_chat", 
                           user_message=user_message[:100],
                           provided_language=detected_language)
            
            # Load existing conversation history
            existing_history = await self.conversation_manager.get_conversation_history(user_id)
            
            # Initialize state with existing history
            state = {
                "user_message": user_message,
                "user_id": user_id,
                "user_language": detected_language,
                "conversation_state": "greeting",
                "conversation_history": existing_history or []
            }
            
            logger.info("chat_state_initialized", 
                       user_language=detected_language,
                       conversation_history_length=len(existing_history or []))
            
            # Add user message to conversation history immediately
            state = self.add_message_to_history(state, "user", user_message)
            
            # Check if this is a Burmese query and use AI-driven approach
            if detected_language == "my":
                logger.info("using_burmese_customer_service_handler", user_message=user_message[:100])
                
                # Use AI-driven Burmese handler
                burmese_result = await self.burmese_handler.process_burmese_query(
                    user_message, 
                    state.get("conversation_history", [])
                )
                
                # Update state with Burmese analysis
                state.update({
                    "primary_intent": burmese_result.get("intent", "unknown"),
                    "detected_intents": [burmese_result.get("intent", "unknown")],
                    "confidence": burmese_result.get("confidence", 0.0),
                    "relevant_items": burmese_result.get("relevant_items", []),
                    "burmese_analysis": burmese_result.get("analysis", {})
                })
                
                # Use the AI-generated response
                response = burmese_result.get("response", "ကျေးဇူးပြု၍ ပြန်လည်ကြိုးစားကြည့်ပါ။")
                
            else:
                # Use existing enhanced approach for non-Burmese queries
                # Step 1: Enhanced Intent Classification
                logger.info("starting_enhanced_intent_classification", user_message=user_message[:100])
                state = await self.intent_classifier.process(state)
                
                # Step 2: Conversation Management
                logger.info("managing_conversation", primary_intent=state.get("primary_intent"))
                state = await self.conversation_manager.process(state)
                
                # Step 3: Enhanced Response Generation
                logger.info("generating_enhanced_response", 
                           primary_intent=state.get("primary_intent"),
                           user_language=state.get("user_language"))
                response = await self.response_generator.generate_response(state)
            
            # Check if response contains image information
            image_info = None
            
            # Check for new IMAGE_MARKER format
            if "[IMAGE_MARKER:" in response:
                import re
                image_match = re.search(r'\[IMAGE_MARKER:(https?://[^:]+):([^\]]+)\]', response)
                if image_match:
                    image_url = image_match.group(1)
                    item_name = image_match.group(2)
                    image_info = {
                        "image_url": image_url,
                        "caption": f"{item_name} - Cafe Pentagon"
                    }
                    # Remove the marker from the response text
                    response = re.sub(r'\n\n\[IMAGE_MARKER:[^\]]+\]', '', response)
            
            # Fallback: Check for old HTML img tag format (for backward compatibility)
            elif "<img" in response:
                # Extract image URL from HTML img tag
                import re
                image_match = re.search(r'<img[^>]+src=["\'](https?://[^"\']+)["\'][^>]*>', response)
                if image_match:
                    image_url = image_match.group(1)
                    # Extract alt text for caption
                    alt_match = re.search(r'alt=["\']([^"\']+)["\']', response)
                    item_name = alt_match.group(1) if alt_match else "Menu Item"
                    image_info = {
                        "image_url": image_url,
                        "caption": f"{item_name} - Cafe Pentagon"
                    }
                    # Remove the HTML img tag from the response text
                    response = re.sub(r'<img[^>]+>', '', response)
            
            # Fallback: Check for markdown image syntax
            elif "![(" in response or "![(" in response:
                # Extract image URL from markdown image syntax
                import re
                image_match = re.search(r'!\[(.*?)\]\((https?://[^\s\n]+)\)', response)
                if image_match:
                    image_url = image_match.group(2)
                    item_name = image_match.group(1)
                    image_info = {
                        "image_url": image_url,
                        "caption": f"{item_name} - Cafe Pentagon"
                    }
                    # Remove the markdown image syntax from the response text
                    response = re.sub(r'!\[.*?\]\(https?://[^\s\n]+\)', '', response)
            
            # Fallback for old format
            elif "🖼️ **Image**:" in response or "🖼️ **ပုံ**:" in response:
                # Extract image URL from response
                import re
                image_match = re.search(r'🖼️ \*\*.*?\*\*: (https?://[^\s\n]+)', response)
                if image_match:
                    image_url = image_match.group(1)
                    # Extract item name for caption
                    name_match = re.search(r'📸 \*\*(.*?)\*\*', response)
                    item_name = name_match.group(1) if name_match else "Menu Item"
                    image_info = {
                        "image_url": image_url,
                        "caption": f"{item_name} - Cafe Pentagon"
                    }
                    # Remove the old format markers from the response text
                    response = re.sub(r'🖼️ \*\*.*?\*\*: https?://[^\s\n]+', '', response)
                    response = re.sub(r'📸 \*\*.*?\*\*', '', response)
            
            # Add assistant response to conversation history
            state = self.add_message_to_history(state, "assistant", response)
            
            # Save updated conversation history
            await self.conversation_manager.save_conversation_history(user_id, state.get("conversation_history", []))
            
            # Prepare result
            result = {
                "response": response,
                "intents": state.get("detected_intents", []),
                "primary_intent": state.get("primary_intent", "unknown"),
                "conversation_state": state.get("conversation_state", "unknown"),
                "user_language": state.get("user_language", "en"),
                "image_info": image_info
            }
            
            logger.info("enhanced_chat_completed", 
                       primary_intent=result["primary_intent"],
                       conversation_state=result["conversation_state"],
                       user_language=result["user_language"],
                       response_preview=response[:100])
            
            return result
            
        except Exception as e:
            logger.error("enhanced_chat_failed", error=str(e))
            return {
                "response": "I'm sorry, I encountered an error. Please try again.",
                "intents": [],
                "primary_intent": "unknown",
                "conversation_state": "error",
                "user_language": language or "en"
            }

    async def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        try:
            await self.conversation_manager.clear_conversation(user_id)
            logger.info("conversation_cleared", user_id=user_id)
            return True
        except Exception as e:
            logger.error("conversation_clear_failed", error=str(e))
            return False

    async def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        try:
            return await self.conversation_manager.get_conversation_history(user_id)
        except Exception as e:
            logger.error("conversation_history_retrieval_failed", error=str(e))
            return []

    async def process_batch(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple messages in batch"""
        results = []
        for message in messages:
            result = await self.chat(
                message["text"],
                message["user_id"],
                message.get("language")
            )
            results.append(result)
        return results

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state (required by BaseAgent)"""
        user_message = state.get("user_message", "")
        user_id = state.get("user_id", "unknown_user")
        language = state.get("user_language", "en")
        
        result = await self.chat(user_message, user_id, language)
        
        # Update state with result
        state.update(result)
        return state 
