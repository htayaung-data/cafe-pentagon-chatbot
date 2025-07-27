"""
AI-Enhanced Response Generator for Cafe Pentagon Chatbot
Provides contextual, language-aware responses using AI
"""

import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from src.agents.base import BaseAgent
from src.data.loader import get_data_loader
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger("enhanced_response_generator")


class EnhancedResponseGenerator(BaseAgent):
    """
    Enhanced response generator with contextual responses
    """
    
    def __init__(self):
        """Initialize AI-enhanced response generator"""
        super().__init__("ai_enhanced_response_generator")
        self.data_loader = get_data_loader()
        self.settings = get_settings()
        
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
                    "မင်္ဂလာပါ! Cafe Pentagon မှ ကြိုဆိုပါတယ်! ဘာကို ကူညီပေးရမလဲ?"
                ]
            },
            "menu_browse": {
                "en": [
                    "Here's our menu! We have a variety of delicious dishes including {categories}. What would you like to know more about?",
                    "Great choice! Our menu features {categories}. Is there a specific category or dish you're interested in?",
                    "I'd be happy to show you our menu! We offer {categories}. What catches your eye?"
                ],
                "my": [
                    "ဒါကတော့ ကျွန်ုပ်တို့ရဲ့ မီနူးပါ! {categories} အပါအဝင် အရသာရှိတဲ့ အစားအစာများစွာ ရှိပါတယ်။ ဘာကို ပိုမိုသိချင်ပါသလဲ?",
                    "ရွေးချယ်မှု ကောင်းပါတယ်! ကျွန်ုပ်တို့ရဲ့ မီနူးမှာ {categories} ပါဝင်ပါတယ်။ သီးသန့်စိတ်ဝင်စားတဲ့ အမျိုးအစား သို့မဟုတ် အစားအစာ ရှိပါသလား?",
                    "မီနူးကို ပြပေးရတာ ဝမ်းသာပါတယ်! ကျွန်ုပ်တို့မှာ {categories} ရှိပါတယ်။ ဘာက စိတ်ဝင်စားစရာ ကောင်းပါသလဲ?"
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
        
        try:
            # Try AI-powered response generation first
            ai_response = await self._generate_ai_response(user_message, primary_intent, lang_key, state)
            if ai_response:
                return ai_response
        except Exception as e:
            logger.error("ai_response_generation_failed", error=str(e))
            # Fall back to template-based responses
        
        # Generate response based on intent (fallback)
        if primary_intent == "greeting":
            return self._generate_greeting_response(lang_key)
        elif primary_intent == "menu_browse":
            return await self._generate_menu_response(user_message, lang_key, intents)
        elif primary_intent == "faq":
            return await self._generate_faq_response(user_message, lang_key)
        elif primary_intent == "order_place":
            return self._generate_order_response(lang_key)
        elif primary_intent == "reservation":
            return self._generate_reservation_response(lang_key)
        elif primary_intent == "events":
            return await self._generate_events_response(user_message, lang_key)
        elif primary_intent == "complaint":
            return self._generate_complaint_response(lang_key)
        elif primary_intent == "goodbye":
            return self._generate_goodbye_response(lang_key)
        else:
            return self._generate_unknown_response(lang_key)

    async def _generate_ai_response(self, user_message: str, intent: str, language: str, state: Dict[str, Any]) -> Optional[str]:
        """Generate AI-powered response with conversation memory"""
        try:
            # Get relevant data based on intent
            context_data = await self._get_context_data(intent, state)
            
            # Get conversation history for context
            conversation_history = self._get_conversation_context(state)
            
            # Create AI prompt with memory
            prompt = self._create_ai_prompt_with_memory(user_message, intent, language, context_data, conversation_history)
            
            # Get AI response
            response = await self.llm.ainvoke(prompt)
            
            # Debug: Log the prompt and response for troubleshooting
            logger.info("ai_prompt_debug", 
                       prompt_length=len(prompt),
                       conversation_history_length=len(conversation_history),
                       response_length=len(response.content))
            
            return response.content.strip()
            
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

CRITICAL INSTRUCTIONS:
1. Respond ONLY in {language_name} - do not translate or mix languages
2. Use the context data that matches the user's language ({language_name})
3. Be natural, friendly, and conversational - like talking to a friend
4. Keep responses concise but helpful - don't be verbose
5. For menu items: mention name, price in MMK, and key features briefly
6. For FAQ: give clear, direct answers in a friendly tone
7. For events: share relevant details in an engaging way
8. If you don't have specific information, be honest and helpful
9. Use natural {language_name} expressions and tone
10. Don't be formal or robotic - be warm and approachable
11. IMPORTANT: Only use information from the provided context data - do not make up information
12. For complaints: be empathetic, understanding, and offer to help resolve issues

IMPORTANT: If the user is asking in Burmese, use Burmese content from context_data. If asking in English, use English content. Do not translate between languages.

RESPONSE:"""
        
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

    async def _generate_menu_response(self, user_message: str, lang_key: str, intents: List[Dict]) -> str:
        """Generate menu browsing response"""
        try:
            # Load menu data
            menu_data = self.data_loader.load_menu_data()
            if not menu_data:
                return self._get_fallback_response("menu_browse", lang_key)
            
            # Extract dietary preferences from entities
            dietary_pref = None
            for intent in intents:
                if intent.get("intent") == "menu_browse":
                    entities = intent.get("entities", {})
                    dietary_pref = entities.get("dietary_preference")
                    break
            
            # Filter menu items based on query
            filtered_items = self._filter_menu_items(menu_data, user_message, dietary_pref, lang_key)
            
            if not filtered_items:
                return self._get_no_results_response(lang_key)
            
            # Generate response
            if lang_key == "my":
                return self._format_menu_response_my(filtered_items, dietary_pref)
            else:
                return self._format_menu_response_en(filtered_items, dietary_pref)
                
        except Exception as e:
            logger.error("menu_response_generation_failed", error=str(e))
            return self._get_fallback_response("menu_browse", lang_key)

    def _filter_menu_items(self, menu_data: List[Dict], query: str, dietary_pref: Optional[str], lang_key: str) -> List[Dict]:
        """Filter menu items based on query and preferences"""
        query_lower = query.lower()
        filtered_items = []
        
        for item in menu_data:
            # Handle Pydantic model
            if hasattr(item, 'model_dump'):
                item_dict = item.model_dump()
            elif hasattr(item, 'dict'):
                item_dict = item.dict()
            else:
                item_dict = item
            
            # Check if item matches query
            matches = False
            
            # Check English content
            if lang_key == "en":
                name = item_dict.get("english_name", "").lower()
                desc = item_dict.get("description_en", "").lower()
                category = item_dict.get("category", "").lower()
                
                if any(term in name or term in desc or term in category for term in query_lower.split()):
                    matches = True
            else:
                # Check Burmese content
                name = item_dict.get("myanmar_name", "").lower()
                desc = item_dict.get("description_mm", "").lower()
                category = item_dict.get("category", "").lower()
                
                if any(term in name or term in desc or term in category for term in query_lower.split()):
                    matches = True
            
            # Check dietary preferences
            if dietary_pref:
                dietary_info = item_dict.get("dietary_info", {})
                if isinstance(dietary_info, str):
                    try:
                        dietary_info = json.loads(dietary_info)
                    except:
                        dietary_info = {}
                
                if dietary_pref.lower() in str(dietary_info).lower():
                    matches = True
            
            if matches:
                filtered_items.append(item_dict)
        
        return filtered_items[:5]  # Limit to 5 items

    def _format_menu_response_en(self, items: List[Dict], dietary_pref: Optional[str]) -> str:
        """Format menu response in English"""
        if not items:
            return "I couldn't find any items matching your criteria. Please try adjusting your search or let me suggest some alternatives."
        
        response = "Here are some menu items that might interest you:\n\n"
        
        for item in items:
            name = item.get("english_name", "Unknown")
            price = item.get("price", 0)
            currency = item.get("currency", "MMK")
            desc = item.get("description_en", "")
            
            response += f"🍽️ **{name}** - {price:,} {currency}\n"
            if desc:
                response += f"   {desc}\n"
            response += "\n"
        
        if dietary_pref:
            response += f"\nThese items are suitable for {dietary_pref} preferences."
        
        response += "\nWould you like to know more about any specific item or see other categories?"
        return response

    def _format_menu_response_my(self, items: List[Dict], dietary_pref: Optional[str]) -> str:
        """Format menu response in Burmese"""
        if not items:
            return "သင့်ရဲ့ ရှာဖွေမှုနဲ့ ကိုက်ညီတဲ့ အစားအစာများ မတွေ့ရှိပါဘူး။ ရှာဖွေမှုကို ပြင်ဆင်ကြည့်ပါ သို့မဟုတ် အခြားရွေးချယ်မှုများကို အကြံပြုပေးပါရစေ။"
        
        response = "သင့်ကို စိတ်ဝင်စားစရာ ကောင်းမယ့် မီနူးအစားအစာများ:\n\n"
        
        for item in items:
            name = item.get("myanmar_name", "မသိ")
            price = item.get("price", 0)
            currency = item.get("currency", "ကျပ်")
            desc = item.get("description_mm", "")
            
            response += f"🍽️ **{name}** - {price:,} {currency}\n"
            if desc:
                response += f"   {desc}\n"
            response += "\n"
        
        if dietary_pref:
            response += f"\nဒီအစားအစာများက {dietary_pref} ရွေးချယ်မှုများအတွက် သင့်တော်ပါတယ်။"
        
        response += "\nသီးသန့်အစားအစာ သို့မဟုတ် အခြားအမျိုးအစားများကို ပိုမိုသိလိုပါသလား?"
        return response

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
            return "အချက်အလက်များကို ရယူရာတွင် အခက်အခဲရှိနေပါသည်။ ကျေးဇူးပြု၍ နောက်မှ ပြန်လည်ကြိုးစားကြည့်ပါ။"
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