"""
Pytest configuration and fixtures for Cafe Pentagon Chatbot tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import json
from pathlib import Path

# Test data
TEST_USER_MESSAGES = {
    "english_greeting": "Hello, how are you?",
    "english_goodbye": "Thank you, goodbye!",
    "english_menu": "What's on your menu?",
    "english_faq": "What are your opening hours?",
    "english_job": "Do you have any job openings?",
    "english_escalation": "Can I talk to a human?",
    
    # Enhanced Burmese test messages - covering common problematic patterns
    "burmese_greeting": "မင်္ဂလာပါ ခင်ဗျာ",
    "burmese_greeting_casual": "ဟလို",
    "burmese_greeting_formal": "မင်္ဂလာပါ ဦးလေး",
    "burmese_greeting_mixed": "Hello မင်္ဂလာပါ",
    
    "burmese_goodbye": "ကျေးဇူးတင်ပါတယ်",
    "burmese_goodbye_formal": "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ",
    "burmese_goodbye_casual": "ပြန်လာမယ်",
    
    "burmese_escalation": "လူသားနဲ့ပြောချင်ပါတယ်",
    "burmese_escalation_help": "အကူအညီလိုပါတယ်",
    "burmese_escalation_human": "လူသားနဲ့ပြောချင်တယ်",
    
    # Menu queries - common problematic patterns
    "burmese_menu_general": "ဘာတွေရှိလဲ",
    "burmese_menu_what": "ဘာများ",
    "burmese_menu_food": "အစားအစာ ဘာတွေရှိလဲ",
    "burmese_menu_drink": "သောက်စရာ ဘာတွေရှိလဲ",
    "burmese_menu_coffee": "ကော်ဖီ ရှိလား",
    "burmese_menu_price": "ဘယ်လောက်လဲ",
    "burmese_menu_expensive": "စျေးကြီးလား",
    "burmese_menu_cheap": "စျေးပေါလား",
    "burmese_menu_category": "အမျိုးအစား ဘာတွေရှိလဲ",
    "burmese_menu_specific": "ဘာကော်ဖီတွေရှိလဲ",
    "burmese_menu_available": "ရနိုင်လား",
    "burmese_menu_best": "အကောင်းဆုံး ဘာလဲ",
    "burmese_menu_popular": "လူကြိုက်များတာ ဘာလဲ",
    "burmese_menu_recommend": "ဘာညွှန်းလဲ",
    "burmese_menu_spicy": "ငရုတ်သီးစပ် ဘာတွေရှိလဲ",
    "burmese_menu_vegetarian": "သက်သတ်လွတ် ဘာတွေရှိလဲ",
    "burmese_menu_breakfast": "နံနက်စာ ဘာတွေရှိလဲ",
    "burmese_menu_lunch": "နေ့လည်စာ ဘာတွေရှိလဲ",
    "burmese_menu_dinner": "ညစာ ဘာတွေရှိလဲ",
    
    # FAQ queries - common customer service questions
    "burmese_faq_hours": "ဘယ်အချိန်ဖွင့်လဲ",
    "burmese_faq_open": "ဖွင့်လား",
    "burmese_faq_close": "ပိတ်လား",
    "burmese_faq_working": "အလုပ်လုပ်လား",
    "burmese_faq_wifi": "wifi ရှိလား",
    "burmese_faq_internet": "အင်တာနက် ရှိလား",
    "burmese_faq_parking": "ကားရပ်နေရာ ရှိလား",
    "burmese_faq_location": "ဘယ်နေရာလဲ",
    "burmese_faq_address": "လိပ်စာ ဘာလဲ",
    "burmese_faq_phone": "ဖုန်းနံပါတ် ဘာလဲ",
    "burmese_faq_reservation": "ကြိုတင်မှာလား",
    "burmese_faq_booking": "ဘွတ်ကင်လုပ်လို့ရလား",
    "burmese_faq_delivery": "ပို့ပေးလား",
    "burmese_faq_takeaway": "ယူသွားလို့ရလား",
    "burmese_faq_pets": "ကြောင်လေး ခေါ်လို့ရလား",
    "burmese_faq_smoking": "ဆေးလိပ်သောက်လို့ရလား",
    "burmese_faq_outdoor": "အပြင်ထိုင်ခုံ ရှိလား",
    "burmese_faq_aircon": "အဲကွန်း ရှိလား",
    "burmese_faq_payment": "ငွေပေးချေမှု ဘယ်လိုလဲ",
    "burmese_faq_card": "ကတ်လဲ လက်ခံလား",
    "burmese_faq_cash": "ငွေသား လက်ခံလား",
    
    # Job queries - employment related
    "burmese_job_general": "အလုပ်ရှိလား",
    "burmese_job_hiring": "အလုပ်ခန့်လား",
    "burmese_job_position": "ရာထူး ဘာတွေရှိလဲ",
    "burmese_job_waitress": "စားပွဲထိုး အလုပ်ရှိလား",
    "burmese_job_kitchen": "မီးဖိုချောင် အလုပ်ရှိလား",
    "burmese_job_barista": "ဘာရစ်တာ အလုပ်ရှိလား",
    "burmese_job_manager": "မန်နေဂျာ အလုပ်ရှိလား",
    "burmese_job_parttime": "အချိန်ပိုင်း အလုပ်ရှိလား",
    "burmese_job_fulltime": "အချိန်ပြည့် အလုပ်ရှိလား",
    "burmese_job_salary": "လစာ ဘယ်လောက်လဲ",
    "burmese_job_experience": "အတွေ့အကြုံ လိုလား",
    "burmese_job_apply": "လျှောက်လို့ရလား",
    "burmese_job_interview": "အင်တာဗျူး ရှိလား",
    
    # Complex queries that often cause issues
    "burmese_complex_menu_price": "ကော်ဖီတစ်ခွက် ဘယ်လောက်လဲ နဲ့ ဘာတွေပါလဲ",
    "burmese_complex_hours_location": "ဘယ်အချိန်ဖွင့်လဲ နဲ့ ဘယ်နေရာလဲ",
    "burmese_complex_job_salary": "အလုပ်ရှိလား နဲ့ လစာ ဘယ်လောက်လဲ",
    "burmese_complex_delivery_hours": "ပို့ပေးလား နဲ့ ဘယ်အချိန်ထိလဲ",
    "burmese_complex_menu_recommend": "ဘာညွှန်းလဲ နဲ့ ဘယ်လောက်လဲ",
    
    # Edge cases and problematic patterns
    "burmese_edge_empty": "",
    "burmese_edge_whitespace": "   ",
    "burmese_edge_numbers": "123456",
    "burmese_edge_english_only": "coffee",
    "burmese_edge_mixed_chars": "ကော်ဖီ coffee 123",
    "burmese_edge_very_long": "အရမ်းရှည်တဲ့ မေးခွန်းတစ်ခု ဖြစ်ပါတယ် ဒါကြောင့် စစ်ဆေးရတာ ခက်ခဲနိုင်ပါတယ်",
    "burmese_edge_special_chars": "ကော်ဖီ@#$%^&*()",
    "burmese_edge_repeated": "ကော်ဖီ ကော်ဖီ ကော်ဖီ",
    "burmese_edge_question_marks": "ကော်ဖီ?????",
    "burmese_edge_exclamation": "ကော်ဖီ!!!",
    
    # Cultural context specific queries
    "burmese_cultural_respect": "ဦးလေး မင်္ဂလာပါ",
    "burmese_cultural_polite": "ကျေးဇူးပြု၍ ကော်ဖီတစ်ခွက် ရှိပါသလား",
    "burmese_cultural_formal": "ကျေးဇူးတင်ပါတယ် ခင်ဗျာ",
    "burmese_cultural_casual": "ဟေး ဘာတွေရှိလဲ",
    
    # Ambiguous queries that need context
    "burmese_ambiguous_what": "ဘာ",
    "burmese_ambiguous_how": "ဘယ်လို",
    "burmese_ambiguous_where": "ဘယ်မှာ",
    "burmese_ambiguous_when": "ဘယ်အချိန်",
    "burmese_ambiguous_why": "ဘာကြောင့်",
    "burmese_ambiguous_which": "ဘယ်ဟာ",
    
    # Slang and informal language
    "burmese_slang_what": "ဘာလဲ",
    "burmese_slang_how": "ဘယ်လိုလဲ",
    "burmese_slang_where": "ဘယ်မှာလဲ",
    "burmese_slang_when": "ဘယ်အချိန်လဲ",
    "burmese_slang_why": "ဘာကြောင့်လဲ",
    "burmese_slang_which": "ဘယ်ဟာလဲ",
    
    # Regional variations
    "burmese_regional_coffee": "ကော်ဖီပူပူ",
    "burmese_regional_tea": "လက်ဖက်ရည်ပူပူ",
    "burmese_regional_food": "ထမင်းစားစရာ",
    "burmese_regional_drink": "သောက်စရာ",
    
    # Time-related queries
    "burmese_time_now": "အခု ဖွင့်လား",
    "burmese_time_today": "ဒီနေ့ ဖွင့်လား",
    "burmese_time_tomorrow": "မနက်ဖြန် ဖွင့်လား",
    "burmese_time_weekend": "စနေ တနင်္ဂနွေ ဖွင့်လား",
    "burmese_time_holiday": "ရုံးပိတ်ရက် ဖွင့်လား",
    
    # Quantity and amount queries
    "burmese_quantity_how_much": "ဘယ်လောက်လဲ",
    "burmese_quantity_how_many": "ဘယ်နှစ်ခုလဲ",
    "burmese_quantity_how_long": "ဘယ်လောက်ကြာလဲ",
    "burmese_quantity_how_far": "ဘယ်လောက်ဝေးလဲ",
    "burmese_quantity_how_big": "ဘယ်လောက်ကြီးလဲ",
    "burmese_quantity_how_small": "ဘယ်လောက်သေးလဲ"
}

TEST_RAG_RESULTS = {
    "menu": [
        {
            "id": "menu_1",
            "content": "Coffee - $3.50",
            "metadata": {"category": "beverages", "price": 3.50},
            "score": 0.95
        },
        {
            "id": "menu_2", 
            "content": "Burger - $8.99",
            "metadata": {"category": "main_course", "price": 8.99},
            "score": 0.87
        }
    ],
    "faq": [
        {
            "id": "faq_1",
            "content": "We are open from 7 AM to 10 PM daily",
            "metadata": {"category": "hours"},
            "score": 0.92
        }
    ],
    "jobs": [
        {
            "id": "job_1",
            "content": "We are hiring waitstaff and kitchen staff",
            "metadata": {"category": "employment"},
            "score": 0.89
        }
    ]
}

@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    with patch('openai.OpenAI') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Mock chat completion
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mocked AI response"
        mock_instance.chat.completions.create.return_value = mock_response
        
        yield mock_instance

@pytest.fixture
def mock_pinecone():
    """Mock Pinecone vector database"""
    with patch('pinecone.Pinecone') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Mock index
        mock_index = MagicMock()
        mock_instance.Index.return_value = mock_index
        
        # Mock query response
        mock_query_response = {
            "matches": [
                {
                    "id": "test_1",
                    "score": 0.95,
                    "metadata": {"content": "Test content", "category": "test"}
                }
            ]
        }
        mock_index.query.return_value = mock_query_response
        
        yield mock_index

@pytest.fixture
def mock_supabase():
    """Mock Supabase database"""
    with patch('supabase.create_client') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        
        # Mock table operations
        mock_response = MagicMock()
        mock_response.data = [{"id": "test_id", "user_id": "test_user"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        mock_client.table.return_value.update.return_value.execute.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def sample_state():
    """Sample conversation state for testing"""
    return {
        "user_message": "Hello, how are you?",
        "user_id": "test_user_123",
        "conversation_id": "test_conv_456",
        "detected_language": "en",
        "is_greeting": False,
        "is_goodbye": False,
        "is_escalation_request": False,
        "detected_intent": "",
        "intent_confidence": 0.0,
        "all_intents": [],
        "target_namespace": "",
        "intent_reasoning": "",
        "intent_entities": {},
        "rag_results": [],
        "relevance_score": 0.0,
        "rag_enabled": True,
        "human_handling": False,
        "response": "",
        "response_generated": False,
        "response_quality": "",
        "requires_human": False,
        "escalation_reason": "",
        "conversation_history": [],
        "conversation_state": "active",
        "response_time": 0,
        "platform": "test",
        "metadata": {}
    }

@pytest.fixture
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def mock_settings():
    """Mock application settings"""
    with patch('src.config.settings.get_settings') as mock:
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test_openai_key"
        mock_settings.pinecone_api_key = "test_pinecone_key"
        mock_settings.pinecone_environment = "test_env"
        mock_settings.pinecone_index_name = "test_index"
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_anon_key = "test_anon_key"
        mock_settings.supabase_service_role_key = "test_service_key"
        mock_settings.facebook_page_access_token = "test_fb_token"
        mock_settings.facebook_verify_token = "test_verify_token"
        mock.return_value = mock_settings
        yield mock_settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_logger():
    """Mock logger to avoid log output during tests"""
    with patch('src.utils.logger.get_logger') as mock:
        mock_logger = MagicMock()
        mock.return_value = mock_logger
        yield mock_logger 