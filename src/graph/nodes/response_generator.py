"""
Response Generator Node for LangGraph
Generates contextual responses based on retrieved documents and user intent
Enhanced with sophisticated Burmese handling from previous implementation
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.services.semantic_context_extractor import get_semantic_context_extractor

logger = get_logger("response_generator_node")


class ResponseGeneratorNode:
    """
    LangGraph node for response generation
    Generates contextual responses based on RAG results and user intent
    Enhanced with sophisticated Burmese handling
    """
    
    def __init__(self):
        """Initialize response generator node"""
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=self.settings.openai_api_key
        )
        self.semantic_extractor = get_semantic_context_extractor()
        logger.info("response_generator_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate contextual response based on analysis results and routing decisions
        Enhanced for two-LLM-call architecture with better Burmese support
        
        Args:
            state: Current conversation state with analysis and routing results
            
        Returns:
            Updated state with generated response and HITL metadata
        """
        user_message = state.get("user_message", "")
        analysis_result = state.get("analysis_result", {})
        routing_decision = state.get("routing_decision", {})
        rag_results = state.get("rag_results", [])
        
        # Extract information from analysis result
        detected_language = analysis_result.get("detected_language", "en")
        primary_intent = analysis_result.get("primary_intent", "unknown")
        intent_confidence = analysis_result.get("intent_confidence", 0.0)
        cultural_context = analysis_result.get("cultural_context", {})
        conversation_context = analysis_result.get("conversation_context", {})
        
        # Extract information from routing decision
        action_type = routing_decision.get("action_type", "perform_search")
        rag_enabled = routing_decision.get("rag_enabled", True)
        human_handling = routing_decision.get("human_handling", False)
        escalation_reason = routing_decision.get("escalation_reason")
        decision_confidence = routing_decision.get("confidence", 0.5)
        
        # Human assistance is determined by routing decision only - no pattern matching
        requires_human = human_handling
        
        try:
            # Handle different action types based on routing decision
            if action_type == "escalate_to_human":
                response = await self._generate_escalation_response(detected_language, escalation_reason)
            elif action_type == "direct_response":
                if primary_intent == "greeting":
                    response = await self._generate_greeting_response(detected_language, cultural_context)
                elif primary_intent == "goodbye":
                    response = await self._generate_goodbye_response(detected_language, cultural_context)
                else:
                    response = await self._generate_direct_response(user_message, detected_language, primary_intent, cultural_context)
            elif action_type == "perform_search" and rag_enabled:
                if detected_language == "my":
                    # Use enhanced Burmese handling with conversation history
                    conversation_history = state.get("conversation_history", [])
                    response = await self._generate_enhanced_burmese_response(
                            user_message, primary_intent, rag_results, cultural_context, conversation_context
                    )
                else:
                    # Generate contextual response based on RAG results
                    response = await self._generate_contextual_response(
                            user_message, detected_language, primary_intent, rag_results, cultural_context
                    )
            else:
                # Fallback for unknown action types
                response = await self._generate_fallback_response(user_message, detected_language, primary_intent, cultural_context)
            
            # Log response generation
            logger.info("response_generated",
                       intent=primary_intent,
                       language=detected_language,
                       action_type=action_type,
                       intent_confidence=intent_confidence,
                       decision_confidence=decision_confidence,
                       response_length=len(response),
                       has_rag_results=bool(rag_results),
                       rag_enabled=rag_enabled,
                       requires_human=requires_human,
                       human_handling=human_handling)
            
            # Update state with generated response and HITL metadata
            updated_state = state.copy()
            updated_state.update({
                "response": response,
                "response_generated": True,
                "response_quality": self._assess_response_quality(response, intent_confidence, decision_confidence),
                "requires_human": requires_human,
                "human_handling": human_handling,
                "escalation_reason": escalation_reason,
                "action_type": action_type,
                "rag_enabled": rag_enabled
            })
            
            return updated_state
            
        except Exception as e:
            logger.error("response_generation_failed",
                        error=str(e),
                        user_message=user_message[:100])
            
            # Generate fallback response on error
            fallback_response = await self._generate_fallback_response(user_message, detected_language, primary_intent, cultural_context)
            
            updated_state = state.copy()
            updated_state.update({
                "response": fallback_response,
                "response_generated": True,
                "response_quality": "fallback",
                "requires_human": requires_human,
                "human_handling": human_handling,
                "escalation_reason": escalation_reason,
                "action_type": action_type,
                "rag_enabled": rag_enabled
            })
            
            return updated_state
    
    async def _generate_enhanced_burmese_response(self, user_message: str, intent: str, rag_results: List[Dict[str, Any]], cultural_context: Dict[str, Any], conversation_context: Dict[str, Any]) -> str:
        """
        Enhanced Burmese response generation with menu-specific handling
        (Extracted from burmese_customer_services_handler.py)
        """
        try:
            # Check if this is a menu-related query that needs special handling
            if intent == "menu_browse":
                # Handle menu-specific responses
                relevance_score = rag_results[0].get("score", 0.5) if rag_results else 0.0
                return await self._handle_burmese_menu_response(user_message, rag_results, relevance_score)
            
            # Check if we have relevant data
            has_relevant_data = len(rag_results) > 0
            
            if has_relevant_data:
                # Use RAG results to generate contextual response
                context = self._prepare_rag_context(rag_results)
                
                # Log the actual data being used
                logger.info("using_rag_data_for_response",
                           rag_results_count=len(rag_results),
                           context_preview=context[:200])
                
                # Create a prompt that uses the actual Burmese content directly
                prompt = f"""
You are a helpful restaurant chatbot assistant for Cafe Pentagon. Generate a response in Burmese based on the user's question.

USER QUESTION: {user_message}

ACTUAL DATA FROM DATABASE (Use Burmese content directly):
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Use ONLY the actual data provided above
- If the data shows Burmese content (question_mm, answer_mm, myanmar_name, description_mm), use it directly
- Do NOT translate or invent any information not present in the data
- Be friendly and helpful
- Keep the response conversational and natural
- If the data is incomplete, suggest calling +959979732781

IMPORTANT: Use the Burmese content directly from the data. Do not translate or invent information.

RESPONSE:"""
                
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content.strip()
            else:
                # No relevant data found - use sophisticated fallback like the working implementation
                logger.info("no_relevant_rag_data_found", 
                           rag_results_count=len(rag_results))
                return await self._generate_enhanced_burmese_fallback(user_message)
                
        except Exception as e:
            logger.error("enhanced_burmese_response_failed", error=str(e))
            return await self._generate_enhanced_burmese_fallback(user_message)
    
    async def _generate_enhanced_burmese_fallback(self, user_message: str) -> str:
        """Generate sophisticated Burmese fallback response with specific answers for common queries"""
        try:
            # Check for specific common queries and provide direct answers
            user_lower = user_message.lower()
            
            # Location queries
            if any(keyword in user_lower for keyword in ["ဘယ်မှာ", "တည်နေရာ", "လိပ်စာ", "address", "location", "where"]):
                return """အမှတ် ၂၈၅၊ မဟာဗန္ဓုလလမ်း၊ ၃၉ ရပ်ကွက်၊ မြောက်ဒဂုံမြို့နယ်၊ ရန်ကုန်မှာ တည်ရှိပါတယ်။ 

Google Map Link: https://maps.app.goo.gl/G5aFQDUkuW4RuTKe9

ပိုမိုသိရှိလိုပါက +959979732781 ကို ဆက်သွယ်နိုင်ပါတယ်။"""
            
            # Hours queries
            elif any(keyword in user_lower for keyword in ["ဘယ်အချိန်", "ပိတ်ချိန်", "ဖွင့်ချိန်", "opening", "closing", "hours"]):
                return """ကျွန်ုပ်တို့က ၉ နာရီကနေ ၁၀ နာရီအထိ နေ့စဉ်ဖွင့်ပါတယ်။ ၁၀ နာရီမှာပိတ်ပါတယ်။

နောက်ထပ်မေးမြန်းရန်ရှိလျှင် ကျေးဇူးပြု၍ +959979732781 ကို ဆက်သွယ်ပါ။"""
            
            # Photo queries
            elif any(keyword in user_lower for keyword in ["ဓါတ်ပုံ", "ရိုက်ကူး", "photo", "photography"]):
                return """ဓါတ်ပုံရိုက်ကူးခွင့်ရှိပါတယ်။ သို့သော် Professional Camera များအတွက် ခွင့်ပြုချက်လိုအပ်ပါတယ်။

Mobile Phone ဖြင့်ရိုက်ကူးခြင်းကို ခွင့်ပြုထားပါတယ်။

ပိုမိုသိရှိလိုပါက +959979732781 ကို ဆက်သွယ်နိုင်ပါတယ်။"""
            
            # Menu queries
            elif any(keyword in user_lower for keyword in ["ဘာ", "အစားအစာ", "menu", "food", "dish"]):
                return """ကျနော်တို့ရဲ့ မီနူးမှာ ဒီအမျိုးအစားတွေ ရှိပါတယ်:

• **ခေါက်ဆွဲ**
• **ဆလပ်**
• **ထမင်းဟင်း**
• **နံနက်စာ**
• **ပါစတာ**
• **ဟင်းရည်**
• **အဓိကဟင်း**
• **အရံဟင်း**
• **အသားညှပ် နှင့် ဘာဂါ**

ဘယ်အမျိုးအစားကို ကြည့်ချင်ပါသလဲ?"""
            
            # Contact queries
            elif any(keyword in user_lower for keyword in ["ဖုန်း", "ဆက်သွယ်", "phone", "contact", "call"]):
                return """ကျွန်ုပ်တို့ကို ဆက်သွယ်ရန်:

📞 Phone: +959979732781
📍 Address: အမှတ် ၂၈၅၊ မဟာဗန္ဓုလလမ်း၊ ၃၉ ရပ်ကွက်၊ မြောက်ဒဂုံမြို့နယ်၊ ရန်ကုန်

အသေးစိတ်သိရှိလိုပါက ဖုန်းဆက်သွယ်နိုင်ပါတယ်။"""
            
            # Delivery queries
            elif any(keyword in user_lower for keyword in ["ပို့ပေးမှု", "delivery", "ပို့ဆောင်မှု"]):
                return """ပို့ဆောင်မှုဝန်ဆောင်မှုရှိပါတယ်။ 

ပို့ဆောင်မှုအတွက် +959979732781 ကို ဆက်သွယ်ပါ။

ပို့ဆောင်ခမှာ အကွာအဝေးပေါ်မူတည်ပြီး ပြောင်းလဲနိုင်ပါတယ်။"""
            
            # WiFi queries
            elif any(keyword in user_lower for keyword in ["ဝိုင်ဖိုင်", "wifi", "အင်တာနက်", "internet"]):
                return """အခမဲ့ WiFi ဝန်ဆောင်မှုရှိပါတယ်။

WiFi စကားဝှက်ကို စားပွဲတင်ဝန်ထမ်းများထံ မေးမြန်းနိုင်ပါတယ်။

အင်တာနက်အသုံးပြုရာတွင် ပြဿနာရှိပါက +959979732781 ကို ဆက်သွယ်နိုင်ပါတယ်။"""
            
            # General fallback for other queries
            else:
                return "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ် ခင်ဗျာ။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ် ခင်ဗျာ။ နားလည်ပေးတဲ့အတွက် ကျေးဇူး အများကြီး တင်ပါတယ်။"
            
        except Exception as e:
            logger.error("enhanced_burmese_fallback_failed", error=str(e))
            return "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ် ခင်ဗျာ။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ် ခင်ဗျာ။ နားလည်ပေးတဲ့အတွက် ကျေးဇူး အများကြီး တင်ပါတယ်။"
    
    async def _handle_burmese_menu_response(self, user_message: str, rag_results: List[Dict[str, Any]], relevance_score: float) -> str:
        """
        Handle Burmese menu-specific responses using LLM - NO PATTERN MATCHING
        """
        try:
            # Use LLM to generate menu response based on RAG results
            context = self._prepare_rag_context(rag_results)
            prompt = self._create_enhanced_menu_prompt(user_message, context)
            
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
                
        except Exception as e:
            logger.error("burmese_menu_response_handling_failed", error=str(e))
            return "မီနူးနဲ့ပတ်သက်တဲ့ အချက်အလက်ကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"
    
    async def _generate_categories_response(self) -> str:
        """Generate response showing menu categories (extracted from burmese_customer_services_handler.py)"""
        try:
            # Get categories from vector search
            from src.services.vector_search_service import get_vector_search_service
            vector_service = get_vector_search_service()
            categories = await vector_service.get_menu_categories("my")
            
            if not categories:
                return "မီနူးအမျိုးအစားများကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"
            
            # Format natural response
            response = "ကျနော်တို့ရဲ့ မီနူးမှာ ဒီအမျိုးအစားတွေ ရှိပါတယ်:\n\n"
            for category in categories:
                display_name = category["display_name"]
                response += f"• **{display_name}**\n"
            response += "\nဘယ်အမျိုးအစားကို ကြည့်ချင်ပါသလဲ?"
            
            return response
            
        except Exception as e:
            logger.error("categories_response_generation_failed", error=str(e))
            return "မီနူးအမျိုးအစားများကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"
    
    async def _generate_category_items_response(self, category: str) -> str:
        """Generate response showing items from a specific category (extracted from burmese_customer_services_handler.py)"""
        try:
            # Get items from vector search
            from src.services.vector_search_service import get_vector_search_service
            vector_service = get_vector_search_service()
            items = await vector_service.get_category_items(category, "my", limit=12)
            
            if not items:
                return f"'{category}' အမျိုးအစားမှာ အစားအစာများ မတွေ့ရှိပါဘူး။"
            
            # Format response with names and prices
            category_name = vector_service._get_category_display_name(category, "my")
            response = f"**{category_name}** အစားအစာတွေပါ:\n\n"
            
            for i, item in enumerate(items, 1):
                name = item.get("name", "N/A")
                myanmar_name = item.get("name_other", "")
                price = item.get("price", "N/A")
                currency = item.get("currency", "MMK")
                
                if myanmar_name:
                    response += f"{i}. **{name}** ({myanmar_name})\n"
                    response += f"   💰 {price:,} {currency}\n\n"
                else:
                    response += f"{i}. **{name}**\n"
                    response += f"   💰 {price:,} {currency}\n\n"
            
            response += "ဘယ်အစားအစာကို ပိုမိုသိချင်ပါသလဲ?"
            
            return response
            
        except Exception as e:
            logger.error("category_items_response_generation_failed", error=str(e))
            return f"'{category}' အမျိုးအစားမှာ အစားအစာများကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"
    
    async def _generate_item_details_response(self, item_name: str) -> str:
        """Generate response with detailed information about a specific item (extracted from burmese_customer_services_handler.py)"""
        try:
            # Get item details from vector search
            from src.services.vector_search_service import get_vector_search_service
            vector_service = get_vector_search_service()
            item = await vector_service.get_item_details(item_name, "my")
            
            if not item:
                return f"'{item_name}' အစားအစာကို မတွေ့ရှိပါဘူး။"
            
            # Check if this is a clarification request
            if item.get("type") == "clarification_needed":
                return item["message"]
            
            # Check if we have a confidence score
            if not item.get("similarity_score"):
                return f"'{item_name}' အစားအစာနဲ့ပတ်သက်တဲ့ အသေးစိတ်အချက်အလက်ကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"
            
            # Format natural conversational response
            response = f"**{item['name']}** အကြောင်း ပြောပြပေးပါရစေ။\n\n"
            response += f"ဈေးနှုန်းကတော့ {item['price']:,} {item['currency']} ဖြစ်ပါတယ်။\n"
            response += f"{item['description']}\n\n"
            response += f"ပြင်ဆင်ချိန်က {item['preparation_time']} ဖြစ်ပါတယ်။\n"
            response += f"အစပ်အဆင့်က {item['spice_level']}/4 ဖြစ်ပါတယ်။\n"
            
            if item.get("ingredients"):
                response += f"\nပါဝင်ပစ္စည်းတွေကတော့ {', '.join(item['ingredients'])} တို့ ဖြစ်ပါတယ်။\n"
            
            if item.get("allergens"):
                response += f"\nဓာတ်မတည့်မှုရှိတဲ့ ပါဝင်ပစ္စည်းတွေကတော့ {', '.join(item['allergens'])} တို့ ဖြစ်ပါတယ်။\n"
            
            # Add suggested alternatives if available
            if item.get('suggested_alternatives'):
                response += f"\nအလားတူ အစားအသောက်များ: {', '.join(item['suggested_alternatives'])}"
            
            response += f"\nပုံကို ကြည့်ချင်ပါသလား?"
            
            return response
            
        except Exception as e:
            logger.error("item_details_response_generation_failed", error=str(e))
            return f"'{item_name}' အစားအစာနဲ့ပတ်သက်တဲ့ အသေးစိတ်အချက်အလက်ကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"
    


    def _create_enhanced_menu_prompt(self, user_message: str, context: str) -> str:
        """Create enhanced menu response prompt that uses actual Burmese data"""
        return f"""
You are a helpful restaurant chatbot assistant for Cafe Pentagon. Generate a response in Burmese based on the user's question about the menu.

USER QUESTION: {user_message}

ACTUAL MENU DATA FROM DATABASE (Burmese content included):
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Use ONLY the actual menu data provided above
- If the data shows Burmese names (myanmar_name), use them
- If the data shows Burmese descriptions (description_mm), use them
- Do NOT translate or invent any information not present in the data
- If the data shows specific items with prices, describe them accurately
- Be friendly and helpful
- Keep the response conversational and natural
- If the data is incomplete, mention that more details can be found by calling +959979732781

IMPORTANT: Use the Burmese content directly from the data. Do not translate or invent information.

RESPONSE:"""

    def _create_enhanced_faq_prompt(self, user_message: str, context: str) -> str:
        """Create enhanced FAQ response prompt that uses actual Burmese data"""
        return f"""
You are a helpful restaurant chatbot assistant for Cafe Pentagon. Generate a response in Burmese based on the user's FAQ question.

USER QUESTION: {user_message}

ACTUAL FAQ DATA FROM DATABASE (Burmese content included):
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Use ONLY the actual FAQ data provided above
- If the data shows Burmese questions (question_mm), use them
- If the data shows Burmese answers (answer_mm), use them
- Do NOT translate or invent any information not present in the data
- If the data shows specific answers, provide them accurately
- If the data shows opening hours, location, or other details, use them exactly
- Be friendly and helpful
- Keep the response conversational and natural
- If the data is incomplete, suggest calling +959979732781 for more details

IMPORTANT: Use the Burmese content directly from the data. Do not translate or invent information.

RESPONSE:"""

    def _create_enhanced_job_prompt(self, user_message: str, context: str) -> str:
        """Create enhanced job response prompt that uses actual Burmese data"""
        return f"""
You are a helpful restaurant chatbot assistant for Cafe Pentagon. Generate a response in Burmese about job opportunities.

USER QUESTION: {user_message}

ACTUAL JOB DATA FROM DATABASE (Burmese content included):
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Use ONLY the actual job data provided above
- If the data shows Burmese titles (title_mm), use them
- If the data shows Burmese descriptions (description_mm), use them
- Do NOT translate or invent any information not present in the data
- If the data shows available positions, describe them accurately
- If the data shows application process, include it
- Be friendly and professional
- Keep the response helpful and informative

IMPORTANT: Use the Burmese content directly from the data. Do not translate or invent information.

RESPONSE:"""

    def _create_enhanced_general_prompt(self, user_message: str, context: str) -> str:
        """Create enhanced general response prompt that uses actual Burmese data"""
        return f"""
You are a helpful restaurant chatbot assistant for Cafe Pentagon. Generate a response in Burmese based on the user's question.

USER QUESTION: {user_message}

ACTUAL DATA FROM DATABASE (Burmese content included):
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Use ONLY the actual data provided above
- If the data shows Burmese content (title_mm, description_mm, etc.), use it directly
- Do NOT translate or invent any information not present in the data
- Provide relevant information based on the data
- Be friendly and helpful
- Keep the response conversational and natural
- If information is incomplete, suggest calling +959979732781

IMPORTANT: Use the Burmese content directly from the data. Do not translate or invent information.

RESPONSE:"""

    async def _generate_greeting_response(self, language: str, cultural_context: Dict[str, Any]) -> str:
        """Generate greeting response with cultural context awareness"""
        formality_level = cultural_context.get("formality_level", "casual")
        uses_honorifics = cultural_context.get("uses_honorifics", False)
        
        if language == "my":
            if formality_level == "very_formal" or uses_honorifics:
                return "မင်္ဂလာပါ ခင်ဗျာ! ကျနော်တို့ Cafe Pentagon မှာ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ ခင်ဗျာ?"
            elif formality_level == "formal":
                return "မင်္ဂလာပါ! ကျနော်တို့ Cafe Pentagon မှာ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ?"
            else:
                return "မင်္ဂလာ! ကျနော်တို့ Cafe Pentagon မှာ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ?"
        else:
            return "Hello! Welcome to Cafe Pentagon. How can I help you today?"
    
    async def _generate_goodbye_response(self, language: str, cultural_context: Dict[str, Any]) -> str:
        """Generate goodbye response with cultural context awareness"""
        formality_level = cultural_context.get("formality_level", "casual")
        uses_honorifics = cultural_context.get("uses_honorifics", False)
        
        if language == "my":
            if formality_level == "very_formal" or uses_honorifics:
                return "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ! အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော် ခင်ဗျာ။"
            elif formality_level == "formal":
                return "ကျေးဇူးတင်ပါတယ်! အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော်။"
            else:
                return "ကျေးဇူးပါ! အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော်။"
        else:
            return "Thank you! Feel free to ask if you need anything else."
    
    async def _generate_escalation_response(self, language: str, escalation_reason: Optional[str]) -> str:
        """Generate escalation response with specific reason"""
        if language == "my":
            if escalation_reason and "human assistance" in escalation_reason.lower():
                return "တာဝန်ရှိ ဝန်ထမ်းတစ်ယောက် လာပြီး ကူညီပေးပါလိမ့်မယ်..၊ ခဏစောင့်ပေးပါ ခင်ဗျာ.."
            elif escalation_reason:
                return f"ကျေးဇူးပြု၍ ခဏစောင့်ပေးပါ ခင်ဗျာ...။ {escalation_reason} အတွက် သက်ဆိုင်ရာ ဝန်ထမ်းက ကူညီပေးပါလိမ့်မယ်။"
            else:
                return "တာဝန်ရှိ ဝန်ထမ်းတစ်ယောက် လာပြီး ကူညီပေးပါလိမ့်မယ်..၊ ခဏစောင့်ပေးပါ ခင်ဗျာ.."
        else:
            if escalation_reason and "human assistance" in escalation_reason.lower():
                return "The responsible staff will be here and assist to you. could you wait a moment"
            elif escalation_reason:
                return f"Please wait while I connect you to a human staff member who can help you with {escalation_reason.lower()}."
            else:
                return "The responsible staff will be here and assist to you. could you wait a moment"
    
    async def _generate_fallback_response(self, user_message: str, language: str, intent: str, cultural_context: Dict[str, Any]) -> str:
        """Generate fallback response when no relevant information is found"""
        formality_level = cultural_context.get("formality_level", "casual")
        uses_honorifics = cultural_context.get("uses_honorifics", False)
        
        if language == "my":
            if formality_level == "very_formal" or uses_honorifics:
                return "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ် ခင်ဗျာ။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ် ခင်ဗျာ။ နားလည်ပေးတဲ့အတွက် ကျေးဇူး အများကြီး တင်ပါတယ်။"
            elif formality_level == "formal":
                return "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ်။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ်။"
            else:
                return "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ်။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ်။"
        else:
            return "I'm sorry, I don't have specific information about that. Please call +959979732781 for detailed assistance. Thank you for your understanding."
    
    async def _generate_contextual_response(self, user_message: str, language: str, intent: str, rag_results: List[Dict[str, Any]], cultural_context: Dict[str, Any]) -> str:
        """Generate contextual response based on RAG results with cultural context"""
        
        # Prepare context from RAG results
        context = self._prepare_rag_context(rag_results)
        
        # Create prompt based on intent
        if intent == "menu_browse":
            prompt = self._create_menu_response_prompt(user_message, context, language)
        elif intent == "faq":
            prompt = self._create_faq_response_prompt(user_message, context, language)
        elif intent in ["job_application", "jobs"]:
            prompt = self._create_job_response_prompt(user_message, context, language)
        else:
            prompt = self._create_general_response_prompt(user_message, context, language)
        
        try:
            # Generate response using LLM
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
            
        except Exception as e:
            logger.error("llm_response_generation_failed", error=str(e))
            return await self._generate_fallback_response(user_message, language, intent, cultural_context)
    
    def _prepare_rag_context(self, rag_results: List[Dict[str, Any]]) -> str:
        """Prepare context string from RAG results with detailed information"""
        if not rag_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(rag_results[:5], 1):  # Top 5 results
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)
            source = result.get("source", "")
            
            # Add detailed information
            context_parts.append(f"=== Result {i} (Score: {score:.3f}, Source: {source}) ===")
            context_parts.append(f"Content: {content}")
            
            # Add metadata details if available
            if metadata:
                if "title" in metadata:
                    context_parts.append(f"Title: {metadata['title']}")
                if "category" in metadata:
                    context_parts.append(f"Category: {metadata['category']}")
                if "price" in metadata:
                    context_parts.append(f"Price: {metadata['price']}")
                if "description" in metadata:
                    context_parts.append(f"Description: {metadata['description']}")
                if "name" in metadata:
                    context_parts.append(f"Name: {metadata['name']}")
                if "myanmar_name" in metadata:
                    context_parts.append(f"Myanmar Name: {metadata['myanmar_name']}")
                # Add Burmese-specific fields
                if "question_mm" in metadata:
                    context_parts.append(f"Question (Myanmar): {metadata['question_mm']}")
                if "answer_mm" in metadata:
                    context_parts.append(f"Answer (Myanmar): {metadata['answer_mm']}")
                if "description_mm" in metadata:
                    context_parts.append(f"Description (Myanmar): {metadata['description_mm']}")
                if "title_mm" in metadata:
                    context_parts.append(f"Title (Myanmar): {metadata['title_mm']}")
            
            context_parts.append("")  # Empty line for separation
        
        return "\n".join(context_parts)
    
    def _create_menu_response_prompt(self, user_message: str, context: str, language: str) -> str:
        """Create prompt for menu-related responses"""
        if language == "my":
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response in Burmese based on the user's question about the menu.

