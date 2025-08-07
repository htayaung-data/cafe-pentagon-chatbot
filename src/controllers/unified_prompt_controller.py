"""
Unified Prompt Controller for Cafe Pentagon Chatbot
Single LLM call that handles intent classification, namespace routing, HITL detection, and cultural analysis
Enhanced with comprehensive structured JSON output schema and advanced prompt engineering
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from src.utils.logger import get_logger
from src.utils.api_client import get_openai_client, get_fallback_manager
from src.config.settings import get_settings
from src.controllers.advanced_prompt_engine import get_advanced_prompt_engine, PromptContext

logger = get_logger("unified_prompt_controller")


class UnifiedPromptController:
    """
    Enhanced unified prompt controller that handles all classification and routing in a single LLM call
    Features comprehensive structured JSON output with confidence scoring and multi-intent support
    """
    
    def __init__(self):
        """Initialize enhanced unified prompt controller with advanced prompt engineering"""
        self.settings = get_settings()
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        
        # Initialize Advanced Prompt Engine for context-aware prompt generation
        self.advanced_prompt_engine = get_advanced_prompt_engine()
        
        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=self.settings.openai_api_key
        )
        
        # Fallback prompt template (used only if advanced engine fails)
        self.fallback_prompt = """
You are an intelligent restaurant chatbot assistant for Cafe Pentagon. Analyze the user's message and provide a comprehensive structured response with confidence scoring and multi-intent detection.

CONTEXT:
- User Message: {user_message}
- Language: {detected_language}
- Conversation History: {conversation_history}
- Available Namespaces: faq, menu, jobs, events

TASKS:
1. Classify the user's intent (primary and secondary)
2. Determine appropriate namespaces for retrieval (primary and fallback)
3. Assess if human intervention is needed
4. Extract relevant entities with confidence scores
5. Analyze cultural context (especially for Burmese)
6. Provide detailed reasoning for all decisions

AVAILABLE INTENTS:
- greeting: User is greeting or starting conversation
- menu_browse: User wants to see menu, food options, browse dishes
- order_place: User wants to place an order or buy food
- reservation: User wants to make reservation or book table
- faq: User asking about services, location, hours, policies
- events: User asking about events, promotions, entertainment
- complaint: User expressing dissatisfaction or problems
- job_application: User asking about job opportunities, employment
- goodbye: User ending conversation or saying thank you
- unknown: Cannot determine intent

NAMESPACE MAPPING:
- faq: General questions, reservations, events, complaints
- menu: Food items, menu browsing, ordering
- jobs: Job applications, employment, careers
- events: Special events, promotions, entertainment

HITL ESCALATION TRIGGERS:
- Complex complaints or issues
- Specific requests that require human expertise
- Payment or billing questions
- Special dietary requirements
- Event booking complications
- Job application submissions

BURMESE LANGUAGE GUIDELINES:
- Pay attention to honorifics (အစ်ကို, အစ်မ, ဦးလေး, အမေကြီး)
- Consider politeness levels and formality
- Understand food vocabulary variations
- Recognize cultural expressions and context
- Handle mixed language queries appropriately

