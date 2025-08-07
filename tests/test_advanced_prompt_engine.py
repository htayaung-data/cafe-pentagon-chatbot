"""
Advanced Prompt Engine Tests
Tests the sophisticated prompt engineering system with context-aware generation and cultural adaptations
"""

import pytest
from typing import Dict, Any, List
from src.controllers.advanced_prompt_engine import (
    AdvancedPromptEngine,
    PromptContext,
    get_advanced_prompt_engine
)


class TestAdvancedPromptEngine:
    """Test advanced prompt engine functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create advanced prompt engine for testing"""
        return AdvancedPromptEngine()
    
    @pytest.fixture
    def basic_context(self):
        """Create basic prompt context"""
        return PromptContext(
            user_message="What's on the menu?",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
    
    def test_engine_initialization(self, engine):
        """Test that engine initializes correctly"""
        assert engine is not None
        assert hasattr(engine, 'base_templates')
        assert hasattr(engine, 'cultural_adapters')
        assert hasattr(engine, 'confidence_adapters')
        
        # Check that all template types are loaded
        expected_templates = [
            "standard", "complex_query", "multi_intent", "escalation",
            "cultural_sensitive", "low_confidence", "cross_domain", "burmese_enhanced"
        ]
        for template_type in expected_templates:
            assert template_type in engine.base_templates
    
    def test_cultural_adapters_loading(self, engine):
        """Test that cultural adapters are loaded correctly"""
        assert "en" in engine.cultural_adapters
        assert "my" in engine.cultural_adapters
        
        # Check English cultural rules
        english_rules = engine.cultural_adapters["en"]
        assert "formality_levels" in english_rules
        assert "honorifics" in english_rules
        assert "cultural_nuances" in english_rules
        assert "response_patterns" in english_rules
        
        # Check Burmese cultural rules
        burmese_rules = engine.cultural_adapters["my"]
        assert "formality_levels" in burmese_rules
        assert "honorifics" in burmese_rules
        assert "cultural_nuances" in burmese_rules
        assert "response_patterns" in burmese_rules
        
        # Check Burmese-specific honorifics
        assert "ဦး" in burmese_rules["honorifics"]
        assert "ဒေါ်" in burmese_rules["honorifics"]
        assert "မ" in burmese_rules["honorifics"]
    
    def test_confidence_adapters_loading(self, engine):
        """Test that confidence adapters are loaded correctly"""
        expected_levels = ["high_confidence", "medium_confidence", "low_confidence"]
        
        for level in expected_levels:
            assert level in engine.confidence_adapters
            rules = engine.confidence_adapters[level]
            assert "analysis_depth" in rules
            assert "fallback_threshold" in rules
            assert "response_style" in rules
            assert "detail_level" in rules
    
    def test_standard_template_generation(self, engine, basic_context):
        """Test standard template generation"""
        prompt = engine.generate_enhanced_prompt(basic_context)
        
        # Check that prompt contains essential sections
        assert "ENHANCED UNIFIED ANALYSIS PROMPT" in prompt
        assert "CURRENT CONTEXT" in prompt
        assert "CONVERSATION CONTEXT" in prompt
        assert "USER PREFERENCES" in prompt
        assert "CULTURAL CONTEXT ANALYSIS" in prompt
        assert "CONFIDENCE SCORING GUIDELINES" in prompt
        assert "ENHANCED OUTPUT FORMAT (JSON)" in prompt
        assert "FALLBACK LOGIC" in prompt
        
        # Check that user message is included
        assert "What's on the menu?" in prompt
        assert "en" in prompt  # detected language
    
    def test_burmese_template_selection(self, engine):
        """Test that Burmese language triggers burmese_enhanced template"""
        burmese_context = PromptContext(
            user_message="မင်္ဂလာပါ",
            detected_language="my",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(burmese_context)
        
        # Check for Burmese-specific enhancements
        assert "BURMESE LANGUAGE ENHANCEMENT" in prompt
        assert "အရပ်စကား" in prompt
        assert "အလယ်အလတ်" in prompt
        assert "ရုံးစကား" in prompt
        assert "မင်္ဂလာပါ" in prompt
    
    def test_escalation_template_selection(self, engine):
        """Test that escalation keywords trigger escalation template"""
        escalation_context = PromptContext(
            user_message="I need help with a problem",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(escalation_context)
        
        # Check for escalation-specific guidance
        assert "ESCALATION ANALYSIS GUIDANCE" in prompt
        assert "escalation urgency" in prompt
        assert "root causes" in prompt
        assert "emotional state" in prompt
    
    def test_multi_intent_template_selection(self, engine):
        """Test that multi-intent keywords trigger multi-intent template"""
        multi_intent_context = PromptContext(
            user_message="I want to order pizza and also get delivery",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(multi_intent_context)
        
        # Check for multi-intent guidance
        assert "MULTI-INTENT ANALYSIS GUIDANCE" in prompt
        assert "distinct user intents" in prompt
        assert "secondary_intents" in prompt
        assert "cross-domain detection" in prompt
    
    def test_cross_domain_template_selection(self, engine):
        """Test that cross-domain keywords trigger cross-domain template"""
        cross_domain_context = PromptContext(
            user_message="What food do you have and are you hiring?",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(cross_domain_context)
        
        # Check for cross-domain guidance
        assert "CROSS-DOMAIN ANALYSIS GUIDANCE" in prompt
        assert "relevant domains" in prompt
        assert "fallback_namespaces" in prompt
        assert "cross_domain_detected" in prompt
    
    def test_low_confidence_template_selection(self, engine):
        """Test that low confidence context triggers low confidence template"""
        # Create context with low confidence history
        low_confidence_history = [
            {"intent_confidence": 0.3, "user_message": "Previous message"},
            {"intent_confidence": 0.4, "user_message": "Another message"}
        ]
        
        low_confidence_context = PromptContext(
            user_message="What do you mean?",
            detected_language="en",
            conversation_history=low_confidence_history,
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(low_confidence_context)
        
        # Check for low confidence guidance
        assert "LOW CONFIDENCE ANALYSIS GUIDANCE" in prompt
        assert "conservative confidence scoring" in prompt
        assert "multiple fallback options" in prompt
        assert "clarification questions" in prompt
    
    def test_complex_query_template_selection(self, engine):
        """Test that complex queries trigger complex query template"""
        complex_context = PromptContext(
            user_message="I would like to know about your menu options, pricing, availability, and whether you can accommodate special dietary requirements for a group of 15 people on Saturday evening",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(complex_context)
        
        # Check for complex query guidance
        assert "COMPLEX QUERY ANALYSIS GUIDANCE" in prompt
        assert "multiple intents" in prompt
        assert "temporal and logical relationships" in prompt
        assert "detailed reasoning" in prompt
    
    def test_cultural_sensitive_template_selection(self, engine):
        """Test that culturally sensitive keywords trigger cultural sensitive template"""
        cultural_context = PromptContext(
            user_message="What are your customs and traditions?",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(cultural_context)
        
        # Check for cultural sensitivity guidance
        assert "CULTURAL SENSITIVITY GUIDANCE" in prompt
        assert "cultural context and nuances" in prompt
        assert "formality levels" in prompt
        assert "cultural taboos" in prompt
    
    def test_conversation_history_integration(self, engine):
        """Test that conversation history is properly integrated"""
        history = [
            {
                "detected_intent": "greeting",
                "intent_confidence": 0.9,
                "user_message": "Hello"
            },
            {
                "detected_intent": "menu_browse",
                "intent_confidence": 0.8,
                "user_message": "What's on the menu?"
            }
        ]
        
        context_with_history = PromptContext(
            user_message="Tell me more about the pizza",
            detected_language="en",
            conversation_history=history,
            cultural_context={},
            previous_intents=["greeting", "menu_browse"],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        prompt = engine.generate_enhanced_prompt(context_with_history)
        
        # Check that history is included
        assert "Recent conversation context:" in prompt
        assert "greeting" in prompt
        assert "menu_browse" in prompt
        assert "0.90" in prompt  # confidence from history
        assert "0.80" in prompt  # confidence from history
    
    def test_user_preferences_integration(self, engine):
        """Test that user preferences are properly integrated"""
        preferences = {
            "language": "english",
            "formality": "casual",
            "response_length": "detailed",
            "dietary_restrictions": "vegetarian"
        }
        
        context_with_preferences = PromptContext(
            user_message="What do you recommend?",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences=preferences
        )
        
        prompt = engine.generate_enhanced_prompt(context_with_preferences)
        
        # Check that preferences are included
        assert "User preferences:" in prompt
        assert "language: english" in prompt
        assert "formality: casual" in prompt
        assert "response_length: detailed" in prompt
        assert "dietary_restrictions: vegetarian" in prompt
    
    def test_confidence_level_determination(self, engine):
        """Test confidence level determination based on conversation history"""
        # Test high confidence
        high_confidence_history = [
            {"intent_confidence": 0.9},
            {"intent_confidence": 0.8},
            {"intent_confidence": 0.85}
        ]
        
        high_confidence_context = PromptContext(
            user_message="Test",
            detected_language="en",
            conversation_history=high_confidence_history,
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        confidence_level = engine._get_confidence_level(high_confidence_context)
        assert confidence_level == "high_confidence"
        
        # Test low confidence
        low_confidence_history = [
            {"intent_confidence": 0.3},
            {"intent_confidence": 0.2},
            {"intent_confidence": 0.4}
        ]
        
        low_confidence_context = PromptContext(
            user_message="Test",
            detected_language="en",
            conversation_history=low_confidence_history,
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        confidence_level = engine._get_confidence_level(low_confidence_context)
        assert confidence_level == "low_confidence"
    
    def test_fallback_prompt_generation(self, engine):
        """Test fallback prompt generation when main generation fails"""
        # Create a context that might cause issues
        problematic_context = PromptContext(
            user_message="",  # Empty message might cause issues
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        # Force fallback by causing an exception in the main generation
        # We'll test the fallback method directly
        fallback_prompt = engine._get_fallback_prompt(problematic_context)
        
        # Check fallback prompt structure
        assert "ENHANCED UNIFIED ANALYSIS PROMPT (FALLBACK)" in fallback_prompt
        assert "USER MESSAGE" in fallback_prompt
        assert "LANGUAGE" in fallback_prompt
        assert "intent_analysis" in fallback_prompt
        assert "namespace_routing" in fallback_prompt
        assert "hitl_assessment" in fallback_prompt
    
    def test_global_instance_access(self):
        """Test global instance access through get_advanced_prompt_engine"""
        engine1 = get_advanced_prompt_engine()
        engine2 = get_advanced_prompt_engine()
        
        # Should return the same instance (singleton pattern)
        assert engine1 is engine2
        assert isinstance(engine1, AdvancedPromptEngine)
    
    def test_template_type_determination(self, engine):
        """Test template type determination logic"""
        # Test standard template
        standard_context = PromptContext(
            user_message="Hello",
            detected_language="en",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        template_type = engine._determine_template_type(standard_context)
        assert template_type == "standard"
        
        # Test burmese template
        burmese_context = PromptContext(
            user_message="Hello",
            detected_language="my",
            conversation_history=[],
            cultural_context={},
            previous_intents=[],
            confidence_thresholds={},
            platform="messenger",
            user_preferences={}
        )
        
        template_type = engine._determine_template_type(burmese_context)
        assert template_type == "burmese_enhanced"
    
    def test_context_extraction_methods(self, engine):
        """Test context extraction methods"""
        # Test history context extraction
        history = [
            {"detected_intent": "greeting", "intent_confidence": 0.9, "user_message": "Hello there"},
            {"detected_intent": "menu_browse", "intent_confidence": 0.8, "user_message": "What's on the menu today?"}
        ]
        
        history_context = engine._extract_history_context(history)
        assert "Recent conversation context:" in history_context
        assert "greeting" in history_context
        assert "menu_browse" in history_context
        assert "0.90" in history_context
        assert "0.80" in history_context
        
        # Test preferences context extraction
        preferences = {"language": "english", "formality": "casual"}
        preferences_context = engine._extract_preferences_context(preferences)
        assert "User preferences:" in preferences_context
        assert "language: english" in preferences_context
        assert "formality: casual" in preferences_context
        
        # Test empty contexts
        empty_history_context = engine._extract_history_context([])
        assert "No previous conversation context available" in empty_history_context
        
        empty_preferences_context = engine._extract_preferences_context({})
        assert "No user preferences available" in empty_preferences_context


if __name__ == "__main__":
    pytest.main([__file__])
