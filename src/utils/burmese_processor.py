"""
Burmese Language Processing Utilities for Cafe Pentagon Chatbot
Enhanced Burmese language understanding and processing with comprehensive coverage
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from src.utils.logger import get_logger
import json

logger = get_logger("burmese_processor")

# Enhanced Burmese character detection
BURMESE_CHARACTERS = set('ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအဣဤဥဦဧဨဩဪါာိီုူေဲဳဴဵံ့း္်ျြွှ၀၁၂၃၄၅၆၇၈၉၏ၐၑၒၓၔၕၖၗၘၙၚၛၜၝၞၟၠၡၢၣၤၥၦၧၨၩၪၫၬၭၮၯၰၱၲၳၴၵၶၷၸၹၺၻၼၽၾၿႀႁႂႃႄႅႆႇႈႉႊႋႌႍႎႏ႐႑႒႓႔႕႖႗႘႙ႚႛႜႝ႞႟ႠႡႢႣႤႥႦႧႨႩႪႫႬႭႮႯႰႱႲႳႴႵႶႷႸႹႺႻႼႽႾႿፀፁፂፃፄፅፆፇፈፉፊፋፌፍፎፏፐፑፒፓፔፕፖፗፘፙፚ፛፜፝፞፟፠፡።፣፤፥፦፧፨፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼')

# Comprehensive Burmese food vocabulary mapping
BURMESE_FOOD_VOCABULARY = {
    # Meat and protein
    "ကြက်သား": ["chicken", "chicken meat", "poultry"],
    "ငါး": ["fish", "seafood"],
    "ဝက်သား": ["pork", "pork meat"],
    "အမဲသား": ["beef", "beef meat"],
    "ကြက်ဥ": ["egg", "chicken egg"],
    "ပုဇွန်": ["shrimp", "prawn", "seafood"],
    "ကြက်ဆင်": ["turkey", "turkey meat"],
    "ဆိတ်သား": ["mutton", "goat meat"],
    
    # Noodles and pasta
    "ခေါက်ဆွဲ": ["noodles", "noodle"],
    "ခေါက်ဆွဲကြော်": ["fried noodles", "stir fried noodles", "noodle dish"],
    "ခေါက်ဆွဲဟင်း": ["noodle soup", "noodles in soup"],
    "ပါစတာ": ["pasta", "spaghetti", "noodles"],
    "ကြာဇံ": ["vermicelli", "glass noodles", "rice vermicelli"],
    "ကြာဇံကြော်": ["fried vermicelli", "stir fried vermicelli"],
    
    # Rice dishes
    "ထမင်း": ["rice", "steamed rice"],
    "ထမင်းကြော်": ["fried rice", "rice dish"],
    "ဆန်": ["rice", "uncooked rice"],
    "ထမင်းလုံး": ["rice ball", "rice cake"],
    
    # Western dishes
    "ဘာဂါ": ["burger", "hamburger", "sandwich"],
    "ပီဇာ": ["pizza", "pizza pie"],
    "ကြက်ဉလိပ်": ["omelette", "omelet", "egg omelette"],
    "ကြက်ဉလိပ်ကြော်": ["fried omelette", "omelette", "egg dish"],
    "ဆန်းဝစ်": ["sandwich", "bread sandwich"],
    
    # Soups and broths
    "ဟင်းရည်": ["soup", "broth", "soup dish"],
    "ကြက်သားဟင်းရည်": ["chicken soup", "chicken broth", "soup with chicken"],
    "ငါးဟင်းရည်": ["fish soup", "fish broth", "soup with fish"],
    "ဟင်းချို": ["soup", "clear soup"],
    
    # Cooking methods
    "ကြော်": ["fried", "crispy", "deep fried"],
    "ချက်": ["curry", "cooked", "stewed"],
    "ပြုတ်": ["boiled", "steamed"],
    "ဖုတ်": ["baked", "roasted", "grilled"],
    "ကင်း": ["grilled", "barbecued"],
    "အစိမ်း": ["raw", "fresh"],
    
    # Vegetables and fruits
    "ဟင်းသီးဟင်းရွက်": ["vegetables", "veggies", "vegetable dish"],
    "သီးနှံ": ["fruits", "fruit", "fresh fruit"],
    "ခရမ်းချဉ်သီး": ["tomato", "tomatoes"],
    "ကြက်သွန်နီ": ["onion", "onions"],
    "ကြက်သွန်ဖြူ": ["garlic", "garlic cloves"],
    "ချင်း": ["ginger", "ginger root"],
    "ငရုတ်သီး": ["chili", "hot pepper", "spice"],
    "သခွားသီး": ["cucumber", "cucumbers"],
    "ကန်စွန်းဥ": ["sweet potato", "yam"],
    "အာလူး": ["potato", "potatoes"],
    
    # Beverages
    "ကော်ဖီ": ["coffee", "hot coffee"],
    "လက်ဖက်ရည်": ["tea", "hot tea"],
    "ဖျော်ရည်": ["juice", "drink", "beverage"],
    "ရေ": ["water", "drinking water"],
    "နို့": ["milk", "dairy milk"],
    "အရက်": ["alcohol", "beer", "wine"],
    "ဘီယာ": ["beer", "alcoholic beverage"],
    
    # Common food items
    "ပေါင်မုန့်": ["bread", "toast", "sandwich bread"],
    "ချိစ်": ["cheese", "dairy"],
    "ထောပတ်": ["butter", "dairy butter"],
    "ဆီ": ["oil", "cooking oil"],
    "ဆား": ["salt", "seasoning"],
    "ငရုတ်ကောင်း": ["pepper", "black pepper"],
    "သကြား": ["sugar", "sweetener"],
    "ပျားရည်": ["honey", "natural sweetener"],
    
    # Traditional Burmese dishes
    "မုန့်ဟင်းခါး": ["mohinga", "traditional fish soup"],
    "လက်ဖက်သုပ်": ["tea leaf salad", "lahpet thoke"],
    "အုန်းနို့ခေါက်ဆွဲ": ["coconut noodle", "ohn no khao swe"],
    "ထမင်းလိပ်ပြာ": ["rice roll", "traditional rice dish"],
    "ငါးပိရည်": ["fish sauce", "traditional condiment"],
    "ငံပြာရည်": ["fish sauce", "traditional sauce"],
}

# Enhanced Burmese question patterns with comprehensive coverage
BURMESE_QUESTION_PATTERNS = {
    "greeting": [
        "မင်္ဂလာ", "ဟယ်လို", "ဟေး", "ဘယ်လိုလဲ", "ဘယ်လိုရှိလဲ", "ဘယ်လိုနေလဲ",
        "မင်္ဂလာပါ", "မင်္ဂလာပါ ခင်ဗျာ", "မင်္ဂလာပါ အစ်ကို", "မင်္ဂလာပါ အစ်မ",
        "ဟေး ဘယ်လိုလဲ", "ဟေး ဘယ်လိုနေလဲ", "ဟယ်လို ဘယ်လိုလဲ"
    ],
    "menu_browse": [
        "မီနူး", "အစားအစာ", "ဘာတွေ ရှိလဲ", "ဘာတွေ စားလို့ရလဲ", 
        "ဘယ်လို [food] တွေ ရှိလဲ", "[food] ဘာတွေ ရှိလဲ",
        "ဘာတွေ ရှိသလဲ", "ဘာတွေ စားလို့ရသလဲ", "ဘာတွေ ရှိလဲ",
        "ဘာတွေ စားလို့ရလဲ", "ဘာတွေ ရှိသလဲ", "ဘာတွေ စားလို့ရသလဲ",
        "ဘာတွေ ရှိလဲ", "ဘာတွေ စားလို့ရလဲ", "ဘာတွေ ရှိသလဲ",
        "ဘာတွေ စားလို့ရသလဲ", "ဘာတွေ ရှိလဲ", "ဘာတွေ စားလို့ရလဲ"
    ],
    "faq": [
        "ဘာ", "ဘယ်", "ဘယ်လို", "ဘာကြောင့်", "ရှိလား", "ပါသလား",
        "လိပ်စာ", "ဖုန်းနံပါတ်", "ဖွင့်ချိန်", "ဈေးနှုန်း", "ဘယ်မှာ",
        "ဘယ်အချိန်", "ဘယ်နေရာ", "ဘယ်လို", "ဘာကြောင့်", "ရှိလား",
        "ပါသလား", "လိပ်စာ", "ဖုန်းနံပါတ်", "ဖွင့်ချိန်", "ဈေးနှုန်း",
        "ဘယ်မှာ", "ဘယ်အချိန်", "ဘယ်နေရာ", "ဘယ်လို", "ဘာကြောင့်"
    ],
    "order": [
        "မှာယူ", "အမှာယူ", "ဝယ်ယူ", "အော်ဒါ", "ပြင်ဆင်ပေး", "ယူသွား", "ပို့ပေး",
        "မှာယူချင်ပါတယ်", "အမှာယူချင်ပါတယ်", "ဝယ်ယူချင်ပါတယ်",
        "အော်ဒါပေးချင်ပါတယ်", "ပြင်ဆင်ပေးချင်ပါတယ်", "ယူသွားချင်ပါတယ်",
        "ပို့ပေးချင်ပါတယ်", "မှာယူချင်တယ်", "အမှာယူချင်တယ်",
        "ဝယ်ယူချင်တယ်", "အော်ဒါပေးချင်တယ်", "ပြင်ဆင်ပေးချင်တယ်",
        "ယူသွားချင်တယ်", "ပို့ပေးချင်တယ်"
    ],
    "reservation": [
        "ကြိုတင်မှာယူ", "စားပွဲကြို", "ဘွတ်ကင်", "ကြိုတင်စီစဉ်", "စားပွဲ",
        "ကြိုတင်မှာယူချင်ပါတယ်", "စားပွဲကြိုချင်ပါတယ်", "ဘွတ်ကင်ချင်ပါတယ်",
        "ကြိုတင်စီစဉ်ချင်ပါတယ်", "စားပွဲချင်ပါတယ်", "ကြိုတင်မှာယူချင်တယ်",
        "စားပွဲကြိုချင်တယ်", "ဘွတ်ကင်ချင်တယ်", "ကြိုတင်စီစဉ်ချင်တယ်",
        "စားပွဲချင်တယ်"
    ],
    "goodbye": [
        "ကျေးဇူးတင်ပါတယ်", "ပြန်လာမယ်", "သွားပါတယ်", "နှုတ်ဆက်ပါတယ်", "ကျေးဇူး",
        "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ", "ပြန်လာမယ် ခင်ဗျာ", "သွားပါတယ် ခင်ဗျာ",
        "နှုတ်ဆက်ပါတယ် ခင်ဗျာ", "ကျေးဇူး ခင်ဗျာ", "ကျေးဇူးတင်ပါတယ် အစ်ကို",
        "ပြန်လာမယ် အစ်ကို", "သွားပါတယ် အစ်ကို", "နှုတ်ဆက်ပါတယ် အစ်ကို",
        "ကျေးဇူး အစ်ကို", "ကျေးဇူးတင်ပါတယ် အစ်မ", "ပြန်လာမယ် အစ်မ",
        "သွားပါတယ် အစ်မ", "နှုတ်ဆက်ပါတယ် အစ်မ", "ကျေးဇူး အစ်မ"
    ],
    "escalation": [
        "လူသားနဲ့ပြောချင်ပါတယ်", "အကူအညီလိုပါတယ်", "ကူညီပေးပါ",
        "လူသားနဲ့ပြောချင်တယ်", "အကူအညီလိုတယ်", "ကူညီပေးပါ",
        "ဝန်ထမ်းနဲ့ပြောချင်ပါတယ်", "မန်နေဂျာနဲ့ပြောချင်ပါတယ်",
        "သက်ဆိုင်ရာဝန်ထမ်းနဲ့ပြောချင်ပါတယ်", "ပြဿနာရှိပါတယ်",
        "အခက်အခဲရှိပါတယ်", "အဆင်မပြေတာရှိပါတယ်", "ကြုံခဲ့ရတာရှိပါတယ်",
        "ဝန်ထမ်းနဲ့ပြောချင်တယ်", "မန်နေဂျာနဲ့ပြောချင်တယ်",
        "သက်ဆိုင်ရာဝန်ထမ်းနဲ့ပြောချင်တယ်", "ပြဿနာရှိတယ်",
        "အခက်အခဲရှိတယ်", "အဆင်မပြေတာရှိတယ်", "ကြုံခဲ့ရတာရှိတယ်"
    ]
}

# Enhanced Burmese cultural context patterns
BURMESE_CULTURAL_PATTERNS = {
    "polite_greetings": [
        "မင်္ဂလာပါ အစ်ကို", "မင်္ဂလာပါ အစ်မ", "မင်္ဂလာပါ ဦးလေး", "မင်္ဂလာပါ အမေကြီး",
        "မင်္ဂလာပါ ဆရာ", "မင်္ဂလာပါ ဆရာမ", "မင်္ဂလာပါ ဦး", "မင်္ဂလာပါ ဒေါ်",
        "မင်္ဂလာပါ မ", "မင်္ဂလာပါ ကို", "မင်္ဂလာပါ မယ်"
    ],
    "polite_requests": [
        "ကျေးဇူးပြု၍", "ကျေးဇူးပြု၍ ပြောပေးပါ", "ကျေးဇူးပြု၍ ကူညီပေးပါ",
        "ကျေးဇူးပြု၍ ပြောပေးပါ ခင်ဗျာ", "ကျေးဇူးပြု၍ ကူညီပေးပါ ခင်ဗျာ",
        "ကျေးဇူးပြု၍ ပြောပေးပါ အစ်ကို", "ကျေးဇူးပြု၍ ကူညီပေးပါ အစ်ကို",
        "ကျေးဇူးပြု၍ ပြောပေးပါ အစ်မ", "ကျေးဇူးပြု၍ ကူညီပေးပါ အစ်မ"
    ],
    "polite_responses": [
        "ကျေးဇူးတင်ပါတယ်", "ကျေးဇူးပါ", "ကျေးဇူးပါ အစ်ကို/အစ်မ",
        "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ", "ကျေးဇူးပါ ခင်ဗျာ",
        "ကျေးဇူးတင်ပါတယ် အစ်ကို", "ကျေးဇူးပါ အစ်ကို",
        "ကျေးဇူးတင်ပါတယ် အစ်မ", "ကျေးဇူးပါ အစ်မ"
    ],
    "honorifics": [
        "ဦး", "ဒေါ်", "မ", "ကို", "မယ်", "အစ်ကို", "အစ်မ", "ဦးလေး", "အမေကြီး",
        "ဆရာ", "ဆရာမ", "ဦးကြီး", "ဒေါ်ကြီး", "မိကြီး", "ကိုကြီး", "မယ်ကြီး"
    ],
    "formality_indicators": [
        "ပါ", "ပါတယ်", "ပါသလား", "ပါသလို", "ပါသလို့", "ပါသလို", "ပါသလို့",
        "ခင်ဗျာ", "အစ်ကို", "အစ်မ", "ဦးလေး", "အမေကြီး", "ဆရာ", "ဆရာမ"
    ]
}

def detect_burmese_language(text: str) -> Dict[str, Any]:
    """
    Enhanced Burmese language detection with comprehensive coverage
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with language detection results
    """
    if not text or not text.strip():
        return {
            "is_burmese": False,
            "confidence": 0.0,
            "burmese_character_count": 0,
            "total_character_count": 0,
            "burmese_ratio": 0.0,
            "detected_language": "unknown"
        }
    
    # Count Burmese characters
    burmese_chars = sum(1 for char in text if char in BURMESE_CHARACTERS)
    total_chars = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    
    # Calculate ratio
    burmese_ratio = burmese_chars / total_chars if total_chars > 0 else 0.0
    
    # Enhanced detection logic
    is_burmese = False
    confidence = 0.0
    detected_language = "unknown"
    
    # Strong indicators
    if burmese_ratio >= 0.3:  # At least 30% Burmese characters
        is_burmese = True
        confidence = min(1.0, burmese_ratio + 0.3)
        detected_language = "my"
    
    # Check for specific Burmese patterns
    burmese_patterns = [
        r'[ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအ]',  # Burmese consonants
        r'[ါာိီုူေဲဳဴဵံ့း္်ျြွှ]',  # Burmese vowels and diacritics
        r'[၀၁၂၃၄၅၆၇၈၉၏]',  # Burmese digits
        r'[ပါတယ်|ပါသလား|ခင်ဗျာ|အစ်ကို|အစ်မ]'  # Common Burmese phrases
    ]
    
    # Simple Burmese character detection only
    if burmese_chars > 0:
        is_burmese = True
        confidence = max(confidence, 0.6)
        detected_language = "my"
    
    # Check for mixed language (Burmese + English)
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    if english_words > 0 and burmese_chars > 0:
        # Mixed language detected
        is_burmese = True
        confidence = max(confidence, 0.7)
        detected_language = "mixed"
    
    # Fallback for edge cases
    if not is_burmese and burmese_chars > 0:
        is_burmese = True
        confidence = 0.5
        detected_language = "my"
    
    return {
        "is_burmese": is_burmese,
        "confidence": confidence,
        "burmese_character_count": burmese_chars,
        "total_character_count": total_chars,
        "burmese_ratio": burmese_ratio,
        "detected_language": detected_language,
        "pattern_matches": 0,
        "english_words": english_words
    }

def extract_burmese_food_terms(text: str) -> List[str]:
    """
    Extract Burmese food terms from text with enhanced coverage
    
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
    
    # No partial matching - only exact matches
    
    return list(set(found_terms))  # Remove duplicates

