"""
Tests for Intelligent Namespace Router
Validates dynamic namespace selection and cross-domain query handling
"""

import pytest
from unittest.mock import Mock, patch
from src.services.intelligent_namespace_router import (
    get_intelligent_namespace_router,
    IntelligentNamespaceRouter,
    SearchContext,
    NamespaceRoute
)


@pytest.fixture
def mock_namespace_router():
    """Create a mock namespace router for testing"""
    return IntelligentNamespaceRouter()


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


class TestIntelligentNamespaceRouter:
    """Test cases for Intelligent Namespace Router"""
    
    def test_router_initialization(self, mock_namespace_router):
        """Test router initialization with proper configuration"""
        assert mock_namespace_router.available_namespaces is not None
        assert mock_namespace_router.namespace_weights is not None
        assert mock_namespace_router.cross_domain_patterns is not None
        assert mock_namespace_router.confidence_thresholds is not None
    
    def test_namespace_weights_initialization(self, mock_namespace_router):
        """Test namespace weights are properly initialized"""
        weights = mock_namespace_router.namespace_weights
        assert "faq" in weights
        assert "menu" in weights
        assert "jobs" in weights
        assert "events" in weights
        assert all(0 <= weight <= 1 for weight in weights.values())
    
    def test_cross_domain_patterns_initialization(self, mock_namespace_router):
        """Test cross-domain patterns are properly initialized"""
        patterns = mock_namespace_router.cross_domain_patterns
        assert "menu_faq" in patterns
        assert "events_menu" in patterns
        assert "jobs_faq" in patterns
        assert all(isinstance(keywords, list) for keywords in patterns.values())
    
    def test_intent_to_namespace_mapping(self, mock_namespace_router):
        """Test intent to namespace mapping"""
        mapping_tests = [
            ("menu_browse", "menu"),
            ("order_place", "menu"),
            ("faq", "faq"),
            ("job_application", "jobs"),
            ("events", "events"),
            ("unknown", "faq")
        ]
        
        for intent, expected_namespace in mapping_tests:
            result = mock_namespace_router._map_intent_to_namespace(intent)
            assert result == expected_namespace
    
    def test_entity_based_namespace_selection(self, mock_namespace_router):
        """Test namespace selection based on extracted entities (simplified)"""
        # Test food items -> menu
        food_entities = {
            "food_items": [{"item": "pizza"}],
            "locations": [],
            "time_references": []
        }
        result = mock_namespace_router._get_entity_based_namespace(food_entities)
        assert result == "menu"
        
        # Test no food items -> faq (default)
        no_food_entities = {
            "food_items": [],
            "locations": [{"location": "job center"}],
            "time_references": []
        }
        result = mock_namespace_router._get_entity_based_namespace(no_food_entities)
        assert result == "faq"
        
        # Test event-related time -> faq (default)
        event_entities = {
            "food_items": [],
            "locations": [],
            "time_references": [{"time": "event tomorrow"}]
        }
        result = mock_namespace_router._get_entity_based_namespace(event_entities)
        assert result == "faq"
    
    def test_cultural_based_namespace_selection(self, mock_namespace_router):
        """Test namespace selection based on cultural context"""
        # Test formal queries -> FAQ
        formal_context = {
            "formality_level": "formal",
            "language_mix": "english_only"
        }
        result = mock_namespace_router._get_cultural_based_namespace(formal_context)
        assert result == "faq"
        
        # Test Burmese language -> menu
        burmese_context = {
            "formality_level": "casual",
            "language_mix": "burmese_only"
        }
        result = mock_namespace_router._get_cultural_based_namespace(burmese_context)
        assert result == "menu"
    
    def test_primary_namespace_selection(self, mock_namespace_router, sample_search_context):
        """Test primary namespace selection with weighted decision"""
        result = mock_namespace_router._select_primary_namespace(sample_search_context)
        assert result in ["menu", "faq", "jobs", "events"]
    
    def test_primary_confidence_calculation(self, mock_namespace_router, sample_search_context):
        """Test primary confidence calculation"""
        result = mock_namespace_router._calculate_primary_confidence(sample_search_context)
        assert 0.0 <= result <= 1.0
        assert isinstance(result, float)
    
    def test_cross_domain_detection(self, mock_namespace_router, sample_search_context):
        """Test cross-domain query detection"""
        # Test cross-domain query
        result = mock_namespace_router._detect_cross_domain_query(sample_search_context)
        assert isinstance(result, bool)
        
        # Test single-domain query
        single_domain_context = SearchContext(
            user_message="Show me the menu",
            detected_language="en",
            primary_intent="menu_browse",
            intent_confidence=0.9,
            secondary_intents=[],
            cultural_context={},
            entity_extraction={},
            conversation_history=[],
            previous_namespaces=[],
            user_preferences={}
        )
        result = mock_namespace_router._detect_cross_domain_query(single_domain_context)
        assert isinstance(result, bool)
    
    def test_fallback_namespace_selection(self, mock_namespace_router, sample_search_context):
        """Test fallback namespace selection"""
        primary_namespace = "menu"
        cross_domain = True
        
        result = mock_namespace_router._select_fallback_namespaces(
            sample_search_context, primary_namespace, cross_domain
        )
        
        assert isinstance(result, list)
        for fallback in result:
            assert "namespace" in fallback
            assert "confidence" in fallback
            assert "reasoning" in fallback
            assert 0.0 <= fallback["confidence"] <= 1.0
    
    def test_search_strategy_determination(self, mock_namespace_router):
        """Test search strategy determination"""
        # Test multi strategy
        result = mock_namespace_router._determine_search_strategy(0.7, True, [{"namespace": "faq"}])
        assert result == "multi"
        
        # Test hybrid strategy
        result = mock_namespace_router._determine_search_strategy(0.5, False, [{"namespace": "faq"}])
        assert result == "hybrid"
        
        # Test single strategy
        result = mock_namespace_router._determine_search_strategy(0.8, False, [])
        assert result == "single"
    
    def test_routing_quality_assessment(self, mock_namespace_router):
        """Test routing quality assessment"""
        primary_confidence = 0.8
        cross_domain = True
        fallback_namespaces = [{"confidence": 0.6}]
        
        result = mock_namespace_router._assess_routing_quality(
            primary_confidence, cross_domain, fallback_namespaces
        )
        
        assert 0.0 <= result <= 1.0
        assert isinstance(result, float)
    
    def test_routing_reasoning_generation(self, mock_namespace_router, sample_search_context):
        """Test routing reasoning generation"""
        primary_namespace = "menu"
        primary_confidence = 0.8
        cross_domain = True
        fallback_namespaces = [{"namespace": "jobs", "confidence": 0.6, "reasoning": "Job intent"}]
        
        result = mock_namespace_router._generate_routing_reasoning(
            sample_search_context, primary_namespace, primary_confidence, 
            cross_domain, fallback_namespaces
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "menu" in result
        assert "menu_browse" in result
    
    @pytest.mark.asyncio
    async def test_complete_namespace_routing(self, mock_namespace_router, sample_search_context):
        """Test complete namespace routing process"""
        result = await mock_namespace_router.route_namespaces(sample_search_context)
        
        assert isinstance(result, NamespaceRoute)
        assert result.primary_namespace in ["menu", "faq", "jobs", "events"]
        assert 0.0 <= result.primary_confidence <= 1.0
        assert isinstance(result.fallback_namespaces, list)
        assert isinstance(result.cross_domain_detected, bool)
        assert isinstance(result.routing_reasoning, str)
        assert result.search_strategy in ["single", "multi", "hybrid"]
        assert 0.0 <= result.quality_score <= 1.0
    
    def test_fallback_route_generation(self, mock_namespace_router, sample_search_context):
        """Test fallback route generation when routing fails"""
        result = mock_namespace_router._get_fallback_route(sample_search_context)
        
        assert isinstance(result, NamespaceRoute)
        assert result.primary_namespace == "faq"
        assert result.primary_confidence == 0.3
        assert len(result.fallback_namespaces) > 0
        assert result.search_strategy == "single"
        assert result.quality_score == 0.3
    
    def test_entities_support_namespace(self, mock_namespace_router):
        """Test entity support for namespace validation"""
        # Test food entities supporting menu intent
        food_entities = {"food_items": [{"item": "pizza"}]}
        result = mock_namespace_router._entities_support_namespace(food_entities, "menu_browse")
        assert result is True
        
        # Test no entities supporting non-menu intent
        no_entities = {"food_items": []}
        result = mock_namespace_router._entities_support_namespace(no_entities, "faq")
        assert result is False


class TestGlobalAccess:
    """Test global access to namespace router"""
    
    def test_get_intelligent_namespace_router(self):
        """Test global instance access"""
        router1 = get_intelligent_namespace_router()
        router2 = get_intelligent_namespace_router()
        
        assert router1 is router2  # Singleton pattern
        assert isinstance(router1, IntelligentNamespaceRouter)
