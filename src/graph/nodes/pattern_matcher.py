"""
Pattern Matcher Node for LangGraph
Detects greetings, goodbyes, and escalation requests before RAG processing
"""

import re
from typing import Dict, Any, List, Tuple
from src.utils.language import detect_language, is_burmese_text
from src.utils.burmese_processor import detect_burmese_intent_patterns, get_burmese_cultural_context
from src.utils.logger import get_logger

logger = get_logger("pattern_matcher_node")


class PatternMatcherNode:
    """
    LangGraph node for pattern matching
    Detects greetings, goodbyes, and escalation requests
    """
    
    def __init__(self):
        """Initialize pattern matcher node"""
        # English patterns
        self.english_greeting_patterns = [
            r'\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b',
            r'\b(how are you|how\'s it going|how do you do)\b',
            r'\b(nice to meet you|pleasure to meet you)\b'
        ]
        
        self.english_goodbye_patterns = [
            r'\b(bye|goodbye|see you|see ya|take care|farewell)\b',
            r'\b(thank you|thanks|thank you so much)\b',
            r'\b(that\'s all|that\'s it|end|finish)\b'
        ]
        
        self.english_escalation_patterns = [
            r'\b(can I talk to someone|speak to someone|talk to a person|talk to someone)\b',
            r'\b(human|real person|staff member|employee)\b',
            r'\b(help me|I need help|assistance|support)\b',
            r'\b(complaint|problem|issue|not working)\b'
        ]
        
        # Enhanced Burmese patterns (extracted from burmese_customer_services_handler.py)
        self.burmese_greeting_patterns = [
            "မင်္ဂလာပါ ခင်ဗျာ", "မင်္ဂလာပါ", "ဟလို", "ဟေး", "ဟယ်လို",
            "အစ်ကို", "အစ်မ", "ဦးလေး", "အမေကြီး", "ဘယ်လိုလဲ", "ဘယ်လိုရှိလဲ", "ဘယ်လိုနေလဲ"
        ]
        
        self.burmese_goodbye_patterns = [
            "ကျေးဇူးတင်ပါတယ်", "ကျေးဇူး", "ကျေးဇူးပါ", 
            "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ", "ကျေးဇူးပါ ခင်ဗျာ",
            "ပြန်လာမယ်", "သွားပါတယ်", "နှုတ်ဆက်ပါတယ်", "ပြန်တွေ့မယ်"
        ]
        
        self.burmese_escalation_patterns = [
            "လူသားနဲ့ပြောချင်ပါတယ်", "အကူအညီလိုပါတယ်",
            "ပိုကောင်းတဲ့အကူအညီလိုပါတယ်", "သူငယ်ချင်းနဲ့ပြောချင်ပါတယ်",
            "လူသားနဲ့ပြောချင်တယ်", "အကူအညီလိုတယ်",
            "လူသားနဲ့ပြောချင်ပါတယ်", "အကူအညီလိုပါတယ်"
        ]
        
        # Menu-related patterns for early detection
        self.burmese_menu_patterns = [
            "ဘာ", "အစားအစာ", "ရှိလား", "ရလဲ", "menu", "food", "dish", "item",
            "ဘယ်လို", "ဘာတွေ", "ဘာများ", "ဘာရှိ", "what", "kind", "available",
            "အမျိုးအစား", "category", "ဘာတွေ", "ဘာများ", "ဘာရှိ"
        ]
        
        # Customer service patterns
        self.burmese_customer_service_patterns = [
            # Infrastructure & Services
            "wifi", "internet", "မီးပျက်", "generator", "မီးစက်", "အဲကွန်း", "aircon", "air conditioning",
            "အပူချိန်", "temperature", "အအေး", "cooling", "အပူ", "heating",
            
            # Policies & Rules
            "ဓါတ်ပုံ", "photo", "ကြောင်လေး", "pet", "ခွေး", "dog", "ကြောင်", "cat",
            "အပြင်ထိုင်ခုံ", "outdoor", "အပြင်", "outside", "ဆေးလိပ်", "smoking",
            "အစားအစာ", "food", "အပြင်က", "outside food", "ယူဆောင်", "bring",
            
            # General Business Questions
            "ဖွင့်လား", "open", "ပိတ်လား", "closed", "အလုပ်လုပ်လား", "working",
            "ရရှိနိုင်လား", "available", "ရနိုင်လား", "can get", "ဖြစ်နိုင်လား", "possible"
        ]
        
        logger.info("pattern_matcher_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state and detect patterns
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with pattern detection results
        """
        user_message = state.get("user_message", "")
        if not user_message:
            logger.warning("empty_user_message")
            return state
        
        # Detect language if not already set
        if not state.get("detected_language"):
            detected_lang = detect_language(user_message)
            state["detected_language"] = detected_lang
            logger.info("language_detected", language=detected_lang, message=user_message[:50])
        
        # Detect patterns based on language
        if state["detected_language"] in ["my", "myanmar"]:
            # Use Burmese pattern detection
            is_greeting, is_goodbye, is_escalation = self._detect_burmese_patterns(user_message)
            cultural_context = get_burmese_cultural_context(user_message)
            state["metadata"]["burmese_cultural_context"] = cultural_context
        else:
            # Use English pattern detection
            is_greeting, is_goodbye, is_escalation = self._detect_english_patterns(user_message)
        
        # Update state with pattern detection results
        state.update({
            "is_greeting": is_greeting,
            "is_goodbye": is_goodbye,
            "is_escalation_request": is_escalation
        })
        
        # Log pattern detection results
        logger.info(
            "pattern_detection_completed",
            user_message=user_message[:50],
            language=state["detected_language"],
            is_greeting=is_greeting,
            is_goodbye=is_goodbye,
            is_escalation_request=is_escalation
        )
        
        return state
    
    def _detect_burmese_patterns(self, message: str) -> Tuple[bool, bool, bool]:
        """
        Enhanced Burmese pattern detection (extracted from burmese_customer_services_handler.py)
        
        Args:
            message: User message in Burmese
            
        Returns:
            Tuple of (is_greeting, is_goodbye, is_escalation)
        """
        # Normalize message
        normalized_message = message.lower().strip()
        
        # Check for simple greetings (exact matches)
        is_greeting = self._is_simple_greeting(message)
        
        # Check for simple thanks (exact matches)
        is_goodbye = self._is_simple_thanks(message)
        
        # Check for escalation requests
        is_escalation = any(pattern in normalized_message for pattern in self.burmese_escalation_patterns)
        
        # Use existing Burmese intent detection as backup
        if not any([is_greeting, is_goodbye, is_escalation]):
            try:
                burmese_intents = detect_burmese_intent_patterns(message)
                if burmese_intents.get("greeting", 0) > 0.5:
                    is_greeting = True
                elif burmese_intents.get("goodbye", 0) > 0.5:
                    is_goodbye = True
            except Exception as e:
                logger.warning("burmese_intent_detection_failed", error=str(e))
        
        return is_greeting, is_goodbye, is_escalation
    
    def _is_simple_greeting(self, user_message: str) -> bool:
        """
        Check if the message is a simple greeting that should get immediate response
        (Extracted from burmese_customer_services_handler.py)
        """
        greeting_patterns = [
            "မင်္ဂလာပါ ခင်ဗျာ",
            "မင်္ဂလာပါ",
            "ဟလို",
            "ဟေး",
            "ဟယ်လို",
            "အစ်ကို",
            "အစ်မ",
            "ဦးလေး",
            "အမေကြီး",
            "ဘယ်လိုလဲ",
            "ဘယ်လိုရှိလဲ",
            "ဘယ်လိုနေလဲ"
        ]
        
        user_message_lower = user_message.lower().strip()
        return any(pattern.lower() in user_message_lower for pattern in greeting_patterns)
    
    def _is_simple_thanks(self, user_message: str) -> bool:
        """
        Check if the message is a simple thank you that should get immediate response
        (Extracted from burmese_customer_services_handler.py)
        """
        thanks_patterns = [
            "ကျေးဇူးတင်ပါတယ်",
            "ကျေးဇူး",
            "ကျေးဇူးပါ",
            "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ",
            "ကျေးဇူးပါ ခင်ဗျာ"
        ]
        
        user_message_lower = user_message.lower().strip()
        return any(pattern.lower() in user_message_lower for pattern in thanks_patterns)
    
    def is_menu_related_query(self, user_message: str) -> bool:
        """
        Check if this is a menu-related query
        (Extracted from burmese_customer_services_handler.py)
        """
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in self.burmese_menu_patterns)
    
    def is_customer_service_question(self, user_message: str) -> bool:
        """
        Check if this is a customer service question that manager can answer
        (Extracted from burmese_customer_services_handler.py)
        """
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in self.burmese_customer_service_patterns)
    
    def _detect_english_patterns(self, message: str) -> Tuple[bool, bool, bool]:
        """
        Detect English patterns using regex
        
        Args:
            message: User message in English
            
        Returns:
            Tuple of (is_greeting, is_goodbye, is_escalation)
        """
        # Normalize message
        normalized_message = message.lower().strip()
        
        # Check for greetings
        is_greeting = any(re.search(pattern, normalized_message) for pattern in self.english_greeting_patterns)
        
        # Check for goodbyes
        is_goodbye = any(re.search(pattern, normalized_message) for pattern in self.english_goodbye_patterns)
        
        # Check for escalation requests
        is_escalation = any(re.search(pattern, normalized_message) for pattern in self.english_escalation_patterns)
        
        return is_greeting, is_goodbye, is_escalation
    
    def get_pattern_confidence(self, message: str, pattern_type: str, language: str) -> float:
        """
        Get confidence score for pattern detection
        
        Args:
            message: User message
            pattern_type: Type of pattern (greeting, goodbye, escalation)
            language: Detected language
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if language in ["my", "myanmar"]:
            return self._get_burmese_pattern_confidence(message, pattern_type)
        else:
            return self._get_english_pattern_confidence(message, pattern_type)
    
    def _get_burmese_pattern_confidence(self, message: str, pattern_type: str) -> float:
        """Get confidence for Burmese pattern detection"""
        normalized_message = message.lower().strip()
        
        if pattern_type == "greeting":
            patterns = self.burmese_greeting_patterns
        elif pattern_type == "goodbye":
            patterns = self.burmese_goodbye_patterns
        elif pattern_type == "escalation":
            patterns = self.burmese_escalation_patterns
        else:
            return 0.0
        
        # Count matching patterns
        matches = sum(1 for pattern in patterns if pattern in normalized_message)
        
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.7
        else:
            return 0.9
    
    def _get_english_pattern_confidence(self, message: str, pattern_type: str) -> float:
        """Get confidence for English pattern detection"""
        normalized_message = message.lower().strip()
        
        if pattern_type == "greeting":
            patterns = self.english_greeting_patterns
        elif pattern_type == "goodbye":
            patterns = self.english_goodbye_patterns
        elif pattern_type == "escalation":
            patterns = self.english_escalation_patterns
        else:
            return 0.0
        
        # Count matching patterns
        matches = sum(1 for pattern in patterns if re.search(pattern, normalized_message))
        
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.8
        else:
            return 0.95 