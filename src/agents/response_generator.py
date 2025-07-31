"""
AI-Enhanced Response Generator for Cafe Pentagon Chatbot
Provides contextual, language-aware responses using AI with vector search
"""

import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from src.agents.base import BaseAgent
from src.data.loader import get_data_loader
from src.services.vector_search_service import get_vector_search_service
from src.utils.logger import get_logger
from src.utils.burmese_processor import enhance_burmese_response, translate_burmese_food_request, create_burmese_aware_prompt
from src.config.settings import get_settings

logger = get_logger("enhanced_response_generator")


class EnhancedResponseGenerator(BaseAgent):
    """
    Enhanced response generator with contextual responses using vector search
    """
    
    def __init__(self):
        """Initialize AI-enhanced response generator"""
        super().__init__("ai_enhanced_response_generator")
        self.data_loader = get_data_loader()
        self.settings = get_settings()
        self.vector_search = get_vector_search_service()
        
        # Initialize OpenAI model for response generation
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Use GPT-4o for better quality
            temperature=0.3,  # Lower temperature for more consistent responses
            max_tokens=500,   # Limit response length for conciseness
            api_key=self.settings.openai_api_key
        )
        
        # Response templates
        self.response_templates = {
            "greeting": {
                "en": [
                    "Hi! Welcome to Cafe Pentagon! 🍽️ How can I help you today?",
                    "Hello there! What would you like to know about our menu or services?",
                    "Hey! Welcome to Cafe Pentagon! What can I help you with?"
                ],
                "my": [
                    "မင်္ဂလာပါ! Cafe Pentagon မှ ကြိုဆိုပါတယ်! 🍽️ ဘယ်လိုကူညီပေးရမလဲ?",
                    "ဟယ်လို! မီနူး သို့မဟုတ် ဝန်ဆောင်မှုများကို မေးနိုင်ပါတယ်!",
                    "မင်္ဂလာပါ! Cafe Pentagon မှ ကြိုဆိုပါတယ်! ဘာကို ကူညီပေးရမလဲ?",
                    "မင်္ဂလာပါ အစ်ကို/အစ်မ! Cafe Pentagon မှ ကြိုဆိုပါတယ်! ဘာကို ကူညီပေးရမလဲ?",
                    "ဟယ်လို! ကျနော်တို့ရဲ့ မီနူး သို့မဟုတ် ဝန်ဆောင်မှုများကို မေးနိုင်ပါတယ်!"
                ]
            },
            "menu_browse": {
                "en": [
                    "Here's our menu! We have a variety of delicious dishes including {categories}. What would you like to know more about?",
                    "Great choice! Our menu features {categories}. Is there a specific category or dish you're interested in?",
                    "I'd be happy to show you our menu! We offer {categories}. What catches your eye?"
                ],
                "my": [
                    "ဒါကတော့ ကျနော်တို့ရဲ့ မီနူးပါ! {categories} အပါအဝင် အရသာရှိတဲ့ အစားအစာများစွာ ရှိပါတယ်။ ဘာကို ပိုမိုသိချင်ပါသလဲ?",
                    "ရွေးချယ်မှု ကောင်းပါတယ်! ကျနော်တို့ရဲ့ မီနူးမှာ {categories} ပါဝင်ပါတယ်။ သီးသန့်စိတ်ဝင်စားတဲ့ အမျိုးအစား သို့မဟုတ် အစားအစာ ရှိပါသလား?",
                    "မီနူးကို ပြပေးရတာ ဝမ်းသာပါတယ်! ကျနော်တို့မှာ {categories} ရှိပါတယ်။ ဘာက စိတ်ဝင်စားစရာ ကောင်းပါသလဲ?",
                    "ကျနော်တို့ရဲ့ မီနူးမှာ {categories} တွေ ရှိပါတယ်။ ဘယ်အမျိုးအစားကို ကြည့်ချင်ပါသလဲ?",
                    "အရသာရှိတဲ့ အစားအစာတွေ များစွာ ရှိပါတယ်။ {categories} စတဲ့ အမျိုးအစားတွေ ပါဝင်ပါတယ်။ ဘာကို ကြည့်ချင်ပါသလဲ?"
                ]
            },
            "faq": {
                "en": [
                    "I found some information that might help: {answer}",
                    "Here's what I know about that: {answer}",
                    "Let me share this information with you: {answer}"
                ],
                "my": [
                    "ကူညီနိုင်မယ့် အချက်အလက်တွေ တွေ့ရှိပါတယ်: {answer}",
                    "ဒါနဲ့ပတ်သက်ပြီး သိရှိရတာက: {answer}",
                    "ဒီအချက်အလက်ကို မျှဝေပေးပါရစေ: {answer}"
                ]
            },
            "unknown": {
                "en": [
                    "Sorry, I didn't quite understand. Could you rephrase that? I can help with menu, reservations, and more!",
                    "I'm not sure what you mean. Could you try asking differently? I'm here to help!",
                    "Let me help you better. What are you looking for? I can assist with menu, location, hours, and other info."
                ],
                "my": [
                    "နားမလည်ပါဘူး။ ပြန်ပြောပေးနိုင်ပါသလား? မီနူး၊ ကြိုတင်မှာယူခြင်း နှင့် အခြားအရာများကို ကူညီပေးနိုင်ပါတယ်!",
                    "သေချာမကြားပါဘူး။ နောက်တစ်မျိုး မေးကြည့်နိုင်ပါသလား? ကူညီပေးရန် ရှိနေပါတယ်!",
                    "ပိုကောင်းအောင် ကူညီပေးပါရစေ။ ဘာကို ရှာဖွေနေတာလဲ? မီနူး၊ နေရာ၊ ဖွင့်ချိန် နှင့် အခြားအချက်အလက်များကို ကူညီပေးနိုင်ပါတယ်။"
                ]
            }
        }

    async def generate_response(self, state: Dict[str, Any]) -> str:
        """Generate contextual response based on state using AI"""
        user_message = state.get("user_message", "")
        primary_intent = state.get("primary_intent", "unknown")
        user_language = state.get("user_language", "en")
        intents = state.get("detected_intents", [])
        
        # Get language key
        lang_key = "my" if user_language in ["my", "myanmar"] else "en"
        
        # Debug logging for language detection
        logger.info("language_debug", 
                   user_message=user_message[:100],
                   user_language=user_language,
                   lang_key=lang_key,
                   primary_intent=primary_intent)
        
        # For menu browsing, prioritize vector search service
        if primary_intent == "menu_browse":
            try:
                response = await self._generate_menu_response(user_message, lang_key, state)
                logger.info("vector_search_menu_response_generated", 
                           response_language=lang_key,
                           response_length=len(response),
                           response_preview=response[:100])
                return response
            except Exception as e:
                logger.error("vector_search_menu_response_failed", error=str(e))
                # Fall back to AI response
        
        try:
            # Try AI-powered response generation for other intents
            ai_response = await self._generate_ai_response(user_message, primary_intent, lang_key, state)
            if ai_response:
                logger.info("ai_response_generated", 
                           response_language=lang_key,
                           response_length=len(ai_response),
                           response_preview=ai_response[:100])
                return ai_response
        except Exception as e:
            logger.error("ai_response_generation_failed", error=str(e))
            # Fall back to template-based responses
        
        # Generate response based on intent (fallback)
        if primary_intent == "greeting":
            response = self._generate_greeting_response(lang_key)
        elif primary_intent == "faq":
            response = await self._generate_faq_response(user_message, lang_key)
        elif primary_intent == "order_place":
            response = self._generate_order_response(lang_key)
        elif primary_intent == "reservation":
            response = self._generate_reservation_response(lang_key)
        elif primary_intent == "events":
            response = await self._generate_events_response(user_message, lang_key)
        elif primary_intent == "complaint":
            response = self._generate_complaint_response(lang_key)
        elif primary_intent == "goodbye":
            response = self._generate_goodbye_response(lang_key)
        else:
            response = self._generate_unknown_response(lang_key)
        
        logger.info("template_response_generated", 
                   response_language=lang_key,
                   response_length=len(response),
                   response_preview=response[:100])
        
        return response

    async def _generate_ai_response(self, user_message: str, intent: str, language: str, state: Dict[str, Any]) -> Optional[str]:
        """Generate AI-powered response with conversation memory"""
        try:
            # Get relevant data based on intent
            context_data = await self._get_context_data(intent, state)
            
            # Get conversation history for context
            conversation_history = self._get_conversation_context(state)
            
            # For Burmese, use enhanced prompt
            if language in ["my", "myanmar"]:
                prompt = create_burmese_aware_prompt(user_message, intent)
                # Add context data to prompt
                prompt += f"\n\nCONTEXT DATA:\n{json.dumps(context_data, indent=2, ensure_ascii=False)}"
            else:
                # Create AI prompt with memory for other languages
                prompt = self._create_ai_prompt_with_memory(user_message, intent, language, context_data, conversation_history)
            
            # Get AI response
            response = await self.llm.ainvoke(prompt)
            
            # For Burmese, enhance the response with cultural context
            response_text = response.content.strip()
            if language in ["my", "myanmar"]:
                cultural_context = state.get("burmese_cultural_context", {})
                response_text = enhance_burmese_response(response_text, cultural_context)
            
            # Debug: Log the prompt and response for troubleshooting
            logger.info("ai_prompt_debug", 
                       prompt_length=len(prompt),
                       conversation_history_length=len(conversation_history),
                       response_length=len(response_text),
                       language=language)
            
            return response_text
            
        except Exception as e:
            logger.error("ai_response_generation_error", error=str(e))
            return None
    
    def _create_ai_prompt(self, user_message: str, intent: str, language: str, context_data: Dict[str, Any]) -> str:
        """Create AI prompt for response generation"""
        language_name = "Burmese" if language == "my" else "English"
        
        prompt = f"""
You are a helpful and friendly restaurant chatbot for Cafe Pentagon. You are having a natural conversation with a customer.

USER MESSAGE: {user_message}
DETECTED INTENT: {intent}
LANGUAGE: {language_name}

CONTEXT DATA:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

CRITICAL INSTRUCTIONS:
1. Respond ONLY in {language_name} - do not translate or mix languages
2. Use the context data that matches the user's language ({language_name})
3. Be natural, friendly, and conversational - like talking to a friend
4. Keep responses concise but helpful - don't be verbose
5. For menu items: mention name, price, and key features briefly
6. For FAQ: give clear, direct answers in a friendly tone
7. For events: share relevant details in an engaging way
8. If you don't have specific information, be honest and helpful
9. Use natural {language_name} expressions and tone
10. Don't be formal or robotic - be warm and approachable

IMPORTANT: If the user is asking in Burmese, use Burmese content from context_data. If asking in English, use English content. Do not translate between languages.

RESPONSE:"""
        
        return prompt
    
    def _get_conversation_context(self, state: Dict[str, Any]) -> str:
        """Get conversation history as context string"""
        history = state.get("conversation_history", [])
        if not history:
            logger.info("no_conversation_history")
            return ""
        
        # Get last 8 messages for context (increased for better memory)
        recent_messages = history[-8:]
        context_lines = []
        
        # Add a header to emphasize this is conversation history
        context_lines.append("=== FULL CONVERSATION HISTORY (USE ALL INFORMATION) ===")
        
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            # Clean content to remove any HTML tags
            import re
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            context_lines.append(f"{role}: {clean_content}")
        
        context_str = "\n".join(context_lines)
        logger.info("conversation_context_created", 
                   history_length=len(history), 
                   recent_messages=len(recent_messages),
                   context_length=len(context_str))
        
        # Debug: Log the actual conversation history being sent
        logger.info("conversation_history_debug", 
                   context_str=context_str,
                   recent_messages_content=[msg["content"] for msg in recent_messages])
        
        return context_str
    
    def _create_ai_prompt_with_memory(self, user_message: str, intent: str, language: str, context_data: Dict[str, Any], conversation_history: str) -> str:
        """Create AI prompt with conversation memory"""
        language_name = "Burmese" if language == "my" else "English"
        
        # Smart contextual awareness - only use history when contextually necessary
        user_message_lower = user_message.lower()
        
        # Check for explicit memory requests
        explicit_memory_keywords = [
            "what did i ask", "what did we discuss", "what did we talk about",
            "what is my name", "do you remember my name", "what's my name",
            "what did i say", "what did i tell you", "what did i mention",
            "ဘာမေးခဲ့လဲ", "ဘာပြောခဲ့လဲ", "ကျွန်တော့်နာမည်", "အမည်", "မှတ်မိလား"
        ]
        
        # Check for contextual follow-up questions
        contextual_keywords = [
            "price", "how much", "cost", "fee", "charge",
            "that", "it", "them", "those", "this",
            "recommend", "suggest", "what about", "how about",
            "ဈေးနှုန်း", "ဘယ်လောက်", "ဒါ", "ဒါတွေ", "အကြံပြု"
        ]
        
        is_explicit_memory_request = any(keyword in user_message_lower for keyword in explicit_memory_keywords)
        is_contextual_followup = any(keyword in user_message_lower for keyword in contextual_keywords)
        
        if is_explicit_memory_request:
            # User explicitly asks about previous conversation
            memory_instruction = f"""
🚨 EXPLICIT MEMORY REQUEST: The user is asking about previous conversation or their name.
You MUST check the conversation history below and provide a relevant response.

RECENT CONVERSATION HISTORY:
{conversation_history}

MEMORY INSTRUCTIONS:
- If user asks "what is my name", find their name in the conversation history
- If user asks "what did I ask", tell them what they asked about previously
- If user asks "what did we discuss", summarize the conversation topics
- Use ONLY information from the conversation history above
- Be specific and accurate about what was discussed
"""
        elif is_contextual_followup and conversation_history.strip():
            # User asks a follow-up question that needs context
            memory_instruction = f"""
🎯 CONTEXTUAL FOLLOW-UP: The user is asking a follow-up question that requires context from our conversation.

CONVERSATION HISTORY (FOR CONTEXT):
{conversation_history}

CONTEXTUAL RESPONSE RULES:
1. **UNDERSTAND THE CONTEXT**: Use the conversation history to understand what the user is referring to
2. **NATURAL FOLLOW-UP**: If they ask "price please" after discussing menu items, provide prices for those specific items
3. **REMEMBER DETAILS**: Remember names, preferences, dietary restrictions, and specific items mentioned
4. **BE SPECIFIC**: Don't give generic answers - use the context to provide specific, relevant information
5. **NATURAL LANGUAGE**: Don't mention "as we discussed" unless the user specifically asks about previous conversation

📝 EXAMPLES:
- User: "Do you have Kid Menu?" → You: "Yes, we have Omelette, Burger, Cake, etc."
- User: "Price please?" → You: "The Kid Menu items are: Omelette - $8, Burger - $10, Cake - $5"
- User: "What about vegetarian options?" → You: "For vegetarian options, we have..."
- User: "How much is that?" → You: "The vegetarian options are priced at..."
"""
        else:
            # Normal conversation - minimal history usage
            memory_instruction = f"""
💬 NORMAL CONVERSATION: This appears to be a new topic or standalone question.

CONVERSATION HISTORY (MINIMAL REFERENCE):
{conversation_history}

CONVERSATION RULES:
1. **FOCUS ON CURRENT QUESTION**: Answer the user's current question directly
2. **MINIMAL HISTORY USAGE**: Only reference conversation history if absolutely necessary for context
3. **NATURAL RESPONSE**: Don't force previous conversation topics into your response
4. **REMEMBER ESSENTIALS**: Remember user's name and key preferences if mentioned, but don't bring them up unless relevant
5. **FRESH START**: Treat this as a new conversation topic unless context clearly indicates otherwise

📝 EXAMPLES:
- User: "What's your menu?" → You: "Here's our menu..." (don't mention previous topics)
- User: "Hello, my name is John" → You: "Hello John! How can I help you today?"
- User: "What are your opening hours?" → You: "We're open..." (don't reference previous conversation)
"""
        
        prompt = f"""
You are a helpful and friendly restaurant chatbot for Cafe Pentagon. You are having a natural conversation with a customer.

CURRENT USER MESSAGE: {user_message}
DETECTED INTENT: {intent}
LANGUAGE: {language_name}

{memory_instruction}

CONTEXT DATA:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

🚨 CRITICAL LANGUAGE INSTRUCTION 🚨
YOU MUST RESPOND ONLY IN {language_name.upper()} LANGUAGE!
- If language is "Burmese": Respond ONLY in Burmese (မြန်မာဘာသာ)
- If language is "English": Respond ONLY in English
- DO NOT mix languages or translate
- DO NOT use any other language

CRITICAL INSTRUCTIONS:
1. Respond ONLY in {language_name} - do not translate or mix languages
2. Use the context data that matches the user's language ({language_name})
3. Be natural, friendly, and conversational - like talking to a friend
4. Keep responses concise but helpful - don't be verbose
5. For menu items: mention name, price, and key features briefly
6. For FAQ: give clear, direct answers in a friendly tone
7. For events: share relevant details in an engaging way
8. If you don't have specific information, be honest and helpful
9. Use natural {language_name} expressions and tone
10. Don't be formal or robotic - be warm and approachable

IMPORTANT: If the user is asking in Burmese, use Burmese content from context_data. If asking in English, use English content. Do not translate between languages.

RESPONSE (IN {language_name.upper()} ONLY):"""
        
        return prompt
        
        return prompt
    
    async def _get_context_data(self, intent: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant context data based on intent"""
        context_data = {}
        user_language = state.get("user_language", "en")
        
        try:
            if intent == "menu_browse":
                menu_data = self.data_loader.load_menu_data()
                if user_language == "my":
                    # For Burmese users, prioritize Burmese content
                    context_data["menu_items"] = [
                        {
                            "name": item.myanmar_name,
                            "name_en": item.english_name,
                            "price": f"{item.price} MMK",
                            "description": item.description_mm,
                            "description_en": item.description_en,
                            "category": str(item.category)
                        }
                        for item in menu_data[:15]  # More items for better context
                    ]
                else:
                    # For English users, prioritize English content
                    context_data["menu_items"] = [
                        {
                            "name": item.english_name,
                            "name_mm": item.myanmar_name,
                            "price": f"{item.price} MMK",
                            "description": item.description_en,
                            "description_mm": item.description_mm,
                            "category": str(item.category)
                        }
                        for item in menu_data[:15]  # More items for better context
                    ]
            
            elif intent == "faq":
                faq_data = self.data_loader.load_faq_data()
                if user_language == "my":
                    # For Burmese users, prioritize Burmese content
                    context_data["faq_items"] = [
                        {
                            "question": item.question_mm,
                            "question_en": item.question_en,
                            "answer": item.answer_mm,
                            "answer_en": item.answer_en,
                            "category": item.category
                        }
                        for item in faq_data[:10]  # More items for better context
                    ]
                else:
                    # For English users, prioritize English content
                    context_data["faq_items"] = [
                        {
                            "question": item.question_en,
                            "question_mm": item.question_mm,
                            "answer": item.answer_en,
                            "answer_mm": item.answer_mm,
                            "category": item.category
                        }
                        for item in faq_data[:10]  # More items for better context
                    ]
            
            elif intent == "events":
                events_data = self.data_loader.load_events_data()
                if user_language == "my":
                    # For Burmese users, prioritize Burmese content
                    context_data["events"] = [
                        {
                            "title": item.title_mm,
                            "title_en": item.title_en,
                            "description": item.description_mm,
                            "description_en": item.description_en,
                            "date": item.date,
                            "time": item.time
                        }
                        for item in events_data[:5]  # More events for better context
                    ]
                else:
                    # For English users, prioritize English content
                    context_data["events"] = [
                        {
                            "title": item.title_en,
                            "title_mm": item.title_mm,
                            "description": item.description_en,
                            "description_mm": item.description_mm,
                            "date": item.date,
                            "time": item.time
                        }
                        for item in events_data[:5]  # More events for better context
                    ]
            
            elif intent == "complaint":
                # For complaints, provide customer service context
                context_data["customer_service"] = {
                    "language": user_language,
                    "restaurant_name": "Cafe Pentagon",
                    "contact_info": "Please contact us directly for immediate assistance"
                }
            
        except Exception as e:
            logger.error("context_data_retrieval_error", error=str(e))
        
        return context_data

    def _generate_greeting_response(self, lang_key: str) -> str:
        """Generate greeting response"""
        import random
        templates = self.response_templates["greeting"][lang_key]
        return random.choice(templates)

    async def _generate_menu_response(self, user_message: str, lang_key: str, state: Dict[str, Any]) -> str:
        """Generate menu browsing response using AI-driven decision making and vector search"""
        try:
            # Get conversation history for context
            conversation_history = state.get("conversation_history", [])
            
            # Use AI to analyze user request
            analysis = await self.vector_search.analyze_user_request(user_message, conversation_history)
            
            logger.info("menu_request_analyzed", 
                       user_message=user_message[:100],
                       action=analysis.get("action"),
                       confidence=analysis.get("confidence"))
            
            # Handle different actions based on AI analysis
            action = analysis.get("action", "OTHER")
            
            if action == "SHOW_CATEGORIES":
                return await self._generate_categories_response(lang_key)
            
            elif action == "SHOW_CATEGORY_ITEMS":
                category = analysis.get("category")
                if category:
                    return await self._generate_category_items_response(category, lang_key)
                else:
                    return self._get_fallback_response("menu_browse", lang_key)
            
            elif action == "SHOW_ITEM_DETAILS":
                item_name = analysis.get("item_name")
                if item_name:
                    return await self._generate_item_details_response(item_name, lang_key)
                else:
                    return self._get_fallback_response("menu_browse", lang_key)
            
            elif action == "SHOW_ITEM_IMAGE":
                item_name = analysis.get("item_name")
                if item_name:
                    return await self._generate_item_image_response(item_name, lang_key)
                else:
                    return self._get_fallback_response("menu_browse", lang_key)
            
            else:
                # Check if this is a category browsing question
                if await self._is_category_browsing_question(user_message, lang_key):
                    category = await self._extract_category_from_question(user_message, lang_key)
                    if category:
                        return await self._generate_category_items_response(category, lang_key)
                
                # Fallback to general menu response
                return await self._generate_categories_response(lang_key)
                
        except Exception as e:
            logger.error("menu_response_generation_failed", error=str(e))
            return self._get_fallback_response("menu_browse", lang_key)

    async def _is_category_browsing_question(self, user_message: str, lang_key: str) -> bool:
        """Check if user is asking about what kinds of items are available in a category"""
        try:
            # Use AI to determine if this is a category browsing question
            prompt = f"""
Analyze this user message and determine if they are asking about what kinds of items are available in a specific category.

User message: "{user_message}"
Language: {"Burmese" if lang_key == "my" else "English"}

Look for patterns like:
- "what kind of [category]"
- "what [category] do you have"
- "show me [category]"
- "ဘယ်လို [category] တွေ ရှိလဲ"
- "[category] ဘာတွေ ရှိလဲ"

Return only "YES" if it's a category browsing question, or "NO" if not.
"""
            
            response = await self.llm.ainvoke(prompt)
            result = response.content.strip().upper()
            
            return result == "YES"
            
        except Exception as e:
            logger.error("category_browsing_detection_failed", error=str(e))
            return False

    async def _extract_category_from_question(self, user_message: str, lang_key: str) -> str:
        """Extract the category from a user's question using AI"""
        try:
            prompt = f"""
Extract the menu category from this user question.

User message: "{user_message}"
Language: {"Burmese" if lang_key == "my" else "English"}

Available categories: breakfast, main_course, appetizers_sides, soups, noodles, sandwiches_burgers, salads, pasta, rice_dishes

Examples:
- "what kind of noodles" → "noodles"
- "ခေါက်ဆွဲဘာတွေ ရှိလဲ" → "noodles"
- "what burgers do you have" → "sandwiches_burgers"
- "ဘာဂါဘာတွေ ရှိလဲ" → "sandwiches_burgers"

Return only the category name, or "unknown" if unclear.
"""
            
            response = await self.llm.ainvoke(prompt)
            category = response.content.strip().lower()
            
            # Validate category
            valid_categories = ["breakfast", "main_course", "appetizers_sides", "soups", "noodles", "sandwiches_burgers", "salads", "pasta", "rice_dishes"]
            
            if category in valid_categories:
                return category
            else:
                return "unknown"
                
        except Exception as e:
            logger.error("category_extraction_failed", error=str(e))
            return "unknown"

    async def _generate_categories_response(self, lang_key: str) -> str:
        """Generate response showing menu categories"""
        try:
            # Get categories from vector search
            categories = await self.vector_search.get_menu_categories(lang_key)
            
            if not categories:
                return self._get_fallback_response("menu_browse", lang_key)
            
            # Format natural response
            if lang_key == "my":
                response = "ကျနော်တို့ရဲ့ မီနူးမှာ ဒီအမျိုးအစားတွေ ရှိပါတယ်:\n\n"
                for category in categories:
                    display_name = category["display_name"]
                    response += f"• **{display_name}**\n"
                response += "\nဘယ်အမျိုးအစားကို ကြည့်ချင်ပါသလဲ?"
            else:
                response = "Here are our menu categories:\n\n"
                for category in categories:
                    display_name = category["display_name"]
                    response += f"• **{display_name}**\n"
                response += "\nWhich category would you like to see?"
            
            return response
            
        except Exception as e:
            logger.error("categories_response_generation_failed", error=str(e))
            return self._get_fallback_response("menu_browse", lang_key)

    async def _generate_category_items_response(self, category: str, lang_key: str) -> str:
        """Generate response showing items from a specific category"""
        try:
            # Get items from vector search - show more items for category browsing
            items = await self.vector_search.get_category_items(category, lang_key, limit=12)
            
            if not items:
                if lang_key == "my":
                    return f"'{category}' အမျိုးအစားမှာ အစားအစာများ မတွေ့ရှိပါဘူး။"
                else:
                    return f"No items found in the '{category}' category."
            
            # Format simple response with just names and prices - using proper line breaks
            if lang_key == "my":
                category_name = self.vector_search._get_category_display_name(category, lang_key)
                response = f"**{category_name}** အစားအစာတွေပါ:\n\n"
                
                for i, item in enumerate(items, 1):
                    name = item["name"]
                    myanmar_name = item.get("name_other", "")
                    price = item["price"]
                    currency = item["currency"]
                    
                    if myanmar_name:
                        response += f"{i}. **{name}** ({myanmar_name})\n"
                        response += f"   💰 {price:,} {currency}\n\n"
                    else:
                        response += f"{i}. **{name}**\n"
                        response += f"   💰 {price:,} {currency}\n\n"
                
                response += "ဘယ်အစားအစာကို ပိုမိုသိချင်ပါသလဲ?"
            else:
                category_name = self.vector_search._get_category_display_name(category, lang_key)
                response = f"Here are our **{category_name}** items:\n\n"
                
                for i, item in enumerate(items, 1):
                    name = item["name"]
                    myanmar_name = item.get("name_other", "")
                    price = item["price"]
                    currency = item["currency"]
                    
                    if myanmar_name:
                        response += f"{i}. **{name}** ({myanmar_name})\n"
                        response += f"   💰 {price:,} {currency}\n\n"
                    else:
                        response += f"{i}. **{name}**\n"
                        response += f"   💰 {price:,} {currency}\n\n"
                
                response += "Which item would you like to know more about?"
            
            return response
            
        except Exception as e:
            logger.error("category_items_response_generation_failed", error=str(e))
            return self._get_fallback_response("menu_browse", lang_key)

    async def _generate_item_details_response(self, item_name: str, lang_key: str) -> str:
        """Generate response with detailed information about a specific item"""
        try:
            # Get item details from vector search
            item = await self.vector_search.get_item_details(item_name, lang_key)
            
            if not item:
                if lang_key == "my":
                    return f"'{item_name}' အစားအစာကို မတွေ့ရှိပါဘူး။"
                else:
                    return f"Item '{item_name}' not found."
            
            # Format natural conversational response
            if lang_key == "my":
                response = f"**{item['name']}** အကြောင်း ပြောပြပေးပါရစေ။\n\n"
                response += f"ဈေးနှုန်းကတော့ {item['price']:,} {item['currency']} ဖြစ်ပါတယ်။\n"
                response += f"{item['description']}\n\n"
                response += f"ပြင်ဆင်ချိန်က {item['preparation_time']} ဖြစ်ပါတယ်။\n"
                response += f"အစပ်အဆင့်က {item['spice_level']}/4 ဖြစ်ပါတယ်။\n"
                
                if item.get("ingredients"):
                    response += f"\nပါဝင်ပစ္စည်းတွေကတော့ {', '.join(item['ingredients'])} တို့ ဖြစ်ပါတယ်။\n"
                
                if item.get("allergens"):
                    response += f"\nဓာတ်မတည့်မှုရှိတဲ့ ပါဝင်ပစ္စည်းတွေကတော့ {', '.join(item['allergens'])} တို့ ဖြစ်ပါတယ်။\n"
                
                response += f"\nပုံကို ကြည့်ချင်ပါသလား?"
            else:
                response = f"Here's information about **{item['name']}**.\n\n"
                response += f"The price is {item['price']:,} {item['currency']}.\n"
                response += f"{item['description']}\n\n"
                response += f"Preparation time is {item['preparation_time']}.\n"
                response += f"Spice level is {item['spice_level']}/4.\n"
                
                if item.get("ingredients"):
                    response += f"\nIngredients include {', '.join(item['ingredients'])}.\n"
                
                if item.get("allergens"):
                    response += f"\nAllergens include {', '.join(item['allergens'])}.\n"
                
                response += f"\nWould you like to see the image?"
            
            return response
            
        except Exception as e:
            logger.error("item_details_response_generation_failed", error=str(e))
            return self._get_fallback_response("menu_browse", lang_key)

    async def _generate_item_image_response(self, item_name: str, lang_key: str) -> str:
        """Generate response with image information for a specific item using AI-powered understanding"""
        try:
            # Use AI to better understand the user's request, especially for Burmese
            if lang_key == "my" or any('\u1000' <= char <= '\u109F' for char in item_name):
                # Use AI to understand and translate the Burmese request
                understood_item = await self._understand_burmese_request(item_name)
                if understood_item:
                    item_name = understood_item
            
            # Get image information from vector search
            image_info = await self.vector_search.get_item_image(item_name)
            
            if not image_info:
                if lang_key == "my":
                    return f"'{item_name}' အစားအစာရဲ့ ပုံကို မတွေ့ရှိပါဘူး။ ကျေးဇူးပြု၍ အခြားအစားအစာကို မေးကြည့်ပါ။"
                else:
                    return f"Image for '{item_name}' not found. Please try asking for a different menu item."
            
            # Format natural conversational response WITHOUT HTML img tags
            if lang_key == "my":
                # Natural Burmese response
                response = f"**{image_info['item_name']}** ပုံပါ ခင်ဗျာ။ "
                response += f"ဈေးနှုန်းလေးကတော့ {image_info['price']} ဖြစ်ပါတယ်။"
               
            else:
                # Natural English response
                response = f"Here is the photo of **{image_info['item_name']}**. "
                response += f"The price is {image_info['price']}."
                
            
            # Add a special marker to indicate this response should include an image
            # The main agent will detect this marker and extract the image info
            response += f"\n\n[IMAGE_MARKER:{image_info['image_url']}:{image_info['item_name']}]"
            
            return response
            
        except Exception as e:
            logger.error("item_image_response_generation_failed", error=str(e))
            return self._get_fallback_response("menu_browse", lang_key)

    async def _understand_burmese_request(self, burmese_text: str) -> Optional[str]:
        """
        Use AI to understand and translate Burmese food requests to English menu item names
        """
        try:
            # First, try using the Burmese processor for direct translation
            translations = translate_burmese_food_request(burmese_text)
            
            if translations and len(translations) > 1:
                # Return the first non-original translation
                for translation in translations:
                    if translation != burmese_text:
                        logger.info("burmese_request_understood_via_processor", 
                                   original=burmese_text,
                                   translated_item=translation)
                        return translation
            
            # Fallback to AI-based translation with enhanced prompt
            from src.config.settings import get_settings
            from openai import OpenAI
            
            settings = get_settings()
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Enhanced prompt with comprehensive Burmese food vocabulary
            prompt = f"""
            You are a helpful assistant that understands Burmese food requests and translates them to specific English menu item names.
            
            The user is asking for a food item in Burmese: "{burmese_text}"
            
            Please analyze this request and provide the most likely English menu item name that the user is looking for.
            
            Consider:
            1. The specific food item being requested
            2. Common menu item names that would match this request
            3. The context of a restaurant menu
            4. Burmese food vocabulary and common dishes
            
            Common Burmese food terms and their English equivalents:
            - ကြက်သား = chicken
            - ငါး = fish
            - ခေါက်ဆွဲ = noodles
            - ခေါက်ဆွဲကြော် = fried noodles
            - ပတ်ထိုင်းခေါက်ဆွဲကြော် = pad thai
            - အီတလီခေါက်ဆွဲ = italian noodles/pasta
            - ဘာဂါ = burger
            - ဘေကွန် = bacon
            - အမဲသားညှပ်ပေါင်မုန့် = beef sandwich
            - ဝက်ပေါင်ခြောက် = ham
            - ပီဇာ = pizza
            - ဟင်းရည် = soup
            - ကြော် = fried
            - ချက် = cooked/curry
            - ကြက်ဉလိပ် = omelette
            - ထမင်း = rice
            - ဆန် = rice
            - ဟင်းသီးဟင်းရွက် = vegetables
            - သီးနှံ = fruits
            - ကော်ဖီ = coffee
            - လက်ဖက်ရည် = tea
            - ဖျော်ရည် = juice/drink
            - ပင်လယ်စာ = seafood
            - ပုံ = image/picture
            - ပြပါ = show/display
            - အကြောင်း = about/information
            - ပြောပြပါ = tell me/explain
            
            IMPORTANT: For compound terms, combine the English equivalents logically.
            Examples:
            - "ဘေကွန် အမဲသားညှပ်ပေါင်မုန့်" = bacon beef sandwich
            - "ဝက်ပေါင်ခြောက် အီတလီ ခေါက်ဆွဲ" = ham italian noodles
            - "ပတ်ထိုင်းခေါက်ဆွဲကြော် ပင်လယ်စာ" = pad thai seafood
            
            Return only the English menu item name. Do not include explanations or additional text.
            
            If you're not sure about the exact item, return the most likely match based on the Burmese text.
            
            Examples:
            Burmese: "ကြက်သားဟင်းရည်" → English: chicken soup
            Burmese: "ခေါက်ဆွဲကြော်" → English: fried noodles
            Burmese: "ဘာဂါ" → English: burger
            Burmese: "ကြက်ဉလိပ်ကြော်" → English: omelette
            Burmese: "ငါးကြော်" → English: fried fish
            Burmese: "ထမင်းကြော်" → English: fried rice
            Burmese: "ဘေကွန် အမဲသားညှပ်ပေါင်မုန့်" → English: bacon beef sandwich
            Burmese: "ဝက်ပေါင်ခြောက် အီတလီ ခေါက်ဆွဲ" → English: ham italian noodles
            Burmese: "ပတ်ထိုင်းခေါက်ဆွဲကြော် ပင်လယ်စာ" → English: pad thai seafood
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a food translation expert that helps translate Burmese food requests to specific English menu item names. Always return only the English menu item name, nothing else."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            # Extract the translated item name
            translated_item = response.choices[0].message.content.strip()
            
            logger.info("burmese_request_understood_via_ai", 
                       original=burmese_text,
                       translated_item=translated_item)
            
            return translated_item if translated_item else None
            
        except Exception as e:
            logger.error("burmese_understanding_failed", 
                        burmese_text=burmese_text,
                        error=str(e))
            return None


    async def _generate_faq_response(self, user_message: str, lang_key: str) -> str:
        """Generate FAQ response"""
        try:
            # Load FAQ data
            faq_data = self.data_loader.load_faq_data()
            if not faq_data:
                return self._get_fallback_response("faq", lang_key)
            
            # Find relevant FAQ
            relevant_faq = self._find_relevant_faq(faq_data, user_message, lang_key)
            
            if relevant_faq:
                if lang_key == "my":
                    return relevant_faq.get("answer_mm", "အဖြေမတွေ့ရှိပါဘူး။")
                else:
                    return relevant_faq.get("answer_en", "Answer not found.")
            else:
                return self._get_fallback_response("faq", lang_key)
                
        except Exception as e:
            logger.error("faq_response_generation_failed", error=str(e))
            return self._get_fallback_response("faq", lang_key)

    def _find_relevant_faq(self, faq_data: List[Dict], query: str, lang_key: str) -> Optional[Dict]:
        """Find relevant FAQ based on query"""
        query_lower = query.lower()
        best_match = None
        best_score = 0
        
        for faq in faq_data:
            # Handle Pydantic model
            if hasattr(faq, 'model_dump'):
                faq_dict = faq.model_dump()
            elif hasattr(faq, 'dict'):
                faq_dict = faq.dict()
            else:
                faq_dict = faq
            
            # Calculate relevance score
            score = 0
            
            if lang_key == "my":
                question = faq_dict.get("question_mm", "").lower()
                tags = faq_dict.get("tags", [])
            else:
                question = faq_dict.get("question_en", "").lower()
                tags = faq_dict.get("tags", [])
            
            # Check for keyword matches
            for word in query_lower.split():
                if word in question:
                    score += 2
                if word in str(tags).lower():
                    score += 1
            
            # Check for exact phrase matches
            if any(phrase in query_lower for phrase in ["wifi", "internet", "ဝိုင်ဖိုင်", "အင်တာနက်"]):
                if any(tag in ["wifi", "internet"] for tag in tags):
                    score += 5
            
            if any(phrase in query_lower for phrase in ["location", "address", "where", "နေရာ", "လိပ်စာ", "ဘယ်မှာ"]):
                if any(tag in ["location", "address"] for tag in tags):
                    score += 5
            
            if any(phrase in query_lower for phrase in ["hours", "time", "open", "ချိန်", "ဖွင့်"]):
                if any(tag in ["hours", "opening_times"] for tag in tags):
                    score += 5
            
            if score > best_score:
                best_score = score
                best_match = faq_dict
        
        return best_match if best_score > 0 else None

    async def _generate_events_response(self, user_message: str, lang_key: str) -> str:
        """Generate events response"""
        try:
            # Load events data
            events_data = self.data_loader.load_events_data()
            if not events_data:
                return self._get_fallback_response("events", lang_key)
            
            # Find relevant events
            relevant_events = self._find_relevant_events(events_data, user_message, lang_key)
            
            if relevant_events:
                if lang_key == "my":
                    return self._format_events_response_my(relevant_events)
                else:
                    return self._format_events_response_en(relevant_events)
            else:
                return self._get_fallback_response("events", lang_key)
                
        except Exception as e:
            logger.error("events_response_generation_failed", error=str(e))
            return self._get_fallback_response("events", lang_key)

    def _find_relevant_events(self, events_data: List[Dict], query: str, lang_key: str) -> List[Dict]:
        """Find relevant events based on query"""
        query_lower = query.lower()
        relevant_events = []
        
        for event in events_data:
            # Handle Pydantic model
            if hasattr(event, 'model_dump'):
                event_dict = event.model_dump()
            elif hasattr(event, 'dict'):
                event_dict = event.dict()
            else:
                event_dict = event
            
            # Check if event matches query
            if lang_key == "my":
                title = event_dict.get("title_mm", "").lower()
                desc = event_dict.get("description_mm", "").lower()
            else:
                title = event_dict.get("title_en", "").lower()
                desc = event_dict.get("description_en", "").lower()
            
            # Check for music-related keywords
            music_keywords = ["music", "show", "performance", "entertainment", "ဂီတ", "ပြပွဲ", "ဖျော်ဖြေရေး"]
            if any(keyword in query_lower for keyword in music_keywords):
                if any(keyword in title or keyword in desc for keyword in music_keywords):
                    relevant_events.append(event_dict)
        
        return relevant_events[:3]  # Limit to 3 events

    def _format_events_response_en(self, events: List[Dict]) -> str:
        """Format events response in English"""
        if not events:
            return "I couldn't find any events matching your criteria."
        
        response = "Here are some events that might interest you:\n\n"
        
        for event in events:
            title = event.get("title_en", "Unknown Event")
            desc = event.get("description_en", "")
            date = event.get("date", "")
            time = event.get("time", "")
            
            response += f"🎵 **{title}**\n"
            if desc:
                response += f"   {desc}\n"
            if date and time:
                response += f"   📅 {date} at {time}\n"
            response += "\n"
        
        return response

    def _format_events_response_my(self, events: List[Dict]) -> str:
        """Format events response in Burmese"""
        if not events:
            return "သင့်ရဲ့ ရှာဖွေမှုနဲ့ ကိုက်ညီတဲ့ ပွဲများ မတွေ့ရှိပါဘူး။"
        
        response = "သင့်ကို စိတ်ဝင်စားစရာ ကောင်းမယ့် ပွဲများ:\n\n"
        
        for event in events:
            title = event.get("title_mm", "မသိတဲ့ပွဲ")
            desc = event.get("description_mm", "")
            date = event.get("date", "")
            time = event.get("time", "")
            
            response += f"🎵 **{title}**\n"
            if desc:
                response += f"   {desc}\n"
            if date and time:
                response += f"   📅 {date} မှာ {time}\n"
            response += "\n"
        
        return response

    def _generate_order_response(self, lang_key: str) -> str:
        """Generate order response"""
        if lang_key == "my":
            return "အမှာယူခြင်းစနစ်က မကြာမီ ရရှိလာမှာပါ! ကျေးဇူးပြု၍ နောက်မှ ပြန်လည်ကြိုးစားကြည့်ပါ။"
        else:
            return "The ordering system is coming soon! Please try again later."

    def _generate_reservation_response(self, lang_key: str) -> str:
        """Generate reservation response"""
        if lang_key == "my":
            return "ကြိုတင်မှာယူခြင်းစနစ်က မကြာမီ ရရှိလာမှာပါ! ကျေးဇူးပြု၍ နောက်မှ ပြန်လည်ကြိုးစားကြည့်ပါ။"
        else:
            return "The reservation system is coming soon! Please try again later."

    def _generate_complaint_response(self, lang_key: str) -> str:
        """Generate complaint response"""
        if lang_key == "my":
            return "တိုင်ကြားချက်စနစ်က မကြာမီ ရရှိလာမှာပါ! ကျေးဇူးပြု၍ နောက်မှ ပြန်လည်ကြိုးစားကြည့်ပါ။"
        else:
            return "The complaint system is coming soon! Please try again later."

    def _generate_goodbye_response(self, lang_key: str) -> str:
        """Generate goodbye response"""
        if lang_key == "my":
            return "ကျေးဇူးတင်ပါတယ်! ပြန်လည်လာရောက်ကြည့်ရှုပေးပါ။ ကောင်းသောနေ့ဖြစ်ပါစေ!"
        else:
            return "Thank you! Please visit us again. Have a great day!"

    def _generate_unknown_response(self, lang_key: str) -> str:
        """Generate unknown intent response"""
        import random
        templates = self.response_templates["unknown"][lang_key]
        return random.choice(templates)

    def _get_fallback_response(self, intent: str, lang_key: str) -> str:
        """Get fallback response for failed intent processing"""
        if lang_key == "my":
            return "အချက်အလက်များကို ရယူရာတွင် အခက်အခဲရှိနေပါတယ်။ ကျေးဇူးပြု၍ နောက်မှ ပြန်လည်ကြိုးစားကြည့်ပါ။"
        else:
            return "I'm having trouble retrieving information. Please try again later."

    def _get_no_results_response(self, lang_key: str) -> str:
        """Get response when no results are found"""
        if lang_key == "my":
            return "သင့်ရဲ့ ရှာဖွေမှုနဲ့ ကိုက်ညီတဲ့ အစားအစာများ မတွေ့ရှိပါဘူး။ ရှာဖွေမှုကို ပြင်ဆင်ကြည့်ပါ သို့မဟုတ် အခြားရွေးချယ်မှုများကို အကြံပြုပေးပါရစေ။"
        else:
            return "I couldn't find any items matching your criteria. Please try adjusting your search or let me suggest some alternatives."

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state (required by BaseAgent)"""
        response = await self.generate_response(state)
        state["response"] = response
        return state 
