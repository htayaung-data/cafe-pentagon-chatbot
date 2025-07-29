"""
Vector Search Service for Cafe Pentagon Chatbot
Handles Pinecone queries for menu categories, items, and images
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from src.config.settings import get_settings
from src.config.constants import PINECONE_NAMESPACES
from src.utils.logger import get_logger

logger = get_logger("vector_search_service")


class VectorSearchService:
    """
    Service for vector-based search using Pinecone
    """
    
    def __init__(self):
        """Initialize vector search service"""
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=self.settings.openai_api_key
        )
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=self.settings.openai_api_key
        )
        
        # Initialize Pinecone
        from pinecone import Pinecone
        pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.pinecone_index = pc.Index(self.settings.pinecone_index_name)
        
        logger.info("vector_search_service_initialized")

    async def analyze_user_request(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use AI to analyze user request and determine what action to take
        """
        try:
            # Create context from conversation history
            context = self._create_conversation_context(conversation_history)
            
            # AI prompt for request analysis
            prompt = f"""
You are analyzing a user's request about a restaurant menu. Based on the user's message and conversation history, determine what they want.

USER MESSAGE: {user_message}

CONVERSATION HISTORY:
{context}

ANALYSIS TASK:
Determine the user's intent and what information they need. Choose from these options:

1. SHOW_CATEGORIES - User wants to see menu categories (e.g., "What is available?", "Show me your menu", "What do you have?")
2. SHOW_CATEGORY_ITEMS - User wants to see items from a specific category (e.g., "Show me breakfast", "I want pasta", "What salads do you have?", "ခေါက်ဆွဲထဲ က ဘာတွေ ရှိလဲ", "what kind of noodles can we have")
3. SHOW_ITEM_DETAILS - User wants details about a specific item (e.g., "Tell me about the burger", "What's in the omelette?")
4. SHOW_ITEM_IMAGE - User wants to see an image of a specific item (e.g., "Show me the picture", "Can I see the image?", "Show photo")
5. OTHER - User is asking something else

IMPORTANT: For category browsing questions, look for patterns like:
- "what kind of [category]"
- "what [category] do you have" 
- "[category] ဘာတွေ ရှိလဲ"
- "ဘယ်လို [category] တွေ ရှိလဲ"

Available categories: breakfast, main_course, appetizers_sides, soups, noodles, sandwiches_burgers, salads, pasta, rice_dishes

RESPONSE FORMAT:
Return a JSON object with:
- "action": the determined action (SHOW_CATEGORIES, SHOW_CATEGORY_ITEMS, SHOW_ITEM_DETAILS, SHOW_ITEM_IMAGE, OTHER)
- "category": the specific category if relevant (e.g., "breakfast", "pasta", "salads", "noodles", "sandwiches_burgers", etc.)
- "item_name": the specific item name if relevant
- "reasoning": brief explanation of your decision
- "confidence": confidence score 0.0-1.0

RESPONSE:"""

            # Get AI analysis
            response = await self.llm.ainvoke(prompt)
            response_text = response.content.strip()
            
            # Parse JSON response
            try:
                # Clean response text
                cleaned_response = response_text.strip()
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
                
                logger.info("user_request_analyzed", 
                           user_message=user_message[:100],
                           action=result.get("action"),
                           confidence=result.get("confidence"))
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error("ai_analysis_parse_error", error=str(e), response=response_text)
                return {
                    "action": "OTHER",
                    "category": None,
                    "item_name": None,
                    "reasoning": "Failed to parse AI response",
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error("user_request_analysis_failed", error=str(e))
            return {
                "action": "OTHER",
                "category": None,
                "item_name": None,
                "reasoning": "Analysis failed",
                "confidence": 0.5
            }

    async def get_menu_categories(self, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get all menu categories from Pinecone
        """
        try:
            # Get all data from Pinecone to extract categories
            results = self.pinecone_index.query(
                vector=[0.0] * 1536,  # Dummy vector to get all data
                namespace=PINECONE_NAMESPACES["menu"],
                top_k=1000,  # Get all items
                include_metadata=True
            )
            
            # Extract unique categories and count items
            categories = {}
            for match in results.matches:
                category = match.metadata.get("category", "")
                if category:
                    if category not in categories:
                        categories[category] = {
                            "category": category,
                            "display_name": self._get_category_display_name(category, language),
                            "count": 1
                        }
                    else:
                        categories[category]["count"] += 1
            
            category_list = list(categories.values())
            
            # Sort by category name for consistent ordering
            category_list.sort(key=lambda x: x["display_name"])
            
            logger.info("menu_categories_retrieved", 
                       categories_count=len(category_list),
                       language=language)
            
            return category_list
            
        except Exception as e:
            logger.error("menu_categories_retrieval_failed", error=str(e))
            return []

    async def get_category_items(self, category: str, language: str = "en", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get items from a specific category
        """
        try:
            # First, get all available categories from Pinecone to find the best match
            all_results = self.pinecone_index.query(
                vector=[0.0] * 1536,  # Dummy vector to get all data
                namespace=PINECONE_NAMESPACES["menu"],
                top_k=1000,
                include_metadata=True
            )
            
            # Extract all unique categories
            available_categories = set()
            for match in all_results.matches:
                cat = match.metadata.get("category", "")
                if cat:
                    available_categories.add(cat)
            
            # Find the best matching category using AI
            category_mapping_prompt = f"""
Given the user's request for category "{category}", find the best matching category from the available categories.

AVAILABLE CATEGORIES: {list(available_categories)}

USER REQUEST: {category}

TASK: Return the exact category name from the available categories that best matches the user's request.

EXAMPLES:
- User asks for "burger" or "ဘာဂါ" → return "sandwiches_burgers"
- User asks for "main dishes" or "အဓိကဟင်း" → return "main_course"  
- User asks for "salad" or "ဆလပ်" → return "salads"
- User asks for "rice dishes" or "ထမင်းဟင်း" → return "rice_dishes"
- User asks for "noodles" or "ခေါက်ဆွဲ" → return "noodles"
- User asks for "breakfast" or "နံနက်စာ" → return "breakfast"
- User asks for "soups" or "ဟင်းရည်" → return "soups"
- User asks for "pasta" or "ပါစတာ" → return "pasta"

RESPONSE: Return only the exact category name from the available categories list.
"""
            
            mapping_response = await self.llm.ainvoke(category_mapping_prompt)
            best_category = mapping_response.content.strip()
            
            # If AI didn't return a valid category, try direct match
            if best_category not in available_categories:
                # Try to find a partial match
                for available_cat in available_categories:
                    if category.lower() in available_cat.lower() or available_cat.lower() in category.lower():
                        best_category = available_cat
                        break
                else:
                    # Try Burmese to English mapping for common categories
                    burmese_mapping = {
                        "ခေါက်ဆွဲ": "noodles",
                        "ဆလပ်": "salads", 
                        "ထမင်းဟင်း": "rice_dishes",
                        "အဓိကဟင်း": "main_course",
                        "နံနက်စာ": "breakfast",
                        "ဟင်းရည်": "soups",
                        "ပါစတာ": "pasta",
                        "ဘာဂါ": "sandwiches_burgers"
                    }
                    
                    if category in burmese_mapping:
                        best_category = burmese_mapping[category]
                    else:
                        # If no match found, use the original category
                        best_category = category
            
            # Search for items in the specific category
            query_text = f"menu items {category}"
            embedding = self.embeddings.embed_query(query_text)
            
            # Query Pinecone
            results = self.pinecone_index.query(
                vector=embedding,
                namespace=PINECONE_NAMESPACES["menu"],
                top_k=limit * 2,  # Get more to filter by category
                include_metadata=True,
                filter={"category": best_category}
            )
            
            # Process results
            items = []
            for match in results.matches:
                metadata = match.metadata
                # Check if the item belongs to the requested category
                if metadata.get("category") == best_category:
                    item = {
                        "id": metadata.get("id"),
                        "name": metadata.get("name") if language == "en" else metadata.get("myanmar_name"),
                        "name_other": metadata.get("myanmar_name") if language == "en" else metadata.get("name"),
                        "price": metadata.get("price"),
                        "currency": metadata.get("currency", "MMK"),
                        "description": metadata.get("description") if language == "en" else metadata.get("description_mm"),
                        "image_url": metadata.get("image_url"),
                        "category": metadata.get("category"),
                        "dietary_info": json.loads(metadata.get("dietary_info", "{}")),
                        "allergens": json.loads(metadata.get("allergens", "[]")),
                        "spice_level": metadata.get("spice_level"),
                        "preparation_time": metadata.get("preparation_time"),
                        "similarity_score": match.score
                    }
                    items.append(item)
            
            # Sort by similarity score and limit
            items.sort(key=lambda x: x["similarity_score"], reverse=True)
            items = items[:limit]
            
            logger.info("category_items_retrieved", 
                       category=category,
                       items_count=len(items),
                       language=language)
            
            return items
            
        except Exception as e:
            logger.error("category_items_retrieval_failed", 
                        category=category, 
                        error=str(e))
            return []

    async def get_item_details(self, item_name: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific item with improved search accuracy
        """
        try:
            # Create more specific search queries
            search_queries = []
            
            # Add the original item name
            search_queries.append(item_name)
            
            # Add category-specific searches with better Burmese support
            if any(word in item_name.lower() for word in ["burger", "ဘာဂါ", "အမဲသား", "အသားညှပ်"]):
                search_queries.extend(["burger", "beef burger", "အမဲသားညှပ်ပေါင်မုန့်", "ဘာဂါ"])
            elif any(word in item_name.lower() for word in ["tuna", "တူနာ", "ငါး", "ငါးအသား"]):
                search_queries.extend(["tuna", "tuna sandwich", "တူနာငါးအသားညှပ်ပေါင်မုန့်", "တူနာ"])
            elif any(word in item_name.lower() for word in ["pasta", "ပါစတာ", "ခေါက်ဆွဲ"]):
                search_queries.extend(["pasta", "ပါစတာ", "noodles"])
            elif any(word in item_name.lower() for word in ["salad", "ဆလပ်", "အရွက်"]):
                search_queries.extend(["salad", "ဆလပ်", "vegetables"])
            elif any(word in item_name.lower() for word in ["noodle", "ခေါက်ဆွဲ", "ခေါက်ဆွဲခြောက်"]):
                search_queries.extend(["noodle", "ခေါက်ဆွဲ", "noodles"])
            elif any(word in item_name.lower() for word in ["rice", "ထမင်း", "ထမင်းဟင်း"]):
                search_queries.extend(["rice", "ထမင်း", "rice dish"])
            elif any(word in item_name.lower() for word in ["soup", "ဟင်းရည်", "ဟင်းချို"]):
                search_queries.extend(["soup", "ဟင်းရည်", "soups"])
            
            # Try each search query
            best_match = None
            best_score = 0
            
            for query in search_queries:
                embedding = self.embeddings.embed_query(query)
                
                # Query Pinecone with higher top_k for better matching
                results = self.pinecone_index.query(
                    vector=embedding,
                    namespace=PINECONE_NAMESPACES["menu"],
                    top_k=15,  # Increased for better matching
                    include_metadata=True
                )
                
                # Find the best match for this query
                for match in results.matches:
                    metadata = match.metadata
                    score = match.score
                    
                    # Check if this is a better match
                    if score > best_score:
                        # Additional validation for better accuracy
                        item_name_lower = item_name.lower()
                        english_name = metadata.get("name", "").lower()
                        myanmar_name = metadata.get("myanmar_name", "").lower()
                        
                        # Check for exact or partial matches
                        if (item_name_lower in english_name or 
                            item_name_lower in myanmar_name or
                            english_name in item_name_lower or
                            myanmar_name in item_name_lower):
                            best_match = metadata
                            best_score = score
                        # For category-specific searches, be more lenient
                        elif any(word in item_name_lower for word in ["burger", "ဘာဂါ", "အသားညှပ်"]) and "burger" in english_name:
                            best_match = metadata
                            best_score = score
                        elif any(word in item_name_lower for word in ["tuna", "တူနာ", "ငါး"]) and "tuna" in english_name:
                            best_match = metadata
                            best_score = score
                        elif any(word in item_name_lower for word in ["noodle", "ခေါက်ဆွဲ"]) and "noodle" in english_name:
                            best_match = metadata
                            best_score = score
                        elif any(word in item_name_lower for word in ["pasta", "ပါစတာ"]) and "pasta" in english_name:
                            best_match = metadata
                            best_score = score
            
            if best_match and best_score > 0.6:  # Lowered threshold for better Burmese matching
                item = {
                    "id": best_match.get("id"),
                    "name": best_match.get("name") if language == "en" else best_match.get("myanmar_name"),
                    "name_other": best_match.get("myanmar_name") if language == "en" else best_match.get("name"),
                    "price": best_match.get("price"),
                    "currency": best_match.get("currency", "MMK"),
                    "description": best_match.get("description") if language == "en" else best_match.get("description_mm"),
                    "image_url": best_match.get("image_url"),
                    "category": best_match.get("category"),
                    "dietary_info": json.loads(best_match.get("dietary_info", "{}")),
                    "allergens": json.loads(best_match.get("allergens", "[]")),
                    "spice_level": best_match.get("spice_level"),
                    "preparation_time": best_match.get("preparation_time"),
                    "ingredients": best_match.get("ingredients", []),
                    "similarity_score": best_score
                }
                
                logger.info("item_details_retrieved", 
                           item_name=item_name,
                           found_item=item["name"],
                           language=language,
                           similarity_score=best_score)
                
                return item
            
            logger.warning("item_not_found", item_name=item_name, best_score=best_score)
            return None
            
        except Exception as e:
            logger.error("item_details_retrieval_failed", 
                        item_name=item_name, 
                        error=str(e))
            return None

    async def get_item_image(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Get image information for a specific item with improved Burmese text handling
        """
        try:
            # Try to get item details in English first
            item = await self.get_item_details(item_name, language="en")
            
            # If not found and the input looks like Burmese, try Burmese search
            if not item and any('\u1000' <= char <= '\u109F' for char in item_name):
                # Try searching with Burmese language
                item = await self.get_item_details(item_name, language="my")
            
            if item and item.get("image_url"):
                image_info = {
                    "item_name": item["name"],
                    "image_url": item["image_url"],
                    "category": item["category"],
                    "price": f"{item['price']} {item['currency']}"
                }
                
                logger.info("item_image_retrieved", 
                           item_name=item_name,
                           image_url=item["image_url"])
                
                return image_info
            
            logger.warning("item_image_not_found", item_name=item_name)
            return None
            
        except Exception as e:
            logger.error("item_image_retrieval_failed", 
                        item_name=item_name, 
                        error=str(e))
            return None

    def _create_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Create context string from conversation history"""
        if not conversation_history:
            return "No previous conversation."
        
        # Get last 5 messages for context
        recent_messages = conversation_history[-5:]
        context_lines = []
        
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            # Clean content
            import re
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            context_lines.append(f"{role}: {clean_content}")
        
        return "\n".join(context_lines)

    def _get_category_display_name(self, category: str, language: str) -> str:
        """Get display name for category in specified language"""
        # Handle enum format categories
        if category.startswith("MenuCategoryEnum."):
            category = category.replace("MenuCategoryEnum.", "").lower()
        
        category_names = {
            "en": {
                "breakfast": "Breakfast",
                "main_course": "Main Course",
                "appetizers_sides": "Appetizers & Sides",
                "soups": "Soups",
                "noodles": "Noodles",
                "sandwiches_burgers": "Sandwiches & Burgers",
                "salads": "Salad",
                "salad": "Salad",  # Handle both singular and plural
                "pasta": "Pasta",
                "rice_dishes": "Rice Dishes"
            },
            "my": {
                "breakfast": "နံနက်စာ",
                "main_course": "အဓိကဟင်း",
                "appetizers_sides": "အစာစတင် နှင့် ဘေးထွက်ဟင်း",
                "soups": "ဟင်းရည်",
                "noodles": "ခေါက်ဆွဲ",
                "sandwiches_burgers": "အသားညှပ် နှင့် ဘာဂါ",
                "salads": "ဆလပ်",
                "salad": "ဆလပ်",  # Handle both singular and plural
                "pasta": "ပါစတာ",
                "rice_dishes": "ထမင်းဟင်း"
            }
        }
        
        return category_names.get(language, {}).get(category, category.title())


def get_vector_search_service() -> VectorSearchService:
    """Get vector search service instance"""
    return VectorSearchService() 