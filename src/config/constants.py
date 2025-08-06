"""
Constants for Cafe Pentagon Chatbot
"""

# Language Constants
SUPPORTED_LANGUAGES = ["en", "my"]
DEFAULT_LANGUAGE = "en"

# Pinecone Namespaces
PINECONE_NAMESPACES = {
    "menu": "menu",
    "faq": "faq",
    "reservations": "reservations",
    "events": "events",
    "jobs": "jobs"
}

# Intent Categories
INTENT_CATEGORIES = {
    "greeting": "greeting",
    "menu_browse": "menu_browse",
    "order_place": "order_place",
    "reservation": "reservation",
    "faq": "faq",
    "complaint": "complaint",
    "events": "events",
    "jobs": "jobs",
    "goodbye": "goodbye",
    "unknown": "unknown"
}

# Conversation States
CONVERSATION_STATES = {
    "idle": "idle",
    "menu_browsing": "menu_browsing",
    "ordering": "ordering",
    "reservation_flow": "reservation_flow",
    "complaint_handling": "complaint_handling",
    "event_booking": "event_booking",
    "job_application": "job_application",
    "human_handoff": "human_handoff"
}

# Menu Categories
MENU_CATEGORIES = [
    "breakfast",
    "main_course",
    "appetizers_sides",
    "soups",
    "noodles",
    "sandwiches_burgers",
    "salads",
    "pasta",
    "rice_dishes"
]

# Dietary Information
DIETARY_TYPES = {
    "vegetarian": ["vegetarian", "veggie", "veggies"],
    "vegan": ["vegan"],
    "gluten_free": ["gluten", "gluten-free", "gluten free"],
    "contains_dairy": ["dairy", "milk", "cheese", "cream"],
    "contains_eggs": ["eggs", "egg"]
}

# Allergens
ALLERGENS = [
    "dairy",
    "eggs",
    "gluten",
    "nuts",
    "fish",
    "shellfish",
    "chicken",
    "pork",
    "beef",
    "sesame"
]

# Spice Levels
SPICE_LEVELS = {
    "mild": ["mild", "not spicy", "no spice"],
    "medium": ["medium", "moderate"],
    "hot": ["hot", "spicy", "spice"],
    "very_hot": ["very hot", "very spicy", "extra spicy"]
}

# Reservation Status
RESERVATION_STATUS = {
    "pending": "pending",
    "confirmed": "confirmed",
    "cancelled": "cancelled",
    "completed": "completed"
}

# Complaint Severity
COMPLAINT_SEVERITY = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "critical"
}

# Event Types
EVENT_TYPES = {
    "live_music": "live_music",
    "special_occasion": "special_occasion",
    "celebration": "celebration",
    "promotion": "promotion"
}

# Job Departments
JOB_DEPARTMENTS = {
    "service": "service",
    "kitchen": "kitchen",
    "beverage": "beverage",
    "management": "management"
}

# Employment Types
EMPLOYMENT_TYPES = {
    "full_time": "full_time",
    "part_time": "part_time",
    "contract": "contract",
    "internship": "internship"
}

# Response Templates
RESPONSE_TEMPLATES = {
    "greeting": {
        "en": "Hello! Welcome to Cafe Pentagon. How can I help you today?",
        "my": "မင်္ဂလာပါ! Cafe Pentagon မှ ကြိုဆိုပါတယ်။ ဘယ်လိုကူညီပေးရမလဲ?"
    },
    "goodbye": {
        "en": "Thank you for visiting Cafe Pentagon. Have a great day!",
        "my": "Cafe Pentagon ကို လာရောက်တဲ့အတွက် ကျေးဇူးတင်ပါတယ်။ နေ့လည်ကောင်းပါစေ!"
    },
    "unknown_intent": {
        "en": "I'm sorry, I didn't understand that. Could you please rephrase or ask something else?",
        "my": "ဆ sorry ပါတယ်၊ နားမလည်ပါဘူး။ ပြန်ပြောပေးနိုင်မလား သို့မဟုတ် တခြားမေးခွန်းမေးနိုင်မလား?"
    },
    "human_handoff": {
        "en": "I'm connecting you to our staff who will be happy to help you further.",
        "my": "ကျနော်တို့၏ ဝန်ထမ်းများနှင့် ချိတ်ဆက်ပေးနေပါတယ်။ သူတို့က ဆက်လက်ကူညီပေးပါလိမ့်မယ်။"
    }
}

# Error Messages
ERROR_MESSAGES = {
    "api_error": {
        "en": "I'm experiencing technical difficulties. Please try again in a moment.",
        "my": "နည်းပညာဆိုင်ရာ အခက်အခဲများ ကြုံတွေ့နေပါတယ်။ ခဏအကြာတွင် ပြန်လည်ကြိုးစားကြည့်ပါ။"
    },
    "data_error": {
        "en": "I'm having trouble accessing the information. Please try again.",
        "my": "အချက်အလက်များကို ရယူရာတွင် အခက်အခဲရှိနေပါတယ်။ ပြန်လည်ကြိုးစားကြည့်ပါ။"
    },
    "timeout": {
        "en": "The request is taking longer than expected. Please try again.",
        "my": "တောင်းဆိုမှုက မျှော်လင့်ထားတာထက် ပိုကြာနေပါတယ်။ ပြန်လည်ကြိုးစားကြည့်ပါ။"
    }
}

# Cache Keys
CACHE_KEYS = {
    "user_profile": "user_profile:{user_id}",
    "conversation": "conversation:{user_id}",
    "menu_cache": "menu_cache",
    "faq_cache": "faq_cache",
    "reservation_cache": "reservation_cache",
    "event_cache": "event_cache",
    "job_cache": "job_cache"
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    "user_profile": 86400,  # 24 hours
    "conversation": 3600,   # 1 hour
    "menu_cache": 3600,     # 1 hour
    "faq_cache": 7200,      # 2 hours
    "reservation_cache": 300,  # 5 minutes
    "event_cache": 3600,    # 1 hour
    "job_cache": 7200       # 2 hours
}

# API Rate Limits
RATE_LIMITS = {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "max_conversation_length": 50
}

# File Paths
DATA_FILES = {
    "menu": "data/Menu.json",
    "faq": "data/FAQ_QA.json",
    "reservations": "data/reservations_config.json",
    "events": "data/events_promotions.json",
    "jobs": "data/jobs_positions.json"
}

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    "max_response_time": 5.0,  # seconds
    "max_embedding_time": 2.0,  # seconds
    "max_llm_response_time": 10.0  # seconds
} 