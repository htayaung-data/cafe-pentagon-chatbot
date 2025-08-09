"""
Simple Analysis Node for LangGraph
Ultra-simple LLM-based analysis without intent classification
Single LLM call to determine language, search terms, and response strategy
"""

import json
import re
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.api_client import get_openai_client, get_fallback_manager, QuotaExceededError, APIClientError

logger = get_logger("simple_analysis_node")


class SimpleAnalysisNode:
    """
    Simple analysis node that uses a single LLM call for comprehensive analysis
    No intent classification - just language detection, search terms, and response strategy
    """
    
    def __init__(self):
        """Initialize simple analysis node"""
        self.settings = get_settings()
        
        # Initialize robust API client
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        
        # Initialize OpenAI model for analysis
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=0.1,  # Low temperature for consistent analysis
            api_key=self.settings.openai_api_key
        )
        
        # Simple analysis prompt - no intent classification
        self.analysis_prompt = """
You are a simple analysis system for a restaurant chatbot. Analyze the user's message and provide search guidance.

ANALYSIS TASK:
Analyze the user's message and determine:
1. What language is this message in?
2. What English search terms should I use to find relevant information?
3. Which database namespace should I search (menu, faq, events, jobs)?
4. What response strategy should I use?

USER MESSAGE: {user_message}

CONVERSATION HISTORY:
{conversation_history}

NAMESPACE GUIDELINES:
- menu: Food, drinks, dishes, menu items, prices, ingredients
- faq: Location, hours, contact, policies, services, general questions
- events: Events, promotions, entertainment, special offers
- jobs: Employment, job opportunities, hiring, careers

RESPONSE STRATEGIES:
- direct_answer: For greetings, goodbyes, thanks - respond directly
- search_and_answer: For questions that need database lookup
- polite_fallback: When unsure or no relevant data found

IMPORTANT RULES:
- Always provide English search terms for database lookup
- For Burmese text, translate key concepts to English for search
- Be specific with search terms to find relevant content
- If unsure about namespace, default to "faq"
- For greetings/goodbyes, use "direct_answer" strategy

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{{
  "user_language": "my|en|mixed",
  "search_terms": ["term1", "term2", "term3"],
  "search_namespace": "menu|faq|events|jobs",
  "response_strategy": "direct_answer|search_and_answer|polite_fallback",
  "confidence": 0.0-1.0
}}

EXAMPLES:

User: "မင်္ဂလာ"
Response: {{
  "user_language": "my",
  "search_terms": [],
  "search_namespace": null,
  "response_strategy": "direct_answer",
  "confidence": 0.9
}}

User: "ဆိုင်ဘယ်မှာလဲ"
Response: {{
  "user_language": "my", 
  "search_terms": ["location", "address", "where"],
  "search_namespace": "faq",
  "response_strategy": "search_and_answer",
  "confidence": 0.9
}}

User: "What's on the menu?"
Response: {{
  "user_language": "en",
  "search_terms": ["menu", "food", "dishes", "items"],
  "search_namespace": "menu", 
  "response_strategy": "search_and_answer",
  "confidence": 0.9
}}

User: "ဘာတွေစားလို့ရလဲ"
Response: {{
  "user_language": "my",
  "search_terms": ["menu", "food", "dishes", "what to eat"],
  "search_namespace": "menu",
  "response_strategy": "search_and_answer", 
  "confidence": 0.9
}}

RESPONSE:"""

        logger.info("simple_analysis_node_initialized")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform simple analysis of user message
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with analysis results
        """
        user_message = state.get("user_message", "")
        conversation_history = state.get("conversation_history", [])
        
        if not user_message:
            logger.warning("empty_user_message")
            return self._set_default_analysis(state)
        
        try:
            # Perform simple analysis
            if self.settings.test_mode:
                # Deterministic analysis for tests
                analysis_result = self._fallback_analysis(user_message, conversation_history)
            else:
                analysis_result = await self._perform_simple_analysis(user_message, conversation_history)
            
            # Update state with analysis results
            updated_state = state.copy()
            updated_state.update({
                "analysis_result": analysis_result,
                "user_language": analysis_result.get("user_language", "en"),
                "search_terms": analysis_result.get("search_terms", []),
                "search_namespace": analysis_result.get("search_namespace"),
                "response_strategy": analysis_result.get("response_strategy", "polite_fallback"),
                "analysis_confidence": analysis_result.get("confidence", 0.0)
            })
            
            # Log analysis results
            logger.info("simple_analysis_completed",
                       user_message=user_message[:100],
                       user_language=analysis_result.get("user_language"),
                       search_terms=analysis_result.get("search_terms"),
                       search_namespace=analysis_result.get("search_namespace"),
                       response_strategy=analysis_result.get("response_strategy"),
                       confidence=analysis_result.get("confidence"))
            
            return updated_state
            
        except Exception as e:
            logger.error("simple_analysis_failed",
                        error=str(e),
                        user_message=user_message[:100])
            
            # Fallback to default analysis
            return self._set_default_analysis(state)

    async def _perform_simple_analysis(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform simple analysis using LLM
        
        Args:
            user_message: User's input message
            conversation_history: Previous conversation context
            
        Returns:
            Analysis result dictionary
        """
        try:
            # Check cache first
            cache_key = f"simple_analysis_{hash(user_message + str(conversation_history))}"
            cached_result = await self.fallback_manager.get_cached_response(cache_key)
            if cached_result:
                # Additional validation of cached result
                if self._validate_cached_analysis_result(cached_result):
                    logger.info("using_cached_simple_analysis", cache_key=cache_key)
                    return cached_result
                else:
                    logger.warning("invalid_cached_analysis_result", cache_key=cache_key)
                    # Remove invalid cache entry
                    await self.fallback_manager.cache_response(cache_key, {}, ttl=1)
            
            # Prepare conversation context
            conversation_context = self._create_conversation_context(conversation_history)
            
            # Prepare prompt
            prompt = self.analysis_prompt.format(
                user_message=user_message,
                conversation_history=conversation_context
            )
            
            # Get LLM analysis
            try:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=prompt)])
                response_text = response.content.strip()
                
                # Parse JSON response
                analysis_result = self._parse_analysis_response(response_text)
                
                # Validate and enhance analysis
                analysis_result = self._validate_and_enhance_analysis(analysis_result, user_message)
                
                # Cache the result
                await self.fallback_manager.cache_response(cache_key, analysis_result, ttl=1800)  # 30 minutes
                
                return analysis_result
                
            except QuotaExceededError as e:
                logger.error("openai_quota_exceeded_fallback", error=str(e))
                return self._fallback_analysis(user_message, conversation_history)
            except APIClientError as e:
                logger.error("openai_api_error_fallback", error=str(e))
                return self._fallback_analysis(user_message, conversation_history)
                
        except Exception as e:
            logger.error("simple_analysis_llm_failed", error=str(e))
            return self._fallback_analysis(user_message, conversation_history)

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract JSON
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed analysis result
        """
        try:
            # Clean response text
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
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
            
            # Parse JSON
            result = json.loads(cleaned_response)
            
            # Ensure all required fields are present
            return self._ensure_required_fields(result)
            
        except json.JSONDecodeError as e:
            logger.error("analysis_response_parse_error", error=str(e), response=response_text)
            raise ValueError(f"Failed to parse analysis response: {str(e)}")

    def _ensure_required_fields(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all required fields are present in analysis result
        
        Args:
            result: Parsed analysis result
            
        Returns:
            Result with all required fields
        """
        # Default values for required fields
        defaults = {
            "user_language": "en",
            "search_terms": [],
            "search_namespace": None,
            "response_strategy": "polite_fallback",
            "confidence": 0.5
        }
        
        # Merge with defaults
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
        
        # Ensure confidence is within bounds
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
        
        return result

    def _validate_and_enhance_analysis(self, analysis_result: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """
        Validate and enhance analysis with additional context
        
        Args:
            analysis_result: Analysis result from LLM
            user_message: Original user message
            
        Returns:
            Enhanced analysis result
        """
        # Force Burmese detection if text contains Burmese characters
        if self._contains_burmese_text(user_message):
            analysis_result["user_language"] = "my"
            logger.info("forced_burmese_detection_in_analysis", user_message=user_message[:50])
        
        # Ensure search terms are provided for search_and_answer strategy
        if analysis_result["response_strategy"] == "search_and_answer" and not analysis_result["search_terms"]:
            # Generate basic search terms based on message
            analysis_result["search_terms"] = self._generate_basic_search_terms(user_message)
            logger.info("generated_basic_search_terms", search_terms=analysis_result["search_terms"])
        
        return analysis_result
    
    def _contains_burmese_text(self, text: str) -> bool:
        """
        Check if text contains Burmese characters
        """
        burmese_chars = set("ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအဣဤဥဦဧဨဩဪါာိီုူေဲဳဴဵံ့း္်ျြွှဿ၀၁၂၃၄၅၆၇၈၉၏ၐၑၒၓၔၕၖၗၘၙၚၛၜၝၞၟၠၡၢၣၤၥၦၧၨၩၪၫၬၭၮၯၰၱၲၳၴၵၶၷၸၹၺၻၼၽၾၿႀႁႂႃႄႅႆႇႈႉႊႋႌႍႎႏ႐႑႒႓႔႕႖႗႘႙ႚႛႜႝ႞႟ႠႡႢႣႤႥႦႧႨႩႪႫႬႭႮႯႰႱႲႳႴႵႶႷႸႹႺႻႼႽႾႿ")
        return any(char in burmese_chars for char in text)

    def _generate_basic_search_terms(self, user_message: str) -> List[str]:
        """
        Generate basic search terms when LLM doesn't provide them
        """
        # Simple keyword extraction for common patterns
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["မီနူး", "အစားအစာ", "ဘာတွေ", "စားလို့ရ"]):
            return ["menu", "food", "dishes"]
        elif any(word in message_lower for word in ["လိပ်စာ", "ဘယ်မှာ", "တည်နေရာ"]):
            return ["location", "address", "where"]
        elif any(word in message_lower for word in ["အချိန်", "ဖွင့်ချိန်", "ပိတ်ချိန်"]):
            return ["hours", "opening", "time"]
        elif any(word in message_lower for word in ["ဖုန်း", "ဆက်သွယ်", "ဖုန်းနံပါတ်"]):
            return ["phone", "contact", "number"]
        else:
            return ["general", "information"]

    def _create_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Create conversation context string for LLM analysis
        
        Args:
            conversation_history: List of previous messages
            
        Returns:
            Formatted conversation context
        """
        if not conversation_history:
            return "No previous conversation history."
        
        context_parts = []
        for i, message in enumerate(conversation_history[-3:], 1):  # Last 3 messages
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            context_parts.append(f"Message {i} ({role}): {content}")
        
        return "\n".join(context_parts)

    def _fallback_analysis(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback analysis when LLM fails
        
        Args:
            user_message: User message
            conversation_history: Conversation history
            
        Returns:
            Fallback analysis result
        """
        # Check for Burmese text first
        if self._contains_burmese_text(user_message):
            user_language = "my"
        else:
            user_language = "en"
        
        # Simple keyword-based fallback
        message_lower = user_message.lower()
        
        # Check for greetings/goodbyes
        greeting_words = ["hello", "hi", "မင်္ဂလာ", "ဟယ်လို", "ဟေး"]
        goodbye_words = ["bye", "goodbye", "thanks", "thank you", "ကျေးဇူးတင်ပါတယ်", "ဘိုင်"]
        
        if any(word in message_lower for word in greeting_words + goodbye_words):
            return {
                "user_language": user_language,
                "search_terms": [],
                "search_namespace": None,
                "response_strategy": "direct_answer",
                "confidence": 0.7
            }
        
        # Default to FAQ search
        return {
            "user_language": user_language,
            "search_terms": ["general", "information"],
            "search_namespace": "faq",
            "response_strategy": "search_and_answer",
            "confidence": 0.3
        }

    def _validate_cached_analysis_result(self, cached_result: Dict[str, Any]) -> bool:
        """
        Validate cached analysis result structure and content
        
        Args:
            cached_result: Cached analysis result
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if it's a dictionary
            if not isinstance(cached_result, dict):
                return False
            
            # Check required fields
            required_fields = ["user_language", "search_terms", "search_namespace", "response_strategy", "confidence"]
            for field in required_fields:
                if field not in cached_result:
                    return False
                if cached_result[field] is None:
                    return False
            
            # Validate specific field types
            if not isinstance(cached_result.get("search_terms"), list):
                return False
            if not isinstance(cached_result.get("confidence"), (int, float)):
                return False
            
            # Validate language values
            valid_languages = ["en", "my", "mixed"]
            if cached_result.get("user_language") not in valid_languages:
                return False
            
            # Validate strategy values
            valid_strategies = ["direct_answer", "search_and_answer", "polite_fallback"]
            if cached_result.get("response_strategy") not in valid_strategies:
                return False
            
            return True
            
        except Exception as e:
            logger.error("cached_analysis_validation_failed", error=str(e))
            return False

    def _set_default_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
                    """
                    Set default analysis when processing fails
                    
                    Args:
                        state: Current state
                        
                    Returns:
                        State with default analysis
                    """
                    user_message = state.get("user_message", "")
                    
                    # Check for Burmese text
                    if self._contains_burmese_text(user_message):
                        user_language = "my"
                    else:
                        user_language = "en"
                    
                    default_analysis = {
                        "user_language": user_language,
                        "search_terms": ["general", "information"],
                        "search_namespace": "faq",
                        "response_strategy": "search_and_answer",
                        "confidence": 0.3
                    }
                    
                    updated_state = state.copy()
                    updated_state.update({
                        "analysis_result": default_analysis,
                        "user_language": default_analysis["user_language"],
                        "search_terms": default_analysis["search_terms"],
                        "search_namespace": default_analysis["search_namespace"],
                        "response_strategy": default_analysis["response_strategy"],
                        "analysis_confidence": default_analysis["confidence"]
                    })
                    
                    return updated_state