def detect_burmese_intent_patterns(text: str) -> Dict[str, float]:
    """
    Enhanced intent pattern detection in Burmese text
    
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
    
    # No pattern matching - let LLM handle intent classification
    return intent_scores

def translate_burmese_food_request(text: str) -> List[str]:
    """
    Enhanced translation of Burmese food request to English terms
    
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
    
    # Enhanced variations based on context
    for term in food_terms:
        if "chicken" in term:
            translations.extend(["chicken", "poultry", "chicken dish", "chicken meal"])
        elif "fish" in term:
            translations.extend(["fish", "seafood", "fish dish", "fish meal"])
        elif "noodle" in term:
            translations.extend(["noodles", "noodle dish", "pasta", "noodle meal"])
        elif "rice" in term:
            translations.extend(["rice", "rice dish", "steamed rice", "rice meal"])
        elif "soup" in term:
            translations.extend(["soup", "broth", "soup dish", "soup meal"])
        elif "vermicelli" in term:
            translations.extend(["vermicelli", "glass noodles", "rice vermicelli", "vermicelli dish"])
        elif "pork" in term:
            translations.extend(["pork", "pork meat", "pork dish", "pork meal"])
        elif "shrimp" in term or "prawn" in term:
            translations.extend(["shrimp", "prawn", "seafood", "shrimp dish", "prawn dish"])
    
    # Add the original text as fallback
    translations.append(text)
    
    return list(set(translations))  # Remove duplicates

