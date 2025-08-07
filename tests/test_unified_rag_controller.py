"""
Tests for Unified RAG Controller
Validates orchestration of namespace routing and enhanced vector search
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.controllers.unified_rag_controller import (
    get_unified_rag_controller,
    UnifiedRAGController,
    RAGRequest,
    RAGResponse
)
from src.services.intelligent_namespace_router import NamespaceRoute
from src.services.enhanced_vector_search_service import MultiNamespaceSearchResult, SearchResult


@pytest.fixture
def mock_unified_rag_controller():
    """Create a mock unified RAG controller for testing"""
    with patch('src.controllers.unified_rag_controller.get_intelligent_namespace_router'), \
         patch('src.controllers.unified_rag_controller.get_enhanced_vector_search_service'), \
         patch('src.controllers.unified_rag_controller.get_unified_prompt_controller'):
        return UnifiedRAGController()


@pytest.fixture
def sample_rag_request():
    """Create a sample RAG request for testing"""
    return RAGRequest(
        user_message="I want to see the menu and also ask about job opportunities",
        conversation_state={
            "user_message": "I want to see the menu and also ask about job opportunities",
            "detected_language": "en",
            "detected_intent": "menu_browse",
            "intent_confidence": 0.8,
            "secondary_intents": [
                {"intent": "job_application", "confidence": 0.6, "reasoning": "Job mention in query"}
            ],
            "cultural_context": {
                "formality_level": "casual",
                "language_mix": "english_only",
                "cultural_confidence": 0.9
            },
            "entity_extraction": {
                "food_items": [{"item": "pizza", "confidence": 0.8}],
                "extraction_confidence": 0.8
            },
            "conversation_history": [],
            "user_preferences": {}
        },
        user_preferences={},
        platform="messenger",
        request_id="test_request_001"
    )


@pytest.fixture
def sample_namespace_route():
    """Create a sample namespace route for testing"""
    return NamespaceRoute(
        primary_namespace="menu",
        primary_confidence=0.8,
        fallback_namespaces=[
            {"namespace": "jobs", "confidence": 0.6, "reasoning": "Secondary intent"}
        ],
        cross_domain_detected=True,
        routing_reasoning="Cross-domain query detected",
        search_strategy="multi",
        quality_score=0.85
    )


@pytest.fixture
def sample_search_result():
    """Create a sample search result for testing"""
    return SearchResult(
        content="Delicious pizza with fresh ingredients",
        metadata={"content": "Delicious pizza with fresh ingredients", "category": "main_course"},
        namespace="menu",
        relevance_score=0.85,
        confidence_score=0.8,
        source_type="menu_item",
        cultural_relevance=0.7,
        language_match=0.9,
        context_alignment=0.8
    )


@pytest.fixture
def sample_multi_namespace_search_result(sample_search_result):
    """Create a sample multi-namespace search result for testing"""
    return MultiNamespaceSearchResult(
        primary_results=[sample_search_result],
        fallback_results=[],
        cross_domain_results=[],
        overall_relevance_score=0.85,
        search_strategy="multi",
        namespace_coverage={"menu": 1},
        quality_metrics={
            "avg_relevance": 0.85,
            "avg_confidence": 0.8,
            "cultural_alignment": 0.7,
            "language_alignment": 0.9,
            "context_alignment": 0.8,
            "diversity_score": 0.25
        }
    )


class TestUnifiedRAGController:
    """Test cases for Unified RAG Controller"""
    
    def test_controller_initialization(self, mock_unified_rag_controller):
        """Test controller initialization with proper services"""
        controller = mock_unified_rag_controller
        assert controller.settings is not None
        assert controller.namespace_router is not None
        assert controller.vector_search_service is not None
        assert controller.unified_prompt_controller is not None
        assert controller.request_count == 0
        assert controller.avg_processing_time == 0.0
    
    def test_create_search_context_from_analysis(self, mock_unified_rag_controller):
        """Test search context creation from analysis state"""
        analysis_state = {
            "user_message": "Show me the menu",
            "detected_language": "en",
            "detected_intent": "menu_browse",
            "intent_confidence": 0.9,
            "secondary_intents": [],
            "cultural_context": {"formality_level": "casual"},
            "entity_extraction": {"food_items": []},
            "conversation_history": [],
            "user_preferences": {}
        }
        
        context = mock_unified_rag_controller._create_search_context_from_analysis(analysis_state)
        
        assert context.user_message == "Show me the menu"
        assert context.detected_language == "en"
        assert context.primary_intent == "menu_browse"
        assert context.intent_confidence == 0.9
    
    def test_extract_previous_namespaces(self, mock_unified_rag_controller):
        """Test extraction of previous namespaces from conversation history"""
        state = {
            "conversation_history": [
                {"role": "assistant", "metadata": {"target_namespace": "menu"}},
                {"role": "user", "content": "hello"},
                {"role": "assistant", "metadata": {"target_namespace": "faq"}},
                {"role": "assistant", "metadata": {"target_namespace": "menu"}}  # Duplicate
            ]
        }
        
        previous_namespaces = mock_unified_rag_controller._extract_previous_namespaces(state)
        
        assert isinstance(previous_namespaces, list)
        assert "menu" in previous_namespaces
        assert "faq" in previous_namespaces
        assert len(previous_namespaces) == 2  # Duplicates removed
    
    def test_calculate_overall_quality_score(self, mock_unified_rag_controller, 
                                           sample_multi_namespace_search_result, 
                                           sample_namespace_route):
        """Test overall quality score calculation"""
        analysis_state = {
            "analysis_confidence": 0.8,
            "cultural_context": {"cultural_confidence": 0.9}
        }
        
        quality_score = mock_unified_rag_controller._calculate_overall_quality_score(
            sample_multi_namespace_search_result, sample_namespace_route, analysis_state
        )
        
        assert 0.0 <= quality_score <= 1.0
        assert isinstance(quality_score, float)
    
    def test_generate_recommendations(self, mock_unified_rag_controller, 
                                    sample_multi_namespace_search_result, 
                                    sample_namespace_route):
        """Test recommendation generation"""
        analysis_state = {
            "cultural_context": {"cultural_confidence": 0.9}
        }
        
        recommendations = mock_unified_rag_controller._generate_recommendations(
            sample_multi_namespace_search_result, sample_namespace_route, analysis_state
        )
        
        assert isinstance(recommendations, list)
        # Should have cross-domain recommendation
        assert any("cross-domain" in rec.lower() for rec in recommendations)
    
    def test_update_performance_metrics(self, mock_unified_rag_controller):
        """Test performance metrics update"""
        controller = mock_unified_rag_controller
        
        # First update
        controller._update_performance_metrics(1.5)
        assert controller.request_count == 1
        assert controller.avg_processing_time == 1.5
        
        # Second update
        controller._update_performance_metrics(2.5)
        assert controller.request_count == 2
        assert controller.avg_processing_time == 2.0  # Average of 1.5 and 2.5
    
    @pytest.mark.asyncio
    async def test_create_fallback_response(self, mock_unified_rag_controller, sample_rag_request):
        """Test fallback response creation"""
        start_time = 100.0
        
        response = await mock_unified_rag_controller._create_fallback_response(sample_rag_request, start_time)
        
        assert isinstance(response, RAGResponse)
        assert len(response.primary_results) > 0
        assert response.quality_score == 0.3
        assert "fallback" in response.recommendations[0].lower()
        assert response.response_guidance["tone"] == "apologetic"
    
    @pytest.mark.asyncio
    async def test_get_rag_statistics(self, mock_unified_rag_controller):
        """Test RAG statistics retrieval"""
        controller = mock_unified_rag_controller
        controller.request_count = 5
        controller.avg_processing_time = 1.2
        
        stats = await controller.get_rag_statistics()
        
        assert stats["total_requests"] == 5
        assert stats["avg_processing_time"] == 1.2
        assert stats["system_status"] == "operational"
        assert "namespace_router" in stats["services"]
        assert "vector_search_service" in stats["services"]
        assert "unified_prompt_controller" in stats["services"]
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_unified_rag_controller):
        """Test health check functionality"""
        controller = mock_unified_rag_controller
        
        health_status = await controller.health_check()
        
        assert "status" in health_status
        assert "timestamp" in health_status
        assert "services" in health_status
        assert isinstance(health_status["services"], dict)
    
    @pytest.mark.asyncio
    async def test_process_rag_request_success(self, mock_unified_rag_controller, 
                                             sample_rag_request, 
                                             sample_namespace_route, 
                                             sample_multi_namespace_search_result):
        """Test successful RAG request processing"""
        controller = mock_unified_rag_controller
        
        # Mock the unified prompt controller
        mock_analysis_state = {
            "user_message": "I want to see the menu and also ask about job opportunities",
            "detected_language": "en",
            "detected_intent": "menu_browse",
            "intent_confidence": 0.8,
            "secondary_intents": [],
            "cultural_context": {"cultural_confidence": 0.9},
            "entity_extraction": {},
            "conversation_history": [],
            "user_preferences": {},
            "response_guidance": {"tone": "friendly", "language": "en"},
            "analysis_confidence": 0.8
        }
        controller.unified_prompt_controller.process_query = AsyncMock(return_value=mock_analysis_state)
        
        # Mock the namespace router
        controller.namespace_router.route_namespaces = AsyncMock(return_value=sample_namespace_route)
        
        # Mock the vector search service
        controller.vector_search_service.search_with_intelligent_routing = AsyncMock(
            return_value=sample_multi_namespace_search_result
        )
        
        response = await controller.process_rag_request(sample_rag_request)
        
        assert isinstance(response, RAGResponse)
        assert len(response.primary_results) > 0
        assert response.namespace_route == sample_namespace_route
        assert response.processing_time > 0
        assert 0.0 <= response.quality_score <= 1.0
        assert isinstance(response.recommendations, list)
        assert controller.request_count == 1
    
    @pytest.mark.asyncio
    async def test_process_rag_request_failure(self, mock_unified_rag_controller, sample_rag_request):
        """Test RAG request processing with failure"""
        controller = mock_unified_rag_controller
        
        # Mock the unified prompt controller to raise an exception
        controller.unified_prompt_controller.process_query = AsyncMock(side_effect=Exception("Test error"))
        
        response = await controller.process_rag_request(sample_rag_request)
        
        assert isinstance(response, RAGResponse)
        assert len(response.primary_results) > 0
        assert response.quality_score == 0.3
        assert "fallback" in response.recommendations[0].lower()
        assert response.response_guidance["tone"] == "apologetic"
    
    def test_quality_score_calculation_edge_cases(self, mock_unified_rag_controller):
        """Test quality score calculation with edge cases"""
        controller = mock_unified_rag_controller
        
        # Test with no primary results
        empty_search_results = MultiNamespaceSearchResult(
            primary_results=[],
            fallback_results=[],
            cross_domain_results=[],
            overall_relevance_score=0.5,
            search_strategy="single",
            namespace_coverage={},
            quality_metrics={}
        )
        
        namespace_route = NamespaceRoute(
            primary_namespace="faq",
            primary_confidence=0.5,
            fallback_namespaces=[],
            cross_domain_detected=False,
            routing_reasoning="Test",
            search_strategy="single",
            quality_score=0.5
        )
        
        analysis_state = {
            "analysis_confidence": 0.5,
            "cultural_context": {"cultural_confidence": 0.5}
        }
        
        quality_score = controller._calculate_overall_quality_score(
            empty_search_results, namespace_route, analysis_state
        )
        
        assert 0.0 <= quality_score <= 1.0
        assert isinstance(quality_score, float)
    
    def test_recommendations_edge_cases(self, mock_unified_rag_controller):
        """Test recommendation generation with edge cases"""
        controller = mock_unified_rag_controller
        
        # Test with low quality metrics
        low_quality_search_results = MultiNamespaceSearchResult(
            primary_results=[],
            fallback_results=[],
            cross_domain_results=[],
            overall_relevance_score=0.3,  # Low relevance
            search_strategy="single",
            namespace_coverage={},
            quality_metrics={}
        )
        
        low_quality_route = NamespaceRoute(
            primary_namespace="faq",
            primary_confidence=0.3,
            fallback_namespaces=[],
            cross_domain_detected=False,
            routing_reasoning="Test",
            search_strategy="single",
            quality_score=0.3  # Low quality
        )
        
        analysis_state = {
            "cultural_context": {"cultural_confidence": 0.3}  # Low confidence
        }
        
        recommendations = controller._generate_recommendations(
            low_quality_search_results, low_quality_route, analysis_state
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0  # Should have recommendations for low quality


class TestGlobalAccess:
    """Test global access to unified RAG controller"""
    
    def test_get_unified_rag_controller(self):
        """Test global instance access"""
        with patch('src.controllers.unified_rag_controller.get_intelligent_namespace_router'), \
             patch('src.controllers.unified_rag_controller.get_enhanced_vector_search_service'), \
             patch('src.controllers.unified_rag_controller.get_unified_prompt_controller'):
            
            controller1 = get_unified_rag_controller()
            controller2 = get_unified_rag_controller()
            
            assert controller1 is controller2  # Singleton pattern
            assert isinstance(controller1, UnifiedRAGController)


class TestRAGRequestResponse:
    """Test RAG request and response dataclasses"""
    
    def test_rag_request_creation(self):
        """Test RAG request dataclass creation"""
        request = RAGRequest(
            user_message="Test message",
            conversation_state={"test": "data"},
            user_preferences={"language": "en"},
            platform="messenger",
            request_id="test_001"
        )
        
        assert request.user_message == "Test message"
        assert request.conversation_state == {"test": "data"}
        assert request.user_preferences == {"language": "en"}
        assert request.platform == "messenger"
        assert request.request_id == "test_001"
    
    def test_rag_response_creation(self, sample_search_result, sample_namespace_route):
        """Test RAG response dataclass creation"""
        response = RAGResponse(
            primary_results=[sample_search_result],
            fallback_results=[],
            cross_domain_results=[],
            namespace_route=sample_namespace_route,
            search_metrics={"test": "metrics"},
            response_guidance={"tone": "friendly"},
            processing_time=1.5,
            quality_score=0.8,
            recommendations=["Test recommendation"]
        )
        
        assert len(response.primary_results) == 1
        assert response.namespace_route == sample_namespace_route
        assert response.processing_time == 1.5
        assert response.quality_score == 0.8
        assert len(response.recommendations) == 1
