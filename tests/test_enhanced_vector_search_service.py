"""
Tests for Enhanced Vector Search Service
Validates multi-namespace retrieval with relevance scoring and context-aware search
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.enhanced_vector_search_service import (
    get_enhanced_vector_search_service,
    EnhancedVectorSearchService,
    SearchResult,
    MultiNamespaceSearchResult
)
from src.services.intelligent_namespace_router import SearchContext, NamespaceRoute


@pytest.fixture
def mock_enhanced_vector_search_service():
    """Create a mock enhanced vector search service for testing"""
    with patch('src.services.enhanced_vector_search_service.OpenAIEmbeddings'), \
         patch('src.services.enhanced_vector_search_service.ChatOpenAI'), \
         patch('pinecone.Pinecone'):
        return EnhancedVectorSearchService()


@pytest.fixture
def sample_search_context():
    """Create a sample search context for testing"""
    return SearchContext(
        user_message="I want to see the menu and also ask about job opportunities",
        detected_language="en",
        primary_intent="menu_browse",
        intent_confidence=0.8,
        secondary_intents=[
            {"intent": "job_application", "confidence": 0.6, "reasoning": "Job mention in query"}
        ],
        cultural_context={
            "formality_level": "casual",
            "language_mix": "english_only",
            "cultural_confidence": 0.9
        },
        entity_extraction={
            "food_items": [{"item": "pizza", "confidence": 0.8}],
            "extraction_confidence": 0.8
        },
        conversation_history=[],
        previous_namespaces=["menu"],
        user_preferences={}
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


class TestEnhancedVectorSearchService:
    """Test cases for Enhanced Vector Search Service"""
    
    def test_service_initialization(self, mock_enhanced_vector_search_service):
        """Test service initialization with proper configuration"""
        service = mock_enhanced_vector_search_service
        assert service.settings is not None
        assert service.embeddings is not None
        assert service.llm is not None
        assert service.api_client is not None
        assert service.fallback_manager is not None
        assert service.namespace_router is not None
        assert service.pinecone_index is not None
        assert service.search_config is not None
    
    def test_search_config_initialization(self, mock_enhanced_vector_search_service):
        """Test search configuration is properly initialized"""
        config = mock_enhanced_vector_search_service.search_config
        assert "max_results_per_namespace" in config
        assert "min_relevance_threshold" in config
        assert "context_window_size" in config
        assert "cultural_boost_factor" in config
        assert "language_boost_factor" in config
        assert "cross_domain_penalty" in config
        
        # Validate reasonable values
        assert config["max_results_per_namespace"] > 0
        assert 0 <= config["min_relevance_threshold"] <= 1
        assert config["context_window_size"] > 0
        assert config["cultural_boost_factor"] > 1.0
        assert config["language_boost_factor"] > 1.0
        assert 0 < config["cross_domain_penalty"] < 1.0
    
    def test_create_search_context(self, mock_enhanced_vector_search_service):
        """Test search context creation from state"""
        state = {
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
        
        context = mock_enhanced_vector_search_service._create_search_context(state)
        
        assert isinstance(context, SearchContext)
        assert context.user_message == "Show me the menu"
        assert context.detected_language == "en"
        assert context.primary_intent == "menu_browse"
        assert context.intent_confidence == 0.9
    
    def test_extract_previous_namespaces(self, mock_enhanced_vector_search_service):
        """Test extraction of previous namespaces from conversation history"""
        state = {
            "conversation_history": [
                {"role": "assistant", "metadata": {"target_namespace": "menu"}},
                {"role": "user", "content": "hello"},
                {"role": "assistant", "metadata": {"target_namespace": "faq"}},
                {"role": "assistant", "metadata": {"target_namespace": "menu"}}  # Duplicate
            ]
        }
        
        previous_namespaces = mock_enhanced_vector_search_service._extract_previous_namespaces(state)
        
        assert isinstance(previous_namespaces, list)
        assert "menu" in previous_namespaces
        assert "faq" in previous_namespaces
        assert len(previous_namespaces) == 2  # Duplicates removed
    
    def test_extract_entity_context(self, mock_enhanced_vector_search_service):
        """Test entity context extraction"""
        entity_extraction = {
            "food_items": [
                {"item": "pizza", "confidence": 0.8},
                {"item": "burger", "confidence": 0.7},
                {"item": "salad", "confidence": 0.6}
            ],
            "locations": [{"location": "downtown"}],
            "time_references": [{"time": "tonight"}]
        }
        
        context = mock_enhanced_vector_search_service._extract_entity_context(entity_extraction)
        
        assert "pizza" in context
        assert "burger" in context
        assert "salad" in context
        assert "downtown" in context
        assert "tonight" in context
    
    def test_extract_cultural_context(self, mock_enhanced_vector_search_service):
        """Test cultural context extraction"""
        cultural_context = {
            "language_mix": "burmese_only",
            "formality_level": "formal",
            "honorifics_detected": ["ဦး", "ဒေါ်"]
        }
        
        context = mock_enhanced_vector_search_service._extract_cultural_context(cultural_context, "menu")
        
        assert "burmese language" in context
        assert "formal tone" in context
        assert "honorifics" in context
    
    def test_extract_conversation_context(self, mock_enhanced_vector_search_service):
        """Test conversation context extraction"""
        conversation_history = [
            {"role": "user", "content": "Show me the menu"},
            {"role": "assistant", "content": "Here's our menu"},
            {"role": "user", "content": "What about pizza?"},
            {"role": "assistant", "content": "We have pizza"},
            {"role": "user", "content": "Tell me about the pizza"}
        ]
        
        context = mock_enhanced_vector_search_service._extract_conversation_context(conversation_history)
        
        assert "pizza" in context
        assert len(context) > 0
    
    def test_calculate_confidence_score(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test confidence score calculation"""
        mock_match = Mock()
        mock_match.score = 0.8
        mock_match.metadata = {"content": "pizza with fresh ingredients"}
        
        confidence = mock_enhanced_vector_search_service._calculate_confidence_score(mock_match, sample_search_context)
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
    
    def test_calculate_entity_match_boost(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test entity match boost calculation"""
        mock_match = Mock()
        mock_match.metadata = {"content": "delicious pizza with fresh ingredients"}
        
        boost = mock_enhanced_vector_search_service._calculate_entity_match_boost(mock_match, sample_search_context)
        
        assert 0.0 <= boost <= 0.3  # Capped at 0.3
        assert isinstance(boost, float)
    
    def test_calculate_intent_alignment_boost(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test intent alignment boost calculation"""
        mock_match = Mock()
        mock_match.metadata = {"content": "menu items and food options"}
        
        boost = mock_enhanced_vector_search_service._calculate_intent_alignment_boost(mock_match, sample_search_context)
        
        assert 0.0 <= boost <= 0.2  # Capped at 0.2
        assert isinstance(boost, float)
    
    def test_calculate_cultural_relevance(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test cultural relevance calculation"""
        mock_match = Mock()
        mock_match.metadata = {"content": "အစားအသောက်များ နှင့် စျေးနှုန်းများ"}
        
        relevance = mock_enhanced_vector_search_service._calculate_cultural_relevance(mock_match, sample_search_context)
        
        assert 0.0 <= relevance <= 1.0
        assert isinstance(relevance, float)
    
    def test_calculate_language_match(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test language match calculation"""
        mock_match = Mock()
        mock_match.metadata = {"content": "English content"}
        
        match_score = mock_enhanced_vector_search_service._calculate_language_match(mock_match, sample_search_context)
        
        assert 0.0 <= match_score <= 1.0
        assert isinstance(match_score, float)
    
    def test_calculate_context_alignment(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test context alignment calculation"""
        mock_match = Mock()
        mock_match.metadata = {"content": "pizza menu items"}
        
        # Add conversation history to context
        sample_search_context.conversation_history = [
            {"role": "user", "content": "Show me pizza options"}
        ]
        
        alignment = mock_enhanced_vector_search_service._calculate_context_alignment(mock_match, sample_search_context)
        
        assert 0.0 <= alignment <= 1.0
        assert isinstance(alignment, float)
    
    def test_calculate_enhanced_relevance(self, mock_enhanced_vector_search_service):
        """Test enhanced relevance calculation"""
        relevance = mock_enhanced_vector_search_service._calculate_enhanced_relevance(
            base_relevance=0.8,
            confidence=0.7,
            cultural_relevance=0.6,
            language_match=0.9,
            context_alignment=0.8,
            is_primary=True
        )
        
        assert 0.0 <= relevance <= 1.0
        assert isinstance(relevance, float)
    
    def test_determine_source_type(self, mock_enhanced_vector_search_service):
        """Test source type determination"""
        mock_match = Mock()
        mock_match.metadata = {}
        
        # Test different namespaces
        assert mock_enhanced_vector_search_service._determine_source_type(mock_match, "menu") == "menu_item"
        assert mock_enhanced_vector_search_service._determine_source_type(mock_match, "jobs") == "job_posting"
        assert mock_enhanced_vector_search_service._determine_source_type(mock_match, "events") == "event"
        assert mock_enhanced_vector_search_service._determine_source_type(mock_match, "faq") == "faq"
    
    def test_identify_cross_domain_results(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test cross-domain result identification"""
        primary_results = [
            SearchResult(
                content="Menu items with food and event information",
                metadata={},
                namespace="menu",
                relevance_score=0.8,
                confidence_score=0.7,
                source_type="menu_item",
                cultural_relevance=0.6,
                language_match=0.8,
                context_alignment=0.7
            )
        ]
        fallback_results = []
        
        cross_domain = mock_enhanced_vector_search_service._identify_cross_domain_results(
            primary_results, fallback_results, sample_search_context
        )
        
        assert isinstance(cross_domain, list)
    
    def test_calculate_overall_relevance(self, mock_enhanced_vector_search_service):
        """Test overall relevance calculation"""
        primary_results = [
            SearchResult(
                content="Test content",
                metadata={},
                namespace="menu",
                relevance_score=0.8,
                confidence_score=0.7,
                source_type="menu_item",
                cultural_relevance=0.6,
                language_match=0.8,
                context_alignment=0.7
            )
        ]
        fallback_results = []
        cross_domain_results = []
        
        overall_relevance = mock_enhanced_vector_search_service._calculate_overall_relevance(
            primary_results, fallback_results, cross_domain_results
        )
        
        assert 0.0 <= overall_relevance <= 1.0
        assert isinstance(overall_relevance, float)
    
    def test_calculate_namespace_coverage(self, mock_enhanced_vector_search_service):
        """Test namespace coverage calculation"""
        primary_results = [
            SearchResult(
                content="Menu item",
                metadata={},
                namespace="menu",
                relevance_score=0.8,
                confidence_score=0.7,
                source_type="menu_item",
                cultural_relevance=0.6,
                language_match=0.8,
                context_alignment=0.7
            )
        ]
        fallback_results = [
            SearchResult(
                content="FAQ item",
                metadata={},
                namespace="faq",
                relevance_score=0.7,
                confidence_score=0.6,
                source_type="faq",
                cultural_relevance=0.5,
                language_match=0.7,
                context_alignment=0.6
            )
        ]
        
        coverage = mock_enhanced_vector_search_service._calculate_namespace_coverage(primary_results, fallback_results)
        
        assert isinstance(coverage, dict)
        assert "menu" in coverage
        assert "faq" in coverage
        assert coverage["menu"] == 1
        assert coverage["faq"] == 1
    
    def test_calculate_quality_metrics(self, mock_enhanced_vector_search_service):
        """Test quality metrics calculation"""
        primary_results = [
            SearchResult(
                content="Test content",
                metadata={},
                namespace="menu",
                relevance_score=0.8,
                confidence_score=0.7,
                source_type="menu_item",
                cultural_relevance=0.6,
                language_match=0.8,
                context_alignment=0.7
            )
        ]
        fallback_results = []
        cross_domain_results = []
        
        metrics = mock_enhanced_vector_search_service._calculate_quality_metrics(
            primary_results, fallback_results, cross_domain_results
        )
        
        assert isinstance(metrics, dict)
        assert "avg_relevance" in metrics
        assert "avg_confidence" in metrics
        assert "cultural_alignment" in metrics
        assert "language_alignment" in metrics
        assert "context_alignment" in metrics
        assert "diversity_score" in metrics
        
        for value in metrics.values():
            assert 0.0 <= value <= 1.0
            assert isinstance(value, float)
    
    @pytest.mark.asyncio
    async def test_perform_multi_namespace_search(self, mock_enhanced_vector_search_service, 
                                                sample_search_context, sample_namespace_route):
        """Test multi-namespace search performance"""
        # Mock the namespace search method
        mock_enhanced_vector_search_service._search_namespace = AsyncMock(return_value=[])
        
        result = await mock_enhanced_vector_search_service._perform_multi_namespace_search(
            sample_search_context, sample_namespace_route
        )
        
        assert isinstance(result, MultiNamespaceSearchResult)
        assert result.search_strategy == "multi"
        assert isinstance(result.primary_results, list)
        assert isinstance(result.fallback_results, list)
        assert isinstance(result.cross_domain_results, list)
        assert 0.0 <= result.overall_relevance_score <= 1.0
        assert isinstance(result.namespace_coverage, dict)
        assert isinstance(result.quality_metrics, dict)
    
    @pytest.mark.asyncio
    async def test_perform_hybrid_search(self, mock_enhanced_vector_search_service, 
                                       sample_search_context, sample_namespace_route):
        """Test hybrid search performance"""
        # Mock the namespace search method
        mock_enhanced_vector_search_service._search_namespace = AsyncMock(return_value=[])
        
        result = await mock_enhanced_vector_search_service._perform_hybrid_search(
            sample_search_context, sample_namespace_route
        )
        
        assert isinstance(result, MultiNamespaceSearchResult)
        assert result.search_strategy == "hybrid"
    
    @pytest.mark.asyncio
    async def test_perform_single_namespace_search(self, mock_enhanced_vector_search_service, 
                                                 sample_search_context, sample_namespace_route):
        """Test single namespace search performance"""
        # Mock the namespace search method
        mock_enhanced_vector_search_service._search_namespace = AsyncMock(return_value=[])
        
        result = await mock_enhanced_vector_search_service._perform_single_namespace_search(
            sample_search_context, sample_namespace_route
        )
        
        assert isinstance(result, MultiNamespaceSearchResult)
        assert result.search_strategy == "single"
    
    @pytest.mark.asyncio
    async def test_search_with_intelligent_routing(self, mock_enhanced_vector_search_service, sample_search_context):
        """Test complete search with intelligent routing"""
        # Mock the namespace router
        mock_route = NamespaceRoute(
            primary_namespace="menu",
            primary_confidence=0.8,
            fallback_namespaces=[],
            cross_domain_detected=False,
            routing_reasoning="Test routing",
            search_strategy="single",
            quality_score=0.8
        )
        mock_enhanced_vector_search_service.namespace_router.route_namespaces = AsyncMock(return_value=mock_route)
        
        # Mock the search methods
        mock_enhanced_vector_search_service._perform_single_namespace_search = AsyncMock(
            return_value=MultiNamespaceSearchResult(
                primary_results=[],
                fallback_results=[],
                cross_domain_results=[],
                overall_relevance_score=0.8,
                search_strategy="single",
                namespace_coverage={},
                quality_metrics={}
            )
        )
        
        state = {
            "user_message": "Show me the menu",
            "detected_language": "en",
            "detected_intent": "menu_browse",
            "intent_confidence": 0.9,
            "secondary_intents": [],
            "cultural_context": {},
            "entity_extraction": {},
            "conversation_history": [],
            "user_preferences": {}
        }
        
        result = await mock_enhanced_vector_search_service.search_with_intelligent_routing(state)
        
        assert isinstance(result, MultiNamespaceSearchResult)
        assert result.search_strategy == "single"


class TestGlobalAccess:
    """Test global access to enhanced vector search service"""
    
    def test_get_enhanced_vector_search_service(self):
        """Test global instance access"""
        with patch('src.services.enhanced_vector_search_service.OpenAIEmbeddings'), \
             patch('src.services.enhanced_vector_search_service.ChatOpenAI'), \
             patch('pinecone.Pinecone'):
            
            service1 = get_enhanced_vector_search_service()
            service2 = get_enhanced_vector_search_service()
            
            assert service1 is service2  # Singleton pattern
            assert isinstance(service1, EnhancedVectorSearchService)