USER QUESTION: {user_message}

MENU INFORMATION:
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Be friendly and helpful
- Provide relevant menu information
- If specific items are mentioned, include details like price, description, ingredients
- If no specific items are mentioned, suggest popular items or categories
- Keep the response conversational and natural

RESPONSE:"""
        else:
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response based on the user's question about the menu.

USER QUESTION: {user_message}

MENU INFORMATION:
{context}

INSTRUCTIONS:
- Be friendly and helpful
- Provide relevant menu information
- If specific items are mentioned, include details like price, description, ingredients
- If no specific items are mentioned, suggest popular items or categories
- Keep the response conversational and natural

RESPONSE:"""
    
    def _create_faq_response_prompt(self, user_message: str, context: str, language: str) -> str:
        """Create prompt for FAQ-related responses"""
        if language == "my":
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response in Burmese based on the user's FAQ question.

USER QUESTION: {user_message}

FAQ INFORMATION:
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Be friendly and helpful
- Provide clear and accurate information
- If information is incomplete, suggest calling +959979732781
- Keep the response conversational and natural

RESPONSE:"""
        else:
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response based on the user's FAQ question.

USER QUESTION: {user_message}

FAQ INFORMATION:
{context}

INSTRUCTIONS:
- Be friendly and helpful
- Provide clear and accurate information
- If information is incomplete, suggest calling +959979732781
- Keep the response conversational and natural

RESPONSE:"""
    
    def _create_job_response_prompt(self, user_message: str, context: str, language: str) -> str:
        """Create prompt for job-related responses"""
        if language == "my":
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response in Burmese about job opportunities.

