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
        Get detailed information about a specific item using semantic understanding
        """
        try:
            # Extract semantic context for better understanding
            semantic_context = await self._extract_semantic_context(item_name, language)
            
            # Search using semantic context
            search_results = await self._semantic_search_menu_items(semantic_context, item_name, language)
            
            if search_results:
                best_match = search_results[0]  # Get the best match
                confidence = best_match.get("confidence", 0)
                
                # If confidence is high enough, return the item
                if confidence > 0.70:
                    item = self._format_item_details(best_match["metadata"], language)
                    item["similarity_score"] = confidence
                    item["suggested_alternatives"] = [r["metadata"].get("name", r["metadata"].get("myanmar_name", "")) for r in search_results[1:3]]
                    
                    logger.info("item_details_retrieved", 
                               item_name=item_name,
                               found_item=item["name"],
                               language=language,
                               similarity_score=confidence)
                    
                    return item
                else:
                    # Low confidence - suggest alternatives with both names when available
                    alternatives = []
                    for r in search_results[:3]:
                        metadata = r["metadata"]
                        english_name = metadata.get("name", "")
                        burmese_name = metadata.get("myanmar_name", "")
                        if english_name and burmese_name:
                            alternatives.append(f"{english_name} ({burmese_name})")
                        else:
                            alternatives.append(english_name or burmese_name)
                    
                    # Format message in Burmese with bullet points showing both English and Burmese names
                    if language == "my":
                        message = f"အောက်ပါ အစားအစာများထဲက တစ်ခုခုကို ဆိုလိုတာလား?\n\n"
                        for alt in alternatives:
                            message += f"• {alt}\n"
                    else:
                        message = f"Please, do you mean one of these items?\n\n"
                        for alt in alternatives:
                            message += f"• {alt}\n"
                    
                    return {
                        "type": "clarification_needed",
                        "message": message,
                        "alternatives": alternatives,
                        "confidence": confidence
                    }
            
            # No relevant matches found
            logger.warning("item_not_found", item_name=item_name)
            return None
            
        except Exception as e:
            logger.error("item_details_retrieval_failed", 
                        item_name=item_name, 
                        error=str(e))
            return None

    def _format_item_details(self, metadata: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Format item details from metadata
        """
        return {
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
            "ingredients": metadata.get("ingredients", [])
        }

    async def _find_exact_burmese_match(self, burmese_query: str) -> Optional[Dict[str, Any]]:
        """
        Find exact matches for Burmese menu items using text similarity
        """
        try:
            # Create embeddings for the Burmese query
            query_embedding = self.embeddings.embed_query(burmese_query)
            
            # Search in Pinecone
            results = self.pinecone_index.query(
                vector=query_embedding,
                namespace=PINECONE_NAMESPACES["menu"],
                top_k=50,  # Search more items for exact matching
                include_metadata=True
            )
            
            # Look for high-confidence matches
            for match in results.matches:
                metadata = match.metadata
                score = match.score
                
                # Check if the Burmese name contains key terms from the query
                myanmar_name = metadata.get("myanmar_name", "")
                if myanmar_name:
                    # Calculate text similarity score
                    text_similarity = self._calculate_text_similarity(burmese_query, myanmar_name)
                    
                    # Combine vector similarity with text similarity
                    combined_score = (score + text_similarity) / 2
                    
                    if combined_score > 0.8:  # High threshold for exact matches
                        return {
                            **metadata,
                            "similarity_score": combined_score
                        }
            
            return None
            
        except Exception as e:
            logger.error("exact_match_search_failed", 
                        burmese_query=burmese_query,
                        error=str(e))
            return None

    def _calculate_text_similarity(self, query: str, target: str) -> float:
        """
        Calculate text similarity between query and target using simple character matching
        """
        try:
            # Remove common words and punctuation
            query_clean = ''.join(c for c in query if c.isalnum() or '\u1000' <= c <= '\u109F')
            target_clean = ''.join(c for c in target if c.isalnum() or '\u1000' <= c <= '\u109F')
            
            # Count matching characters
            matches = 0
            total_chars = len(query_clean)
            
            for char in query_clean:
                if char in target_clean:
                    matches += 1
            
            if total_chars == 0:
                return 0.0
                
            return matches / total_chars
            
        except Exception:
            return 0.0

    async def _extract_semantic_context(self, query: str, language: str) -> str:
        """
        Extract semantic context from user query for better understanding
        """
        try:
            from src.config.settings import get_settings
            from openai import OpenAI
            
            settings = get_settings()
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Create a prompt to extract semantic meaning
            prompt = f"""
            Extract the semantic meaning from this food/drink query: "{query}"
            
            Language: {language}
            
            Focus on:
            1. Main ingredients (meat, vegetables, noodles, etc.)
            2. Cooking method (fried, grilled, steamed, etc.)
            3. Dish type (soup, noodle dish, rice dish, etc.)
            4. Any specific flavors or styles
            
            Return a clear, concise English description that captures the essence of what the user is asking for.
            Do not include explanations, just the semantic description.
            
            Examples:
            - "ကြာဇံကြော် ဝက်သား" → "glass noodle stir-fry with pork"
            - "ခေါက်ဆွဲကြော် ကြက်သား" → "fried noodle with chicken"
            - "ပုဇွန်ပဲကြာဇံကြော်" → "glass noodle with prawns"
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts semantic meaning from food queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            semantic_context = response.choices[0].message.content.strip()
            logger.info("semantic_context_extracted", 
                       original_query=query,
                       semantic_context=semantic_context)
            
            return semantic_context
            
        except Exception as e:
            logger.error("semantic_context_extraction_failed", 
                        query=query,
                        error=str(e))
            # Fallback to original query
            return query

    async def _semantic_search_menu_items(self, semantic_context: str, original_query: str, language: str) -> List[Dict[str, Any]]:
        """
        Search menu items using semantic context and calculate confidence scores
        """
        try:
            # Create embedding for semantic context
            embedding = self.embeddings.embed_query(semantic_context)
            
            # Search in Pinecone
            results = self.pinecone_index.query(
                vector=embedding,
                namespace=PINECONE_NAMESPACES["menu"],
                top_k=20,
                include_metadata=True
            )
            
            # Calculate confidence scores for each match
            scored_results = []
            
            for match in results.matches:
                metadata = match.metadata
                vector_score = match.score
                
                # Calculate text similarity if Burmese
                text_similarity = 0.0
                if language == "my" and metadata.get("myanmar_name"):
                    text_similarity = self._calculate_text_similarity(original_query, metadata.get("myanmar_name", ""))
                
                # Additional semantic checks for Burmese
                semantic_bonus = 0.0
                if language == "my":
                    # Check for key ingredient matches
                    myanmar_name = metadata.get("myanmar_name", "").lower()
                    query_lower = original_query.lower()
                    
                    # For very short queries (1-2 words), be more strict
                    query_words = query_lower.split()
                    if len(query_words) <= 2:
                        # Reduce semantic bonus for ambiguous queries
                        semantic_bonus -= 0.1
                    
                    # Check for protein matches with higher weight
                    protein_keywords = {
                        "ဝက်သား": ["ဝက်", "pork"],
                        "ကြက်သား": ["ကြက်", "chicken"],
                        "ပုဇွန်": ["ပုဇွန်", "prawn", "shrimp"],
                        "ငါး": ["ငါး", "fish"]
                    }
                    
                    for protein_burmese, keywords in protein_keywords.items():
                        if protein_burmese in query_lower:
                            if any(keyword in myanmar_name for keyword in keywords):
                                semantic_bonus += 0.25  # Increased from 0.15
                            else:
                                semantic_bonus -= 0.25  # Increased penalty
                    
                    # Check for noodle type matches with higher weight
                    noodle_keywords = {
                        "ကြာဇံ": ["ကြာဇံ", "vermicelli", "glass noodle"],
                        "ခေါက်ဆွဲ": ["ခေါက်ဆွဲ", "noodle"]
                    }
                    
                    for noodle_burmese, keywords in noodle_keywords.items():
                        if noodle_burmese in query_lower:
                            if any(keyword in myanmar_name for keyword in keywords):
                                semantic_bonus += 0.2  # Increased from 0.1
                            else:
                                semantic_bonus -= 0.2  # Increased penalty
                    
                    # Check for cooking method matches (critical distinction)
                    cooking_keywords = {
                        "ကြော်": ["ကြော်", "fried", "stir-fry"],
                        "ပြုတ်": ["ပြုတ်", "soup", "boiled"]
                    }
                    
                    for cooking_burmese, keywords in cooking_keywords.items():
                        if cooking_burmese in query_lower:
                            if any(keyword in myanmar_name for keyword in keywords):
                                semantic_bonus += 0.3  # Increased from 0.2
                            else:
                                semantic_bonus -= 0.3  # Increased penalty
                    
                    # Special handling for "နဲ့" (with) queries - boost score for items containing both ingredients
                    if "နဲ့" in query_lower:
                        # Check if both ingredients are present in the item name
                        query_parts = query_lower.split("နဲ့")
                        if len(query_parts) == 2:
                            part1, part2 = query_parts[0].strip(), query_parts[1].strip()
                            # Check if both parts are found in the item name
                            if (any(keyword in myanmar_name for keyword in part1.split()) and 
                                any(keyword in myanmar_name for keyword in part2.split())):
                                semantic_bonus += 0.15  # Bonus for "with" queries that match both ingredients
                
                # Combine scores with semantic bonus
                if text_similarity > 0:
                    # Give higher weight to text similarity for exact matches
                    combined_score = (vector_score * 0.3 + text_similarity * 0.5 + semantic_bonus)
                else:
                    combined_score = (vector_score * 0.6 + semantic_bonus)
                
                # Ensure score is between 0 and 1
                combined_score = max(0.0, min(1.0, combined_score))
                
                scored_results.append({
                    "metadata": metadata,
                    "vector_score": vector_score,
                    "text_similarity": text_similarity,
                    "confidence": combined_score
                })
            
            # Sort by confidence score
            scored_results.sort(key=lambda x: x["confidence"], reverse=True)
            
            logger.info("semantic_search_completed", 
                       semantic_context=semantic_context,
                       results_count=len(scored_results),
                       top_confidence=scored_results[0]["confidence"] if scored_results else 0)
            
            return scored_results
            
        except Exception as e:
            logger.error("semantic_search_failed", 
                        semantic_context=semantic_context,
                        error=str(e))
            return []

    async def _translate_burmese_request(self, burmese_text: str) -> List[str]:
        """
        Use AI to translate and understand Burmese food requests
        """
        try:
            from src.config.settings import get_settings
            from openai import OpenAI
            
            settings = get_settings()
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Create a prompt that helps the AI understand and translate the request
            prompt = f"""
            You are a helpful assistant that translates Burmese food requests to English menu item names.
            
            The user is asking for a food item in Burmese: "{burmese_text}"
            
            Please analyze this request and provide 3-5 English translations or related menu item names that would help find the correct food item.
            
            Consider:
            1. Direct translations of the Burmese text
            2. Common English names for similar dishes
            3. Related food categories or ingredients
            4. Popular menu item names that might match the request
            
            Common Burmese food vocabulary:
            - ကြက်သား = chicken
            - ဝက်သား = pork
            - ငါး = fish
            - ပုဇွန် = shrimp/prawn
            - ခေါက်ဆွဲ = noodles (regular wheat noodles)
            - ကြာဇံ = glass noodles/vermicelli (rice vermicelli)
            - ပါစတာ = pasta
            - ဘာဂါ = burger
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
            
            IMPORTANT: Be very specific about the type of meat/protein mentioned.
            - If the user mentions "ဝက်သား" (pork), include "pork" in the translation
            - If the user mentions "ကြက်သား" (chicken), include "chicken" in the translation
            - If the user mentions "ပုဇွန်" (shrimp), include "shrimp" or "prawn" in the translation
            
            Return only the English terms, separated by commas. Do not include explanations or additional text.
            
            Examples:
            Burmese: "ကြာဇံကြော် ဝက်သား" → English: vermicelli with pork, glass noodle with pork, rice vermicelli with pork, fried vermicelli pork, glass noodle pork dish
            Burmese: "ကြာဇံကြော် ကြက်သား" → English: vermicelli with chicken, glass noodle with chicken, rice vermicelli with chicken, fried vermicelli chicken, glass noodle chicken dish
            Burmese: "ခေါက်ဆွဲကြော် ဝက်သား" → English: fried noodle with pork, wheat noodle with pork, stir fried noodle pork, noodle pork dish, fried noodle pork
            Burmese: "ခေါက်ဆွဲကြော် ကြက်သား" → English: fried noodle with chicken, wheat noodle with chicken, stir fried noodle chicken, noodle chicken dish, fried noodle chicken
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a food translation expert that helps translate Burmese food requests to English menu terms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            # Extract the translated terms
            translated_text = response.choices[0].message.content.strip()
            translated_terms = [term.strip() for term in translated_text.split(',') if term.strip()]
            
            # Add the original Burmese text as a fallback
            translated_terms.append(burmese_text)
            
            logger.info("burmese_request_translated", 
                       original=burmese_text,
                       translated_terms=translated_terms)
            
            return translated_terms
            
        except Exception as e:
            logger.error("burmese_translation_failed", 
                        burmese_text=burmese_text,
                        error=str(e))
            # Fallback to original text if translation fails
            return [burmese_text]

    async def get_item_image(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Get image information for a specific item using AI-powered natural language understanding
        """
        try:
            # Determine if the input is in Burmese
            is_burmese = any('\u1000' <= char <= '\u109F' for char in item_name)
            
            # Use AI-powered approach for better understanding
            if is_burmese:
                # Use AI to translate and understand the Burmese request
                translated_queries = await self._translate_burmese_request(item_name)
            else:
                # For English, use the original item name
                translated_queries = [item_name]
            
            # Try each translated query to find the best match
            best_match = None
            best_score = 0
            
            for query in translated_queries:
                embedding = self.embeddings.embed_query(query)
                
                # Query Pinecone
                results = self.pinecone_index.query(
                    vector=embedding,
                    namespace=PINECONE_NAMESPACES["menu"],
                    top_k=15,
                    include_metadata=True
                )
                
                # Find the best match for this query
                for match in results.matches:
                    metadata = match.metadata
                    score = match.score
                    
                    if score > best_score:
                        best_match = metadata
                        best_score = score
            
            if best_match and best_score > 0.5 and best_match.get("image_url"):
                # Additional verification for noodle types
                if "vermicelli" in item_name.lower() or "ကြာဇံ" in item_name:
                    # For vermicelli requests, prefer items with "vermicelli" in the name
                    if "vermicelli" not in best_match.get("english_name", "").lower():
                        # Try to find a better vermicelli match
                        for query in translated_queries:
                            if "vermicelli" in query.lower():
                                vermicelli_embedding = self.embeddings.embed_query(query)
                                vermicelli_results = self.pinecone_index.query(
                                    vector=vermicelli_embedding,
                                    namespace=PINECONE_NAMESPACES["menu"],
                                    top_k=10,
                                    include_metadata=True
                                )
                                for match in vermicelli_results.matches:
                                    if (match.score > best_score and 
                                        "vermicelli" in match.metadata.get("english_name", "").lower() and
                                        match.metadata.get("image_url")):
                                        best_match = match.metadata
                                        best_score = match.score
                                        break
                
                image_info = {
                    "item_name": best_match.get("english_name", best_match.get("name")),
                    "image_url": best_match.get("image_url"),
                    "category": best_match.get("category"),
                    "price": f"{best_match.get('price', 0)} {best_match.get('currency', 'MMK')}"
                }
                
                logger.info("item_image_retrieved", 
                           item_name=item_name,
                           found_item=image_info["item_name"],
                           image_url=best_match.get("image_url"),
                           similarity_score=best_score,
                           translated_queries=translated_queries)
                
                return image_info
            
            logger.warning("item_image_not_found", 
                          item_name=item_name, 
                          best_score=best_score,
                          translated_queries=translated_queries)
            return None
            
        except Exception as e:
            logger.error("item_image_retrieval_failed", 
                        item_name=item_name, 
                        error=str(e))
            return None

    async def search_pinecone_for_data(self, user_message: str, language: str = "en") -> Dict[str, Any]:
        """
        Search Pinecone for relevant FAQ, menu, and events data with improved Burmese handling
        """
        try:
            faq_results = []
            menu_results = []
            events_results = []
            
            # For Burmese queries, use semantic context extraction
            if language in ["my", "myanmar", "mm"]:
                from src.services.semantic_context_extractor import get_semantic_context_extractor
                semantic_extractor = get_semantic_context_extractor()
                
                # Extract English semantic context from Burmese query
                semantic_context = await semantic_extractor.extract_semantic_context(user_message)
                english_context = semantic_context.get("english_context", user_message)
                query_type = semantic_context.get("query_type", "general")
                
                logger.info("using_semantic_context", 
                           burmese_query=user_message[:50],
                           english_context=english_context,
                           query_type=query_type)
                
                # Strategy 1: Search with English semantic context
                faq_query_results = self.pinecone_index.query(
                    vector=self.embeddings.embed_query(english_context),
                    namespace="faq",
                    top_k=10,
                    include_metadata=True
                )
                if faq_query_results.matches:
                    faq_results.extend([match.metadata for match in faq_query_results.matches if match.score > 0.4])
                
                # Strategy 2: Search menu with English semantic context
                menu_query_results = self.pinecone_index.query(
                    vector=self.embeddings.embed_query(english_context),
                    namespace="menu",
                    top_k=15,
                    include_metadata=True
                )
                if menu_query_results.matches:
                    menu_results.extend([match.metadata for match in menu_query_results.matches if match.score > 0.4])
                
                # Strategy 3: Search events namespace
                events_query_results = self.pinecone_index.query(
                    vector=self.embeddings.embed_query(english_context),
                    namespace="events",
                    top_k=8,
                    include_metadata=True
                )
                if events_query_results.matches:
                    events_results.extend([match.metadata for match in events_query_results.matches if match.score > 0.4])
                
                # Strategy 4: Additional search with original Burmese query as fallback
                faq_fallback_results = self.pinecone_index.query(
                    vector=self.embeddings.embed_query(user_message),
                    namespace="faq",
                    top_k=5,
                    include_metadata=True
                )
                if faq_fallback_results.matches:
                    fallback_faqs = [match.metadata for match in faq_fallback_results.matches if match.score > 0.5]
                    # Add unique results
                    for faq in fallback_faqs:
                        if not any(existing.get('id') == faq.get('id') for existing in faq_results):
                            faq_results.append(faq)
                
                # Strategy 5: Direct keyword search for specific Burmese queries
                # Photo-related queries
                if any(word in user_message.lower() for word in ["ဓါတ်ပုံ", "photo", "ရိုက်ကူး", "shooting", "ကင်မရာ", "camera"]):
                    photo_queries = [
                        "photo camera professional mobile phone",
                        "ဓါတ်ပုံ ရိုက်ကူး ကင်မရာ professional",
                        "photography policy camera phone"
                    ]
                    for photo_query in photo_queries:
                        photo_results = self.pinecone_index.query(
                            vector=self.embeddings.embed_query(photo_query),
                            namespace="faq",
                            top_k=3,
                            include_metadata=True
                        )
                        if photo_results.matches:
                            for match in photo_results.matches:
                                if match.score > 0.4 and not any(existing.get('id') == match.metadata.get('id') for existing in faq_results):
                                    faq_results.append(match.metadata)
                
                # Opening hours queries
                if any(word in user_message.lower() for word in ["ဖွင့်ချိန်", "opening", "ပိတ်ချိန်", "closing", "အချိန်", "time", "ဘယ်အချိန်"]):
                    time_queries = [
                        "opening hours time schedule cafe restaurant",
                        "ဖွင့်ချိန် ပိတ်ချိန် အချိန် ဆိုင်",
                        "cafe hours opening closing time"
                    ]
                    for time_query in time_queries:
                        time_results = self.pinecone_index.query(
                            vector=self.embeddings.embed_query(time_query),
                            namespace="faq",
                            top_k=3,
                            include_metadata=True
                        )
                        if time_results.matches:
                            for match in time_results.matches:
                                if match.score > 0.4 and not any(existing.get('id') == match.metadata.get('id') for existing in faq_results):
                                    faq_results.append(match.metadata)
                
                # Band/music queries
                if any(word in user_message.lower() for word in ["တီးဝိုင်း", "band", "ဂီတ", "music", "သီချင်း", "song", "ဖျော်ဖြေ", "entertainment"]):
                    music_queries = [
                        "live music band entertainment",
                        "တီးဝိုင်း ဂီတ ဖျော်ဖြေ",
                        "music band live entertainment"
                    ]
                    for music_query in music_queries:
                        music_results = self.pinecone_index.query(
                            vector=self.embeddings.embed_query(music_query),
                            namespace="faq",
                            top_k=3,
                            include_metadata=True
                        )
                        if music_results.matches:
                            for match in music_results.matches:
                                if match.score > 0.4 and not any(existing.get('id') == match.metadata.get('id') for existing in faq_results):
                                    faq_results.append(match.metadata)
                
            else:
                # For English queries, use original strategy
                try:
                    # Strategy 1: Direct query
                    faq_query_results = self.pinecone_index.query(
                        vector=self.embeddings.embed_query(user_message),
                        namespace="faq",
                        top_k=8,
                        include_metadata=True
                    )
                    if faq_query_results.matches:
                        faq_results.extend([match.metadata for match in faq_query_results.matches if match.score > 0.6])
                    
                    # Strategy 2: Extract key Burmese words and search (for Burmese queries)
                    if language in ["my", "myanmar", "mm"]:
                        burmese_keywords = self._extract_burmese_keywords(user_message)
                        if burmese_keywords:
                            keyword_query = " ".join(burmese_keywords[:3])  # Use top 3 keywords
                            keyword_results = self.pinecone_index.query(
                                vector=self.embeddings.embed_query(keyword_query),
                                namespace="faq",
                                top_k=5,
                                include_metadata=True
                            )
                            if keyword_results.matches:
                                keyword_faqs = [match.metadata for match in keyword_results.matches if match.score > 0.5]
                                # Add unique results
                                for faq in keyword_faqs:
                                    if not any(existing.get('id') == faq.get('id') for existing in faq_results):
                                        faq_results.append(faq)
                    
                    # Strategy 3: Direct category search for location queries
                    if any(word in user_message.lower() for word in ["ဘယ်မှာ", "လိပ်စာ", "တည်နေရာ", "where", "location", "address"]):
                        # Try multiple location-related queries to ensure we find the location FAQ
                        location_queries = [
                            "location address where cafe restaurant",
                            "ဆိုင်တည်နေရာ လိပ်စာ ဘယ်မှာ",
                            "cafe location address yangon",
                            "restaurant address location"
                        ]
                        
                        for location_query in location_queries:
                            location_results = self.pinecone_index.query(
                                vector=self.embeddings.embed_query(location_query),
                                namespace="faq",
                                top_k=5,
                                include_metadata=True
                            )
                            if location_results.matches:
                                location_faqs = [match.metadata for match in location_results.matches if match.score > 0.3]
                                # Add unique results, prioritizing location category
                                for faq in location_faqs:
                                    if not any(existing.get('id') == faq.get('id') for existing in faq_results):
                                        faq_results.append(faq)
                                        # If we found a location FAQ, break early
                                        if faq.get('category') == 'location':
                                            break
                    
                    # Strategy 4: Direct search for photo-related queries
                    if any(word in user_message.lower() for word in ["ဓါတ်ပုံ", "photo", "ရိုက်ကူး", "shooting", "ကင်မရာ", "camera", "professional"]):
                        # Try multiple photo-related queries to ensure we find the photo policy FAQ
                        photo_queries = [
                            "photo camera professional mobile phone",
                            "ဓါတ်ပုံ ရိုက်ကူး ကင်မရာ professional",
                            "photography policy camera phone",
                            "photo taking allowed camera"
                        ]
                        
                        for photo_query in photo_queries:
                            photo_results = self.pinecone_index.query(
                                vector=self.embeddings.embed_query(photo_query),
                                namespace="faq",
                                top_k=5,
                                include_metadata=True
                            )
                            if photo_results.matches:
                                photo_faqs = [match.metadata for match in photo_results.matches if match.score > 0.3]
                                # Add unique results, prioritizing photo/policy category
                                for faq in photo_faqs:
                                    if not any(existing.get('id') == faq.get('id') for existing in faq_results):
                                        faq_results.append(faq)
                                        # If we found a photo policy FAQ, break early
                                        if faq.get('category') == 'policies' and 'photo' in str(faq).lower():
                                            break
                    
                    # Strategy 5: Direct search for opening hours queries
                    if any(word in user_message.lower() for word in ["ဖွင့်ချိန်", "opening", "ပိတ်ချိန်", "closing", "အချိန်", "time", "schedule", "ဘယ်အချိန်"]):
                        # Try multiple time-related queries to ensure we find the hours FAQ
                        time_queries = [
                            "opening hours time schedule cafe restaurant",
                            "ဖွင့်ချိန် ပိတ်ချိန် အချိန် ဆိုင်",
                            "cafe hours opening closing time"
                        ]
                        
                        for time_query in time_queries:
                            time_results = self.pinecone_index.query(
                                vector=self.embeddings.embed_query(time_query),
                                namespace="faq",
                                top_k=5,
                                include_metadata=True
                            )
                            if time_results.matches:
                                time_faqs = [match.metadata for match in time_results.matches if match.score > 0.3]
                                # Add unique results, prioritizing hours category
                                for faq in time_faqs:
                                    if not any(existing.get('id') == faq.get('id') for existing in faq_results):
                                        faq_results.append(faq)
                                        # If we found a hours FAQ, break early
                                        if faq.get('category') == 'hours':
                                            break
                    
                    # Strategy 6: Direct search for band/music queries
                    if any(word in user_message.lower() for word in ["တီးဝိုင်း", "band", "ဂီတ", "music", "သီချင်း", "song", "ဖျော်ဖြေ", "entertainment"]):
                        # Try multiple music-related queries to ensure we find the entertainment FAQ
                        music_queries = [
                            "live music band entertainment",
                            "တီးဝိုင်း ဂီတ ဖျော်ဖြေ",
                            "music band live entertainment"
                        ]
                        
                        for music_query in music_queries:
                            music_results = self.pinecone_index.query(
                                vector=self.embeddings.embed_query(music_query),
                                namespace="faq",
                                top_k=5,
                                include_metadata=True
                            )
                            if music_results.matches:
                                music_faqs = [match.metadata for match in music_results.matches if match.score > 0.3]
                                # Add unique results, prioritizing entertainment category
                                for faq in music_faqs:
                                    if not any(existing.get('id') == faq.get('id') for existing in faq_results):
                                        faq_results.append(faq)
                                        # If we found an entertainment FAQ, break early
                                        if faq.get('category') == 'entertainment':
                                            break
                
                except Exception as e:
                    logger.error(f"FAQ search error: {str(e)}")
                
                # Search menu namespace with improved strategies
                try:
                    # Strategy 1: Direct query
                    menu_query_results = self.pinecone_index.query(
                        vector=self.embeddings.embed_query(user_message),
                        namespace="menu",
                        top_k=12,
                        include_metadata=True
                    )
                    if menu_query_results.matches:
                        menu_results.extend([match.metadata for match in menu_query_results.matches if match.score > 0.5])
                    
                    # Strategy 2: Category-based search for menu items
                    if self._is_specific_category_question(user_message):
                        category_keywords = self._extract_category_keywords(user_message)
                        if category_keywords:
                            category_query = " ".join(category_keywords)
                            category_results = self.pinecone_index.query(
                                vector=self.embeddings.embed_query(category_query),
                                namespace="menu",
                                top_k=10,
                                include_metadata=True
                            )
                            if category_results.matches:
                                category_items = [match.metadata for match in category_results.matches if match.score > 0.4]
                                # Add unique results
                                for item in category_items:
                                    if not any(existing.get('id') == item.get('id') for existing in menu_results):
                                        menu_results.append(item)
                    
                except Exception as e:
                    logger.error(f"Menu search error: {str(e)}")
            
            # Remove duplicates and limit results
            faq_results = self._remove_duplicates(faq_results)
            menu_results = self._remove_duplicates(menu_results)
            events_results = self._remove_duplicates(events_results)
            
            # For location queries, prioritize location FAQs
            if any(word in user_message.lower() for word in ["ဘယ်မှာ", "လိပ်စာ", "တည်နေရာ", "where", "location", "address"]):
                location_faqs = [faq for faq in faq_results if faq.get('category') == 'location']
                other_faqs = [faq for faq in faq_results if faq.get('category') != 'location']
                # Put location FAQs first, then others
                faq_results = location_faqs + other_faqs
            
            faq_results = faq_results[:5]
            menu_results = menu_results[:8]
            events_results = events_results[:5]
            
            return {
                "faq_results": faq_results,
                "menu_results": menu_results,
                "events_results": events_results,
                "found_faq": len(faq_results) > 0,
                "found_menu": len(menu_results) > 0,
                "found_events": len(events_results) > 0
            }
            
        except Exception as e:
            logger.error(f"Pinecone search error: {str(e)}")
            return {
                "faq_results": [],
                "menu_results": [],
                "found_faq": False,
                "found_menu": False
            }
    
    async def determine_data_source(self, user_message: str, query_type: str = None) -> Dict[str, Any]:
        """
        Determine the appropriate data source to query based on the user message and query type
        
        Returns:
            Dict containing:
            - primary_source: The main data source to query (faq, menu, events)
            - secondary_sources: Additional sources to check
            - confidence: Confidence in the source determination
            - reasoning: Explanation of the decision
        """
        try:
            # If query_type is provided, use it for routing
            if query_type:
                if query_type in ["location", "hours", "contact", "policies", "facilities", "delivery", "reservations"]:
                    return {
                        "primary_source": "faq",
                        "secondary_sources": [],
                        "confidence": 0.9,
                        "reasoning": f"Query type '{query_type}' is typically handled by FAQ data"
                    }
                elif query_type in ["menu", "food", "items", "categories"]:
                    return {
                        "primary_source": "menu",
                        "secondary_sources": ["faq"],
                        "confidence": 0.9,
                        "reasoning": f"Query type '{query_type}' is typically handled by menu data"
                    }
                elif query_type in ["entertainment", "events", "band", "music", "rental"]:
                    return {
                        "primary_source": "events",
                        "secondary_sources": ["faq"],
                        "confidence": 0.8,
                        "reasoning": f"Query type '{query_type}' is typically handled by events data"
                    }
            
            # Fallback: Analyze the message content
            message_lower = user_message.lower()
            
            # FAQ-related keywords
            faq_keywords = [
                "ဘယ်မှာ", "လိပ်စာ", "တည်နေရာ", "where", "location", "address",
                "ဖွင့်ချိန်", "ဘယ်အချိန်", "opening", "hours", "time",
                "ဖုန်း", "ဆက်သွယ်", "phone", "contact",
                "ဓါတ်ပုံ", "photo", "ကြောင်လေး", "pet", "ခွေး", "dog",
                "မီးပျက်", "generator", "wifi", "အင်တာနက်", "internet",
                "ဆေးလိပ်", "smoking", "အပြင်ထိုင်ခုံ", "outdoor",
                "အစားအစာ", "outside food", "ပို့ပေးမှု", "delivery",
                "ကြိုတင်မှာယူ", "reservation", "ငွေပေးချေမှု", "payment"
            ]
            
            # Menu-related keywords
            menu_keywords = [
                "အစားအစာ", "မီနူး", "food", "menu", "items", "dishes",
                "ခေါက်ဆွဲ", "noodles", "ပါစတာ", "pasta", "ဘာဂါ", "burger",
                "ကြက်ဉလိပ်", "omelette", "ဟင်းချို", "soup", "ဆလပ်", "salad",
                "သောက်စရာ", "drink", "အချိုပွဲ", "dessert", "မနက်စာ", "breakfast",
                "ဈေးနှုန်း", "price", "ပါဝင်ပစ္စည်း", "ingredient", "အရသာ", "taste"
            ]
            
            # Events-related keywords
            events_keywords = [
                "တီးဝိုင်း", "band", "ဂီတ", "music", "သီချင်း", "song",
                "ဖျော်ဖြေ", "entertainment", "အစီအစဉ်", "program", "ပွဲ", "event",
                "ရိုက်ကူးရေး", "shooting", "ဓါတ်ပုံ", "photo", "ကင်မရာ", "camera",
                "ငှားလို့", "rental", "ဝန်ဆောင်မှု", "service"
            ]
            
            # Count matches for each category
            faq_matches = sum(1 for keyword in faq_keywords if keyword in message_lower)
            menu_matches = sum(1 for keyword in menu_keywords if keyword in message_lower)
            events_matches = sum(1 for keyword in events_keywords if keyword in message_lower)
            
            # Determine primary source based on highest match count
            if faq_matches > menu_matches and faq_matches > events_matches:
                return {
                    "primary_source": "faq",
                    "secondary_sources": ["menu"] if menu_matches > 0 else [],
                    "confidence": min(0.9, 0.5 + (faq_matches * 0.1)),
                    "reasoning": f"FAQ-related keywords detected ({faq_matches} matches)"
                }
            elif menu_matches > faq_matches and menu_matches > events_matches:
                return {
                    "primary_source": "menu",
                    "secondary_sources": ["faq"] if faq_matches > 0 else [],
                    "confidence": min(0.9, 0.5 + (menu_matches * 0.1)),
                    "reasoning": f"Menu-related keywords detected ({menu_matches} matches)"
                }
            elif events_matches > 0:
                return {
                    "primary_source": "events",
                    "secondary_sources": ["faq"],
                    "confidence": min(0.8, 0.4 + (events_matches * 0.1)),
                    "reasoning": f"Events-related keywords detected ({events_matches} matches)"
                }
            else:
                # Default to FAQ for general queries
                return {
                    "primary_source": "faq",
                    "secondary_sources": ["menu"],
                    "confidence": 0.5,
                    "reasoning": "No specific keywords detected, defaulting to FAQ"
                }
                
        except Exception as e:
            logger.error(f"Data source determination error: {str(e)}")
            return {
                "primary_source": "faq",
                "secondary_sources": ["menu"],
                "confidence": 0.3,
                "reasoning": f"Error in determination: {str(e)}"
            }

    def _extract_burmese_keywords(self, user_message: str) -> List[str]:
        """
        Extract key Burmese words for better semantic search
        """
        # Common Burmese keywords for restaurant queries
        burmese_keywords = [
            "ဓါတ်ပုံ", "photo", "ဖွင့်ချိန်", "opening", "ဈေးနှုန်း", "price", "လိပ်စာ", "address",
            "ဘယ်မှာ", "where", "တည်နေရာ", "location", "ဘာဂါ", "burger", "ခေါက်ဆွဲ", "noodle", 
            "ပါစတာ", "pasta", "ကြက်ဥလိပ်", "omelette", "အစားအစာ", "food", "မီနူး", "menu", 
            "ဟင်းချို", "soup", "ဆလပ်", "salad", "သောက်စရာ", "drink", "အချိုပွဲ", "dessert", 
            "မနက်စာ", "breakfast", "ပါဝင်ပစ္စည်း", "ingredient", "အရသာ", "taste", 
            "ပြင်ဆင်ချိန်", "preparation", "ကြောင်လေး", "pet", "ခွေး", "dog", "မီးပျက်", 
            "generator", "wifi", "အင်တာနက်"
        ]
        
        found_keywords = []
        user_lower = user_message.lower()
        
        for keyword in burmese_keywords:
            if keyword in user_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_category_keywords(self, user_message: str) -> List[str]:
        """
        Extract category-specific keywords for menu search
        """
        category_mappings = {
            "ဘာဂါ": ["burger", "hamburger", "ဘာဂါ"],
            "ခေါက်ဆွဲ": ["noodle", "noodles", "ခေါက်ဆွဲ", "pasta"],
            "ပါစတာ": ["pasta", "spaghetti", "ပါစတာ"],
            "ကြက်ဥလိပ်": ["omelette", "egg", "ကြက်ဥ", "လိပ်"],
            "ဟင်းချို": ["soup", "ဟင်းချို"],
            "ဆလပ်": ["salad", "ဆလပ်"],
            "သောက်စရာ": ["drink", "beverage", "သောက်စရာ"],
            "အချိုပွဲ": ["dessert", "sweet", "အချိုပွဲ"],
            "မနက်စာ": ["breakfast", "မနက်စာ"]
        }
        
        user_lower = user_message.lower()
        found_categories = []
        
        for burmese_cat, english_cats in category_mappings.items():
            if burmese_cat in user_lower or any(cat in user_lower for cat in english_cats):
                found_categories.extend(english_cats)
        
        return found_categories
    
    def _remove_duplicates(self, items: List[Dict]) -> List[Dict]:
        """
        Remove duplicate items based on ID
        """
        seen_ids = set()
        unique_items = []
        
        for item in items:
            item_id = item.get('id') or item.get('question_en') or item.get('english_name')
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_items.append(item)
        
        return unique_items
    
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

    def _create_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Create context string from conversation history"""
        if not conversation_history:
            return "No previous conversation."
        
        # Get last 7 messages for context
        recent_messages = conversation_history[-7:]
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
                "appetizers_sides": "အရံဟင်း",
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