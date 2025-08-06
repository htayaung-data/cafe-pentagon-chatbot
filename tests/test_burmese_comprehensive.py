"""
Comprehensive Burmese Language Testing for Cafe Pentagon Chatbot
Focuses on problematic patterns and edge cases that commonly cause issues
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.nodes.pattern_matcher import PatternMatcherNode
from src.graph.nodes.intent_classifier import IntentClassifierNode
from src.graph.nodes.rag_retriever import RAGRetrieverNode
from tests.conftest import TEST_USER_MESSAGES


class TestBurmesePatternMatching:
    """Comprehensive Burmese pattern matching tests"""
    
    @pytest.fixture
    def pattern_matcher(self):
        return PatternMatcherNode()
    
    @pytest.mark.asyncio
    async def test_burmese_greeting_variations(self, pattern_matcher, sample_state):
        """Test various Burmese greeting patterns"""
        greeting_tests = [
            "burmese_greeting",
            "burmese_greeting_casual", 
            "burmese_greeting_formal",
            "burmese_cultural_respect",
            "burmese_cultural_polite"
        ]
        
        for test_key in greeting_tests:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            
            result = await pattern_matcher.process(state)
            
            assert result["is_greeting"] is True, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
            assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_goodbye_variations(self, pattern_matcher, sample_state):
        """Test various Burmese goodbye patterns"""
        goodbye_tests = [
            "burmese_goodbye",
            "burmese_goodbye_formal",
            "burmese_goodbye_casual",
            "burmese_cultural_formal"
        ]
        
        for test_key in goodbye_tests:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            
            result = await pattern_matcher.process(state)
            
            assert result["is_goodbye"] is True, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
            assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_escalation_variations(self, pattern_matcher, sample_state):
        """Test various Burmese escalation patterns"""
        escalation_tests = [
            "burmese_escalation",
            "burmese_escalation_help",
            "burmese_escalation_human"
        ]
        
        for test_key in escalation_tests:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            
            result = await pattern_matcher.process(state)
            
            assert result["is_escalation_request"] is True, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
            assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_edge_cases(self, pattern_matcher, sample_state):
        """Test Burmese edge cases that commonly cause issues"""
        edge_cases = [
            "burmese_edge_empty",
            "burmese_edge_whitespace",
            "burmese_edge_numbers",
            "burmese_edge_english_only",
            "burmese_edge_mixed_chars",
            "burmese_edge_very_long",
            "burmese_edge_special_chars",
            "burmese_edge_repeated",
            "burmese_edge_question_marks",
            "burmese_edge_exclamation"
        ]
        
        for test_key in edge_cases:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            
            result = await pattern_matcher.process(state)
            
            # Edge cases should not trigger pattern matching
            assert result["is_greeting"] is False, f"Should not detect greeting for {test_key}"
            assert result["is_goodbye"] is False, f"Should not detect goodbye for {test_key}"
            assert result["is_escalation_request"] is False, f"Should not detect escalation for {test_key}"
    
    @pytest.mark.asyncio
    async def test_burmese_ambiguous_queries(self, pattern_matcher, sample_state):
        """Test ambiguous Burmese queries that need context"""
        ambiguous_queries = [
            "burmese_ambiguous_what",
            "burmese_ambiguous_how",
            "burmese_ambiguous_where",
            "burmese_ambiguous_when",
            "burmese_ambiguous_why",
            "burmese_ambiguous_which"
        ]
        
        for test_key in ambiguous_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            
            result = await pattern_matcher.process(state)
            
            # Ambiguous queries should not trigger pattern matching
            assert result["is_greeting"] is False, f"Should not detect greeting for {test_key}"
            assert result["is_goodbye"] is False, f"Should not detect goodbye for {test_key}"
            assert result["is_escalation_request"] is False, f"Should not detect escalation for {test_key}"
            assert result["detected_language"] == "my"


class TestBurmeseIntentClassification:
    """Comprehensive Burmese intent classification tests"""
    
    @pytest.fixture
    def intent_classifier(self, mock_openai):
        return IntentClassifierNode()
    
    @pytest.mark.asyncio
    async def test_burmese_menu_intents(self, intent_classifier, sample_state):
        """Test Burmese menu-related intent detection"""
        menu_queries = [
            "burmese_menu_general",
            "burmese_menu_what",
            "burmese_menu_food",
            "burmese_menu_drink",
            "burmese_menu_coffee",
            "burmese_menu_price",
            "burmese_menu_expensive",
            "burmese_menu_cheap",
            "burmese_menu_category",
            "burmese_menu_specific",
            "burmese_menu_available",
            "burmese_menu_best",
            "burmese_menu_popular",
            "burmese_menu_recommend",
            "burmese_menu_spicy",
            "burmese_menu_vegetarian",
            "burmese_menu_breakfast",
            "burmese_menu_lunch",
            "burmese_menu_dinner"
        ]
        
        for test_key in menu_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock Burmese menu analysis
            with patch.object(intent_classifier, '_analyze_burmese_menu_request') as mock_analysis:
                mock_analysis.return_value = {
                    "action": "MENU_BROWSE",
                    "confidence": 0.95,
                    "category": "general"
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "menu_browse", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "menu"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_faq_intents(self, intent_classifier, sample_state):
        """Test Burmese FAQ-related intent detection"""
        faq_queries = [
            "burmese_faq_hours",
            "burmese_faq_open",
            "burmese_faq_close",
            "burmese_faq_working",
            "burmese_faq_wifi",
            "burmese_faq_internet",
            "burmese_faq_parking",
            "burmese_faq_location",
            "burmese_faq_address",
            "burmese_faq_phone",
            "burmese_faq_reservation",
            "burmese_faq_booking",
            "burmese_faq_delivery",
            "burmese_faq_takeaway",
            "burmese_faq_pets",
            "burmese_faq_smoking",
            "burmese_faq_outdoor",
            "burmese_faq_aircon",
            "burmese_faq_payment",
            "burmese_faq_card",
            "burmese_faq_cash"
        ]
        
        for test_key in faq_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{"intent": "faq", "confidence": 0.90}],
                    "primary_intent": "faq",
                    "reasoning": f"Burmese FAQ query: {test_key}",
                    "entities": {"question_type": "general"}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "faq", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "faq"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_job_intents(self, intent_classifier, sample_state):
        """Test Burmese job-related intent detection"""
        job_queries = [
            "burmese_job_general",
            "burmese_job_hiring",
            "burmese_job_position",
            "burmese_job_waitress",
            "burmese_job_kitchen",
            "burmese_job_barista",
            "burmese_job_manager",
            "burmese_job_parttime",
            "burmese_job_fulltime",
            "burmese_job_salary",
            "burmese_job_experience",
            "burmese_job_apply",
            "burmese_job_interview"
        ]
        
        for test_key in job_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{"intent": "job_application", "confidence": 0.88}],
                    "primary_intent": "job_application",
                    "reasoning": f"Burmese job query: {test_key}",
                    "entities": {"job_type": "general"}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "job_application", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "job_application"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_complex_queries(self, intent_classifier, sample_state):
        """Test complex Burmese queries with multiple intents"""
        complex_queries = [
            "burmese_complex_menu_price",
            "burmese_complex_hours_location",
            "burmese_complex_job_salary",
            "burmese_complex_delivery_hours",
            "burmese_complex_menu_recommend"
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
    async def test_burmese_slang_and_informal(self, intent_classifier, sample_state):
        """Test Burmese slang and informal language patterns"""
        slang_queries = [
            "burmese_slang_what",
            "burmese_slang_how",
            "burmese_slang_where",
            "burmese_slang_when",
            "burmese_slang_why",
            "burmese_slang_which"
        ]
        
        for test_key in slang_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response for slang
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{"intent": "unknown", "confidence": 0.30}],
                    "primary_intent": "unknown",
                    "reasoning": f"Burmese slang query: {test_key}",
                    "entities": {"language_style": "informal"}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_language"] == "my"
                # Slang queries might have low confidence
                assert result["intent_confidence"] <= 0.30
    
    @pytest.mark.asyncio
    async def test_burmese_regional_variations(self, intent_classifier, sample_state):
        """Test Burmese regional language variations"""
        regional_queries = [
            "burmese_regional_coffee",
            "burmese_regional_tea",
            "burmese_regional_food",
            "burmese_regional_drink"
        ]
        
        for test_key in regional_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock Burmese menu analysis for regional variations
            with patch.object(intent_classifier, '_analyze_burmese_menu_request') as mock_analysis:
                mock_analysis.return_value = {
                    "action": "MENU_BROWSE",
                    "confidence": 0.92,
                    "category": "regional"
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "menu_browse", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "menu"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_time_related_queries(self, intent_classifier, sample_state):
        """Test Burmese time-related queries"""
        time_queries = [
            "burmese_time_now",
            "burmese_time_today",
            "burmese_time_tomorrow",
            "burmese_time_weekend",
            "burmese_time_holiday"
        ]
        
        for test_key in time_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response for time queries
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{"intent": "faq", "confidence": 0.85}],
                    "primary_intent": "faq",
                    "reasoning": f"Burmese time query: {test_key}",
                    "entities": {"question_type": "time"}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "faq", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "faq"
                assert result["detected_language"] == "my"
    
    @pytest.mark.asyncio
    async def test_burmese_quantity_queries(self, intent_classifier, sample_state):
        """Test Burmese quantity and amount queries"""
        quantity_queries = [
            "burmese_quantity_how_much",
            "burmese_quantity_how_many",
            "burmese_quantity_how_long",
            "burmese_quantity_how_far",
            "burmese_quantity_how_big",
            "burmese_quantity_how_small"
        ]
        
        for test_key in quantity_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["detected_language"] = "my"
            
            # Mock AI classifier response for quantity queries
            with patch.object(intent_classifier.intent_classifier, 'process') as mock_process:
                mock_process.return_value = {
                    "detected_intents": [{"intent": "faq", "confidence": 0.80}],
                    "primary_intent": "faq",
                    "reasoning": f"Burmese quantity query: {test_key}",
                    "entities": {"question_type": "quantity"}
                }
                
                result = await intent_classifier.process(state)
                
                assert result["detected_intent"] == "faq", f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["target_namespace"] == "faq"
                assert result["detected_language"] == "my"


class TestBurmeseRAGRetrieval:
    """Comprehensive Burmese RAG retrieval tests"""
    
    @pytest.fixture
    def rag_retriever(self, mock_pinecone):
        return RAGRetrieverNode()
    
    @pytest.mark.asyncio
    async def test_burmese_menu_search_variations(self, rag_retriever, sample_state):
        """Test Burmese menu search with various query patterns"""
        menu_search_queries = [
            "burmese_menu_general",
            "burmese_menu_coffee",
            "burmese_menu_price",
            "burmese_menu_category",
            "burmese_menu_specific",
            "burmese_menu_recommend",
            "burmese_menu_spicy",
            "burmese_menu_vegetarian"
        ]
        
        for test_key in menu_search_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["target_namespace"] = "menu"
            state["detected_language"] = "my"
            state["intent_confidence"] = 0.95
            
            # Mock Burmese search
            with patch.object(rag_retriever, '_search_burmese_with_namespace') as mock_burmese_search:
                mock_burmese_search.return_value = [
                    {
                        "id": f"menu_{test_key}",
                        "content": f"Test menu item for {test_key}",
                        "metadata": {"category": "test"},
                        "score": 0.95
                    }
                ]
                
                result = await rag_retriever.process(state)
                
                assert len(result["rag_results"]) > 0, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["search_metadata"]["search_type"] == "adapted_sophisticated"
                assert result["search_metadata"]["language"] == "my"
                assert result["relevance_score"] > 0.0
    
    @pytest.mark.asyncio
    async def test_burmese_faq_search_variations(self, rag_retriever, sample_state):
        """Test Burmese FAQ search with various query patterns"""
        faq_search_queries = [
            "burmese_faq_hours",
            "burmese_faq_wifi",
            "burmese_faq_location",
            "burmese_faq_reservation",
            "burmese_faq_delivery",
            "burmese_faq_pets",
            "burmese_faq_payment"
        ]
        
        for test_key in faq_search_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["target_namespace"] = "faq"
            state["detected_language"] = "my"
            state["intent_confidence"] = 0.90
            
            # Mock vector search
            with patch.object(rag_retriever.vector_search, 'search') as mock_search:
                mock_search.return_value = [
                    {
                        "id": f"faq_{test_key}",
                        "content": f"Test FAQ answer for {test_key}",
                        "metadata": {"category": "test"},
                        "score": 0.92
                    }
                ]
                
                result = await rag_retriever.process(state)
                
                assert len(result["rag_results"]) > 0, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["search_metadata"]["target_namespace"] == "faq"
                assert result["detected_language"] == "my"
                assert result["relevance_score"] > 0.0
    
    @pytest.mark.asyncio
    async def test_burmese_job_search_variations(self, rag_retriever, sample_state):
        """Test Burmese job search with various query patterns"""
        job_search_queries = [
            "burmese_job_general",
            "burmese_job_waitress",
            "burmese_job_kitchen",
            "burmese_job_barista",
            "burmese_job_salary",
            "burmese_job_parttime",
            "burmese_job_apply"
        ]
        
        for test_key in job_search_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["target_namespace"] = "job_application"
            state["detected_language"] = "my"
            state["intent_confidence"] = 0.88
            
            # Mock vector search
            with patch.object(rag_retriever.vector_search, 'search') as mock_search:
                mock_search.return_value = [
                    {
                        "id": f"job_{test_key}",
                        "content": f"Test job info for {test_key}",
                        "metadata": {"category": "test"},
                        "score": 0.89
                    }
                ]
                
                result = await rag_retriever.process(state)
                
                assert len(result["rag_results"]) > 0, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["search_metadata"]["target_namespace"] == "job_application"
                assert result["detected_language"] == "my"
                assert result["relevance_score"] > 0.0
    
    @pytest.mark.asyncio
    async def test_burmese_complex_search_queries(self, rag_retriever, sample_state):
        """Test complex Burmese search queries"""
        complex_search_queries = [
            "burmese_complex_menu_price",
            "burmese_complex_hours_location",
            "burmese_complex_job_salary",
            "burmese_complex_delivery_hours",
            "burmese_complex_menu_recommend"
        ]
        
        for test_key in complex_search_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["target_namespace"] = "menu"  # Default to menu for complex queries
            state["detected_language"] = "my"
            state["intent_confidence"] = 0.85
            
            # Mock Burmese search for complex queries
            with patch.object(rag_retriever, '_search_burmese_with_namespace') as mock_burmese_search:
                mock_burmese_search.return_value = [
                    {
                        "id": f"complex_{test_key}",
                        "content": f"Complex search result for {test_key}",
                        "metadata": {"category": "complex"},
                        "score": 0.87
                    }
                ]
                
                result = await rag_retriever.process(state)
                
                assert len(result["rag_results"]) > 0, f"Failed for {test_key}: {TEST_USER_MESSAGES[test_key]}"
                assert result["search_metadata"]["search_type"] == "adapted_sophisticated"
                assert result["search_metadata"]["language"] == "my"
                assert result["relevance_score"] > 0.0
    
    @pytest.mark.asyncio
    async def test_burmese_low_confidence_handling(self, rag_retriever, sample_state):
        """Test handling of low confidence Burmese queries"""
        low_confidence_queries = [
            "burmese_ambiguous_what",
            "burmese_ambiguous_how",
            "burmese_slang_what",
            "burmese_edge_mixed_chars"
        ]
        
        for test_key in low_confidence_queries:
            state = sample_state.copy()
            state["user_message"] = TEST_USER_MESSAGES[test_key]
            state["target_namespace"] = "menu"
            state["detected_language"] = "my"
            state["intent_confidence"] = 0.25  # Low confidence
            
            result = await rag_retriever.process(state)
            
            # Low confidence queries should return empty results
            assert len(result["rag_results"]) == 0, f"Should return empty results for {test_key}"
            assert result["relevance_score"] == 0.0
            assert result["search_metadata"]["search_type"] == "namespace_based"


class TestBurmeseIntegration:
    """Integration tests for complete Burmese workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_burmese_menu_workflow(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for Burmese menu query"""
        from src.graph.state_graph import create_initial_state
        
        # Test with a complex Burmese menu query
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["burmese_complex_menu_price"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Mock Burmese menu analysis
        with patch('src.graph.nodes.intent_classifier.IntentClassifierNode._analyze_burmese_menu_request') as mock_analysis:
            mock_analysis.return_value = {
                "action": "MENU_BROWSE",
                "confidence": 0.95,
                "category": "complex"
            }
            
            # Mock vector search
            with patch('src.services.vector_search_service.VectorSearchService.search') as mock_search:
                mock_search.return_value = [
                    {
                        "id": "menu_complex",
                        "content": "ကော်ဖီတစ်ခွက် $3.50 နဲ့ နို့၊ သကြား ပါဝင်ပါတယ်",
                        "metadata": {"category": "beverages", "price": 3.50},
                        "score": 0.95
                    }
                ]
                
                # Act
                compiled_workflow = conversation_graph.compile()
                final_state = await compiled_workflow.ainvoke(initial_state)
                
                # Assert
                assert final_state["detected_language"] == "my"
                assert final_state["detected_intent"] == "menu_browse"
                assert final_state["target_namespace"] == "menu"
                assert len(final_state["rag_results"]) > 0
                assert final_state["response_generated"] is True
                assert len(final_state["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_complete_burmese_faq_workflow(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for Burmese FAQ query"""
        from src.graph.state_graph import create_initial_state
        
        # Test with a Burmese FAQ query
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["burmese_faq_hours"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Mock AI classifier response
        with patch('src.agents.intent_classifier.AIIntentClassifier.process') as mock_intent:
            mock_intent.return_value = {
                "detected_intents": [{"intent": "faq", "confidence": 0.90}],
                "primary_intent": "faq",
                "reasoning": "Burmese FAQ query about hours",
                "entities": {"question_type": "hours"}
            }
            
            # Mock vector search
            with patch('src.services.vector_search_service.VectorSearchService.search') as mock_search:
                mock_search.return_value = [
                    {
                        "id": "faq_hours",
                        "content": "ကျွန်ုပ်တို့သည် နံနက် ၇ နာရီမှ ည ၁၀ နာရီထိ ဖွင့်ပါသည်",
                        "metadata": {"category": "hours"},
                        "score": 0.92
                    }
                ]
                
                # Act
                compiled_workflow = conversation_graph.compile()
                final_state = await compiled_workflow.ainvoke(initial_state)
                
                # Assert
                assert final_state["detected_language"] == "my"
                assert final_state["detected_intent"] == "faq"
                assert final_state["target_namespace"] == "faq"
                assert len(final_state["rag_results"]) > 0
                assert final_state["response_generated"] is True
                assert len(final_state["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_burmese_edge_case_workflow(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for Burmese edge cases"""
        from src.graph.state_graph import create_initial_state
        
        # Test with a problematic Burmese query
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["burmese_edge_mixed_chars"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Act
        compiled_workflow = conversation_graph.compile()
        final_state = await compiled_workflow.ainvoke(initial_state)
        
        # Assert - should handle gracefully
        assert final_state["detected_language"] == "my"
        assert final_state["response_generated"] is True
        assert len(final_state["response"]) > 0
        # Edge cases might have low confidence or unknown intent
        assert final_state["intent_confidence"] <= 0.5 or final_state["detected_intent"] == "unknown" 