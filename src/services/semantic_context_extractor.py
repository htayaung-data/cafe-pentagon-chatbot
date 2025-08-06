"""
Semantic Context Extractor for Burmese Queries
Extracts English semantic context from Burmese queries for better Pinecone search
"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.config import get_settings
from src.utils.logger import get_logger
from src.utils.api_client import get_openai_client, get_fallback_manager, QuotaExceededError, APIClientError

logger = get_logger("semantic_context_extractor")


class SemanticContextExtractor:
    """
    Extracts English semantic context from Burmese queries for better vector search
    """
    
    def __init__(self):
        """Initialize the semantic context extractor"""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        
    async def extract_semantic_context(self, burmese_query: str) -> Dict[str, Any]:
        """
        Extract English semantic context from Burmese query
        
        Args:
            burmese_query: The original Burmese query
            
        Returns:
            Dict containing:
            - english_context: English semantic context for search
            - query_type: Type of query (location, menu, hours, etc.)
            - confidence: Confidence score
            - keywords: Extracted keywords
        """
        try:
            # Create prompt for semantic context extraction
            prompt = f"""
You are a semantic context extractor for a restaurant chatbot. Your task is to extract the English semantic context from a Burmese query to help with vector search.

BURMESE QUERY: "{burmese_query}"

TASK: Extract the semantic meaning and context in English that would help find relevant information in a restaurant database.

EXAMPLES:
- Burmese: "ဆိုင်က ဘယ်မှာ ရှိတာလဲ" → English: "cafe restaurant location address where"
- Burmese: "ဆိုင် ဘယ်အချိန် ဖွင့်လဲ" → English: "restaurant opening hours time schedule"
- Burmese: "ဆိုင်မှာ ဘာအစားအစာတွေ ရလဲ" → English: "restaurant menu food items available"
- Burmese: "Pasta ထဲက ဘာတွေ ရနိုင်လဲ" → English: "pasta menu items available"
- Burmese: "ခေါက်ဆွဲ ထဲက ဘာတွေ ရှိလဲ" → English: "noodles menu items available"
- Burmese: "တီးဝိုင်း ရှိလား" → English: "band music entertainment live"
- Burmese: "ရိုက်ကူးရေးအတွက် ငှားလို့ ရလား" → English: "photo video shooting rental service"
- Burmese: "ဓါတ်ပုံ ရိုက်လို့ ရလား" → English: "photo photography policy"
- Burmese: "မီးပျက်ရင် မီးစက်နှိုးပေးလား" → English: "power outage generator backup"

QUERY TYPES:
- location: address, where, map, directions
- hours: opening time, schedule, business hours
- menu: food, items, dishes, categories
- services: wifi, parking, delivery, takeout
- entertainment: band, music, events
- rental: photo, video, shooting, equipment
- facilities: generator, power, parking, wifi

RESPONSE FORMAT:
Return a JSON object with:
- "english_context": English semantic context for search (string)
- "query_type": Type of query (string)
- "confidence": Confidence score 0.0-1.0 (float)
- "keywords": List of relevant English keywords (array)

RESPONSE:"""

            # Get AI response using robust API client
            try:
                response = await self.api_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a semantic context extractor that helps convert Burmese restaurant queries to English semantic context for better search results."},
                        {"role": "user", "content": prompt}
                    ],
                    model="gpt-4o",
                    temperature=0.1,
                    max_tokens=200
                )
            except (QuotaExceededError, APIClientError) as e:
                logger.error("semantic_context_extraction_failed", error=str(e))
                return self._fallback_extraction(burmese_query)
            
            response_text = response.choices[0].message.content.strip()
            
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
                
                logger.info("semantic_context_extracted", 
                           burmese_query=burmese_query[:50],
                           english_context=result.get("english_context"),
                           query_type=result.get("query_type"),
                           confidence=result.get("confidence"))
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error("semantic_context_parse_error", error=str(e), response=response_text)
                # Fallback to basic extraction
                return self._fallback_extraction(burmese_query)
                
        except Exception as e:
            logger.error("semantic_context_extraction_failed", error=str(e))
            return self._fallback_extraction(burmese_query)
    
    def _fallback_extraction(self, burmese_query: str) -> Dict[str, Any]:
        """
        Fallback extraction when AI extraction fails
        """
        # Basic keyword mapping for common queries
        keyword_mappings = {
            "ဘယ်မှာ": "location address where",
            "လိပ်စာ": "address location",
            "တည်နေရာ": "location address",
            "ဖွင့်ချိန်": "opening hours time",
            "ဘယ်အချိန်": "time hours schedule",
            "အစားအစာ": "food menu items",
            "မီနူး": "menu food items",
            "ခေါက်ဆွဲ": "noodles pasta",
            "ပါစတာ": "pasta noodles",
            "ဘာဂါ": "burger hamburger",
            "တီးဝိုင်း": "band music entertainment",
            "ရိုက်ကူးရေး": "photo video shooting",
            "ဓါတ်ပုံ": "photo photography",
            "မီးပျက်": "power outage generator",
            "မီးစက်": "generator power backup"
        }
        
        # Find matching keywords
        english_context_parts = []
        query_type = "general"
        
        for burmese_keyword, english_context in keyword_mappings.items():
            if burmese_keyword in burmese_query:
                english_context_parts.append(english_context)
        
        # Determine query type based on keywords
        if any(word in burmese_query for word in ["ဘယ်မှာ", "လိပ်စာ", "တည်နေရာ"]):
            query_type = "location"
        elif any(word in burmese_query for word in ["ဖွင့်ချိန်", "ဘယ်အချိန်"]):
            query_type = "hours"
        elif any(word in burmese_query for word in ["အစားအစာ", "မီနူး"]):
            query_type = "menu"
        elif any(word in burmese_query for word in ["ခေါက်ဆွဲ", "ပါစတာ", "ဘာဂါ"]):
            query_type = "menu"
        elif any(word in burmese_query for word in ["တီးဝိုင်း"]):
            query_type = "entertainment"
        elif any(word in burmese_query for word in ["ရိုက်ကူးရေး", "ဓါတ်ပုံ"]):
            query_type = "rental"
        elif any(word in burmese_query for word in ["မီးပျက်", "မီးစက်"]):
            query_type = "facilities"
        
        english_context = " ".join(english_context_parts) if english_context_parts else "restaurant cafe"
        
        return {
            "english_context": english_context,
            "query_type": query_type,
            "confidence": 0.6,
            "keywords": english_context.split()
        }


def get_semantic_context_extractor() -> SemanticContextExtractor:
    """Get semantic context extractor instance"""
    return SemanticContextExtractor() 