"""
Contextual Response Node for LangGraph
Generates responses in user's language using real data from search results
Handles different response strategies: direct_answer, search_and_answer, polite_fallback
"""

import json
import re
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.api_client import get_openai_client, get_fallback_manager, QuotaExceededError, APIClientError

logger = get_logger("contextual_response_node")


class ContextualResponseNode:
    """
    Contextual response node that generates responses in user's language
    Uses real data from search results, not AI-generated content
    """
    
    def __init__(self):
        """Initialize contextual response node"""
        self.settings = get_settings()
        
        # Initialize robust API client
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        
        # Initialize OpenAI model for response generation
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=0.3,  # Slightly higher for more natural responses
            api_key=self.settings.openai_api_key
        )
        
        # Response generation prompt
        self.response_prompt = """
You are a helpful restaurant chatbot assistant. Generate a natural, contextual response in the user's language using the provided data.

USER MESSAGE: {user_message}
USER LANGUAGE: {user_language}
RESPONSE STRATEGY: {response_strategy}

SEARCH RESULTS:
{search_results}

RESPONSE GUIDELINES:
1. Respond in the user's language (English or Burmese)
2. Use ONLY the provided search results data - do not make up information
3. Be natural, friendly, and helpful
4. Keep responses concise but informative
5. If no relevant data found, provide a polite fallback response

RESPONSE STRATEGIES:
- direct_answer: For greetings, goodbyes, thanks - respond naturally
- search_and_answer: Use search results to answer the user's question
- polite_fallback: When no relevant data found, provide helpful fallback

BURMESE RESPONSE GUIDELINES:
- Use appropriate formality level
- Include honorifics when appropriate
- Be culturally sensitive
- Use natural Burmese expressions
 - Before finalizing, briefly self-check tone for naturalness and politeness; avoid overly literal translations
- STRICT STYLE RULES:
- Do NOT use pronouns: "ငါ", "သင်", "မင်း", "ကျွန်ုပ်"
- Do NOT use formal endings: "သည်", "မည်"
- Keep it concise (1-3 short sentences) and non-redundant
- Prefer polite, neutral endings like "...ပါ", "...ပေးပါ", avoid overuse of filler words

ENGLISH RESPONSE GUIDELINES:
- Be friendly and professional
- Use clear, simple language
- Provide helpful information

IMPORTANT:
- NEVER make up information not in the search results
- If search results are empty or irrelevant, use polite_fallback strategy
- Always respond in the user's language
- Be helpful and informative

Generate a natural response:"""

        # Fallback response templates
        self.fallback_responses = {
            "my": {
                "greeting": "မင်္ဂလာပါ! Cafe Pentagon မှ ကြိုဆိုပါတယ်။ ဘယ်လိုကူညီပေးရမလဲခင်ဗျာ?",
                "goodbye": "ကျေးဇူးတင်ပါတယ်။ ပြန်လည်လာရောက်လည်ပတ်ပေးပါ။",
                "thanks": "ကျေးဇူးတင်ပါတယ်။ နောက်ထပ်မေးခွန်းရှိရင် မေးနိုင်ပါတယ်။",
                "no_data": "ဆောင်းပါးများကို ရှာဖွေနေပါတယ်။ နောက်ထပ်မေးခွန်းတစ်ခုခု မေးနိုင်ပါတယ်။",
                "general": "ကျေးဇူးပြု၍ နောက်ထပ်မေးခွန်းတစ်ခုခု မေးနိုင်ပါတယ်။"
            },
            "en": {
                "greeting": "Hello! Welcome to Cafe Pentagon. How can I help you today?",
                "goodbye": "Thank you for visiting. Please come back again!",
                "thanks": "You're welcome! Feel free to ask if you have any other questions.",
                "no_data": "I'm searching for information. Please try asking another question.",
                "general": "Please feel free to ask another question."
            }
        }

        logger.info("contextual_response_node_initialized")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate contextual response based on search results and user language
        
        Args:
            state: Current conversation state with search results
            
        Returns:
            Updated state with generated response
        """
        user_message = state.get("user_message", "")
        user_language = state.get("user_language", "en")
        response_strategy = state.get("response_strategy", "polite_fallback")
        search_results = state.get("search_results", [])
        data_found = state.get("data_found", False)
        
        # Check if HITL has already generated a response
        requires_human = state.get("requires_human", False)
        human_handling = state.get("human_handling", False)
        escalation_blocked = state.get("escalation_blocked", False)
        
        if not user_message:
            logger.warning("empty_user_message_in_contextual_response")
            return self._set_default_response(state)
        
        # If HITL has blocked response generation, return state unchanged
        if escalation_blocked:
            logger.info("hitl_response_blocked", 
                       requires_human=requires_human,
                       human_handling=human_handling,
                       escalation_blocked=escalation_blocked)
            return state
        
        # For escalated conversations, generate contextual response but add escalation note
        if requires_human and not human_handling:
            logger.info("generating_response_for_escalated_conversation", 
                       user_message=user_message[:100])
            
            try:
                # Generate contextual response
                response = await self._generate_contextual_response(
                    user_message, user_language, response_strategy, search_results, data_found
                )
                
                # Add escalation note to response
                escalation_note = self._get_escalation_note(user_language)
                full_response = f"{response}\n\n{escalation_note}"
                
                # Update state with response
                updated_state = state.copy()
                updated_state.update({
                    "response": full_response,
                    "response_language": user_language,
                    "response_generated": True,
                    "response_quality": "contextual_with_escalation"
                })
                
                return updated_state
                
            except Exception as e:
                logger.error("escalated_response_generation_failed", error=str(e))
                return self._set_default_response(state)
        
        # For non-escalated conversations, generate normal response
        try:
            # Generate contextual response
            response = await self._generate_contextual_response(
                user_message, user_language, response_strategy, search_results, data_found
            )
            
            # Update state with response
            updated_state = state.copy()
            updated_state.update({
                "response": response,
                "response_language": user_language,
                "response_generated": True,
                "response_quality": "contextual"
            })
            
            # Log response generation
            logger.info("contextual_response_generated",
                       user_message=user_message[:100],
                       user_language=user_language,
                       response_strategy=response_strategy,
                       data_found=data_found,
                       response_length=len(response))
            
            return updated_state
            
        except Exception as e:
            logger.error("contextual_response_failed",
                        error=str(e),
                        user_message=user_message[:100])
            
            # Fallback to default response
            return self._set_default_response(state)

    async def _generate_contextual_response(self, user_message: str, user_language: str, 
                                          response_strategy: str, search_results: List[Any], 
                                          data_found: bool) -> str:
        """
        Generate contextual response based on strategy and data
        
        Args:
            user_message: Original user message
            user_language: User's language
            response_strategy: Response strategy
            search_results: Search results from database
            data_found: Whether relevant data was found
            
        Returns:
            Generated response in user's language
        """
        try:
            # Handle direct answer strategy (greetings, goodbyes, thanks)
            if response_strategy == "direct_answer":
                reply = self._generate_direct_response(user_message, user_language)
                if user_language == "my":
                    reply = self._polish_burmese(reply)
                return reply
            
            # Handle search and answer strategy
            if response_strategy == "search_and_answer":
                if data_found and search_results:
                    if self.settings.test_mode:
                        # Deterministic response in tests
                        reply = self._format_search_results_for_llm(search_results)[:200]
                    else:
                        reply = await self._generate_search_based_response(user_message, user_language, search_results)
                    if user_language == "my":
                        reply = self._polish_burmese(reply)
                    return reply
                else:
                    # No data found, generate contextual fallback based on user message
                    reply = self._generate_contextual_fallback(user_message, user_language)
                    if user_language == "my":
                        reply = self._polish_burmese(reply)
                    return reply
            
            # Handle polite fallback strategy
            if response_strategy == "polite_fallback":
                reply = self._generate_contextual_fallback(user_message, user_language)
                if user_language == "my":
                    reply = self._polish_burmese(reply)
                return reply
            
            # Default fallback
            reply = self._generate_fallback_response(user_language, "general")
            if user_language == "my":
                reply = self._polish_burmese(reply)
            return reply
            
        except Exception as e:
            logger.error("contextual_response_generation_failed", error=str(e))
            return self._generate_fallback_response(user_language, "general")
    
    def _generate_contextual_fallback(self, user_message: str, user_language: str) -> str:
        """
        Generate contextual fallback response based on user message content
        
        Args:
            user_message: User's message
            user_language: User's language
            
        Returns:
            Contextual fallback response
        """
        if user_language == "my":
            # Check for waiting-related questions
            if any(word in user_message for word in ["စောင့်", "ကြာ", "ဘယ်လောက်ကြာ"]):
                return "ကျေးဇူးပြုပါ။ ခဏသာ စောင့်ပေးပါ။ ဝန်ထမ်းမှ မကြာခင် ဆက်သွယ်ပေးပါမယ်။"
            
            # Check for questions about previous messages
            elif any(word in user_message for word in ["မေးခဲ့", "ပြောခဲ့", "ဘာတွေ", "ဘာလဲ"]):
                return "မေးခွန်းတွေ မှတ်သားထားပြီးပါပြီ။ တာဝန်ရှိသူနဲ့ အကြောင်းပြောရင် +959979732781 ကို ဖုန်းဆက်နိုင်ပါတယ်။"
            
            # Check for general questions
            elif any(word in user_message for word in ["ဘာလဲ", "ဘယ်လို", "ဘယ်မှာ", "ဘယ်အချိန်"]):
                return "နောက်ထပ်မေးခွန်း မေးနိုင်ပါတယ်။ တာဝန်ရှိသူနဲ့ ဆက်သွယ်ခင် +959979732781 ကို ဖုန်းဆက်နိုင်ပါတယ်။"
            
            # Default fallback
            else:
                return "ဆောင်းပါးများကို ရှာဖွေနေပါတယ်။ နောက်ထပ်မေးခွန်းတစ်ခုခု မေးနိုင်ပါတယ်။"
        else:
            # Check for waiting-related questions
            if any(word in user_message.lower() for word in ["wait", "long", "how long", "when"]):
                return "Please wait patiently. Our staff will contact you shortly."
            
            # Check for questions about previous messages
            elif any(word in user_message.lower() for word in ["asked", "said", "what", "told"]):
                return "We have noted your questions. To speak with a staff member, please call +959979732781."
            
            # Check for general questions
            elif any(word in user_message.lower() for word in ["what", "how", "where", "when"]):
                return "Please feel free to ask another question. To speak with a staff member, please call +959979732781."
            
            # Default fallback
            else:
                return "I'm searching for information. Please try asking another question."

    def _generate_direct_response(self, user_message: str, user_language: str) -> str:
        """
        Generate direct response for greetings, goodbyes, thanks
        
        Args:
            user_message: User message
            user_language: User language
            
        Returns:
            Direct response
        """
        message_lower = user_message.lower()
        
        # Burmese greetings
        if user_language == "my":
            if any(word in message_lower for word in ["မင်္ဂလာ", "ဟယ်လို", "ဟေး"]):
                return self.fallback_responses["my"]["greeting"]
            elif any(word in message_lower for word in ["ဘိုင်", "သွားပါတယ်", "နှုတ်ဆက်ပါတယ်"]):
                return self.fallback_responses["my"]["goodbye"]
            elif any(word in message_lower for word in ["ကျေးဇူးတင်ပါတယ်", "ကျေးဇူး"]):
                return self.fallback_responses["my"]["thanks"]
        
        # English greetings
        elif user_language == "en":
            if any(word in message_lower for word in ["hello", "hi", "hey"]):
                return self.fallback_responses["en"]["greeting"]
            elif any(word in message_lower for word in ["bye", "goodbye", "see you"]):
                return self.fallback_responses["en"]["goodbye"]
            elif any(word in message_lower for word in ["thanks", "thank you", "thank"]):
                return self.fallback_responses["en"]["thanks"]
        
        # Default greeting
        return self.fallback_responses[user_language]["greeting"]

    async def _generate_search_based_response(self, user_message: str, user_language: str, 
                                            search_results: List[Any]) -> str:
        """
        Generate response based on search results using LLM
        
        Args:
            user_message: User message
            user_language: User language
            search_results: Search results from database
            
        Returns:
            Generated response using real data
        """
        try:
            # Check cache first
            cache_key = f"search_response_{hash(user_message + str(search_results) + user_language)}"
            cached_response = await self.fallback_manager.get_cached_response(cache_key)
            if cached_response:
                logger.info("using_cached_search_response", cache_key=cache_key)
                return cached_response
            
            # Format search results for LLM
            formatted_results = self._format_search_results_for_llm(search_results)
            
            # Prepare prompt
            prompt = self.response_prompt.format(
                user_message=user_message,
                user_language=user_language,
                response_strategy="search_and_answer",
                search_results=formatted_results
            )
            
            # Get LLM response
            try:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=prompt)])
                response_text = response.content.strip()
                
                # Clean and validate response
                cleaned_response = self._clean_llm_response(response_text)
                
                # Cache the response
                await self.fallback_manager.cache_response(cache_key, cleaned_response, ttl=1800)  # 30 minutes
                
                return cleaned_response
                
            except QuotaExceededError as e:
                logger.error("openai_quota_exceeded_fallback", error=str(e))
                return self._generate_fallback_response(user_language, "no_data")
            except APIClientError as e:
                logger.error("openai_api_error_fallback", error=str(e))
                return self._generate_fallback_response(user_language, "no_data")
                
        except Exception as e:
            logger.error("search_based_response_failed", error=str(e))
            return self._generate_fallback_response(user_language, "no_data")

    def _polish_burmese(self, text: str) -> str:
        """
        Post-process Burmese text to enforce style rules:
        - Remove forbidden pronouns
        - Avoid formal endings
        - Trim redundancy and whitespace
        """
        try:
            forbidden_pronouns = ["ငါ", "သင်", "မင်း", "ကျွန်ုပ်"]
            formal_endings = ["သည်", "မည်"]
            for w in forbidden_pronouns:
                text = text.replace(w, "")
            for e in formal_endings:
                text = text.replace(e, "")
            # Simple redundancy cleanup
            text = text.replace("  ", " ").strip()
            # Keep responses concise: trim to ~300 chars while preserving sentence end
            if len(text) > 300:
                text = text[:300]
                # Try not to cut in the middle of Burmese word endings
                if "၊" in text:
                    text = text[:text.rfind("၊") + 1]
            return text
        except Exception:
            return text

    def _format_search_results_for_llm(self, search_results: List[Any]) -> str:
        """
        Format search results for LLM consumption
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted string for LLM
        """
        if not search_results:
            return "No search results available."
        
        formatted_parts = []
        for i, result in enumerate(search_results[:3], 1):  # Limit to top 3 results
            try:
                content = result.content if hasattr(result, 'content') else str(result)
                namespace = result.namespace if hasattr(result, 'namespace') else "unknown"
                score = result.relevance_score if hasattr(result, 'relevance_score') else 0.0
                
                formatted_parts.append(f"Result {i} (Namespace: {namespace}, Score: {score:.2f}):\n{content}")
                
            except Exception as e:
                logger.error("failed_to_format_search_result", error=str(e))
                continue
        
        return "\n\n".join(formatted_parts) if formatted_parts else "No search results available."

    def _clean_llm_response(self, response_text: str) -> str:
        """
        Clean and validate LLM response
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Cleaned response
        """
        # Remove markdown code blocks
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        # Remove any remaining markdown
        cleaned = re.sub(r'^\s*```\w*\s*', '', cleaned)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Ensure response is not empty
        if not cleaned:
            return "I apologize, but I couldn't generate a proper response."
        
        return cleaned

    def _generate_fallback_response(self, user_language: str, fallback_type: str) -> str:
        """
        Generate fallback response when no data found or LLM fails
        
        Args:
            user_language: User language
            fallback_type: Type of fallback response
            
        Returns:
            Fallback response
        """
        try:
            return self.fallback_responses[user_language][fallback_type]
        except KeyError:
            # Fallback to English if language not supported
            return self.fallback_responses["en"][fallback_type]

    def _set_default_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default response when processing fails
        
        Args:
            state: Current state
            
        Returns:
            State with default response
        """
        user_language = state.get("user_language", "en")
        default_response = self._generate_fallback_response(user_language, "general")
        
        updated_state = state.copy()
        updated_state.update({
            "response": default_response,
            "response_language": user_language,
            "response_generated": True,
            "response_quality": "fallback"
        })
        
        return updated_state
    
    def _get_escalation_note(self, user_language: str) -> str:
        """
        Get escalation note in user's language
        
        Args:
            user_language: User's language (en, my)
            
        Returns:
            Escalation note in appropriate language
        """
        if user_language == "my":
            return "💬 နောက်ထပ်မေးခွန်းများအတွက် +959979732781 သို့ ဖုန်းဆက်နိုင်ပါသည်။"
        else:
            return "💬 For additional questions, please call +959979732781."