USER QUESTION: {user_message}

JOB INFORMATION:
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Be friendly and professional
- Provide information about available positions
- Include application process if mentioned
- Encourage qualified candidates to apply

RESPONSE:"""
        else:
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response about job opportunities.

USER QUESTION: {user_message}

JOB INFORMATION:
{context}

INSTRUCTIONS:
- Be friendly and professional
- Provide information about available positions
- Include application process if mentioned
- Encourage qualified candidates to apply

RESPONSE:"""
    
    def _create_general_response_prompt(self, user_message: str, context: str, language: str) -> str:
        """Create prompt for general responses"""
        if language == "my":
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response in Burmese based on the user's question.

USER QUESTION: {user_message}

RELEVANT INFORMATION:
{context}

INSTRUCTIONS:
- Respond in Burmese language
- Be friendly and helpful
- Provide relevant information
- If information is incomplete, suggest calling +959979732781
- Keep the response conversational and natural

RESPONSE:"""
        else:
            return f"""
You are a helpful restaurant chatbot assistant. Generate a response based on the user's question.

USER QUESTION: {user_message}

RELEVANT INFORMATION:
{context}

INSTRUCTIONS:
- Be friendly and helpful
- Provide relevant information
- If information is incomplete, suggest calling +959979732781
- Keep the response conversational and natural

