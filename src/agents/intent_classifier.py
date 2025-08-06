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
from src.utils.burmese_processor import detect_burmese_intent_patterns, get_burmese_cultural_context
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.api_client import get_openai_client, get_fallback_manager, QuotaExceededError, APIClientError

logger = get_logger("ai_intent_classifier")


class AIIntentClassifier(BaseAgent):
    """
    AI-powered intent classifier using OpenAI for dynamic classification
    """
    
    def __init__(self):
        """Initialize AI intent classifier"""
        super().__init__("ai_intent_classifier")
        self.settings = get_settings()
        
        # Initialize robust API client
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        
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
8. job_application - User is asking about job opportunities, employment, or career
9. goodbye - User is ending the conversation or saying thank you
10. unknown - Cannot determine intent

BURMESE LANGUAGE PATTERNS:
For Burmese language, pay special attention to these patterns:

GREETING PATTERNS:
- "မင်္ဂလာ", "ဟယ်လို", "ဟေး", "အစ်ကို", "အစ်မ", "ဦးလေး", "အမေကြီး"
- "ဘယ်လိုလဲ", "ဘယ်လိုရှိလဲ", "ဘယ်လိုနေလဲ"

MENU BROWSE PATTERNS:
- "မီနူး", "အစားအစာ", "ဘာတွေ ရှိလဲ", "ဘာတွေ စားလို့ရလဲ"
- "ခေါက်ဆွဲ", "ဘာဂါ", "ပီဇာ", "ကြက်သား", "ငါး", "ဟင်းရည်"
- "ဘယ်လို [food] တွေ ရှိလဲ", "[food] ဘာတွေ ရှိလဲ"

FAQ PATTERNS:
- "ဘယ်မှာ", "လိပ်စာ", "ဖုန်းနံပါတ်", "ဖွင့်ချိန်", "ဈေးနှုန်း"
- "ဘယ်လို", "ဘာကြောင့်", "ဘယ်အချိန်", "ဘယ်နေရာ"

ORDER PATTERNS:
- "မှာယူ", "အမှာယူ", "ဝယ်ယူ", "အော်ဒါ", "ပြင်ဆင်ပေး"

RESERVATION PATTERNS:
- "ကြိုတင်မှာယူ", "စားပွဲကြို", "ဘွတ်ကင်", "ကြိုတင်စီစဉ်"

JOB APPLICATION PATTERNS:
- "အလုပ်", "အလုပ်လျှောက်", "အလုပ်လျှောက်လို့ရလား", "အလုပ်ရှိလား", "အလုပ်ခန့်လား"
- "အလုပ်လုပ်ချင်တယ်", "အလုပ်လျှောက်ချင်တယ်", "အလုပ်အကိုင်ရှိလား"

EVENTS PATTERNS:
- "ပွဲ", "ဖျော်ဖြေရေး", "ဂီတ", "ပြပွဲ", "အထူးအစီအစဉ်"

GOODBYE PATTERNS:
- "ကျေးဇူးတင်ပါတယ်", "ပြန်လာမယ်", "သွားပါတယ်", "နှုတ်ဆက်ပါတယ်"

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
        
        # For Burmese, also use pattern-based classification as backup
        if state["user_language"] in ["my", "myanmar"]:
            burmese_patterns = detect_burmese_intent_patterns(user_message)
            cultural_context = get_burmese_cultural_context(user_message)
            
            # If AI classification has low confidence, use pattern-based
            if intents and intents[0].get("confidence", 0) < 0.6:
                for intent_type, confidence in burmese_patterns.items():
                    if confidence > 0.5:
                        intents = [{
                            "intent": intent_type,
                            "confidence": confidence,
                            "entities": {},
                            "reasoning": f"Burmese pattern-based classification: {intent_type}",
                            "priority": self._get_priority(intent_type)
                        }]
                        break
            
            # Add cultural context to state
            state["burmese_cultural_context"] = cultural_context
        
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
        """Classify intents using AI with robust error handling"""
        try:
            # Check cache first
            cache_key = f"intent_{language}_{hash(user_message)}"
            cached_result = await self.fallback_manager.get_cached_response(cache_key)
            if cached_result and self.fallback_manager.is_cache_valid(cache_key):
                logger.info("using_cached_intent_classification", cache_key=cache_key)
                return [cached_result]
            
            # Prepare prompt
            prompt = self.intent_prompt.format(
                user_message=user_message,
                language=language
            )
            
            # Get AI response using robust API client
            try:
                response = await self.api_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are an intent classifier for a restaurant chatbot."},
                        {"role": "user", "content": prompt}
                    ],
                    model="gpt-4o",
                    temperature=0.1,
                    max_tokens=200
                )
                response_text = response.choices[0].message.content.strip()
                
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
                    
                    # Cache the result
                    await self.fallback_manager.cache_response(cache_key, intent_data, ttl=1800)  # 30 minutes
                    
                    return [intent_data]
                    
                except json.JSONDecodeError as e:
                    logger.error("ai_response_parse_error", error=str(e), response=response_text)
                    return self._fallback_classification(user_message, language)
                    
            except QuotaExceededError as e:
                logger.error("openai_quota_exceeded_fallback", error=str(e))
                return self._fallback_classification(user_message, language)
            except APIClientError as e:
                logger.error("openai_api_error_fallback", error=str(e))
                return self._fallback_classification(user_message, language)
                
        except Exception as e:
            logger.error("ai_classification_failed", error=str(e))
            return self._fallback_classification(user_message, language)
    
    def _fallback_classification(self, message: str, language: str) -> List[Dict[str, Any]]:
        """Fallback classification when AI fails"""
        # Use the fallback manager for consistent fallback logic
        fallback_result = self.fallback_manager.get_fallback_intent(message, language)
        
        # Add priority based on intent
        fallback_result["priority"] = self._get_priority(fallback_result["intent"])
        
        return [fallback_result]
    
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