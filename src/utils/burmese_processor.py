"""
Burmese Language Processing Utilities for Cafe Pentagon Chatbot
Enhanced Burmese language understanding and processing
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from src.utils.logger import get_logger
import json

logger = get_logger("burmese_processor")

# Burmese food vocabulary mapping
BURMESE_FOOD_VOCABULARY = {
    # Meat and protein
    "ကြက်သား": ["chicken", "chicken meat", "poultry"],
    "ငါး": ["fish", "seafood"],
    "ဝက်သား": ["pork", "pork meat"],
    "အမဲသား": ["beef", "beef meat"],
    "ကြက်ဥ": ["egg", "chicken egg"],
    
    # Noodles and pasta
    "ခေါက်ဆွဲ": ["noodles", "noodle"],
    "ခေါက်ဆွဲကြော်": ["fried noodles", "stir fried noodles", "noodle dish"],
    "ခေါက်ဆွဲဟင်း": ["noodle soup", "noodles in soup"],
    "ပါစတာ": ["pasta", "spaghetti", "noodles"],
    
    # Rice dishes
    "ထမင်း": ["rice", "steamed rice"],
    "ထမင်းကြော်": ["fried rice", "rice dish"],
    "ဆန်": ["rice", "uncooked rice"],
    
    # Western dishes
    "ဘာဂါ": ["burger", "hamburger", "sandwich"],
    "ပီဇာ": ["pizza", "pizza pie"],
    "ကြက်ဉလိပ်": ["omelette", "omelet", "egg omelette"],
    "ကြက်ဉလိပ်ကြော်": ["fried omelette", "omelette", "egg dish"],
    
    # Soups and broths
    "ဟင်းရည်": ["soup", "broth", "soup dish"],
    "ကြက်သားဟင်းရည်": ["chicken soup", "chicken broth", "soup with chicken"],
    "ငါးဟင်းရည်": ["fish soup", "fish broth", "soup with fish"],
    
    # Cooking methods
    "ကြော်": ["fried", "crispy", "deep fried"],
    "ချက်": ["curry", "cooked", "stewed"],
    "ပြုတ်": ["boiled", "steamed"],
    "ဖုတ်": ["baked", "roasted", "grilled"],
    
    # Vegetables and fruits
    "ဟင်းသီးဟင်းရွက်": ["vegetables", "veggies", "vegetable dish"],
    "သီးနှံ": ["fruits", "fruit", "fresh fruit"],
    "ခရမ်းချဉ်သီး": ["tomato", "tomatoes"],
    "ကြက်သွန်နီ": ["onion", "onions"],
    "ကြက်သွန်ဖြူ": ["garlic", "garlic cloves"],
    
    # Beverages
    "ကော်ဖီ": ["coffee", "hot coffee"],
    "လက်ဖက်ရည်": ["tea", "hot tea"],
    "ဖျော်ရည်": ["juice", "drink", "beverage"],
    "ရေ": ["water", "drinking water"],
    
    # Common food items
    "ပေါင်မုန့်": ["bread", "toast", "sandwich bread"],
    "ချိစ်": ["cheese", "dairy"],
    "နို့": ["milk", "dairy milk"],
    "ထောပတ်": ["butter", "dairy butter"],
    
    # Spices and seasonings
    "ဆား": ["salt", "seasoning"],
    "ငရုတ်ကောင်း": ["pepper", "black pepper"],
    "ငရုတ်သီး": ["chili", "hot pepper", "spice"],
}

# Burmese question patterns
BURMESE_QUESTION_PATTERNS = {
    "greeting": [
        "မင်္ဂလာ", "ဟယ်လို", "ဟေး", "ဘယ်လိုလဲ", "ဘယ်လိုရှိလဲ", "ဘယ်လိုနေလဲ"
    ],
    "menu_browse": [
        "မီနူး", "အစားအစာ", "ဘာတွေ ရှိလဲ", "ဘာတွေ စားလို့ရလဲ", 
        "ဘယ်လို [food] တွေ ရှိလဲ", "[food] ဘာတွေ ရှိလဲ"
    ],
    "faq": [
        "ဘာ", "ဘယ်", "ဘယ်လို", "ဘာကြောင့်", "ရှိလား", "ပါသလား",
        "လိပ်စာ", "ဖုန်းနံပါတ်", "ဖွင့်ချိန်", "ဈေးနှုန်း", "ဘယ်မှာ"
    ],
    "order": [
        "မှာယူ", "အမှာယူ", "ဝယ်ယူ", "အော်ဒါ", "ပြင်ဆင်ပေး", "ယူသွား", "ပို့ပေး"
    ],
    "reservation": [
        "ကြိုတင်မှာယူ", "စားပွဲကြို", "ဘွတ်ကင်", "ကြိုတင်စီစဉ်", "စားပွဲ"
    ],
    "goodbye": [
        "ကျေးဇူးတင်ပါတယ်", "ပြန်လာမယ်", "သွားပါတယ်", "နှုတ်ဆက်ပါတယ်", "ကျေးဇူး"
    ]
}

# Burmese cultural context patterns
BURMESE_CULTURAL_PATTERNS = {
    "polite_greetings": [
        "မင်္ဂလာပါ အစ်ကို", "မင်္ဂလာပါ အစ်မ", "မင်္ဂလာပါ ဦးလေး", "မင်္ဂလာပါ အမေကြီး"
    ],
    "polite_requests": [
        "ကျေးဇူးပြု၍", "ကျေးဇူးပြု၍ ပြောပေးပါ", "ကျေးဇူးပြု၍ ကူညီပေးပါ"
    ],
    "polite_responses": [
        "ကျေးဇူးတင်ပါတယ်", "ကျေးဇူးပါ", "ကျေးဇူးပါ အစ်ကို/အစ်မ"
    ]
}


def extract_burmese_food_terms(text: str) -> List[str]:
    """
    Extract Burmese food terms from text
    
    Args:
        text: Burmese text to analyze
        
    Returns:
        List of food terms found in the text
    """
    found_terms = []
    text_lower = text.lower()
    
    for burmese_term, english_terms in BURMESE_FOOD_VOCABULARY.items():
        if burmese_term in text_lower:
            found_terms.extend(english_terms)
    
    return list(set(found_terms))  # Remove duplicates


def detect_burmese_intent_patterns(text: str) -> Dict[str, float]:
    """
    Detect intent patterns in Burmese text
    
    Args:
        text: Burmese text to analyze
        
    Returns:
        Dictionary of intent types with confidence scores
    """
    text_lower = text.lower()
    intent_scores = {}
    
    for intent_type, patterns in BURMESE_QUESTION_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if pattern in text_lower:
                score += 1
        
        if score > 0:
            intent_scores[intent_type] = score / len(patterns)
    
    return intent_scores


def translate_burmese_food_request(text: str) -> List[str]:
    """
    Translate Burmese food request to English terms
    
    Args:
        text: Burmese food request text
        
    Returns:
        List of English translations
    """
    translations = []
    text_lower = text.lower()
    
    # Extract food terms
    food_terms = extract_burmese_food_terms(text)
    translations.extend(food_terms)
    
    # Add common variations
    for term in food_terms:
        if "chicken" in term:
            translations.extend(["chicken", "poultry", "chicken dish"])
        elif "fish" in term:
            translations.extend(["fish", "seafood", "fish dish"])
        elif "noodle" in term:
            translations.extend(["noodles", "noodle dish", "pasta"])
        elif "rice" in term:
            translations.extend(["rice", "rice dish", "steamed rice"])
        elif "soup" in term:
            translations.extend(["soup", "broth", "soup dish"])
    
    # Add the original text as fallback
    translations.append(text)
    
    return list(set(translations))  # Remove duplicates


def enhance_burmese_response(response: str, context: Dict[str, Any] = None) -> str:
    """
    Enhance Burmese response with cultural context and politeness
    
    Args:
        response: Original response text
        context: Additional context for enhancement
        
    Returns:
        Enhanced response text
    """
    # Add polite particles if not present
    if not any(polite in response for polite in ["ပါ", "ပါတယ်", "ပါသလား"]):
        # Add polite ending
        if response.endswith("။"):
            response = response[:-1] + "ပါ။"
        elif not response.endswith("ပါ။"):
            response += "ပါ။"
    
    # Add cultural context if needed
    if context and context.get("is_greeting"):
        if "မင်္ဂလာ" not in response:
            response = "မင်္ဂလာပါ! " + response
    
    return response


def normalize_burmese_text(text: str) -> str:
    """
    Normalize Burmese text for better processing
    
    Args:
        text: Burmese text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Normalize common variations
    text = text.replace('။', '။')  # Ensure proper sentence ending
    text = text.replace('၊', '၊')  # Ensure proper comma
    
    return text


