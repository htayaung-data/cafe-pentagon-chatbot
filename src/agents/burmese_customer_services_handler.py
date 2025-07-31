# -*- coding: utf-8 -*-
"""
Burmese Customer Service Handler - Uses Pinecone Vector Database
Always uses Pinecone for data retrieval, acts as manager for customer service
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from openai import OpenAI
from src.config.settings import get_settings
from src.utils.language import is_burmese_text
from src.services.vector_search_service import VectorSearchService
from src.services.semantic_context_extractor import get_semantic_context_extractor
from src.utils.logger import get_logger

logger = get_logger("burmese_customer_services_handler")


class BurmeseCustomerServiceHandler:
    """
    Burmese Customer Service Handler that uses Pinecone vector database
    - Always searches Pinecone for relevant data
    - Acts as restaurant manager for customer service questions
    - Politely says "don't know" for important questions not in Pinecone
    - Enhanced menu handling with structured responses
    """
    
    def __init__(self):
        """Initialize the Burmese customer service handler"""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.vector_service = VectorSearchService()
        self.semantic_extractor = get_semantic_context_extractor()
        
    async def _search_pinecone_for_data(self, user_message: str) -> Dict[str, Any]:
        """
        Search Pinecone for relevant FAQ and menu data with improved Burmese handling
        """
        try:
            # Use the vector service's search method
            return await self.vector_service.search_pinecone_for_data(user_message, "my")
        except Exception as e:
            print(f"Pinecone search error: {str(e)}")
            return {
                "faq_results": [],
                "menu_results": [],
                "found_faq": False,
                "found_menu": False
            }
    
    def _is_general_menu_question(self, user_message: str) -> bool:
        """
        Check if this is a general menu question asking for categories
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
        """
        specific_item_keywords = [
            "ဈေးနှုန်း", "price", "ပါဝင်ပစ္စည်း", "ingredient", "အသေးစိတ်", "detail",
            "ဘယ်လို", "ဘယ်လောက်", "ဘာပါ", "ဘာတွေ", "ဘာများ", "ဘာရှိ",
            "အရသာ", "taste", "ပြင်ဆင်ချိန်", "preparation", "အစပ်", "spice"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in specific_item_keywords)
    
    def _is_customer_service_question(self, user_message: str) -> bool:
        """
        Check if this is a customer service question that manager can answer
        """
        customer_service_keywords = [
            # Infrastructure & Services
            "wifi", "internet", "မီးပျက်", "generator", "မီးစက်", "အဲကွန်း", "aircon", "air conditioning",
            "အပူချိန်", "temperature", "အအေး", "cooling", "အပူ", "heating",
            
            # Policies & Rules
            "ဓါတ်ပုံ", "photo", "ကြောင်လေး", "pet", "ခွေး", "dog", "ကြောင်", "cat",
            "အပြင်ထိုင်ခုံ", "outdoor", "အပြင်", "outside", "ဆေးလိပ်", "smoking",
            "အစားအစာ", "food", "အပြင်က", "outside food", "ယူဆောင်", "bring",
            
            # Customization & Special Requests
            "customize", "ပြင်ဆင်", "အထူး", "special", "အရသာ", "taste", "ပြောင်းလဲ", "change",
            "အကူအညီ", "help", "အကြံပြု", "suggestion", "အကြံဉာဏ်", "advice",
            
            # General Business Questions
            "ဖွင့်လား", "open", "ပိတ်လား", "closed", "အလုပ်လုပ်လား", "working",
            "ရရှိနိုင်လား", "available", "ရနိုင်လား", "can get", "ဖြစ်နိုင်လား", "possible",
            
            # Common Restaurant Questions
            "ဘယ်လို", "how", "ဘာလဲ", "what", "ဘယ်မှာ", "where", "ဘယ်အချိန်", "when",
            "ဘာတွေ", "what things", "ဘာရှိ", "what available", "ဘာလုပ်လို့ရ", "what can do"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in customer_service_keywords)
    
    def _is_important_question(self, user_message: str) -> bool:
        """
        Check if this is an important question that needs accurate data
        """
        important_keywords = [
            "ဖွင့်ချိန်", "opening", "ဈေးနှုန်း", "price", "လိပ်စာ", "address", "ဘယ်မှာ", "where",
            "ဘယ်အချိန်", "when", "ဘာတွေ", "what", "ဘာရှိ", "available", "menu", "မီနူး"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in important_keywords)
    
    def _is_simple_greeting(self, user_message: str) -> bool:
        """
        Check if the message is a simple greeting that should get immediate response
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
    


    async def _get_menu_categories_from_pinecone(self) -> List[str]:
        """
        Get available menu categories from Pinecone
        """
        try:
            # Search for menu items to extract categories
            menu_query_results = self.vector_service.pinecone_index.query(
                vector=self.vector_service.embeddings.embed_query("menu categories"),
                namespace="menu",
                top_k=50,
                include_metadata=True
            )
            
            if menu_query_results.matches:
                categories = set()
                for match in menu_query_results.matches:
                    if match.metadata and match.metadata.get('category'):
                        categories.add(match.metadata['category'])
                
                return list(categories)
            
            return []
            
        except Exception as e:
            print(f"Error getting menu categories: {str(e)}")
            return []
    
    async def _get_category_items_from_pinecone(self, category: str) -> List[Dict]:
        """
        Get menu items for a specific category from Pinecone
        """
        try:
            # Search for items in the specific category
            category_query_results = self.vector_service.pinecone_index.query(
                vector=self.vector_service.embeddings.embed_query(f"{category} menu items"),
                namespace="menu",
                top_k=20,
                include_metadata=True
            )
            
            if category_query_results.matches:
                category_items = []
                for match in category_query_results.matches:
                    if (match.metadata and 
                        match.metadata.get('category', '').lower() == category.lower()):
                        category_items.append(match.metadata)
                
                return category_items[:10]  # Limit to top 10 items
            
            return []
            
        except Exception as e:
            print(f"Error getting category items: {str(e)}")
            return []
    
    async def _create_context_from_pinecone_results(self, search_results: Dict[str, Any], user_message: str) -> str:
        """
        Create context string from Pinecone search results based on question type
        """
        context_parts = []
        
        # Add FAQ results if found - use Burmese content directly
        if search_results.get("found_faq") and search_results.get("faq_results"):
            context_parts.append("RELEVANT FAQ INFORMATION FROM DATABASE:")
            for i, faq in enumerate(search_results["faq_results"][:3], 1):
                # Use Burmese content directly, fallback to English
                question = faq.get('question_mm', faq.get('question_en', 'N/A'))
                answer = faq.get('answer_mm', faq.get('answer_en', 'N/A'))
                category = faq.get('category', 'N/A')
                tags = faq.get('tags', [])
                
                context_parts.append(f"FAQ #{faq.get('id', i)}:")
                context_parts.append(f"Category: {category}")
                context_parts.append(f"Question: {question}")
                context_parts.append(f"Answer: {answer}")
                context_parts.append(f"Tags: {', '.join(tags)}")
                context_parts.append("")
        
        # Add Events results if found
        if search_results.get("found_events") and search_results.get("events_results"):
            context_parts.append("RELEVANT EVENTS INFORMATION FROM DATABASE:")
            for i, event in enumerate(search_results["events_results"][:3], 1):
                # Use Burmese content directly, fallback to English
                title = event.get('title_mm', event.get('title_en', 'N/A'))
                description = event.get('description_mm', event.get('description_en', 'N/A'))
                date = event.get('date', 'N/A')
                time = event.get('time', 'N/A')
                category = event.get('category', 'N/A')
                
                context_parts.append(f"Event #{i}:")
                context_parts.append(f"Title: {title}")
                context_parts.append(f"Date: {date}")
                context_parts.append(f"Time: {time}")
                context_parts.append(f"Category: {category}")
                context_parts.append(f"Description: {description}")
                context_parts.append("")
        
        # Handle menu results based on question type
        if search_results.get("found_menu") and search_results.get("menu_results"):
            if self._is_general_menu_question(user_message):
                # For general menu questions, show categories
                categories = await self._get_menu_categories_from_pinecone()
                if categories:
                    context_parts.append("AVAILABLE MENU CATEGORIES:")
                    for i, category in enumerate(categories, 1):
                        context_parts.append(f"{i}. {category}")
                    context_parts.append("")
            
            elif self._is_specific_category_question(user_message):
                # For category questions, show items in that category
                context_parts.append("MENU ITEMS IN RELEVANT CATEGORIES:")
                for i, item in enumerate(search_results["menu_results"][:8], 1):
                    # Use Burmese names when available
                    item_name = item.get('myanmar_name', item.get('name', 'N/A'))
                    english_name = item.get('name', 'N/A')
                    context_parts.append(f"Item #{i}:")
                    context_parts.append(f"Name: {english_name} ({item_name})")
                    context_parts.append(f"Category: {item.get('category', 'N/A')}")
                    context_parts.append(f"Price: {item.get('price', 'N/A')} {item.get('currency', 'N/A')}")
                    context_parts.append("")
            
            elif self._is_specific_item_question(user_message):
                # For specific item questions, show detailed information
                context_parts.append("DETAILED MENU ITEM INFORMATION:")
                for i, item in enumerate(search_results["menu_results"][:3], 1):
                    item_name = item.get('myanmar_name', item.get('name', 'N/A'))
                    english_name = item.get('name', 'N/A')
                    context_parts.append(f"Item #{i}:")
                    context_parts.append(f"Name: {english_name} ({item_name})")
                    context_parts.append(f"Category: {item.get('category', 'N/A')}")
                    context_parts.append(f"Price: {item.get('price', 'N/A')} {item.get('currency', 'N/A')}")
                    if item.get('description_mm'):
                        context_parts.append(f"Description: {item.get('description_mm')}")
                    elif item.get('description'):
                        context_parts.append(f"Description: {item.get('description')}")
                    if item.get('ingredients'):
                        context_parts.append(f"Ingredients: {item.get('ingredients')}")
                    if item.get('preparation_time'):
                        context_parts.append(f"Preparation Time: {item.get('preparation_time')}")
                    if item.get('spice_level'):
                        context_parts.append(f"Spice Level: {item.get('spice_level')}")
                    context_parts.append("")
            
            else:
                # Default menu display
                context_parts.append("RELEVANT MENU ITEMS FROM DATABASE:")
                for i, item in enumerate(search_results["menu_results"][:5], 1):
                    item_name = item.get('myanmar_name', item.get('name', 'N/A'))
                    english_name = item.get('name', 'N/A')
                    context_parts.append(f"Item #{i}:")
                    context_parts.append(f"Name: {english_name} ({item_name})")
                    context_parts.append(f"Price: {item.get('price', 'N/A')} {item.get('currency', 'N/A')}")
                    if item.get('description_mm'):
                        context_parts.append(f"Description: {item.get('description_mm')}")
                    elif item.get('description'):
                        context_parts.append(f"Description: {item.get('description')}")
                    context_parts.append("")
        
        return "\n".join(context_parts) if context_parts else "NO RELEVANT INFORMATION FOUND IN DATABASE"
    
    async def process_burmese_query(self, user_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process Burmese query using pure AI approach with enhanced menu handling
        """
        if not is_burmese_text(user_message):
            return {
                "response": "I can help you in Burmese. Please ask your question in Burmese.",
                "intent": "language_error",
                "confidence": 1.0
            }
        
        try:
            # Step 1: Early detection for simple greetings and thanks
            if self._is_simple_greeting(user_message):
                return {
                    "response": "မင်္ဂလာပါ ခင်ဗျာ! ကျနော်တို့ Cafe Pentagon မှာ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ ခင်ဗျာ?",
                    "intent": "greeting",
                    "method": "simple_greeting",
                    "confidence": 1.0
                }
            
            if self._is_simple_thanks(user_message):
                return {
                    "response": "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ! အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော်..",
                    "intent": "goodbye",
                    "method": "simple_thanks",
                    "confidence": 1.0
                }
            
            # Step 2: Check if this is a menu-related query
            menu_action = await self._analyze_menu_request(user_message, conversation_history or [])
            
            if menu_action and menu_action.get("action") != "OTHER":
                # Handle menu-specific requests
                return await self._handle_menu_request(user_message, menu_action)
            
            # Step 3: For non-menu queries, use the existing semantic context approach
            return await self._handle_general_query(user_message, conversation_history or [])
            
        except Exception as e:
            logger.error("burmese_query_processing_failed", error=str(e))
            return {
                "response": "တောင်းပန်ပါတယ်၊ ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။ ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ပြန်လည်မေးမြန်းပေးပါ။",
                "intent": "error",
                "method": "error_handling",
                "confidence": 0.0
            } 

    async def _analyze_menu_request(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyze if the request is menu-related and determine the specific action
        """
        try:
            # First, check if this is clearly NOT a menu query
            non_menu_keywords = [
                "တီးဝိုင်း", "ဂီတ", "သီချင်း", "ဖျော်ဖြေ", "အစီအစဉ်", "ပွဲ", "ပါတီ",
                "ဓါတ်ပုံ", "ရိုက်ကူး", "ကင်မရာ",  # Removed "ပုံ" to allow menu image requests
                "ဆိုင်က ဘယ်မှာ", "လိပ်စာ", "တည်နေရာ", "ဘယ်မှာ ရှိ",
                "ဖုန်း", "ဆက်သွယ်", "ခေါ်ဆို", "ဖုန်းနံပါတ်",
                "ဈေးနှုန်း", "စျေးနှုန်း", "ဈေးကြီး", "စျေးသက်သာ",
                "အချိန်", "ဖွင့်ချိန်", "ပိတ်ချိန်", "ဘယ်အချိန်",
                "ဝိုင်ဖိုင်", "wifi", "အင်တာနက်", "အင်တာနက်လိုင်း",
                "မီး", "မီးစက်", "အဲကွန်း", "လေအေးပေးစက်",
                "အပြင်ထိုင်ခုံ", "အပြင်ပန်း", "ဆေးလိပ်", "သောက်ခွင့်",
                "အစားအသောက်", "ပို့ပေးမှု", "delivery", "ပို့ဆောင်မှု",
                "ငွေပေးချေမှု", "ငွေပေးနည်း", "ကတ်", "ငွေသား",
                "ပရိုမိုးရှင်း", "လျှော့စျေး", "အထူးပရိုမိုး",
                "ကလေး", "ကလေးများ", "ကလေးမီနူး",
                "wheelchair", "ဘီးထိုင်ခုံ", "အသုံးပြုခွင့်",
                "အစားအသောက် ဝန်ဆောင်မှု", "catering", "ပွဲထိုး"
            ]
            
            # Check if the query contains non-menu keywords
            user_message_lower = user_message.lower()
            for keyword in non_menu_keywords:
                if keyword.lower() in user_message_lower:
                    return None  # This is not a menu query
            
            # Use the existing analyze_user_request method from vector service
            analysis = await self.vector_service.analyze_user_request(user_message, conversation_history)
            
            # Only return if it's a menu-related action
            action = analysis.get("action", "OTHER")
            if action in ["SHOW_CATEGORIES", "SHOW_CATEGORY_ITEMS", "SHOW_ITEM_DETAILS", "SHOW_ITEM_IMAGE"]:
                return analysis
            
            return None
            
        except Exception as e:
            logger.error("menu_request_analysis_failed", error=str(e))
            return None
    
    async def _handle_menu_request(self, user_message: str, menu_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle menu-specific requests using structured responses
        """
        try:
            action = menu_action.get("action", "OTHER")
            
            if action == "SHOW_CATEGORIES":
                response = await self._generate_categories_response()
                return {
                    "response": response,
                    "intent": "menu_browse",
                    "method": "menu_categories",
                    "found_menu": True,
                    "confidence": 0.8
                }
            
            elif action == "SHOW_CATEGORY_ITEMS":
                category = menu_action.get("category")
                if category:
                    response = await self._generate_category_items_response(category)
                    return {
                        "response": response,
                        "intent": "menu_browse",
                        "method": "menu_category_items",
                        "found_menu": True,
                        "confidence": 0.8
                    }
                else:
                    response = await self._generate_categories_response()
                    return {
                        "response": response,
                        "intent": "menu_browse",
                        "method": "menu_categories_fallback",
                        "found_menu": True,
                        "confidence": 0.8
                    }
            
            elif action == "SHOW_ITEM_DETAILS":
                item_name = menu_action.get("item_name")
                if item_name:
                    response = await self._generate_item_details_response(item_name)
                    return {
                        "response": response,
                        "intent": "menu_browse",
                        "method": "menu_item_details",
                        "found_menu": True,
                        "confidence": 0.8
                    }
                else:
                    response = await self._generate_categories_response()
                    return {
                        "response": response,
                        "intent": "menu_browse",
                        "method": "menu_categories_fallback",
                        "found_menu": True
                    }
            
            elif action == "SHOW_ITEM_IMAGE":
                item_name = menu_action.get("item_name")
                if item_name:
                    response = await self._generate_item_image_response(item_name)
                    return {
                        "response": response,
                        "intent": "menu_browse",
                        "method": "menu_item_image",
                        "found_menu": True,
                        "confidence": 0.8
                    }
                else:
                    response = await self._generate_categories_response()
                    return {
                        "response": response,
                        "intent": "menu_browse",
                        "method": "menu_categories_fallback",
                        "found_menu": True,
                        "confidence": 0.8
                    }
            
            else:
                # Fallback to general menu response
                response = await self._generate_categories_response()
                return {
                    "response": response,
                    "intent": "menu_browse",
                    "method": "menu_categories_fallback",
                    "found_menu": True,
                    "confidence": 0.8
                }
                
        except Exception as e:
            logger.error("menu_request_handling_failed", error=str(e))
            return {
                "response": "မီနူးနဲ့ပတ်သက်တဲ့ အချက်အလက်ကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။",
                "intent": "error",
                "method": "menu_error",
                "confidence": 0.0
            }
    
    async def _generate_categories_response(self) -> str:
        """Generate response showing menu categories"""
        try:
            # Get categories from vector search
            categories = await self.vector_service.get_menu_categories("my")
            
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
        """Generate response showing items from a specific category"""
        try:
            # Get items from vector search
            items = await self.vector_service.get_category_items(category, "my", limit=12)
            
            if not items:
                return f"'{category}' အမျိုးအစားမှာ အစားအစာများ မတွေ့ရှိပါဘူး။"
            
            # Format response with names and prices
            category_name = self.vector_service._get_category_display_name(category, "my")
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
        """Generate response with detailed information about a specific item"""
        try:
            # Get item details from vector search
            item = await self.vector_service.get_item_details(item_name, "my")
            
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
    
    async def _generate_item_image_response(self, item_name: str) -> str:
        """Generate response with image information for a specific item"""
        try:
            # Get image information from vector search
            image_info = await self.vector_service.get_item_image(item_name)
            
            if not image_info:
                return f"'{item_name}' အစားအစာရဲ့ ပုံကို မတွေ့ရှိပါဘူး။ ကျေးဇူးပြု၍ အခြားအစားအစာကို မေးကြည့်ပါ။"
            
            # Format natural conversational response
            response = f"**{image_info['item_name']}** ပုံပါ ခင်ဗျာ။ "
            response += f"ဈေးနှုန်းလေးကတော့ {image_info['price']} ဖြစ်ပါတယ်။"
           
            
            # Add image marker for the main agent to handle
            response += f"\n\n[IMAGE_MARKER:{image_info['image_url']}:{image_info['item_name']}]"
            
            return response
            
        except Exception as e:
            logger.error("item_image_response_generation_failed", error=str(e))
            return f"'{item_name}' အစားအစာရဲ့ ပုံကို ရယူရာတွင် ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။"

    async def _handle_general_query(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Handle general (non-menu) queries using the improved semantic context approach with proper fallback logic
        """
        try:
            # Step 1: Extract English semantic context from Burmese query
            semantic_context = await self.semantic_extractor.extract_semantic_context(user_message)
            english_context = semantic_context.get("english_context", user_message)
            query_type = semantic_context.get("query_type", "general")
            
            logger.info("using_semantic_context", 
                       burmese_query=user_message[:50],
                       english_context=english_context,
                       query_type=query_type)
            
            # Step 2: Determine appropriate data source
            data_source_info = await self.vector_service.determine_data_source(user_message, query_type)
            primary_source = data_source_info.get("primary_source", "faq")
            
            logger.info("data_source_determined", 
                       primary_source=primary_source,
                       reasoning=data_source_info.get("reasoning"),
                       confidence=data_source_info.get("confidence"))
            
            # Step 3: Search Pinecone with semantic context and determined data source
            search_results = await self.vector_service.search_pinecone_for_data(user_message, language="my")
            
            # Step 4: Calculate confidence based on search results
            # Since search_results contains metadata objects, not match objects with scores,
            # we'll use a different approach for confidence calculation
            faq_count = len(search_results.get("faq_results", []))
            menu_count = len(search_results.get("menu_results", []))
            events_count = len(search_results.get("events_results", []))
            
            # Calculate confidence based on data availability and semantic context
            semantic_confidence = semantic_context.get("confidence", 0.0)
            
            # If we found relevant data, use high confidence
            if faq_count > 0 or menu_count > 0 or events_count > 0:
                overall_confidence = max(0.7, semantic_confidence)  # Minimum 0.7 if data found
            else:
                overall_confidence = semantic_confidence * 0.5  # Lower confidence if no data found
            
            # Step 5: Generate response based on confidence and data availability
            if overall_confidence > 0.6 and (search_results.get("found_faq", False) or search_results.get("found_menu", False)):
                # High confidence with data found - use the data
                pinecone_context = await self._create_context_from_pinecone_results(search_results, user_message)
                response = await self._generate_ai_response(user_message, pinecone_context, conversation_history)
                
                return {
                    "response": response,
                    "intent": "ai_understood",
                    "method": "pinecone_vector_search",
                    "found_faq": search_results.get("found_faq", False),
                    "found_menu": search_results.get("found_menu", False),
                    "confidence": overall_confidence,
                    "data_source": primary_source
                }
            else:
                # Low confidence or no data found - use fallback logic
                response = await self._generate_fallback_response(user_message, search_results, conversation_history)
                
                return {
                    "response": response,
                    "intent": "fallback_response",
                    "method": "confidence_based_fallback",
                    "found_faq": search_results.get("found_faq", False),
                    "found_menu": search_results.get("found_menu", False),
                    "confidence": overall_confidence,
                    "data_source": primary_source
                }
            
        except Exception as e:
            logger.error("general_query_handling_failed", error=str(e))
            return {
                "response": "တောင်းပန်ပါတယ်၊ ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။ ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ပြန်လည်မေးမြန်းပေးပါ။",
                "intent": "error",
                "method": "error_handling",
                "confidence": 0.0
            }
    
    async def _generate_ai_response(self, user_message: str, pinecone_context: str, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate AI response for general queries using the existing approach
        """
        try:
            # Create conversation context
            conversation_context = ""
            if conversation_history:
                recent_messages = conversation_history[-3:]  # Keep last 3 messages for context
                conversation_context = "\nRecent conversation:\n"
                for msg in recent_messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    conversation_context += f"{role}: {content}\n"
            
            # Check if we have database information
            has_database_info = (pinecone_context.strip() and 
                               "NO RELEVANT INFORMATION FOUND IN DATABASE" not in pinecone_context and
                               ("RELEVANT FAQ INFORMATION FROM DATABASE" in pinecone_context or 
                                "RELEVANT EVENTS INFORMATION FROM DATABASE" in pinecone_context or
                                "AVAILABLE MENU CATEGORIES" in pinecone_context or
                                "MENU ITEMS IN RELEVANT CATEGORIES" in pinecone_context or
                                "DETAILED MENU ITEM INFORMATION" in pinecone_context or
                                "RELEVANT MENU ITEMS FROM DATABASE" in pinecone_context))
            
            if has_database_info:
                # STRICT DATABASE RESPONSE - Use exact database content
                prompt = f"""
You are a helpful restaurant assistant for Cafe Pentagon in Yangon, Myanmar.

CRITICAL INSTRUCTIONS:
1. You MUST use ONLY the information provided in the database below
2. You MUST use the EXACT Burmese text from the database - do NOT translate or modify
3. You MUST NOT generate any new information not in the database
4. You MUST NOT add explanations or additional details
5. You MUST respond in natural, conversational Burmese style
6. If the database information is NOT relevant to the user's question, respond with the fallback message

DATABASE INFORMATION:
{pinecone_context}

{conversation_context}

Customer Question: {user_message}

IMPORTANT: 
- If the database contains relevant information, use the EXACT Burmese answer from the database
- If the database information is NOT relevant to the user's question, respond with: "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ် ခင်ဗျာ။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ် ခင်ဗျာ။ နားလည်ပေးတဲ့အတွက် ကျေးဇူး အများကြီး တင်ပါတယ်။"

Response:"""
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a Burmese restaurant assistant. CRITICAL: You MUST use ONLY the exact information from the database provided. Do NOT translate, modify, or generate new content. Use the exact Burmese text from the database and respond naturally. If the database information is not relevant to the user's question, use the fallback message."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Very low temperature for consistency
                    max_tokens=300
                )
                
                return response.choices[0].message.content.strip()
                
            else:
                # NO DATABASE INFO - Let AI decide the appropriate response
                prompt = f"""
You are a friendly restaurant assistant for Cafe Pentagon in Yangon, Myanmar.

CUSTOMER MESSAGE: {user_message}

INSTRUCTIONS:
1. If this is a greeting (မင်္ဂလာပါ, ဟလို, ဟေး, etc.) - respond warmly and naturally
2. If this is a thank you (ကျေးဇူးတင်ပါတယ်, ကျေးဇူး, etc.) - respond politely and warmly
3. If this is a question that requires specific information not in our database - politely suggest calling +959979732781
4. For general conversation - be friendly and helpful
5. Keep responses concise and natural in Burmese

Examples:
- Greeting: "မင်္ဂလာပါ ခင်ဗျာ! ကျနော်တို့ Cafe Pentagon မှာ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ ခင်ဗျာ?"
- Thank you: "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ! နောက်တစ်ခါလည်း လာရောက်လည်ပတ်ပေးပါ။"
- Unknown question: "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ် ခင်ဗျာ။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ် ခင်ဗျာ။"

Response:"""
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a friendly Burmese restaurant assistant. Respond naturally and appropriately based on the customer's message. Use the phone referral only when specific information is needed that's not in your knowledge base."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("ai_response_generation_failed", error=str(e))
            return "တောင်းပန်ပါတယ်၊ ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။ ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ပြန်လည်မေးမြန်းပေးပါ။"
    
    async def _generate_fallback_response(self, user_message: str, search_results: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate fallback response when no relevant data is found
        """
        try:
            # Calculate confidence from search results
            faq_count = len(search_results.get("faq_results", []))
            menu_count = len(search_results.get("menu_results", []))
            events_count = len(search_results.get("events_results", []))
            
            # Check if we found any relevant data
            found_data = faq_count > 0 or menu_count > 0 or events_count > 0
            
            # If we found data, use it regardless of confidence (since we have the data)
            if found_data:
                # Use the existing AI response generation with found data
                pinecone_context = await self._create_context_from_pinecone_results(search_results, user_message)
                return await self._generate_ai_response(user_message, pinecone_context, conversation_history)
            
            # No data found or low confidence - Let AI decide the appropriate response
            prompt = f"""
You are a friendly restaurant assistant for Cafe Pentagon in Yangon, Myanmar.

CUSTOMER MESSAGE: {user_message}

INSTRUCTIONS:
1. If this is a greeting (မင်္ဂလာပါ, ဟလို, ဟေး, etc.) - respond warmly and naturally
2. If this is a thank you (ကျေးဇူးတင်ပါတယ်, ကျေးဇူး, etc.) - respond politely and warmly
3. If this is a question that requires specific information not in our database - politely suggest calling +959979732781
4. For general conversation - be friendly and helpful
5. Keep responses concise and natural in Burmese

Examples:
- Greeting: "မင်္ဂလာပါ ခင်ဗျာ! ကျနော်တို့ Cafe Pentagon မှာ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ ခင်ဗျာ?"
- Thank you: "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ! အခြား သိလိုတာ ရှိရင်လည်း ပြောပါနော်.."
- Unknown question: "ဒီအကြောင်းအရာနဲ့ ပတ်သက်ပြီး သေချာ မသိရှိလို့ တောင်းပန်ပါတယ် ခင်ဗျာ။ အသေးစိတ် အချက်အလက်ကို +959979732781 ကို ဆက်သွယ် မေးမြန်းနိုင်ပါတယ် ခင်ဗျာ။"

Response:"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a friendly Burmese restaurant assistant. Respond naturally and appropriately based on the customer's message. Use the phone referral only when specific information is needed that's not in your knowledge base."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error("fallback_response_generation_failed", error=str(e))
            return "တောင်းပန်ပါတယ်၊ ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။ ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ပြန်လည်မေးမြန်းပေးပါ။"
    
 