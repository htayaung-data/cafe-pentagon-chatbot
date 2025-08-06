"""
Unit tests for Intent Classifier Node
Tests intent detection, namespace routing, and Burmese language handling
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.nodes.intent_classifier import IntentClassifierNode
from tests.conftest import TEST_USER_MESSAGES


class TestIntentClassifierNode:
    """Test suite for Intent Classifier Node"""
    
    @pytest.fixture
    def intent_classifier(self, mock_openai):
        """Initialize intent classifier node with mocked OpenAI"""
        return IntentClassifierNode()
    
    @pytest.mark.asyncio
    async def test_menu_intent_detection(self, intent_classifier, sample_state):
        """Test menu intent detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        state["detected_language"] = "en"
        
        # Mock AI classifier response
        with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
            mock_process.return_value = {
                "detected_intents": [{"intent": "menu_browse", "confidence": 0.95}],
                "primary_intent": "menu_browse",
                "reasoning": "User asked about menu items",
                "entities": {"food_type": "general"}
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "menu_browse"
            assert result["intent_confidence"] == 0.95
            assert result["target_namespace"] == "menu"
            assert result["intent_reasoning"] == "User asked about menu items"
    
    @pytest.mark.asyncio
    async def test_faq_intent_detection(self, intent_classifier, sample_state):
        """Test FAQ intent detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_faq"]
        state["detected_language"] = "en"
        
        # Mock AI classifier response
        with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
            mock_process.return_value = {
                "detected_intents": [{"intent": "faq", "confidence": 0.92}],
                "primary_intent": "faq",
                "reasoning": "User asked about business hours",
                "entities": {"question_type": "hours"}
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "faq"
            assert result["intent_confidence"] == 0.92
            assert result["target_namespace"] == "faq"
    
    @pytest.mark.asyncio
    async def test_job_intent_detection(self, intent_classifier, sample_state):
        """Test job application intent detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_job"]
        state["detected_language"] = "en"
        
        # Mock AI classifier response
        with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
            mock_process.return_value = {
                "detected_intents": [{"intent": "job_application", "confidence": 0.88}],
                "primary_intent": "job_application",
                "reasoning": "User asked about job openings",
                "entities": {"job_type": "general"}
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "job_application"
            assert result["intent_confidence"] == 0.88
            assert result["target_namespace"] == "job_application"
    
    @pytest.mark.asyncio
    async def test_burmese_menu_intent_detection(self, intent_classifier, sample_state):
        """Test Burmese menu intent detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["burmese_menu"]
        state["detected_language"] = "my"
        
        # Mock Burmese menu analysis
        with patch.object(intent_classifier, '_analyze_burmese_menu_request') as mock_analysis:
            mock_analysis.return_value = {
                "action": "MENU_BROWSE",
                "confidence": 0.95,
                "category": "general"
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "menu_browse"
            assert result["intent_confidence"] == 0.95
            assert result["target_namespace"] == "menu"
    
    @pytest.mark.asyncio
    async def test_burmese_faq_intent_detection(self, intent_classifier, sample_state):
        """Test Burmese FAQ intent detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["burmese_faq"]
        state["detected_language"] = "my"
        
        # Mock AI classifier response for Burmese
        with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
            mock_process.return_value = {
                "detected_intents": [{"intent": "faq", "confidence": 0.90}],
                "primary_intent": "faq",
                "reasoning": "User asked about opening hours in Burmese",
                "entities": {"question_type": "hours"}
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "faq"
            assert result["intent_confidence"] == 0.90
            assert result["target_namespace"] == "faq"
    
    @pytest.mark.asyncio
    async def test_greeting_skip_intent_classification(self, intent_classifier, sample_state):
        """Test that greetings skip intent classification"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_greeting"]
        state["is_greeting"] = True
        state["detected_language"] = "en"
        
        # Act
        result = await intent_classifier.process(state)
        
        # Assert
        assert result["detected_intent"] == "greeting"
        assert result["intent_confidence"] == 0.0
        assert result["target_namespace"] == ""
    
    @pytest.mark.asyncio
    async def test_goodbye_skip_intent_classification(self, intent_classifier, sample_state):
        """Test that goodbyes skip intent classification"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_goodbye"]
        state["is_goodbye"] = True
        state["detected_language"] = "en"
        
        # Act
        result = await intent_classifier.process(state)
        
        # Assert
        assert result["detected_intent"] == "goodbye"
        assert result["intent_confidence"] == 0.0
        assert result["target_namespace"] == ""
    
    @pytest.mark.asyncio
    async def test_escalation_skip_intent_classification(self, intent_classifier, sample_state):
        """Test that escalation requests skip intent classification"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_escalation"]
        state["is_escalation_request"] = True
        state["detected_language"] = "en"
        
        # Act
        result = await intent_classifier.process(state)
        
        # Assert
        assert result["detected_intent"] == "escalation"
        assert result["intent_confidence"] == 0.0
        assert result["target_namespace"] == ""
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, intent_classifier, sample_state):
        """Test handling of empty messages"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = ""
        
        # Act
        result = await intent_classifier.process(state)
        
        # Assert
        assert result["detected_intent"] == "unknown"
        assert result["intent_confidence"] == 0.0
        assert result["target_namespace"] == ""
    
    @pytest.mark.asyncio
    async def test_low_confidence_intent(self, intent_classifier, sample_state):
        """Test handling of low confidence intent detection"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "Some unclear message"
        state["detected_language"] = "en"
        
        # Mock AI classifier response with low confidence
        with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
            mock_process.return_value = {
                "detected_intents": [{"intent": "unknown", "confidence": 0.25}],
                "primary_intent": "unknown",
                "reasoning": "Low confidence in intent detection",
                "entities": {}
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "unknown"
            assert result["intent_confidence"] == 0.25
            assert result["target_namespace"] == ""
    
    @pytest.mark.asyncio
    async def test_multiple_intents_detection(self, intent_classifier, sample_state):
        """Test detection of multiple intents"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "What's on your menu and do you have job openings?"
        state["detected_language"] = "en"
        
        # Mock AI classifier response with multiple intents
        with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
            mock_process.return_value = {
                "detected_intents": [
                    {"intent": "menu_browse", "confidence": 0.85},
                    {"intent": "job_application", "confidence": 0.78}
                ],
                "primary_intent": "menu_browse",
                "reasoning": "Multiple intents detected, prioritizing menu",
                "entities": {"food_type": "general", "job_type": "general"}
            }
            
            # Act
            result = await intent_classifier.process(state)
            
            # Assert
            assert result["detected_intent"] == "menu_browse"
            assert result["intent_confidence"] == 0.85
            assert len(result["all_intents"]) == 2
            assert result["target_namespace"] == "menu"
    
    def test_intent_to_namespace_mapping(self, intent_classifier):
        """Test mapping of intents to namespaces"""
        # Test menu intents
        assert intent_classifier._map_intent_to_namespace("menu_browse") == "menu"
        assert intent_classifier._map_intent_to_namespace("menu_order") == "menu"
        assert intent_classifier._map_intent_to_namespace("menu_inquiry") == "menu"
        
        # Test FAQ intents
        assert intent_classifier._map_intent_to_namespace("faq") == "faq"
        assert intent_classifier._map_intent_to_namespace("general_question") == "faq"
        
        # Test job intents
        assert intent_classifier._map_intent_to_namespace("job_application") == "job_application"
        assert intent_classifier._map_intent_to_namespace("career_inquiry") == "job_application"
        
        # Test other intents
        assert intent_classifier._map_intent_to_namespace("greeting") == ""
        assert intent_classifier._map_intent_to_namespace("goodbye") == ""
        assert intent_classifier._map_intent_to_namespace("escalation") == ""
        assert intent_classifier._map_intent_to_namespace("unknown") == ""
    
    @pytest.mark.asyncio
    async def test_burmese_menu_analysis(self, intent_classifier):
        """Test Burmese menu analysis functionality"""
        # Arrange
        user_message = "ဘာတွေရှိလဲ"
        conversation_history = []
        
        # Mock the analysis method
        with patch.object(intent_classifier, '_analyze_burmese_menu_request') as mock_analysis:
            mock_analysis.return_value = {
                "action": "MENU_BROWSE",
                "confidence": 0.95,
                "category": "general",
                "items": ["coffee", "burger"]
            }
            
            # Act
            result = await intent_classifier._analyze_burmese_menu_request(user_message, conversation_history)
            
            # Assert
            assert result["action"] == "MENU_BROWSE"
            assert result["confidence"] == 0.95
            assert result["category"] == "general"
    
    @pytest.mark.asyncio
    async def test_burmese_menu_intent_handling(self, intent_classifier, sample_state):
        """Test handling of Burmese menu intents"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "ဘာတွေရှိလဲ"
        state["detected_language"] = "my"
        
        menu_analysis = {
            "action": "MENU_BROWSE",
            "confidence": 0.95,
            "category": "general"
        }
        
        # Act
        result = await intent_classifier._handle_burmese_menu_intent(state, menu_analysis)
        
        # Assert
        assert result["detected_intent"] == "menu_browse"
        assert result["intent_confidence"] == 0.95
        assert result["target_namespace"] == "menu"
        assert result["intent_reasoning"] == "Burmese menu inquiry detected"
    
    def test_general_menu_question_detection(self, intent_classifier):
        """Test detection of general menu questions"""
        general_questions = [
            "What's on your menu?",
            "Show me the menu",
            "What do you serve?",
            "Menu please"
        ]
        
        for question in general_questions:
            assert intent_classifier._is_general_menu_question(question) is True
    
    def test_specific_category_question_detection(self, intent_classifier):
        """Test detection of specific category questions"""
        category_questions = [
            "What drinks do you have?",
            "Show me your beverages",
            "What desserts are available?",
            "Do you have coffee?"
        ]
        
        for question in category_questions:
            assert intent_classifier._is_specific_category_question(question) is True
    
    def test_specific_item_question_detection(self, intent_classifier):
        """Test detection of specific item questions"""
        item_questions = [
            "How much is the coffee?",
            "What's in the burger?",
            "Is the pizza good?",
            "Tell me about the pasta"
        ]
        
        for question in item_questions:
            assert intent_classifier._is_specific_item_question(question) is True 