def enhance_burmese_response(response: str, context: Dict[str, Any] = None) -> str:
    """
    Enhanced Burmese response with cultural context and politeness
    
    Args:
        response: Original response text
        context: Additional context for enhancement
        
    Returns:
        Enhanced response text
    """
    # Add polite ending if not present
    if not response.endswith("ပါ။"):
        if response.endswith("။"):
            response = response[:-1] + "ပါ။"
        else:
            response += "ပါ။"
    
    # Add cultural context if needed
    if context and context.get("is_greeting"):
        if "မင်္ဂလာ" not in response:
            response = "မင်္ဂလာပါ! " + response
    
    # Add honorifics based on context
    if context and context.get("uses_honorifics"):
        honorific = context.get("honorific", "ခင်ဗျာ")
        if honorific not in response:
            response = response.replace("။", f" {honorific}။")
    
    return response

def normalize_burmese_text(text: str) -> str:
    """
    Enhanced normalization of Burmese text for better processing
    
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
    
    # Normalize common Burmese variations
    text = text.replace('ပါတယ်', 'ပါတယ်')  # Standardize polite ending
    text = text.replace('ပါသလား', 'ပါသလား')  # Standardize question ending
    
    return text

def get_burmese_cultural_context(text: str) -> Dict[str, Any]:
    """
    Enhanced cultural context extraction from Burmese text
    
    Args:
        text: Burmese text to analyze
        
    Returns:
        Dictionary with cultural context information
    """
    context = {
        "is_polite": False,
        "uses_honorifics": False,
        "formality_level": "casual",
        "honorifics_detected": [],
        "cultural_nuances": [],
        "language_mix": "burmese_only"
    }
    
    text_lower = text.lower()
    
    # Simple checks without pattern matching
    if "မင်္ဂလာ" in text_lower or "ခင်ဗျာ" in text_lower:
        context["is_polite"] = True
        context["uses_honorifics"] = True
        context["formality_level"] = "formal"
    
    if "ခင်ဗျာ" in text_lower or "အစ်ကို" in text_lower or "အစ်မ" in text_lower:
        context["uses_honorifics"] = True
        context["formality_level"] = "formal"
        context["honorifics_detected"].append("honorific")
    
    if "ကျေးဇူးပြု" in text_lower or "ကျေးဇူးတင်" in text_lower:
        context["is_polite"] = True
        context["formality_level"] = "formal"
    
    # Simple formality check
    formality_count = 0
    if "ကျေးဇူးပြု" in text_lower:
        formality_count += 1
    if "ခင်ဗျာ" in text_lower:
        formality_count += 1
    if "အစ်ကို" in text_lower or "အစ်မ" in text_lower:
        formality_count += 1
    
    if formality_count >= 3:
        context["formality_level"] = "very_formal"
    elif formality_count >= 1:
        context["formality_level"] = "formal"
    
    # Check for language mixing
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    if english_words > 0:
        context["language_mix"] = "mixed"
    
    # Add cultural nuances
    if context["is_polite"]:
        context["cultural_nuances"].append("ရိုသေလေးစား")
    if context["uses_honorifics"]:
        context["cultural_nuances"].append("သီလရှိ")
    if "ကျေးဇူး" in text_lower:
        context["cultural_nuances"].append("ကျေးဇူးတင်")
    
    return context

def create_burmese_aware_prompt(user_message: str, intent: str) -> str:
    """
    Enhanced Burmese-aware prompt for AI processing
    
    Args:
        user_message: User's message in Burmese
        intent: Detected intent
        
    Returns:
        Enhanced prompt for AI processing
    """
    cultural_context = get_burmese_cultural_context(user_message)
    language_detection = detect_burmese_language(user_message)
    
    prompt = f"""
