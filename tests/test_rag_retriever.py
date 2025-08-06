"""
Unit tests for RAG Retriever Node
Tests vector search, document retrieval, and namespace-based routing
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.nodes.rag_retriever import RAGRetrieverNode
from tests.conftest import TEST_USER_MESSAGES, TEST_RAG_RESULTS


class TestRAGRetrieverNode:
    """Test suite for RAG Retriever Node"""
    
    @pytest.fixture
    def rag_retriever(self, mock_pinecone):
        """Initialize RAG retriever node with mocked Pinecone"""
        return RAGRetrieverNode()
    
    @pytest.mark.asyncio
    async def test_menu_namespace_search(self, rag_retriever, sample_state):
        """Test menu namespace search"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        
        # Mock vector search response
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["menu"]
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 2
            assert result["relevance_score"] == 0.9
            assert result["search_metadata"]["search_type"] == "namespace_based"
            assert result["search_metadata"]["target_namespace"] == "menu"
            assert result["retrieved_count"] == 2
    
    @pytest.mark.asyncio
    async def test_faq_namespace_search(self, rag_retriever, sample_state):
        """Test FAQ namespace search"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_faq"]
        state["target_namespace"] = "faq"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.92
        
        # Mock vector search response
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["faq"]
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 1
            assert result["relevance_score"] == 0.9
            assert result["search_metadata"]["target_namespace"] == "faq"
    
    @pytest.mark.asyncio
    async def test_job_namespace_search(self, rag_retriever, sample_state):
        """Test job application namespace search"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_job"]
        state["target_namespace"] = "job_application"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.88
        
        # Mock vector search response
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["jobs"]
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 1
            assert result["relevance_score"] == 0.9
            assert result["search_metadata"]["target_namespace"] == "job_application"
    
    @pytest.mark.asyncio
    async def test_burmese_menu_search(self, rag_retriever, sample_state):
        """Test Burmese menu search with sophisticated logic"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["burmese_menu"]
        state["target_namespace"] = "menu"
        state["detected_language"] = "my"
        state["intent_confidence"] = 0.95
        
        # Mock Burmese search
        with patch.object(rag_retriever, '_search_burmese_with_namespace') as mock_burmese_search:
            mock_burmese_search.return_value = TEST_RAG_RESULTS["menu"]
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 2
            assert result["search_metadata"]["search_type"] == "adapted_sophisticated"
            assert result["search_metadata"]["language"] == "my"
    
    @pytest.mark.asyncio
    async def test_low_confidence_skip_rag(self, rag_retriever, sample_state):
        """Test that RAG is skipped for low confidence intents"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "Some unclear message"
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.25  # Low confidence
        
        # Act
        result = await rag_retriever.process(state)
        
        # Assert
        assert len(result["rag_results"]) == 0
        assert result["relevance_score"] == 0.0
        assert result["search_metadata"]["search_type"] == "namespace_based"
    
    @pytest.mark.asyncio
    async def test_empty_namespace_handling(self, rag_retriever, sample_state):
        """Test handling of empty namespace"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        state["target_namespace"] = ""
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        
        # Act
        result = await rag_retriever.process(state)
        
        # Assert
        assert len(result["rag_results"]) == 0
        assert result["relevance_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, rag_retriever, sample_state):
        """Test handling of empty messages"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = ""
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        
        # Act
        result = await rag_retriever.process(state)
        
        # Assert
        assert len(result["rag_results"]) == 0
        assert result["relevance_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, rag_retriever, sample_state):
        """Test handling of search errors"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        
        # Mock search to raise exception
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.side_effect = Exception("Search failed")
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 0
            assert result["relevance_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_burmese_search_with_namespace(self, rag_retriever):
        """Test Burmese search with namespace routing"""
        # Arrange
        user_message = "ဘာတွေရှိလဲ"
        target_namespace = "menu"
        language = "my"
        
        # Mock the search method
        with patch.object(rag_retriever, '_search_menu_namespace') as mock_menu_search:
            mock_menu_search.return_value = {
                "documents": TEST_RAG_RESULTS["menu"],
                "total_results": 2,
                "search_time": 0.1
            }
            
            # Act
            result = await rag_retriever._search_burmese_with_namespace(user_message, target_namespace, language)
            
            # Assert
            assert len(result) == 2
            assert result[0]["id"] == "menu_1"
            assert result[1]["id"] == "menu_2"
    
    @pytest.mark.asyncio
    async def test_english_search_with_namespace(self, rag_retriever):
        """Test English search with namespace routing"""
        # Arrange
        user_message = "What's on your menu?"
        target_namespace = "menu"
        language = "en"
        
        # Mock vector search
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["menu"]
            
            # Act
            result = await rag_retriever._search_english_with_namespace(user_message, target_namespace, language)
            
            # Assert
            assert len(result) == 2
            assert result[0]["id"] == "menu_1"
            assert result[1]["id"] == "menu_2"
    
    @pytest.mark.asyncio
    async def test_menu_namespace_search_method(self, rag_retriever):
        """Test menu namespace search method"""
        # Arrange
        user_message = "What drinks do you have?"
        language = "en"
        conversation_history = []
        
        # Mock vector search
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["menu"]
            
            # Act
            result = await rag_retriever._search_menu_namespace(user_message, language, conversation_history)
            
            # Assert
            assert "documents" in result
            assert "total_results" in result
            assert "search_time" in result
            assert len(result["documents"]) == 2
    
    @pytest.mark.asyncio
    async def test_faq_namespace_search_method(self, rag_retriever):
        """Test FAQ namespace search method"""
        # Arrange
        user_message = "What are your opening hours?"
        language = "en"
        
        # Mock vector search
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["faq"]
            
            # Act
            result = await rag_retriever._search_faq_namespace(user_message, language)
            
            # Assert
            assert "documents" in result
            assert "total_results" in result
            assert "search_time" in result
            assert len(result["documents"]) == 1
    
    @pytest.mark.asyncio
    async def test_job_namespace_search_method(self, rag_retriever):
        """Test job namespace search method"""
        # Arrange
        user_message = "Do you have any job openings?"
        language = "en"
        
        # Mock vector search
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["jobs"]
            
            # Act
            result = await rag_retriever._search_job_namespace(user_message, language)
            
            # Assert
            assert "documents" in result
            assert "total_results" in result
            assert "search_time" in result
            assert len(result["documents"]) == 1
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, rag_retriever, sample_state):
        """Test handling of empty search results"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        
        # Mock empty search response
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = []
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 0
            assert result["relevance_score"] == 0.0
            assert result["retrieved_count"] == 0
    
    @pytest.mark.asyncio
    async def test_search_metadata_population(self, rag_retriever, sample_state):
        """Test that search metadata is properly populated"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = TEST_USER_MESSAGES["english_menu"]
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        
        # Mock vector search response
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["menu"]
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            metadata = result["search_metadata"]
            assert metadata["search_type"] == "namespace_based"
            assert metadata["language"] == "en"
            assert metadata["total_results"] == 2
            assert metadata["target_namespace"] == "menu"
            assert result["search_query"] == TEST_USER_MESSAGES["english_menu"]
            assert result["search_namespace"] == "menu"
    
    def test_set_empty_results(self, rag_retriever, sample_state):
        """Test setting empty results"""
        # Arrange
        state = sample_state.copy()
        
        # Act
        result = rag_retriever._set_empty_results(state)
        
        # Assert
        assert result["rag_results"] == []
        assert result["relevance_score"] == 0.0
        assert result["search_metadata"]["search_type"] == "namespace_based"
        assert result["retrieved_count"] == 0
        assert result["search_query"] == ""
        assert result["search_namespace"] == ""
    
    @pytest.mark.asyncio
    async def test_conversation_history_integration(self, rag_retriever, sample_state):
        """Test integration with conversation history"""
        # Arrange
        state = sample_state.copy()
        state["user_message"] = "What about coffee?"
        state["target_namespace"] = "menu"
        state["detected_language"] = "en"
        state["intent_confidence"] = 0.95
        state["conversation_history"] = [
            {"role": "user", "content": "What drinks do you have?"},
            {"role": "assistant", "content": "We have coffee, tea, and soft drinks."}
        ]
        
        # Mock vector search
        with patch.object(rag_retriever.vector_search, 'search') as mock_search:
            mock_search.return_value = TEST_RAG_RESULTS["menu"]
            
            # Act
            result = await rag_retriever.process(state)
            
            # Assert
            assert len(result["rag_results"]) == 2
            assert result["relevance_score"] == 0.9 