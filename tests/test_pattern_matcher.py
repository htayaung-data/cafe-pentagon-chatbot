"""
Unit tests for Pattern Matcher Node
Tests greeting, goodbye, and escalation detection for both English and Burmese
"""

import pytest
from unittest.mock import patch, MagicMock
from src.graph.nodes.pattern_matcher import PatternMatcherNode
from tests.conftest import TEST_USER_MESSAGES


class TestPatternMatcherNode:
    """Test suite for Pattern Matcher Node"""
    
    @pytest.fixture
    def pattern_matcher(self):
        """Initialize pattern matcher node"""
        return PatternMatcherNode()
    
    @pytest.mark.asyncio
    async def test_english_greeting_detection(self, pattern_matcher, sample_state):
        """Test English greeting pattern detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_greeting"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is True
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is False
        assert result["detected_language"] == "en"
    
    @pytest.mark.asyncio
    async def test_english_goodbye_detection(self, pattern_matcher, sample_state):
        """Test English goodbye pattern detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_goodbye"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is True
        assert result["is_escalation_request"] is False
    
    @pytest.mark.asyncio
    async def test_english_escalation_detection(self, pattern_matcher, sample_state):
        """Test English escalation pattern detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_escalation"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is True
    
    @pytest.mark.asyncio
    async def test_burmese_greeting_detection(self, pattern_matcher, sample_state):
        """Test Burmese greeting pattern detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["burmese_greeting"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is True
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is False
        assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_goodbye_detection(self, pattern_matcher, sample_state):
        """Test Burmese goodbye pattern detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["burmese_goodbye"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is True
        assert result["is_escalation_request"] is False
    
    @pytest.mark.asyncio
    async def test_burmese_escalation_detection(self, pattern_matcher, sample_state):
        """Test Burmese escalation pattern detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["burmese_escalation"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is True
    
    @pytest.mark.asyncio
    async def test_menu_related_query_detection(self, pattern_matcher, sample_state):
        """Test menu-related query detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is False
        # Menu queries should not be caught by pattern matcher
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, pattern_matcher, sample_state):
        """Test handling of empty messages"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = ""
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is False
    
    @pytest.mark.asyncio
    async def test_whitespace_only_message(self, pattern_matcher, sample_state):
        """Test handling of whitespace-only messages"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "   \n\t   "
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        assert result["is_greeting"] is False
        assert result["is_goodbye"] is False
        assert result["is_escalation_request"] is False
    
    @pytest.mark.asyncio
    async def test_mixed_language_detection(self, pattern_matcher, sample_state):
        """Test detection with mixed language content"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "Hello မင်္ဂလာပါ"
        
        # Act
        result = await pattern_matcher.process(state)
        
        # Assert
        # Should detect as greeting due to English "Hello"
        assert result["is_greeting"] is True
        assert result["detected_language"] in ["en", "my"]
    
    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, pattern_matcher, sample_state):
        """Test case-insensitive pattern detection"""
        # Arrange
        test_cases = [
            "HELLO",
            "Hello",
            "hello",
            "hElLo"
        ]
        
        for message in test_cases:
            state = sample_state.copy()
            state["user_message"] = message
            
            # Act
            result = await pattern_matcher.process(state)
            
            # Assert
            assert result["is_greeting"] is True, f"Failed for message: {message}"
    
    @pytest.mark.asyncio
    async def test_complex_greeting_patterns(self, pattern_matcher, sample_state):
        """Test complex greeting patterns"""
        # Arrange
        complex_greetings = [
            "Good morning! How are you today?",
            "Hey there, nice to meet you!",
            "Hi, how's it going?",
            "Hello, pleasure to meet you!"
        ]
        
        for message in complex_greetings:
            state = sample_state.copy()
            state["user_message"] = message
            
            # Act
            result = await pattern_matcher.process(state)
            
            # Assert
            assert result["is_greeting"] is True, f"Failed for message: {message}"
    
    @pytest.mark.asyncio
    async def test_complex_goodbye_patterns(self, pattern_matcher, sample_state):
        """Test complex goodbye patterns"""
        # Arrange
        complex_goodbyes = [
            "Thank you so much, goodbye!",
            "Thanks for your help, see you later!",
            "That's all I need, take care!",
            "Appreciate it, farewell!"
        ]
        
        for message in complex_goodbyes:
            state = sample_state.copy()
            state["user_message"] = message
            
            # Act
            result = await pattern_matcher.process(state)
            
            # Assert
            assert result["is_goodbye"] is True, f"Failed for message: {message}"
    
    @pytest.mark.asyncio
    async def test_complex_escalation_patterns(self, pattern_matcher, sample_state):
        """Test complex escalation patterns"""
        # Arrange
        complex_escalations = [
            "I need to speak to a real person",
            "Can I talk to someone from your staff?",
            "I want to speak to a human representative",
            "Please connect me to a person"
        ]
        
        for message in complex_escalations:
            state = sample_state.copy()
            state["user_message"] = message
            
            # Act
            result = await pattern_matcher.process(state)
            
            # Assert
            assert result["is_escalation_request"] is True, f"Failed for message: {message}"
    
    def test_pattern_confidence_scoring(self, pattern_matcher):
        """Test pattern confidence scoring"""
        # Test English patterns
        assert pattern_matcher.get_pattern_confidence("Hello", "greeting", "en") > 0.5
        assert pattern_matcher.get_pattern_confidence("Thank you", "goodbye", "en") > 0.5
        assert pattern_matcher.get_pattern_confidence("Can I talk to someone", "escalation", "en") > 0.5
        
        # Test Burmese patterns
        assert pattern_matcher.get_pattern_confidence("မင်္ဂလာပါ", "greeting", "my") > 0.5
        assert pattern_matcher.get_pattern_confidence("ကျေးဇူးတင်ပါတယ်", "goodbye", "my") > 0.5
        assert pattern_matcher.get_pattern_confidence("လူသားနဲ့ပြောချင်ပါတယ်", "escalation", "my") > 0.5
    
    def test_menu_related_detection(self, pattern_matcher):
        """Test menu-related query detection"""
        menu_queries = [
            "What's on your menu?",
            "Show me the food options",
            "What do you serve?",
            "Menu please"
        ]
        
        for query in menu_queries:
            assert pattern_matcher.is_menu_related_query(query) is True
    
    def test_customer_service_detection(self, pattern_matcher):
        """Test customer service question detection"""
        service_queries = [
            "Do you have wifi?",
            "What are your opening hours?",
            "Can I bring my dog?",
            "Is smoking allowed?"
        ]
        
        for query in service_queries:
            assert pattern_matcher.is_customer_service_question(query) is True 