"""
Advanced Prompt Engineering System
Provides sophisticated prompt templates and dynamic composition for enhanced unified analysis
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger("advanced_prompt_engine")


@dataclass
class PromptContext:
    """Context information for prompt generation"""
    user_message: str
    detected_language: str
    conversation_history: List[Dict[str, Any]]
    cultural_context: Dict[str, Any]
    previous_intents: List[str]
    confidence_thresholds: Dict[str, float]
    platform: str
    user_preferences: Dict[str, Any]


class AdvancedPromptEngine:
    """
    Advanced prompt engineering system for enhanced unified analysis
    Provides context-aware, culturally-adapted, and confidence-based prompt generation
    """
    
    def __init__(self):
        """Initialize advanced prompt engine"""
        self.settings = get_settings()
        self.base_templates = self._load_base_templates()
        self.cultural_adapters = self._load_cultural_adapters()
        self.confidence_adapters = self._load_confidence_adapters()
        logger.info("advanced_prompt_engine_initialized")
    
    def _load_base_templates(self) -> Dict[str, str]:
        """Load base prompt templates"""
        return {
            "standard": self._get_standard_template(),
            "complex_query": self._get_complex_query_template(),
            "multi_intent": self._get_multi_intent_template(),
            "escalation": self._get_escalation_template(),
            "cultural_sensitive": self._get_cultural_sensitive_template(),
            "low_confidence": self._get_low_confidence_template(),
            "cross_domain": self._get_cross_domain_template(),
            "burmese_enhanced": self._get_burmese_enhanced_template()
        }
    
    def _load_cultural_adapters(self) -> Dict[str, Dict[str, Any]]:
        """Load cultural adaptation rules"""
        return {
            "en": {
                "formality_levels": ["casual", "neutral", "formal"],
                "honorifics": [],
                "cultural_nuances": ["direct", "indirect", "polite"],
                "response_patterns": ["direct", "contextual", "elaborative"]
            },
            "my": {
                "formality_levels": ["အရပ်စကား", "အလယ်အလတ်", "ရုံးစကား"],
                "honorifics": ["ဦး", "ဒေါ်", "မ", "ကို", "မယ်"],
                "cultural_nuances": ["ရိုသေလေးစား", "သီလရှိ", "ကျေးဇူးတင်"],
                "response_patterns": ["ရိုသေလေးစား", "သီလရှိ", "ကျေးဇူးတင်"]
            }
        }
    
    def _load_confidence_adapters(self) -> Dict[str, Dict[str, Any]]:
        """Load confidence-based adaptation rules"""
        return {
            "high_confidence": {
                "analysis_depth": "comprehensive",
                "fallback_threshold": 0.8,
                "response_style": "assertive",
                "detail_level": "detailed"
            },
            "medium_confidence": {
                "analysis_depth": "balanced",
                "fallback_threshold": 0.6,
                "response_style": "cautious",
                "detail_level": "moderate"
            },
            "low_confidence": {
                "analysis_depth": "conservative",
                "fallback_threshold": 0.4,
                "response_style": "tentative",
                "detail_level": "basic"
            }
        }
    
    def generate_enhanced_prompt(self, context: PromptContext) -> str:
        """
        Generate enhanced prompt based on context
        
        Args:
            context: Prompt context with user message, history, cultural info
            
        Returns:
            Enhanced prompt string optimized for the specific context
        """
        try:
            # Determine prompt template based on context
            template_type = self._determine_template_type(context)
            
            # Get base template
            base_template = self.base_templates[template_type]
            
            # Apply cultural adaptations
            culturally_adapted = self._apply_cultural_adaptations(base_template, context)
            
            # Apply confidence-based adjustments
            confidence_adjusted = self._apply_confidence_adjustments(culturally_adapted, context)
            
            # Apply context-specific enhancements
            context_enhanced = self._apply_context_enhancements(confidence_adjusted, context)
            
            # Final formatting and validation
            final_prompt = self._finalize_prompt(context_enhanced, context)
            
            logger.info("enhanced_prompt_generated",
                       template_type=template_type,
                       language=context.detected_language,
                       confidence_level=self._get_confidence_level(context))
            
            return final_prompt
            
        except Exception as e:
            logger.error("enhanced_prompt_generation_failed", error=str(e))
            return self._get_fallback_prompt(context)
    
    def _determine_template_type(self, context: PromptContext) -> str:
        """Determine the most appropriate template type based on context"""
        # Check for escalation scenarios (highest priority)
        if self._is_escalation_context(context):
            return "escalation"
        
        # Check for low confidence scenarios
        if self._is_low_confidence_context(context):
            return "low_confidence"
        
        # Check for Burmese language (but not escalation)
        if context.detected_language == "my":
            return "burmese_enhanced"
        
        # Check for complex queries (higher priority than multi-intent)
        if self._is_complex_query_context(context):
            return "complex_query"
        
        # Check for cross-domain scenarios
        if self._is_cross_domain_context(context):
            return "cross_domain"
        
        # Check for cultural sensitivity (higher priority than multi-intent)
        if self._is_culturally_sensitive_context(context):
            return "cultural_sensitive"
        
        # Check for multi-intent scenarios
        if self._is_multi_intent_context(context):
            return "multi_intent"
        
        # Default to standard template
        return "standard"
    
    def _is_low_confidence_context(self, context: PromptContext) -> bool:
        """Check if context indicates low confidence scenario"""
        # Check conversation history for previous low confidence responses
        for message in context.conversation_history[-3:]:  # Last 3 messages
            if message.get("intent_confidence", 1.0) < 0.5:
                return True
        return False
    
    def _is_escalation_context(self, context: PromptContext) -> bool:
        """Check if context indicates escalation scenario"""
        # English escalation keywords
        english_escalation_keywords = [
            "help", "problem", "issue", "wrong", "error", "can't", "won't",
            "refund", "cancel", "complaint", "angry", "frustrated", "urgent",
            "assistance", "support", "human", "manager", "staff", "employee"
        ]
        
        # Burmese escalation keywords and patterns
        burmese_escalation_keywords = [
            # Direct assistance requests
            "အကူအညီ", "ကူညီ", "အကူအညီလိုပါတယ်", "ကူညီပေးပါ",
            "အကူအညီရယူ", "အကူအညီရယူရန်", "ဆက်သွယ်ပေးပါ",
            
            # Human interaction requests
            "လူသားနဲ့ပြောချင်ပါတယ်", "လူသားနဲ့ပြောချင်တယ်",
            "ဝန်ထမ်းနဲ့ပြောချင်ပါတယ်", "ဝန်ထမ်းနဲ့စကားပြောချင်ပါတယ်",
            "သက်ဆိုင်ရာဝန်ထမ်း", "သက်ဆိုင်ရာဝန်ထမ်းနဲ့ပြောချင်ပါတယ်",
            "မန်နေဂျာ", "အုပ်ချုပ်သူ", "ဆိုင်ရာဝန်ထမ်း",
            
            # Problem/complaint indicators
            "ပြဿနာ", "အခက်အခဲ", "အဆင်မပြေ", "အဆင်မပြေတာ",
            "ကြုံခဲ့တယ်", "ကြုံတွေ့ခဲ့ရတာ", "အဆင်မပြေတာတွေ",
            
            # Contact/communication requests
            "ဘယ်သူနဲ့စကားပြောလို့ရလဲ", "ဘယ်သူနဲ့ပြောလို့ရလဲ",
            "စကားပြောလို့ရလဲ", "ပြောလို့ရလဲ",
            "အကြောင်းကြားရန်", "အကြောင်းကြားပေးပါ",
            "ဆက်သွယ်ပေးပါမည်",
            
            # Urgency indicators
            "အရေးကြီး", "အရေးတကြီး", "အရေးတကြီးလိုအပ်ပါတယ်",
            "ချက်ချင်း", "အမြန်ဆုံး", "အလျင်အမြန်"
        ]
        
        # Burmese simple query indicators (to avoid false positives)
        burmese_simple_query_indicators = [
            "မီနူး", "menu", "ဘာရှိ", "ဘာတွေ", "ဘာများ", "ရှိလား", "ရလဲ",
            "ကြည့်ချင်", "ကြည့်ချင်ပါတယ်", "သိချင်", "သိချင်ပါတယ်",
            "ဘယ်လို", "ဘယ်လိုလဲ", "ဘယ်လိုရှိလဲ", "ဘယ်လိုနေလဲ"
        ]
        
        message_lower = context.user_message.lower()
        
        # Check for English escalation keywords
        if any(keyword in message_lower for keyword in english_escalation_keywords):
            return True
            
        # For Burmese, be more nuanced to avoid false positives
        if context.detected_language == "my":
            # First check if it's a simple query (should NOT escalate)
            if any(indicator in context.user_message for indicator in burmese_simple_query_indicators):
                # Only escalate if it also contains escalation keywords
                has_escalation_keywords = any(keyword in context.user_message for keyword in burmese_escalation_keywords)
                if not has_escalation_keywords:
                    return False
            
            # Check for Burmese escalation keywords
            if any(keyword in context.user_message for keyword in burmese_escalation_keywords):
                return True
                
            # Check for emotional indicators in Burmese
            burmese_emotional_indicators = [
                "စိတ်မကောင်း", "ဝမ်းနည်း", "ဒေါသထွက်", "စိတ်ဆိုး",
                "အံ့အားသင့်", "အံ့ဩ", "ရှက်လို့", "အားငယ်"
            ]
            
            if any(indicator in context.user_message for indicator in burmese_emotional_indicators):
                return True
                
            # Check for complex problem descriptions (long messages with negative sentiment)
            if len(context.user_message.split()) > 10:
                negative_burmese_words = ["မကောင်း", "မဖြစ်", "မရ", "မလို", "မလုံလောက်"]
                if any(word in context.user_message for word in negative_burmese_words):
                    return True
        
        return False
    
    def _is_multi_intent_context(self, context: PromptContext) -> bool:
        """Check if context indicates multi-intent scenario"""
        # Check for multiple action words or complex sentence structure
        action_words = ["and", "also", "plus", "as well as", "while", "but"]
        return any(word in context.user_message.lower() for word in action_words)
    
    def _is_cross_domain_context(self, context: PromptContext) -> bool:
        """Check if context indicates cross-domain scenario"""
        domain_keywords = {
            "menu": ["food", "dish", "meal", "order", "menu"],
            "faq": ["hours", "location", "contact", "policy"],
            "jobs": ["job", "career", "position", "apply", "hiring"],
            "events": ["event", "party", "celebration", "booking"]
        }
        
        message_lower = context.user_message.lower()
        domains_found = []
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                domains_found.append(domain)
        
        return len(domains_found) > 1
    
    def _is_culturally_sensitive_context(self, context: PromptContext) -> bool:
        """Check if context requires cultural sensitivity"""
        sensitive_keywords = [
            "religion", "politics", "custom", "tradition", "culture",
            "family", "respect", "honor", "ceremony", "ritual"
        ]
        message_lower = context.user_message.lower()
        return any(keyword in message_lower for keyword in sensitive_keywords)
    
    def _is_complex_query_context(self, context: PromptContext) -> bool:
        """Check if context indicates complex query"""
        # Check for long sentences, multiple clauses, or technical terms
        words = context.user_message.split()
        return len(words) > 15 or len(context.user_message) > 100
    
    def _get_confidence_level(self, context: PromptContext) -> str:
        """Determine confidence level based on context"""
        # Check conversation history for confidence patterns
        recent_confidences = [
            msg.get("intent_confidence", 0.5) 
            for msg in context.conversation_history[-3:]
        ]
        
        if not recent_confidences:
            return "medium_confidence"
        
        avg_confidence = sum(recent_confidences) / len(recent_confidences)
        
        if avg_confidence >= 0.7:
            return "high_confidence"
        elif avg_confidence <= 0.4:
            return "low_confidence"
        else:
            return "medium_confidence"
    
    def _get_fallback_prompt(self, context: PromptContext) -> str:
        """Get fallback prompt when generation fails"""
        return f"""
        ENHANCED UNIFIED ANALYSIS PROMPT (FALLBACK):
        
        Analyze the following user message and provide comprehensive analysis:
        
        USER MESSAGE: "{context.user_message}"
        LANGUAGE: {context.detected_language}
        
        Provide analysis in the following JSON format:
        {{
          "intent_analysis": {{
            "primary_intent": "string",
            "primary_confidence": 0.0-1.0,
            "secondary_intents": [],
            "overall_confidence": 0.0-1.0,
            "intent_reasoning": "string"
          }},
          "namespace_routing": {{
            "primary_namespace": "string",
            "primary_confidence": 0.0-1.0,
            "fallback_namespaces": [],
            "routing_confidence": 0.0-1.0,
            "cross_domain_detected": false,
            "routing_reasoning": "string"
          }},
          "hitl_assessment": {{
            "requires_human": false,
            "escalation_confidence": 0.0-1.0,
            "escalation_reason": null,
            "escalation_urgency": "low",
            "escalation_triggers": [],
            "hitl_reasoning": "string"
          }},
          "cultural_context": {{
            "formality_level": "string",
            "uses_honorifics": false,
            "honorifics_detected": [],
            "cultural_nuances": [],
            "language_mix": "string",
            "cultural_confidence": 0.0-1.0,
            "cultural_reasoning": "string"
          }},
          "entity_extraction": {{
            "food_items": [],
            "locations": [],
            "time_references": [],
            "quantities": [],
            "special_requests": [],
            "extraction_confidence": 0.0-1.0,
            "entity_reasoning": "string"
          }},
          "response_guidance": {{
            "tone": "string",
            "language": "string",
            "include_greeting": false,
            "include_farewell": false,
            "response_length": "string",
            "priority_information": [],
            "guidance_confidence": 0.0-1.0,
            "guidance_reasoning": "string"
          }},
          "overall_analysis": {{
            "analysis_confidence": 0.0-1.0,
            "quality_score": 0.0-1.0,
            "fallback_required": false,
            "fallback_reason": null,
            "processing_time_estimate": "string",
            "recommendations": []
          }}
        }}
        """

    def _apply_cultural_adaptations(self, template: str, context: PromptContext) -> str:
        """Apply cultural adaptations to the template"""
        if context.detected_language not in self.cultural_adapters:
            return template
        
        cultural_rules = self.cultural_adapters[context.detected_language]
        
        # Apply language-specific adaptations
        if context.detected_language == "my":
            template = self._apply_burmese_cultural_adaptations(template, context, cultural_rules)
        else:
            template = self._apply_english_cultural_adaptations(template, context, cultural_rules)
        
        return template
    
    def _apply_burmese_cultural_adaptations(self, template: str, context: PromptContext, rules: Dict[str, Any]) -> str:
        """Apply Burmese-specific cultural adaptations"""
        # Add Burmese cultural context
        burmese_context = """
        BURMESE CULTURAL CONTEXT:
        - Show respect through appropriate honorifics (ဦး, ဒေါ်, မ, ကို, မယ်)
        - Use polite language (ရိုသေလေးစား, ကျေးဇူးတင်)
        - Consider hierarchical relationships
        - Be mindful of Buddhist cultural values
        - Use appropriate formality levels based on age and status
        """
        
        # Add Burmese language guidance
        burmese_guidance = """
        BURMESE LANGUAGE GUIDANCE:
        - Detect formality level: အရပ်စကား (casual), အလယ်အလတ် (neutral), ရုံးစကား (formal)
        - Identify honorifics and respectful language patterns
        - Consider cultural nuances in response tone
        - Adapt response style to match user's formality level
        """
        
        return template.replace(
            "CULTURAL CONTEXT ANALYSIS:",
            f"CULTURAL CONTEXT ANALYSIS:\n{burmese_context}\n{burmese_guidance}"
        )
    
    def _apply_english_cultural_adaptations(self, template: str, context: PromptContext, rules: Dict[str, Any]) -> str:
        """Apply English-specific cultural adaptations"""
        # Add English cultural context
        english_context = """
        ENGLISH CULTURAL CONTEXT:
        - Direct communication style preferred
        - Professional but friendly tone
        - Clear and concise responses
        - Respect for individual preferences
        - Inclusive and accessible language
        """
        
        return template.replace(
            "CULTURAL CONTEXT ANALYSIS:",
            f"CULTURAL CONTEXT ANALYSIS:\n{english_context}"
        )
    
    def _apply_confidence_adjustments(self, template: str, context: PromptContext) -> str:
        """Apply confidence-based adjustments to the template"""
        confidence_level = self._get_confidence_level(context)
        confidence_rules = self.confidence_adapters.get(confidence_level, self.confidence_adapters["medium_confidence"])
        
        # Add confidence-specific guidance
        confidence_guidance = f"""
        CONFIDENCE-BASED ANALYSIS GUIDANCE:
        - Analysis Depth: {confidence_rules['analysis_depth']}
        - Fallback Threshold: {confidence_rules['fallback_threshold']}
        - Response Style: {confidence_rules['response_style']}
        - Detail Level: {confidence_rules['detail_level']}
        
        When confidence is {confidence_level}:
        - Be more {'assertive' if confidence_level == 'high_confidence' else 'cautious' if confidence_level == 'low_confidence' else 'balanced'} in analysis
        - Provide {'detailed' if confidence_level == 'high_confidence' else 'basic' if confidence_level == 'low_confidence' else 'moderate'} information
        - Use {'higher' if confidence_level == 'high_confidence' else 'lower' if confidence_level == 'low_confidence' else 'standard'} fallback thresholds
        """
        
        return template.replace(
            "CONFIDENCE SCORING GUIDELINES:",
            f"CONFIDENCE SCORING GUIDELINES:\n{confidence_guidance}"
        )
    
    def _apply_context_enhancements(self, template: str, context: PromptContext) -> str:
        """Apply context-specific enhancements"""
        # Add conversation history context
        if context.conversation_history:
            history_context = self._extract_history_context(context.conversation_history)
            template = template.replace(
                "CONVERSATION CONTEXT:",
                f"CONVERSATION CONTEXT:\n{history_context}"
            )
        
        # Add user preferences context
        if context.user_preferences:
            preferences_context = self._extract_preferences_context(context.user_preferences)
            template = template.replace(
                "USER PREFERENCES:",
                f"USER PREFERENCES:\n{preferences_context}"
            )
        
        return template
    
    def _extract_history_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Extract relevant context from conversation history"""
        if not conversation_history:
            return "No previous conversation context available."
        
        # Get last 3 messages for context
        recent_messages = conversation_history[-3:]
        
        context_lines = ["Recent conversation context:"]
        for i, message in enumerate(recent_messages, 1):
            intent = message.get("detected_intent", "unknown")
            confidence = message.get("intent_confidence", 0.0)
            user_msg = message.get("user_message", "")[:50] + "..." if len(message.get("user_message", "")) > 50 else message.get("user_message", "")
            
            context_lines.append(f"  {i}. Intent: {intent} (confidence: {confidence:.2f}) - User: {user_msg}")
        
        return "\n".join(context_lines)
    
    def _extract_preferences_context(self, user_preferences: Dict[str, Any]) -> str:
        """Extract user preferences context"""
        if not user_preferences:
            return "No user preferences available."
        
        context_lines = ["User preferences:"]
        for key, value in user_preferences.items():
            context_lines.append(f"  - {key}: {value}")
        
        return "\n".join(context_lines)
    
    def _finalize_prompt(self, template: str, context: PromptContext) -> str:
        """Finalize and validate the prompt"""
        # Add dynamic context information
        dynamic_context = f"""
        CURRENT CONTEXT:
        - User Message: "{context.user_message}"
        - Detected Language: {context.detected_language}
        - Platform: {context.platform}
        - Conversation Length: {len(context.conversation_history)} messages
        - Previous Intents: {', '.join(context.previous_intents[-3:]) if context.previous_intents else 'None'}
        """
        
        # Insert dynamic context at the beginning
        template = template.replace(
            "ENHANCED UNIFIED ANALYSIS PROMPT:",
            f"ENHANCED UNIFIED ANALYSIS PROMPT:\n{dynamic_context}"
        )
        
        return template
    
    # Base template methods
    def _get_standard_template(self) -> str:
        """Get standard analysis template"""
        return """
        ENHANCED UNIFIED ANALYSIS PROMPT:
        
        CONVERSATION CONTEXT:
        USER PREFERENCES:
        
        CULTURAL CONTEXT ANALYSIS:
        
        CONFIDENCE SCORING GUIDELINES:
        
        HITL ASSESSMENT GUIDELINES:
        ALWAYS evaluate if human assistance is needed. Consider:
        1. Language-specific escalation indicators (English and Burmese)
        2. Emotional state and tone analysis
        3. Complexity of the request or problem
        4. Cultural sensitivity requirements
        5. Need for personalized attention or direct communication
        6. Requests for contact information or staff interaction
        
        For Burmese language, pay special attention to:
        - Direct assistance requests: အကူအညီ, ကူညီ, အကူအညီလိုပါတယ်
        - Human interaction requests: လူသားနဲ့ပြောချင်ပါတယ်, ဝန်ထမ်းနဲ့ပြောချင်ပါတယ်
        - Problem descriptions: ပြဿနာ, အခက်အခဲ, အဆင်မပြေ, ကြုံခဲ့တယ်
        - Contact requests: ဘယ်သူနဲ့စကားပြောလို့ရလဲ, ဆက်သွယ်ပေးပါ
        - Emotional indicators: စိတ်မကောင်း, ဝမ်းနည်း, ဒေါသထွက်
        
        When in doubt, err on the side of human assistance.
        
        ENHANCED OUTPUT FORMAT (JSON):
        {
          "intent_analysis": {
            "primary_intent": "string",
            "primary_confidence": 0.0-1.0,
            "secondary_intents": [
              {
                "intent": "string",
                "confidence": 0.0-1.0,
                "reasoning": "string"
              }
            ],
            "overall_confidence": 0.0-1.0,
            "intent_reasoning": "string"
          },
          "namespace_routing": {
            "primary_namespace": "string",
            "primary_confidence": 0.0-1.0,
            "fallback_namespaces": [
              {
                "namespace": "string",
                "confidence": 0.0-1.0,
                "reasoning": "string"
              }
            ],
            "routing_confidence": 0.0-1.0,
            "cross_domain_detected": false,
            "routing_reasoning": "string"
          },
          "hitl_assessment": {
            "requires_human": false,
            "escalation_confidence": 0.0-1.0,
            "escalation_reason": null,
            "escalation_urgency": "low",
            "escalation_triggers": [],
            "hitl_reasoning": "string"
          },
          "cultural_context": {
            "formality_level": "string",
            "uses_honorifics": false,
            "honorifics_detected": [],
            "cultural_nuances": [],
            "language_mix": "string",
            "cultural_confidence": 0.0-1.0,
            "cultural_reasoning": "string"
          },
          "entity_extraction": {
            "food_items": [
              {
                "item": "string",
                "confidence": 0.0-1.0,
                "category": "string"
              }
            ],
            "locations": [],
            "time_references": [],
            "quantities": [],
            "special_requests": [],
            "extraction_confidence": 0.0-1.0,
            "entity_reasoning": "string"
          },
          "response_guidance": {
            "tone": "string",
            "language": "string",
            "include_greeting": false,
            "include_farewell": false,
            "response_length": "string",
            "priority_information": [],
            "guidance_confidence": 0.0-1.0,
            "guidance_reasoning": "string"
          },
          "overall_analysis": {
            "analysis_confidence": 0.0-1.0,
            "quality_score": 0.0-1.0,
            "fallback_required": false,
            "fallback_reason": null,
            "processing_time_estimate": "string",
            "recommendations": []
          }
        }
        
        FALLBACK LOGIC:
        - If primary_confidence < 0.5, use fallback_namespaces
        - If overall_confidence < 0.3, set fallback_required = true
        - If cross_domain_detected = true, include multiple namespaces
        - If cultural_confidence < 0.4, use conservative cultural analysis
        """
    
    def _get_complex_query_template(self) -> str:
        """Get template for complex queries"""
        template = self._get_standard_template()
        complex_guidance = """
        COMPLEX QUERY ANALYSIS GUIDANCE:
        - Break down complex queries into multiple intents
        - Identify primary and secondary user goals
        - Consider temporal and logical relationships
        - Analyze query complexity and provide detailed reasoning
        - Use higher confidence thresholds for complex analysis
        - Provide comprehensive entity extraction
        """
        return template.replace("CONFIDENCE SCORING GUIDELINES:", f"CONFIDENCE SCORING GUIDELINES:\n{complex_guidance}")
    
    def _get_multi_intent_template(self) -> str:
        """Get template for multi-intent queries"""
        template = self._get_standard_template()
        multi_intent_guidance = """
        MULTI-INTENT ANALYSIS GUIDANCE:
        - Identify all distinct user intents
        - Prioritize intents by user urgency and importance
        - Consider intent relationships and dependencies
        - Provide comprehensive secondary_intents analysis
        - Use cross-domain detection for related intents
        - Balance multiple response priorities
        """
        return template.replace("CONFIDENCE SCORING GUIDELINES:", f"CONFIDENCE SCORING GUIDELINES:\n{multi_intent_guidance}")
    
    def _get_escalation_template(self) -> str:
        """Get template for escalation scenarios"""
        template = self._get_standard_template()
        escalation_guidance = """
        ESCALATION ANALYSIS GUIDANCE:
        
        CRITICAL HITL ASSESSMENT RULES:
        1. ALWAYS set requires_human = true if ANY of the following are detected:
           - Direct requests for human assistance (any language)
           - Complaints about service quality or experiences
           - Requests to speak with staff, manager, or specific person
           - Emotional distress indicators (frustration, anger, disappointment)
           - Complex problems requiring personalized attention
           - Requests for contact information or direct communication
           - Issues that cannot be resolved with standard information
        
        2. BURMESE LANGUAGE ESCALATION TRIGGERS:
           - Any message containing: အကူအညီ, လူသားနဲ့ပြောချင်ပါတယ်, ဝန်ထမ်းနဲ့ပြောချင်ပါတယ်
           - Problem descriptions: ပြဿနာ, အခက်အခဲ, အဆင်မပြေ, ကြုံခဲ့တယ်
           - Contact requests: ဘယ်သူနဲ့စကားပြောလို့ရလဲ, ဆက်သွယ်ပေးပါ
           - Emotional indicators: စိတ်မကောင်း, ဝမ်းနည်း, ဒေါသထွက်
        
        3. ESCALATION CONFIDENCE SCORING:
           - High confidence (0.8-1.0): Explicit human assistance requests
           - Medium confidence (0.6-0.8): Problem descriptions with emotional indicators
           - Low confidence (0.4-0.6): Complex queries that might need human attention
        
        4. ESCALATION URGENCY LEVELS:
           - "high": Immediate assistance needed, emotional distress, urgent problems
           - "medium": Standard complaints or assistance requests
           - "low": General inquiries that might benefit from human attention
        
        5. ESCALATION TRIGGERS TO DETECT:
           - "explicit_request": Direct request for human assistance
           - "complaint": Service quality or experience complaints
           - "emotional_distress": Signs of frustration, anger, or disappointment
           - "complex_problem": Issues requiring personalized attention
           - "contact_request": Requests for direct communication
           - "cultural_sensitivity": Culturally sensitive matters requiring human judgment
        
        6. HITL REASONING REQUIREMENTS:
           - Provide detailed explanation of why human assistance is needed
           - Identify specific triggers and indicators
           - Consider cultural context and language nuances
           - Explain what type of human assistance would be most appropriate
        
        REMEMBER: When in doubt about escalation, err on the side of human assistance.
        It's better to escalate a conversation that could be handled by AI than to miss
        a conversation that genuinely needs human attention.
        """
        return template.replace("CONFIDENCE SCORING GUIDELINES:", f"CONFIDENCE SCORING GUIDELINES:\n{escalation_guidance}")
    
    def _get_cultural_sensitive_template(self) -> str:
        """Get template for culturally sensitive queries"""
        template = self._get_standard_template()
        cultural_guidance = """
        CULTURAL SENSITIVITY GUIDANCE:
        - Pay special attention to cultural context and nuances
        - Use appropriate formality levels and honorifics
        - Consider cultural taboos and sensitivities
        - Provide culturally appropriate response guidance
        - Use higher cultural confidence thresholds
        - Include cultural adaptation recommendations
        """
        return template.replace("CONFIDENCE SCORING GUIDELINES:", f"CONFIDENCE SCORING GUIDELINES:\n{cultural_guidance}")
    
    def _get_low_confidence_template(self) -> str:
        """Get template for low confidence scenarios"""
        template = self._get_standard_template()
        low_confidence_guidance = """
        LOW CONFIDENCE ANALYSIS GUIDANCE:
        - Use conservative confidence scoring
        - Provide multiple fallback options
        - Include comprehensive reasoning for low confidence
        - Suggest clarification questions
        - Use lower thresholds for escalation
        - Provide detailed uncertainty explanations
        """
        return template.replace("CONFIDENCE SCORING GUIDELINES:", f"CONFIDENCE SCORING GUIDELINES:\n{low_confidence_guidance}")
    
    def _get_cross_domain_template(self) -> str:
        """Get template for cross-domain queries"""
        template = self._get_standard_template()
        cross_domain_guidance = """
        CROSS-DOMAIN ANALYSIS GUIDANCE:
        - Identify all relevant domains and namespaces
        - Provide comprehensive fallback_namespaces
        - Consider domain relationships and priorities
        - Use cross_domain_detected = true
        - Balance multiple domain responses
        - Provide unified response strategy
        """
        return template.replace("CONFIDENCE SCORING GUIDELINES:", f"CONFIDENCE SCORING GUIDELINES:\n{cross_domain_guidance}")
    
    def _get_burmese_enhanced_template(self) -> str:
        """Get enhanced template for Burmese language"""
        template = self._get_standard_template()
        burmese_enhancement = """
        BURMESE LANGUAGE ENHANCEMENT:
        - Enhanced Burmese language detection and analysis
        - Cultural context for Myanmar/Burmese culture
        - Honorific detection and appropriate usage
        - Formality level analysis (အရပ်စကား, အလယ်အလတ်, ရုံးစကား)
        - Buddhist cultural considerations
        - Traditional greeting and farewell patterns
        - Respectful language patterns and nuances
        """
        return template.replace("CULTURAL CONTEXT ANALYSIS:", f"CULTURAL CONTEXT ANALYSIS:\n{burmese_enhancement}")


# Global instance for easy access
_advanced_prompt_engine = None


def get_advanced_prompt_engine() -> AdvancedPromptEngine:
    """Get global advanced prompt engine instance"""
    global _advanced_prompt_engine
    if _advanced_prompt_engine is None:
        _advanced_prompt_engine = AdvancedPromptEngine()
    return _advanced_prompt_engine