ENHANCED OUTPUT FORMAT (JSON):
{{
  "intent_analysis": {{
    "primary_intent": "string",
    "primary_confidence": 0.0-1.0,
    "secondary_intents": [
      {{
        "intent": "string",
        "confidence": 0.0-1.0,
        "reasoning": "string"
      }}
    ],
    "overall_confidence": 0.0-1.0,
    "intent_reasoning": "detailed explanation of intent classification"
  }},
  "namespace_routing": {{
    "primary_namespace": "string",
    "primary_confidence": 0.0-1.0,
    "fallback_namespaces": [
      {{
        "namespace": "string",
        "confidence": 0.0-1.0,
        "reasoning": "string"
      }}
    ],
    "routing_confidence": 0.0-1.0,
    "cross_domain_detected": boolean,
    "routing_reasoning": "detailed explanation of namespace selection"
  }},
  "hitl_assessment": {{
    "requires_human": boolean,
    "escalation_confidence": 0.0-1.0,
    "escalation_reason": "string or null",
    "escalation_urgency": "low|medium|high",
    "escalation_triggers": ["list", "of", "triggers"],
    "hitl_reasoning": "detailed explanation of HITL decision"
  }},
  "cultural_context": {{
    "formality_level": "casual|formal|very_formal",
    "uses_honorifics": boolean,
    "honorifics_detected": ["list", "of", "honorifics"],
    "cultural_nuances": ["list", "of", "nuances"],
    "language_mix": "burmese_only|english_only|mixed",
    "cultural_confidence": 0.0-1.0,
    "cultural_reasoning": "detailed explanation of cultural analysis"
  }},
  "entity_extraction": {{
    "food_items": [
      {{
        "item": "string",
        "confidence": 0.0-1.0,
        "category": "string"
      }}
    ],
    "locations": [
      {{
        "location": "string",
        "confidence": 0.0-1.0,
        "type": "restaurant|address|landmark"
      }}
    ],
    "time_references": [
      {{
        "time": "string",
        "confidence": 0.0-1.0,
        "type": "time|date|duration"
      }}
    ],
    "quantities": [
      {{
        "quantity": "string",
        "confidence": 0.0-1.0,
        "unit": "string"
      }}
    ],
    "special_requests": [
      {{
        "request": "string",
        "confidence": 0.0-1.0,
        "category": "dietary|preparation|service"
      }}
    ],
    "extraction_confidence": 0.0-1.0,
    "entity_reasoning": "detailed explanation of entity extraction"
  }},
  "response_guidance": {{
    "tone": "friendly|formal|casual|professional",
    "language": "burmese|english|mixed",
    "include_greeting": boolean,
    "include_farewell": boolean,
    "response_length": "short|medium|long",
    "priority_information": ["list", "of", "key", "points"],
    "guidance_confidence": 0.0-1.0,
    "guidance_reasoning": "detailed explanation of response guidance"
  }},
  "overall_analysis": {{
    "analysis_confidence": 0.0-1.0,
    "quality_score": 0.0-1.0,
    "fallback_required": boolean,
    "fallback_reason": "string or null",
    "processing_time_estimate": "string",
    "recommendations": ["list", "of", "recommendations"]
  }}
}}

CONFIDENCE SCORING GUIDELINES:
- 0.9-1.0: Very high confidence, clear and unambiguous
- 0.7-0.89: High confidence, mostly clear with minor ambiguity
- 0.5-0.69: Medium confidence, some ambiguity present
- 0.3-0.49: Low confidence, significant ambiguity
- 0.0-0.29: Very low confidence, highly ambiguous or unclear

FALLBACK LOGIC:
- If primary_confidence < 0.5, use fallback_namespaces
- If overall_confidence < 0.3, set fallback_required = true
- If cross_domain_detected = true, consider multiple namespaces
- If cultural_confidence < 0.4, use default cultural context

