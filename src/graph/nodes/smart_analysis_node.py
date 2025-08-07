"""
Smart Analysis Node for LangGraph
Replaces Pattern Matcher + Intent Classifier with comprehensive LLM analysis
Enhanced Burmese language understanding with cultural context awareness
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.api_client import get_openai_client, get_fallback_manager, QuotaExceededError, APIClientError
from src.utils.language import detect_language, is_burmese_text
from src.utils.burmese_processor import detect_burmese_language, get_burmese_cultural_context

logger = get_logger("smart_analysis_node")


class SmartAnalysisNode:
    """
    Smart analysis node that combines pattern matching and intent classification
    Uses a single LLM call for comprehensive analysis with enhanced Burmese support
    """
    
    def __init__(self):
        """Initialize smart analysis node"""
        self.settings = get_settings()
        
        # Initialize robust API client
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        
        # Initialize OpenAI model for analysis
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,  # Low temperature for consistent analysis
            api_key=self.settings.openai_api_key
        )
        
        # Comprehensive analysis prompt
        self.analysis_prompt = """
You are a smart analysis system for a restaurant chatbot. Analyze the user's message comprehensively and provide detailed analysis for decision making.

ANALYSIS TASK:
Analyze the user's message and provide a complete analysis including language detection, intent classification, search requirements, and cultural context.

USER MESSAGE: {user_message}

CONVERSATION HISTORY:
{conversation_history}

LANGUAGE DETECTION:
- Detect if the message is in Burmese, English, or mixed language
- Consider cultural context and formality levels

INTENT CLASSIFICATION:
Classify the primary intent from these categories:
1. greeting - User is greeting or starting conversation
2. goodbye - User is ending conversation or saying thank you
3. menu_browse - User wants to see menu, food options, browse dishes
4. order_place - User wants to place an order or buy food
5. reservation - User wants to make reservation or book table
6. faq - User asking about services, location, hours, policies
7. events - User asking about events, promotions, entertainment
8. complaint - User expressing dissatisfaction or problems
9. job_application - User asking about job opportunities, employment
10. human_assistance - User requesting to speak with human staff, responsible person, or live agent
11. unknown - Cannot determine intent

SEARCH REQUIREMENTS:
Determine if the query requires searching the database:
- requires_search: true/false
- namespace: "menu", "faq", "jobs" (if search needed)
- keywords: relevant search terms
- semantic_query: English translation for search

BURMESE LANGUAGE PATTERNS:
Pay special attention to these Burmese patterns:

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

HUMAN ASSISTANCE PATTERNS:
- "တာဝန်ရှိသူ", "ဝန်ထမ်း", "လူသား", "သူငယ်ချင်း", "အစ်ကို", "အစ်မ"
- "ဒီမှာပဲ ပြောလို့ ရလား", "စကားပြောလို့ ရလား", "ပြောချင်တယ်"
- "ကူညီပေးပါ", "ရှင်းပြပေးပါ", "အကူအညီ လိုအပ်ပါတယ်"
- "လူနဲ့ စကားပြောချင်တယ်", "လူသားနဲ့ စကားပြောချင်တယ်"

CULTURAL CONTEXT:
Analyze cultural context for Burmese:
- formality_level: "casual", "formal", "very_formal"
- uses_honorifics: true/false
- language_mix: "burmese_only", "mixed", "english_only"

CONVERSATION CONTEXT:
- is_follow_up: Is this a follow-up question?
- previous_intent: What was the previous intent?
- clarification_needed: Does user need clarification?

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{{
  "detected_language": "my|en|mixed",
  "primary_intent": "intent_name",
  "intent_confidence": 0.0-1.0,
  "requires_search": true/false,
  "search_context": {{
    "namespace": "menu|faq|jobs|null",
    "keywords": ["keyword1", "keyword2"],
    "semantic_query": "English translation for search"
  }},
  "cultural_context": {{
    "formality_level": "casual|formal|very_formal",
    "uses_honorifics": true/false,
    "language_mix": "burmese_only|mixed|english_only"
  }},
  "conversation_context": {{
    "is_follow_up": true/false,
    "previous_intent": "previous_intent|null",
    "clarification_needed": true/false
  }}
}}

IMPORTANT: 
- For Burmese queries, provide detailed cultural context
- For ambiguous queries like "ဘာ", consider conversation history
- Ensure all confidence scores are between 0.0 and 1.0
- Use null for optional fields when not applicable