You are a helpful restaurant chatbot assistant. The user is speaking in Burmese.

USER MESSAGE: {user_message}
DETECTED INTENT: {intent}
LANGUAGE DETECTION: {language_detection}
CULTURAL CONTEXT: {cultural_context}

IMPORTANT INSTRUCTIONS FOR BURMESE LANGUAGE:
1. Respond ONLY in Burmese (မြန်မာဘာသာ) unless specifically asked otherwise
2. Use appropriate politeness level based on cultural context: {cultural_context['formality_level']}
3. If user uses honorifics {cultural_context['honorifics_detected']}, respond with appropriate respect
4. Use natural Burmese expressions and tone
5. Be warm and friendly, like talking to a friend or family member
6. Use proper Burmese grammar and sentence structure
7. Include polite particles (ပါ, ပါတယ်, ပါသလား) appropriately
8. Consider cultural nuances: {cultural_context['cultural_nuances']}
9. Handle language mixing appropriately: {cultural_context['language_mix']}

BURMESE FOOD VOCABULARY REFERENCE:
{json.dumps(BURMESE_FOOD_VOCABULARY, indent=2, ensure_ascii=False)}

Please provide a natural, helpful response in Burmese that respects the cultural context.
"""
    
    return prompt

def analyze_burmese_complexity(text: str) -> Dict[str, Any]:
    """
    Analyze the complexity of Burmese text for better processing
    
    Args:
        text: Burmese text to analyze
        
    Returns:
        Dictionary with complexity analysis
    """
    if not text:
        return {
            "complexity_level": "simple",
            "word_count": 0,
            "sentence_count": 0,
            "has_questions": False,
            "has_negatives": False,
            "has_conditionals": False,
            "has_emotions": False
        }
    
    # Basic metrics
    words = text.split()
    sentences = text.split('။')
    
    # Complexity indicators
    question_indicators = ["လား", "လဲ", "လို", "လို့", "သလဲ", "သလို", "သလို့"]
    negative_indicators = ["မဟုတ်", "မဖြစ်", "မရ", "မလို", "မလုံလောက်", "မကောင်း"]
    conditional_indicators = ["ဆိုရင်", "ဆိုလျှင်", "ဆိုပါက", "ဆိုလျှင်", "ဆိုပါက"]
    emotional_indicators = ["စိတ်မကောင်း", "ဝမ်းနည်း", "ဒေါသထွက်", "စိတ်ဆိုး", "အံ့အားသင့်", "အံ့ဩ", "ရှက်လို့", "အားငယ်"]
    
    # No pattern matching - use simple metrics only
    has_questions = "?" in text or "လား" in text or "လဲ" in text
    has_negatives = "မဟုတ်" in text or "မဖြစ်" in text
    has_conditionals = "ဆိုရင်" in text or "ဆိုလျှင်" in text
    has_emotions = "စိတ်မကောင်း" in text or "ဝမ်းနည်း" in text
    
    # Determine complexity level
    complexity_score = 0
    if len(words) > 10:
        complexity_score += 1
    if len(sentences) > 2:
        complexity_score += 1
    if has_questions:
        complexity_score += 1
    if has_negatives:
        complexity_score += 1
    if has_conditionals:
        complexity_score += 1
    if has_emotions:
        complexity_score += 1
    
    if complexity_score >= 4:
        complexity_level = "complex"
    elif complexity_score >= 2:
        complexity_level = "moderate"
    else:
        complexity_level = "simple"
    
    return {
        "complexity_level": complexity_level,
        "word_count": len(words),
        "sentence_count": len(sentences),
        "has_questions": has_questions,
        "has_negatives": has_negatives,
        "has_conditionals": has_conditionals,
        "has_emotions": has_emotions,
        "complexity_score": complexity_score
    } 