RESPONSE:"""
    
    def _assess_response_quality(self, response: str, intent_confidence: float, decision_confidence: float) -> str:
        """Assess the quality of the generated response based on confidence scores"""
        # Calculate overall confidence
        overall_confidence = (intent_confidence + decision_confidence) / 2
        
        if overall_confidence > 0.7:
            return "high"
        elif overall_confidence > 0.4:
            return "medium"
        else:
            return "low" 

 

    async def _generate_direct_response(self, user_message: str, language: str, intent: str, cultural_context: Dict[str, Any]) -> str:
        """Generate direct response for non-search intents"""
        formality_level = cultural_context.get("formality_level", "casual")
        uses_honorifics = cultural_context.get("uses_honorifics", False)
        
        if language == "my":
            if intent == "greeting":
                return await self._generate_greeting_response(language, cultural_context)
            elif intent == "goodbye":
                return await self._generate_goodbye_response(language, cultural_context)
            else:
                # Generic direct response
                if formality_level == "very_formal" or uses_honorifics:
                    return "နားလည်ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ် ခင်ဗျာ။ အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော် ခင်ဗျာ။"
                elif formality_level == "formal":
                    return "နားလည်ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်။ အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော်။"
                else:
                    return "ကျေးဇူးပါ။ အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော်။"
        else:
            if intent == "greeting":
                return await self._generate_greeting_response(language, cultural_context)
            elif intent == "goodbye":
                return await self._generate_goodbye_response(language, cultural_context)
            else:
                return "Thank you for your message. Feel free to ask if you need anything else." 