RESPONSE:"""

        logger.info("smart_analysis_node_initialized")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of user message
        
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
            # Perform comprehensive analysis
            analysis_result = await self._perform_smart_analysis(user_message, conversation_history)
            
            # Update state with analysis results
            updated_state = state.copy()
            updated_state.update({
                "analysis_result": analysis_result,
                "detected_language": analysis_result.get("detected_language", "en"),
                "primary_intent": analysis_result.get("primary_intent", "unknown"),
                "intent_confidence": analysis_result.get("intent_confidence", 0.0),
                "requires_search": analysis_result.get("requires_search", False),
                "search_context": analysis_result.get("search_context", {}),
                "cultural_context": analysis_result.get("cultural_context", {}),
                "conversation_context": analysis_result.get("conversation_context", {}),
                "target_namespace": analysis_result.get("search_context", {}).get("namespace", "faq")
            })
            
            # Log analysis results
            logger.info("smart_analysis_completed",
                       user_message=user_message[:100],
                       detected_language=analysis_result.get("detected_language"),
                       primary_intent=analysis_result.get("primary_intent"),
                       intent_confidence=analysis_result.get("intent_confidence"),
                       requires_search=analysis_result.get("requires_search"),
                       namespace=analysis_result.get("search_context", {}).get("namespace"))
            
            return updated_state
            
        except Exception as e:
            logger.error("smart_analysis_failed",
                        error=str(e),
                        user_message=user_message[:100])
            
            # Fallback to default analysis
            return self._set_default_analysis(state)

    async def _perform_smart_analysis(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis using LLM
        
        Args:
            user_message: User's input message
            conversation_history: Previous conversation context
            
        Returns:
            Analysis result dictionary
        """
        try:
            # Check cache first
            cache_key = f"smart_analysis_{hash(user_message + str(conversation_history))}"
            cached_result = await self.fallback_manager.get_cached_response(cache_key)
            if cached_result and self.fallback_manager.is_cache_valid(cache_key):
                logger.info("using_cached_smart_analysis", cache_key=cache_key)
                return cached_result
            
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
            logger.error("smart_analysis_llm_failed", error=str(e))
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
            "detected_language": "en",
            "primary_intent": "unknown",
            "intent_confidence": 0.5,
            "requires_search": False,
            "search_context": {
                "namespace": None,
                "keywords": [],
                "semantic_query": ""
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "english_only"
            },
            "conversation_context": {
                "is_follow_up": False,
                "previous_intent": None,
                "clarification_needed": False
            }
        }
        
        # Merge with defaults
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
            elif isinstance(default_value, dict) and isinstance(result[key], dict):
                for sub_key, sub_default in default_value.items():
                    if sub_key not in result[key]:
                        result[key][sub_key] = sub_default
        
        # Ensure confidence is within bounds
        result["intent_confidence"] = max(0.0, min(1.0, float(result["intent_confidence"])))
        
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
        # Enhance language detection
        if analysis_result["detected_language"] == "my":
            # Use existing Burmese processor for additional context
            burmese_analysis = detect_burmese_language(user_message)
            cultural_context = get_burmese_cultural_context(user_message)
            
            # Enhance cultural context
            analysis_result["cultural_context"].update({
                "burmese_confidence": burmese_analysis.get("confidence", 0.0),
                "burmese_character_count": burmese_analysis.get("burmese_character_count", 0),
                "pattern_matches": burmese_analysis.get("pattern_matches", 0)
            })
            
            # Merge cultural context
            for key, value in cultural_context.items():
                if key not in analysis_result["cultural_context"]:
                    analysis_result["cultural_context"][key] = value
        
        return analysis_result

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
        for i, message in enumerate(conversation_history[-5:], 1):  # Last 5 messages
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            context_parts.append(f"Message {i} ({role}): {content}")
            if timestamp:
                context_parts.append(f"Time: {timestamp}")
        
        return "\n".join(context_parts)

    def _fallback_analysis(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback analysis when LLM fails - NO PATTERN MATCHING
        
        Args:
            user_message: User message
            conversation_history: Conversation history
            
        Returns:
            Fallback analysis result with basic defaults
        """
        # Only use basic language detection, no pattern matching
        detected_lang = detect_language(user_message)
        
        # Return basic default analysis without any pattern matching
        return {
            "detected_language": detected_lang,
            "primary_intent": "unknown",
            "intent_confidence": 0.0,
            "requires_search": False,
            "search_context": {
                "namespace": None,
                "keywords": [],
                "semantic_query": ""
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "burmese_only" if detected_lang == "my" else "english_only"
            },
            "conversation_context": {
                "is_follow_up": len(conversation_history) > 0,
                "previous_intent": None,
                "clarification_needed": False
            }
        }

    def _set_default_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default analysis when processing fails
        
        Args:
            state: Current state
            
        Returns:
            State with default analysis
        """
        default_analysis = {
            "detected_language": "en",
            "primary_intent": "unknown",
            "intent_confidence": 0.0,
            "requires_search": False,
            "search_context": {
                "namespace": None,
                "keywords": [],
                "semantic_query": ""
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "english_only"
            },
            "conversation_context": {
                "is_follow_up": False,
                "previous_intent": None,
                "clarification_needed": False
            }
        }
        
        updated_state = state.copy()
        updated_state.update({
            "analysis_result": default_analysis,
            "detected_language": default_analysis["detected_language"],
            "primary_intent": default_analysis["primary_intent"],
            "intent_confidence": default_analysis["intent_confidence"],
            "requires_search": default_analysis["requires_search"],
            "search_context": default_analysis["search_context"],
            "cultural_context": default_analysis["cultural_context"],
            "conversation_context": default_analysis["conversation_context"],
            "target_namespace": default_analysis["search_context"]["namespace"] or "faq"
        })
        
        return updated_state
