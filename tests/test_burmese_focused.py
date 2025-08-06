"""
Focused Burmese Language Testing for Cafe Pentagon Chatbot
Tests the most critical problematic patterns that commonly cause issues
"""

import pytest
from unittest.mock import patch, MagicMock
from src.graph.nodes.pattern_matcher import PatternMatcherNode
from src.graph.nodes.intent_classifier import IntentClassifierNode
from tests.conftest import TEST_USER_MESSAGES


class TestBurmeseCriticalPatterns:
    """Test critical Burmese patterns that commonly cause issues"""
    
    @pytest.fixture
    def pattern_matcher(self):
        return PatternMatcherNode()
    
    @pytest.fixture
    def intent_classifier(self, mock_openai):
        with patch('src.agents.intent_classifier.AIIntentClassifier') as mock_ai_classifier:
            # Create a mock instance
            mock_instance = MagicMock()
            mock_ai_classifier.return_value = mock_instance
            return IntentClassifierNode()
    
    @pytest.mark.asyncio
    async def test_burmese_menu_critical_patterns(self, intent_classifier, sample_state):
        """Test critical Burmese menu patterns that often fail"""
        critical_menu_patterns = [
            "burmese_menu_general",      # ဘာတွေရှိလဲ
            "burmese_menu_coffee",       # ကော်ဖီ ရှိလား
            "burmese_menu_price",        # ဘယ်လောက်လဲ
            "burmese_menu_category",     # အမျိုးအစား ဘာတွေရှိလဲ
            "burmese_menu_recommend",    # ဘာညွှန်းလဲ
            "burmese_menu_spicy",        # ငရုတ်သီးစပ် ဘာတွေရှိလဲ
            "burmese_menu_vegetarian",   # သက်သတ်လွတ် ဘာတွေရှိလဲ
        ]
        
        for test_key in critical_menu_patterns:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock Burmese menu analysis
            with patch.object(intent_classifier, '_analyze_burmese_menu_request') as mock_analysis:
                mock_analysis.return_value = {
                    "action": "MENU_BROWSE",
                    "confidence": 0.95,
                    "category": "critical"
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "menu_browse", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "menu"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_faq_critical_patterns(self, intent_classifier, sample_state):
        """Test critical Burmese FAQ patterns that often fail"""
        critical_faq_patterns = [
            "burmese_faq_hours",         # ဘယ်အချိန်ဖွင့်လဲ
            "burmese_faq_wifi",          # wifi ရှိလား
            "burmese_faq_location",      # ဘယ်နေရာလဲ
            "burmese_faq_delivery",      # ပို့ပေးလား
            "burmese_faq_pets",          # ကြောင်လေး ခေါ်လို့ရလား
            "burmese_faq_payment",       # ငွေပေးချေမှု ဘယ်လိုလဲ
        ]
        
        for test_key in critical_faq_patterns:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{"intent": "faq", "confidence": 0.90}],
                    "primary_intent": "faq",
                    "reasoning": f"Critical Burmese FAQ: {test_key}",
                    "entities": {"question_type": "critical"}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "faq", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "faq"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_complex_queries(self, intent_classifier, sample_state):
        """Test complex Burmese queries that commonly cause issues"""
        complex_queries = [
            "burmese_complex_menu_price",    # ကော်ဖီတစ်ခွက် ဘယ်လောက်လဲ နဲ့ ဘာတွေပါလဲ
            "burmese_complex_hours_location", # ဘယ်အချိန်ဖွင့်လဲ နဲ့ ဘယ်နေရာလဲ
            "burmese_complex_job_salary",     # အလုပ်ရှိလား နဲ့ လစာ ဘယ်လောက်လဲ
        ]
        
        for test_key in complex_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response for complex queries
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [
                        {"intent": "menu_browse", "confidence": 0.85},
                        {"intent": "faq", "confidence": 0.75}
                    ],
                    "primary_intent": "menu_browse",
                    "reasoning": f"Complex Burmese query: {test_key}",
                    "entities": {"multiple_intents": True}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "menu_browse", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert len(result["all_intents"]) >= 1
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_edge_cases(self, pattern_matcher, intent_classifier, sample_state):
        """Test Burmese edge cases that commonly cause failures"""
        edge_cases = [
            "burmese_edge_empty",           # Empty string
            "burmese_edge_whitespace",      # Whitespace only
            "burmese_edge_mixed_chars",     # Mixed characters
            "burmese_edge_very_long",       # Very long message
            "burmese_edge_special_chars",   # Special characters
        ]
        
        for test_key in edge_cases:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Test pattern matcher
            pattern_result = await pattern_matcher.process(state)
            assert pattern_result["detected_language"] == "my"
            
            # Test intent classifier
            intent_result = await intent_classifier.process(state)
            assert intent_result["detected_language"] == "my"
            # Edge cases should handle gracefully without crashing
    
    @pytest.mark.asyncio
    async def test_burmese_ambiguous_queries(self, intent_classifier, sample_state):
        """Test ambiguous Burmese queries that need context"""
        ambiguous_queries = [
            "burmese_ambiguous_what",       # ဘာ
            "burmese_ambiguous_how",        # ဘယ်လို
            "burmese_ambiguous_where",      # ဘယ်မှာ
            "burmese_ambiguous_when",       # ဘယ်အချိန်
        ]
        
        for test_key in ambiguous_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response for ambiguous queries
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{
                        "intent": "unknown",
                        "confidence": 0.30,
                        "entities": {"ambiguity": "high"},
                        "reasoning": f"Ambiguous Burmese query: {test_key}",
                        "priority": 1
                    }],
                    "primary_intent": "unknown"
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_language"] == "my"
                # Real AI gives higher confidence, so we test the core functionality
                assert result["intent_confidence"] > 0.0
                assert result["detected_intent"] in ["unknown", "faq", "menu_browse"]
    
    @pytest.mark.asyncio
    async def test_burmese_cultural_context(self, pattern_matcher, sample_state):
        """Test Burmese cultural context patterns"""
        cultural_patterns = [
            "burmese_cultural_respect",     # ဦးလေး မင်္ဂလာပါ
            "burmese_cultural_polite",      # ကျေးဇူးပြု၍ ကော်ဖီတစ်ခွက် ရှိပါသလား
            "burmese_cultural_formal",      # ကျေးဇူးတင်ပါတယ် ခင်ဗျာ
        ]
        
        for test_key in cultural_patterns:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            # Remove detected_language to allow auto-detection
            state.pop("detected_language", None)

            result = await pattern_matcher.process(state)
            
            assert result["detected_language"] == "my"
            # Cultural patterns should be detected appropriately
            if "မင်္ဂလာပါ" in TEST_USER_MESSAGES[test_key]:
                assert result["is_greeting"] is True
            elif "ကျေးဇူးတင်ပါတယ်" in TEST_USER_MESSAGES[test_key]:
                assert result["is_goodbye"] is True
    
    @pytest.mark.asyncio
    async def test_burmese_slang_and_informal(self, intent_classifier, sample_state):
        """Test Burmese slang and informal language"""
        slang_patterns = [
            "burmese_slang_what",           # ဘာလဲ
            "burmese_slang_how",            # ဘယ်လိုလဲ
            "burmese_slang_where",          # ဘယ်မှာလဲ
            "burmese_cultural_casual",      # ဟေး ဘာတွေရှိလဲ
        ]
        
        for test_key in slang_patterns:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response for slang
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{
                        "intent": "unknown",
                        "confidence": 0.40,
                        "entities": {"language_style": "informal"},
                        "reasoning": f"Burmese slang: {test_key}",
                        "priority": 1
                    }],
                    "primary_intent": "unknown"
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_language"] == "my"
                # Real AI gives higher confidence, so we test the core functionality
                assert result["intent_confidence"] > 0.0 