def get_burmese_cultural_context(text: str) -> Dict[str, Any]:
    """
    Extract cultural context from Burmese text
    
    Args:
        text: Burmese text to analyze
        
    Returns:
        Dictionary with cultural context information
    """
    context = {
        "is_polite": False,
        "uses_honorifics": False,
        "formality_level": "casual"
    }
    
    text_lower = text.lower()
    
    # Check for polite patterns
    for pattern in BURMESE_CULTURAL_PATTERNS["polite_greetings"]:
        if pattern in text_lower:
            context["is_polite"] = True
            context["uses_honorifics"] = True
            context["formality_level"] = "formal"
            break
    
    # Check for honorifics
    honorifics = ["အစ်ကို", "အစ်မ", "ဦးလေး", "အမေကြီး", "ဆရာ", "ဆရာမ"]
    for honorific in honorifics:
        if honorific in text_lower:
            context["uses_honorifics"] = True
            context["formality_level"] = "formal"
            break
    
    # Check for polite requests
    for pattern in BURMESE_CULTURAL_PATTERNS["polite_requests"]:
        if pattern in text_lower:
            context["is_polite"] = True
            context["formality_level"] = "formal"
            break
    
    return context


def create_burmese_aware_prompt(user_message: str, intent: str) -> str:
    """
    Create a Burmese-aware prompt for AI processing
    
    Args:
        user_message: User's message in Burmese
        intent: Detected intent
        
    Returns:
        Enhanced prompt for AI processing
    """
    cultural_context = get_burmese_cultural_context(user_message)
    
    prompt = f"""
You are a helpful restaurant chatbot assistant. The user is speaking in Burmese.

USER MESSAGE: {user_message}
DETECTED INTENT: {intent}
CULTURAL CONTEXT: {cultural_context}

IMPORTANT INSTRUCTIONS FOR BURMESE LANGUAGE:
1. Respond ONLY in Burmese (မြန်မာဘာသာ)
2. Use appropriate politeness level based on cultural context
3. If user uses honorifics (အစ်ကို, အစ်မ, etc.), respond with appropriate respect
4. Use natural Burmese expressions and tone
5. Be warm and friendly, like talking to a friend or family member
6. Use proper Burmese grammar and sentence structure
7. Include polite particles (ပါ, ပါတယ်, ပါသလား) appropriately

BURMESE FOOD VOCABULARY REFERENCE:
{json.dumps(BURMESE_FOOD_VOCABULARY, indent=2, ensure_ascii=False)}

Please provide a natural, helpful response in Burmese.
"""
    
    return prompt 