"""
Intent Classification Node for LangGraph
Integrates with existing AI intent classifier for FAQ, Menu, Job Application routing
"""

from typing import Dict, Any, List, Optional
from src.agents.intent_classifier import AIIntentClassifier
from src.utils.logger import get_logger

logger = get_logger("intent_classifier_node")


class IntentClassifierNode:
    """
    LangGraph node for intent classification
    Routes queries to appropriate Pinecone namespace (faq, menu, job_application)
    """
    
    def __init__(self):
        """Initialize intent classifier node"""
        self.intent_classifier = AIIntentClassifier()
        logger.info("intent_classifier_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced intent classification with Burmese menu analysis
        (Extracted from burmese_customer_services_handler.py)
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with intent classification and namespace routing
        """
        user_message = state.get("user_message", "")
        detected_language = state.get("detected_language", "en")
        
        if not user_message:
            logger.warning("empty_user_message")
            return self._set_default_intent(state)
        
        try:
            # Skip intent classification for greetings/goodbyes (already handled by pattern matcher)
            if state.get("is_greeting", False) or state.get("is_goodbye", False):
                logger.info("greeting_goodbye_detected")
                return self._set_default_intent(state)
            
            # Skip for escalation requests (handled by escalation system)
            if state.get("is_escalation_request", False):
                logger.info("escalation_request_detected")
                return self._set_default_intent(state)
            
            # Enhanced Burmese menu analysis with conversation history
            conversation_history = state.get("conversation_history", [])
            if detected_language in ["my", "myanmar"]:
                menu_analysis = await self._analyze_burmese_menu_request(user_message, conversation_history)
                if menu_analysis and menu_analysis.get("action") != "OTHER":
                    # Handle menu-specific requests
                    return await self._handle_burmese_menu_intent(state, menu_analysis)
            
            # Use conversation history for better intent classification
            if conversation_history:
                logger.info("using_conversation_history_for_intent_classification", 
                           history_length=len(conversation_history))
            
            # Create state for intent classifier
            classifier_state = {
                "user_message": user_message,
                "user_language": detected_language
            }
            
            # Classify intent using existing AI classifier
            result = await self.intent_classifier.process(classifier_state)
            
            # Extract intent information
            intents = result.get("detected_intents", [])
            primary_intent = result.get("primary_intent", "unknown")
            
            # Get confidence from the first intent
            confidence_score = 0.0
            if intents and len(intents) > 0:
                confidence_score = intents[0].get("confidence", 0.0)
            
            # Map intent to namespace
            target_namespace = self._map_intent_to_namespace(primary_intent)
            
            # Log classification results
            logger.info("intent_classification_completed", 
                       intent=primary_intent,
                       confidence=confidence_score,
                       namespace=target_namespace,
                       language=detected_language)
            
            # Update state with intent classification
            updated_state = state.copy()
            updated_state.update({
                "detected_intent": primary_intent,
                "intent_confidence": confidence_score,
                "all_intents": intents,
                "target_namespace": target_namespace,
                "intent_reasoning": result.get("reasoning", ""),
                "intent_entities": result.get("entities", {})
            })
            
            return updated_state
            
        except Exception as e:
            logger.error("intent_classification_failed", 
                        error=str(e),
                        user_message=user_message[:100])
            
            # Fallback to default intent
            return self._set_default_intent(state)
    
    async def _analyze_burmese_menu_request(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyze if the request is menu-related and determine the specific action
        (Extracted from burmese_customer_services_handler.py)
        """
        try:
            # First, check if this is clearly NOT a menu query
            non_menu_keywords = [
                "တီးဝိုင်း", "ဂီတ", "သီချင်း", "ဖျော်ဖြေ", "အစီအစဉ်", "ပွဲ", "ပါတီ",
                "ဓါတ်ပုံ", "ရိုက်ကူး", "ကင်မရာ",  # Removed "ပုံ" to allow menu image requests
                "ဆိုင်က ဘယ်မှာ", "လိပ်စာ", "တည်နေရာ", "ဘယ်မှာ ရှိ",
                "ဖုန်း", "ဆက်သွယ်", "ခေါ်ဆို", "ဖုန်းနံပါတ်",
                # Removed "ဈေးနှုန်း", "စျေးနှုန်း" to allow menu price queries
                "ဈေးကြီး", "စျေးသက်သာ",
                "အချိန်", "ဖွင့်ချိန်", "ပိတ်ချိန်", "ဘယ်အချိန်",
                "ဝိုင်ဖိုင်", "wifi", "အင်တာနက်", "အင်တာနက်လိုင်း",
                "မီး", "မီးစက်", "အဲကွန်း", "လေအေးပေးစက်",
                "အပြင်ထိုင်ခုံ", "အပြင်ပန်း", "ဆေးလိပ်", "သောက်ခွင့်",
                "အစားအသောက်", "ပို့ပေးမှု", "delivery", "ပို့ဆောင်မှု",
                "ငွေပေးချေမှု", "ငွေပေးနည်း", "ကတ်", "ငွေသား",
                "ပရိုမိုးရှင်း", "လျှော့စျေး", "အထူးပရိုမို",
                "ကလေး", "ကလေးများ", "ကလေးမီနူး",
                "wheelchair", "ဘီးထိုင်ခုံ", "အသုံးပြုခွင့်",
                "အစားအသောက် ဝန်ဆောင်မှု", "catering", "ပွဲထိုး"
            ]
            
            # Check if the query contains non-menu keywords
            user_message_lower = user_message.lower()
            for keyword in non_menu_keywords:
                if keyword.lower() in user_message_lower:
                    return None  # This is not a menu query
            
            # Use vector service to analyze the request
            from src.services.vector_search_service import get_vector_search_service
            vector_service = get_vector_search_service()
            analysis = await vector_service.analyze_user_request(user_message, conversation_history)
            
            # Only return if it's a menu-related action
            action = analysis.get("action", "OTHER")
            if action in ["SHOW_CATEGORIES", "SHOW_CATEGORY_ITEMS", "SHOW_ITEM_DETAILS", "SHOW_ITEM_IMAGE"]:
                return analysis
            
            return None
            
        except Exception as e:
            logger.error("menu_request_analysis_failed", error=str(e))
            return None
    
    async def _handle_burmese_menu_intent(self, state: Dict[str, Any], menu_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle menu-specific requests using structured responses
        (Extracted from burmese_customer_services_handler.py)
        """
        try:
            action = menu_analysis.get("action", "OTHER")
            
            # Map menu actions to intents
            intent_mapping = {
                "SHOW_CATEGORIES": "menu_browse",
                "SHOW_CATEGORY_ITEMS": "menu_browse", 
                "SHOW_ITEM_DETAILS": "menu_browse",
                "SHOW_ITEM_IMAGE": "menu_browse"
            }
            
            detected_intent = intent_mapping.get(action, "menu_browse")
            target_namespace = "menu"
            
            # Update state with menu-specific intent
            updated_state = state.copy()
            updated_state.update({
                "detected_intent": detected_intent,
                "intent_confidence": 0.8,  # High confidence for menu actions
                "all_intents": [{"intent": detected_intent, "confidence": 0.8}],
                "target_namespace": target_namespace,
                "intent_reasoning": f"Menu action detected: {action}",
                "intent_entities": menu_analysis.get("entities", {}),
                "menu_action": action,  # Store the specific menu action
                "menu_analysis": menu_analysis  # Store the full analysis
            })
            
            logger.info("burmese_menu_intent_handled", 
                       action=action,
                       intent=detected_intent,
                       namespace=target_namespace)
            
            return updated_state
                
        except Exception as e:
            logger.error("burmese_menu_intent_handling_failed", error=str(e))
            return self._set_default_intent(state)
    
    def _is_general_menu_question(self, user_message: str) -> bool:
        """
        Check if this is a general menu question asking for categories
        (Extracted from burmese_customer_services_handler.py)
        """
        general_menu_keywords = [
            "ဘာ", "အစားအစာ", "ရှိလား", "ရလဲ", "menu", "food", "dish", "item",
            "ဘယ်လို", "ဘာတွေ", "ဘာများ", "ဘာရှိ", "what", "kind", "available",
            "အမျိုးအစား", "category", "ဘာတွေ", "ဘာများ", "ဘာရှိ"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in general_menu_keywords)
    
    def _is_specific_category_question(self, user_message: str) -> bool:
        """
        Check if this is asking for specific category items
        (Extracted from burmese_customer_services_handler.py)
        """
        category_keywords = [
            "burger", "ဘာဂါ", "noodle", "ခေါက်ဆွဲ", "pasta", "ပါစတာ",
            "rice", "ထမင်း", "salad", "ဆလပ်", "sandwich", "ဆန်းဝစ်",
            "breakfast", "မနက်စာ", "main", "အဓိက", "appetizer", "အစာစား",
            "soup", "ဟင်းချို", "drink", "သောက်စရာ", "dessert", "အချိုပွဲ"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in category_keywords)
    
    def _is_specific_item_question(self, user_message: str) -> bool:
        """
        Check if this is asking for specific item details
        (Extracted from burmese_customer_services_handler.py)
        """
        specific_item_keywords = [
            "ဈေးနှုန်း", "price", "ပါဝင်ပစ္စည်း", "ingredient", "အသေးစိတ်", "detail",
            "ဘယ်လို", "ဘယ်လောက်", "ဘာပါ", "ဘာတွေ", "ဘာများ", "ဘာရှိ",
            "အရသာ", "taste", "ပြင်ဆင်ချိန်", "preparation", "အစပ်", "spice"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in specific_item_keywords)
    
    def _map_intent_to_namespace(self, intent: str) -> str:
        """
        Map detected intent to Pinecone namespace
        
        Args:
            intent: Detected intent from classifier
            
        Returns:
            Target namespace for RAG retrieval
        """
        # Map intents to namespaces
        intent_namespace_mapping = {
            # FAQ-related intents
            "faq": "faq",
            "reservation": "faq",  # Reservation questions go to FAQ
            "events": "faq",       # Event questions go to FAQ
            "complaint": "faq",    # Complaints go to FAQ
            
            # Menu-related intents  
            "menu_browse": "menu",
            "order_place": "menu",  # Ordering goes to menu
            
            # Job application intents
            "job_application": "jobs",
            "career": "jobs",
            "employment": "jobs",
            "work": "jobs",
            "hire": "jobs",
            "position": "jobs",
            
            # Default fallback
            "unknown": "faq",  # Unknown queries go to FAQ as fallback
            "greeting": "faq",  # Greetings go to FAQ for general responses
            "goodbye": "faq"    # Goodbyes go to FAQ for closing responses
        }
        
        return intent_namespace_mapping.get(intent, "faq")
    
    def _set_default_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default intent when classification is skipped or fails
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with default intent
        """
        updated_state = state.copy()
        updated_state.update({
            "detected_intent": "unknown",
            "intent_confidence": 0.0,
            "all_intents": [],
            "target_namespace": "faq",
            "intent_reasoning": "Default fallback intent",
            "intent_entities": {}
        })
        
        return updated_state 