IMPORTANT: Return ONLY valid JSON. Do not include any other text or formatting.
"""

        logger.info("enhanced_unified_prompt_controller_initialized")

    async def process_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user query with enhanced unified prompt approach
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with comprehensive analysis
        """
        user_message = state.get("user_message", "")
        detected_language = state.get("detected_language", "en")
        conversation_history = state.get("conversation_history", [])
        
        if not user_message:
            logger.warning("empty_user_message")
            return self._set_default_enhanced_analysis(state)
        
        try:
            # Check cache first
            cache_key = f"enhanced_unified_{detected_language}_{hash(user_message)}"
            cached_result = await self.fallback_manager.get_cached_response(cache_key)
            
            if cached_result and self.fallback_manager.is_cache_valid(cache_key):
                logger.info("using_cached_enhanced_unified_analysis", cache_key=cache_key)
                return self._update_state_with_enhanced_analysis(state, cached_result)
            
            # Prepare conversation history for context
            history_context = self._format_conversation_history(conversation_history)
            
            # Create PromptContext for advanced prompt generation
            prompt_context = PromptContext(
                user_message=user_message,
                detected_language=detected_language,
                conversation_history=conversation_history,
                cultural_context=state.get("cultural_context", {}),
                previous_intents=self._extract_previous_intents(conversation_history),
                confidence_thresholds={
                    "high": 0.8,
                    "medium": 0.6,
                    "low": 0.4
                },
                platform=state.get("platform", "messenger"),
                user_preferences=state.get("user_preferences", {})
            )
            
            # Generate context-aware prompt using Advanced Prompt Engine
            try:
                prompt = self.advanced_prompt_engine.generate_enhanced_prompt(prompt_context)
                logger.info("advanced_prompt_generated", 
                           template_type=self.advanced_prompt_engine._determine_template_type(prompt_context))
            except Exception as e:
                logger.warning("advanced_prompt_generation_failed", error=str(e))
                # Fallback to basic prompt
                prompt = self.fallback_prompt.format(
                    user_message=user_message,
                    detected_language=detected_language,
                    conversation_history=history_context
                )
            
            # Get AI response
            try:
                response = await self.api_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are an intelligent restaurant chatbot assistant with enhanced analysis capabilities."},
                        {"role": "user", "content": prompt}
                    ],
                    model="gpt-4o",
                    temperature=0.1,
                    max_tokens=800  # Increased for comprehensive analysis
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Parse enhanced JSON response
                analysis = self._parse_enhanced_json_response(response_text)
                
                # Cache the result
                await self.fallback_manager.cache_response(cache_key, analysis, ttl=1800)
                
                # Update state with enhanced analysis
                updated_state = self._update_state_with_enhanced_analysis(state, analysis)
                
                logger.info("enhanced_unified_analysis_completed",
                           primary_intent=analysis.get("intent_analysis", {}).get("primary_intent"),
                           primary_confidence=analysis.get("intent_analysis", {}).get("primary_confidence"),
                           primary_namespace=analysis.get("namespace_routing", {}).get("primary_namespace"),
                           routing_confidence=analysis.get("namespace_routing", {}).get("routing_confidence"),
                           requires_human=analysis.get("hitl_assessment", {}).get("requires_human"),
                           overall_confidence=analysis.get("overall_analysis", {}).get("analysis_confidence"))
                
                return updated_state
                
            except Exception as e:
                logger.error("enhanced_unified_analysis_api_error", error=str(e))
                return self._fallback_enhanced_analysis(state, user_message, detected_language)
                
        except Exception as e:
            logger.error("enhanced_unified_analysis_failed", error=str(e))
            return self._set_default_enhanced_analysis(state)
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt context"""
        if not history:
            return "No previous conversation"
        
        formatted_history = []
        for i, message in enumerate(history[-5:]):  # Last 5 messages
            role = message.get("role", "user")
            content = message.get("content", "")[:100]  # Truncate long messages
            formatted_history.append(f"{role}: {content}")
        
        return "\n".join(formatted_history)
    
    def _extract_previous_intents(self, history: List[Dict[str, Any]]) -> List[str]:
        """Extract previous intents from conversation history for context"""
        previous_intents = []
        for message in history[-10:]:  # Last 10 messages
            if message.get("role") == "assistant":
                # Look for intent in assistant responses
                content = message.get("content", "")
                # Extract intent from metadata if available
                metadata = message.get("metadata", {})
                if "detected_intent" in metadata:
                    previous_intents.append(metadata["detected_intent"])
        
        return previous_intents
    
    def _parse_enhanced_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse enhanced JSON response from LLM"""
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
            
            # Find JSON content
            import re
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
            
            result = json.loads(cleaned_response)
            
            # Validate and structure the result
            return {
                "intent_analysis": result.get("intent_analysis", {}),
                "namespace_routing": result.get("namespace_routing", {}),
                "hitl_assessment": result.get("hitl_assessment", {}),
                "cultural_context": result.get("cultural_context", {}),
                "entity_extraction": result.get("entity_extraction", {}),
                "response_guidance": result.get("response_guidance", {}),
                "overall_analysis": result.get("overall_analysis", {})
            }
            
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), response=response_text)
            raise
    
    def _update_state_with_enhanced_analysis(self, state: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Update state with enhanced analysis results"""
        updated_state = state.copy()
        
        # Intent analysis
        updated_state.update({
            "detected_intent": analysis.get("intent_analysis", {}).get("primary_intent", "unknown"),
            "intent_confidence": analysis.get("intent_analysis", {}).get("primary_confidence", 0.0),
            "intent_reasoning": analysis.get("intent_analysis", {}).get("intent_reasoning", ""),
            "intent_entities": analysis.get("entity_extraction", {}).get("food_items", []) + analysis.get("entity_extraction", {}).get("locations", []) + analysis.get("entity_extraction", {}).get("time_references", []) + analysis.get("entity_extraction", {}).get("quantities", []) + analysis.get("entity_extraction", {}).get("special_requests", [])
        })
        
        # Namespace routing
        updated_state.update({
            "target_namespace": analysis.get("namespace_routing", {}).get("primary_namespace", "faq"),
            "namespace_confidence": analysis.get("namespace_routing", {}).get("routing_confidence", 0.0),
            "fallback_namespaces": analysis.get("namespace_routing", {}).get("fallback_namespaces", []),
            "cross_domain_detected": analysis.get("namespace_routing", {}).get("cross_domain_detected", False),
            "namespace_reasoning": analysis.get("namespace_routing", {}).get("routing_reasoning", "")
        })
        
        # HITL assessment
        updated_state.update({
            "requires_human": analysis.get("hitl_assessment", {}).get("requires_human", False),
            "escalation_reason": analysis.get("hitl_assessment", {}).get("escalation_reason"),
            "escalation_confidence": analysis.get("hitl_assessment", {}).get("escalation_confidence", 0.0),
            "escalation_urgency": analysis.get("hitl_assessment", {}).get("escalation_urgency", "low"),
            "escalation_triggers": analysis.get("hitl_assessment", {}).get("escalation_triggers", []),
            "hitl_reasoning": analysis.get("hitl_assessment", {}).get("hitl_reasoning", "")
        })
        
        # Cultural context
        updated_state.update({
            "cultural_context": analysis.get("cultural_context", {}),
            "cultural_confidence": analysis.get("cultural_context", {}).get("cultural_confidence", 0.0),
            "cultural_reasoning": analysis.get("cultural_context", {}).get("cultural_reasoning", "")
        })
        
        # Entity extraction
        updated_state.update({
            "entity_extraction": analysis.get("entity_extraction", {}),
            "extraction_confidence": analysis.get("entity_extraction", {}).get("extraction_confidence", 0.0),
            "entity_reasoning": analysis.get("entity_extraction", {}).get("entity_reasoning", "")
        })
        
        # Response guidance
        updated_state.update({
            "response_guidance": analysis.get("response_guidance", {}),
            "guidance_confidence": analysis.get("response_guidance", {}).get("guidance_confidence", 0.0),
            "guidance_reasoning": analysis.get("response_guidance", {}).get("guidance_reasoning", "")
        })
        
        # Overall analysis
        updated_state.update({
            "overall_analysis": analysis.get("overall_analysis", {}),
            "analysis_confidence": analysis.get("overall_analysis", {}).get("analysis_confidence", 0.0),
            "quality_score": analysis.get("overall_analysis", {}).get("quality_score", 0.0),
            "fallback_required": analysis.get("overall_analysis", {}).get("fallback_required", False),
            "fallback_reason": analysis.get("overall_analysis", {}).get("fallback_reason"),
            "processing_time_estimate": analysis.get("overall_analysis", {}).get("processing_time_estimate"),
            "recommendations": analysis.get("overall_analysis", {}).get("recommendations", [])
        })
        
        # RAG control based on enhanced analysis
        requires_human = analysis.get("hitl_assessment", {}).get("requires_human", False)
        fallback_required = analysis.get("overall_analysis", {}).get("fallback_required", False)
        
        updated_state.update({
            "rag_enabled": not requires_human and not fallback_required,
            "human_handling": requires_human,
            "secondary_intents": analysis.get("intent_analysis", {}).get("secondary_intents", [])
        })
        
        return updated_state
    
    def _fallback_enhanced_analysis(self, state: Dict[str, Any], user_message: str, language: str) -> Dict[str, Any]:
        """Fallback analysis when API fails"""
        # Use fallback manager for basic classification
        fallback_result = self.fallback_manager.get_fallback_intent(user_message, language)
        
        analysis = {
            "intent_analysis": {
                "primary_intent": fallback_result.get("intent", "unknown"),
                "primary_confidence": fallback_result.get("confidence", 0.3),
                "secondary_intents": [],
                "overall_confidence": fallback_result.get("confidence", 0.3),
                "intent_reasoning": "Fallback analysis due to API error"
            },
            "namespace_routing": {
                "primary_namespace": self._map_intent_to_namespace(fallback_result.get("intent", "unknown")),
                "primary_confidence": fallback_result.get("confidence", 0.3),
                "fallback_namespaces": [],
                "routing_confidence": fallback_result.get("confidence", 0.3),
                "cross_domain_detected": False,
                "routing_reasoning": "Fallback analysis due to API error"
            },
            "hitl_assessment": {
                "requires_human": False,
                "escalation_confidence": fallback_result.get("confidence", 0.3),
                "escalation_reason": None,
                "escalation_urgency": "low",
                "escalation_triggers": [],
                "hitl_reasoning": "Fallback analysis due to API error"
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "burmese_only",
                "cultural_confidence": fallback_result.get("confidence", 0.3),
                "cultural_reasoning": "Fallback analysis due to API error"
            },
            "entity_extraction": {
                "food_items": [],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": [],
                "extraction_confidence": fallback_result.get("confidence", 0.3),
                "entity_reasoning": "Fallback analysis due to API error"
            },
            "response_guidance": {
                "tone": "friendly",
                "language": "burmese",
                "include_greeting": True,
                "include_farewell": True,
                "response_length": "short",
                "priority_information": [],
                "guidance_confidence": fallback_result.get("confidence", 0.3),
                "guidance_reasoning": "Fallback analysis due to API error"
            },
            "overall_analysis": {
                "analysis_confidence": fallback_result.get("confidence", 0.3),
                "quality_score": fallback_result.get("confidence", 0.3),
                "fallback_required": False,
                "fallback_reason": None,
                "processing_time_estimate": "N/A",
                "recommendations": []
            }
        }
        
        return self._update_state_with_enhanced_analysis(state, analysis)
    
    def _set_default_enhanced_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Set default analysis when processing fails"""
        analysis = {
            "intent_analysis": {
                "primary_intent": "unknown",
                "primary_confidence": 0.0,
                "secondary_intents": [],
                "overall_confidence": 0.0,
                "intent_reasoning": "Default analysis due to processing failure"
            },
            "namespace_routing": {
                "primary_namespace": "faq",
                "primary_confidence": 0.0,
                "fallback_namespaces": [],
                "routing_confidence": 0.0,
                "cross_domain_detected": False,
                "routing_reasoning": "Default analysis due to processing failure"
            },
            "hitl_assessment": {
                "requires_human": False,
                "escalation_confidence": 0.0,
                "escalation_reason": None,
                "escalation_urgency": "low",
                "escalation_triggers": [],
                "hitl_reasoning": "Default analysis due to processing failure"
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "burmese_only",
                "cultural_confidence": 0.0,
                "cultural_reasoning": "Default analysis due to processing failure"
            },
            "entity_extraction": {
                "food_items": [],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": [],
                "extraction_confidence": 0.0,
                "entity_reasoning": "Default analysis due to processing failure"
            },
            "response_guidance": {
                "tone": "friendly",
                "language": "burmese",
                "include_greeting": True,
                "include_farewell": True,
                "response_length": "short",
                "priority_information": [],
                "guidance_confidence": 0.0,
                "guidance_reasoning": "Default analysis due to processing failure"
            },
            "overall_analysis": {
                "analysis_confidence": 0.0,
                "quality_score": 0.0,
                "fallback_required": False,
                "fallback_reason": None,
                "processing_time_estimate": "N/A",
                "recommendations": []
            }
        }
        
        return self._update_state_with_enhanced_analysis(state, analysis)
    
    def _map_intent_to_namespace(self, intent: str) -> str:
        """Map intent to namespace"""
        mapping = {
            "faq": "faq",
            "reservation": "faq",
            "events": "faq",
            "complaint": "faq",
            "menu_browse": "menu",
            "order_place": "menu",
            "job_application": "jobs",
            "unknown": "faq",
            "greeting": "faq",
            "goodbye": "faq"
        }
        return mapping.get(intent, "faq")


# Global unified prompt controller instance
_unified_controller: Optional[UnifiedPromptController] = None


def get_unified_prompt_controller() -> UnifiedPromptController:
    """Get or create unified prompt controller instance"""
    global _unified_controller
    if _unified_controller is None:
        _unified_controller = UnifiedPromptController()
    return _unified_controller
