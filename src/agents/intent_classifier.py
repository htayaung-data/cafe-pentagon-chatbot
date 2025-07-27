"""
AI-Powered Intent Classifier for Cafe Pentagon Chatbot
Uses OpenAI to dynamically classify intents instead of hardcoded keywords
"""

import json
import asyncio
from typing import Dict, Any, List, Tuple
from langchain_openai import ChatOpenAI
from src.agents.base import BaseAgent
from src.utils.language import detect_language, is_burmese_text, is_english_text
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger("ai_intent_classifier")


class AIIntentClassifier(BaseAgent):
    """
    AI-powered intent classifier using OpenAI for dynamic classification
    """
    
    def __init__(self):
        """Initialize AI intent classifier"""
        super().__init__("ai_intent_classifier")
        self.settings = get_settings()
        
        # Initialize OpenAI model for intent classification
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Use GPT-4o for better quality
            temperature=0.1,  # Low temperature for consistent classification
            api_key=self.settings.openai_api_key
        )
        
        # Intent classification prompt
        self.intent_prompt = """
You are an intent classifier for a restaurant chatbot. Analyze the user's message and classify it into one of the following intents:

INTENT CATEGORIES:
1. greeting - User is greeting or starting a conversation
2. menu_browse - User wants to see menu, food options, or browse dishes
3. order_place - User wants to place an order or buy food
4. reservation - User wants to make a reservation or book a table
5. faq - User is asking questions about services, location, hours, policies
6. events - User is asking about events, promotions, or entertainment
7. complaint - User is expressing dissatisfaction or problems
8. goodbye - User is ending the conversation or saying thank you
9. unknown - Cannot determine intent

RESPONSE FORMAT:
Return a JSON object with:
- "intent": the classified intent (string)
- "confidence": confidence score 0.0-1.0 (float)
- "entities": any relevant entities extracted (object)
- "reasoning": brief explanation of classification (string)

USER MESSAGE: {user_message}
LANGUAGE: {language}

RESPONSE:"""

        logger.info("ai_intent_classifier_initialized")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify intents from user message using AI"""
        user_message = state.get("user_message", "")
        if not user_message:
            return state
        
        # Detect language if not already set
        if "user_language" not in state:
            detected_lang = detect_language(user_message)
            state["user_language"] = detected_lang
        
        # AI-powered classification
        intents = await self._ai_classify_intents(user_message, state["user_language"])
        
        # Update state with intents
        state["detected_intents"] = intents
        state["primary_intent"] = self._get_primary_intent(intents)
        
        logger.info(
            "ai_intents_classified",
            user_message=user_message[:100],
            intents=[intent["intent"] for intent in intents],
            primary_intent=state["primary_intent"]
        )
        
        return state
    
    async def _ai_classify_intents(self, user_message: str, language: str) -> List[Dict[str, Any]]:
        """Classify intents using AI"""
        try:
            # Prepare prompt
            prompt = self.intent_prompt.format(
                user_message=user_message,
                language=language
            )
            
            # Get AI response
            response = await self.llm.ainvoke(prompt)
            response_text = response.content.strip()
            
            # Parse JSON response - handle markdown formatting
            try:
                # Clean response text - remove markdown code blocks and any extra formatting
                cleaned_response = response_text.strip()
                
                # Remove markdown code blocks
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                
                # Remove any remaining markdown or extra characters
                cleaned_response = cleaned_response.strip()
                
                # Try to find JSON content if it's wrapped in other text
                import re
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(0)
                
                result = json.loads(cleaned_response)
                
                # Validate and structure the result
                intent_data = {
                    "intent": result.get("intent", "unknown"),
                    "confidence": float(result.get("confidence", 0.5)),
                    "entities": result.get("entities", {}),
                    "reasoning": result.get("reasoning", ""),
                    "priority": self._get_priority(result.get("intent", "unknown"))
                }
                
                # Ensure confidence is within bounds
                intent_data["confidence"] = max(0.0, min(1.0, intent_data["confidence"]))
                
                return [intent_data]
                
            except json.JSONDecodeError as e:
                logger.error("ai_response_parse_error", error=str(e), response=response_text)
                return self._fallback_classification(user_message, language)
                
        except Exception as e:
            logger.error("ai_classification_failed", error=str(e))
            return self._fallback_classification(user_message, language)
    
    def _fallback_classification(self, message: str, language: str) -> List[Dict[str, Any]]:
        """Fallback classification when AI fails"""
        # Simple fallback based on basic patterns
        message_lower = message.lower()
        
        # Check for greeting patterns
        greeting_patterns = {
            "en": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "my": ["မင်္ဂလာ", "ဟယ်လို", "ဟေး"]
        }
        
        lang_key = "my" if language in ["my", "myanmar"] else "en"
        patterns = greeting_patterns.get(lang_key, [])
        
        if any(pattern in message_lower for pattern in patterns):
            return [{
                "intent": "greeting",
                "confidence": 0.8,
                "entities": {},
                "reasoning": "Detected greeting pattern",
                "priority": 1
            }]
        
        # Check for question patterns
        question_patterns = {
            "en": ["what", "how", "when", "where", "why", "is there", "do you have"],
            "my": ["ဘာ", "ဘယ်", "ဘယ်လို", "ဘာကြောင့်", "ရှိလား", "ပါသလား"]
        }
        
        patterns = question_patterns.get(lang_key, [])
        if any(pattern in message_lower for pattern in patterns):
            return [{
                "intent": "faq",
                "confidence": 0.7,
                "entities": {},
                "reasoning": "Detected question pattern",
                "priority": 2
            }]
        
        # Default to unknown
        return [{
            "intent": "unknown",
            "confidence": 0.5,
            "entities": {},
            "reasoning": "Fallback classification",
            "priority": 5
        }]
    
    def _get_priority(self, intent_name: str) -> int:
        """Get priority for intent (1=highest, 5=lowest)"""
        priority_map = {
            "greeting": 1,  # Highest priority for greetings
            "goodbye": 1,   # High priority for goodbyes
            "menu_browse": 2,  # Menu browsing is common
            "faq": 2,       # FAQ queries are common
            "events": 3,    # Events are specific
            "order_place": 3,  # Ordering is specific
            "reservation": 3,  # Reservation is specific
            "complaint": 4,    # Complaints are less common
            "unknown": 5
        }
        return priority_map.get(intent_name, 5)
    
    def _get_primary_intent(self, intents: List[Dict[str, Any]]) -> str:
        """Get the primary intent based on confidence and priority"""
        if not intents:
            return "unknown"
        
        # Sort by confidence first (descending), then by priority (ascending)
        sorted_intents = sorted(
            intents,
            key=lambda x: (x["confidence"], -x["priority"]),
            reverse=True
        )
        
        return sorted_intents[0]["intent"]
            
        
# Keep the old class for backward compatibility
class EnhancedIntentClassifier(AIIntentClassifier):
    """Backward compatibility alias"""
    pass 