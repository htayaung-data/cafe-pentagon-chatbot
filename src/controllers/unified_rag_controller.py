"""
Unified RAG Controller for Cafe Pentagon Chatbot
Orchestrates intelligent namespace routing and enhanced vector search
Provides unified interface for multi-modal RAG operations
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.services.intelligent_namespace_router import get_intelligent_namespace_router, SearchContext, NamespaceRoute
from src.services.enhanced_vector_search_service import get_enhanced_vector_search_service, MultiNamespaceSearchResult, SearchResult
from src.controllers.unified_prompt_controller import get_unified_prompt_controller

logger = get_logger("unified_rag_controller")


@dataclass
class RAGRequest:
    """Represents a RAG request with all necessary context"""
    user_message: str
    conversation_state: Dict[str, Any]
    user_preferences: Dict[str, Any]
    platform: str = "messenger"
    request_id: Optional[str] = None


@dataclass
class RAGResponse:
    """Represents a comprehensive RAG response"""
    primary_results: List[SearchResult]
    fallback_results: List[SearchResult]
    cross_domain_results: List[SearchResult]
    namespace_route: NamespaceRoute
    search_metrics: Dict[str, Any]
    response_guidance: Dict[str, Any]
    processing_time: float
    quality_score: float
    recommendations: List[str]


class UnifiedRAGController:
    """
    Unified RAG Controller that orchestrates namespace routing and vector search
    Provides intelligent multi-modal RAG capabilities with cultural awareness
    """
    
    def __init__(self):
        """Initialize unified RAG controller"""
        self.settings = get_settings()
        
        # Initialize core services
        self.namespace_router = get_intelligent_namespace_router()
        self.vector_search_service = get_enhanced_vector_search_service()
        self.unified_prompt_controller = get_unified_prompt_controller()
        
        # Performance tracking
        self.request_count = 0
        self.avg_processing_time = 0.0
        
        logger.info("unified_rag_controller_initialized")
    
    async def process_rag_request(self, rag_request: RAGRequest) -> RAGResponse:
        """
        Process a comprehensive RAG request with intelligent orchestration
        
        Args:
            rag_request: Complete RAG request with context
            
        Returns:
            RAGResponse with comprehensive results and guidance
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Step 1: Enhanced Unified Analysis
            logger.info("rag_request_started", request_id=rag_request.request_id)
            
            # Update conversation state with user message
            state = rag_request.conversation_state.copy()
            state["user_message"] = rag_request.user_message
            state["platform"] = rag_request.platform
            state["user_preferences"] = rag_request.user_preferences
            
            # Perform unified analysis
            analysis_state = await self.unified_prompt_controller.process_query(state)
            
            # Step 2: Intelligent Namespace Routing
            search_context = self._create_search_context_from_analysis(analysis_state)
            namespace_route = await self.namespace_router.route_namespaces(search_context)
            
            # Step 3: Enhanced Vector Search
            search_results = await self.vector_search_service.search_with_intelligent_routing(analysis_state)
            
            # Step 4: Response Synthesis and Quality Assessment
            rag_response = await self._synthesize_rag_response(
                search_results, namespace_route, analysis_state, start_time
            )
            
            # Update performance metrics
            self._update_performance_metrics(rag_response.processing_time)
            
            logger.info("rag_request_completed",
                       request_id=rag_request.request_id,
                       processing_time=rag_response.processing_time,
                       quality_score=rag_response.quality_score,
                       primary_results_count=len(rag_response.primary_results),
                       search_strategy=namespace_route.search_strategy)
            
            return rag_response
            
        except Exception as e:
            logger.error("rag_request_failed", 
                        request_id=rag_request.request_id, 
                        error=str(e))
            
            # Return fallback response
            return await self._create_fallback_response(rag_request, start_time)
    
    def _create_search_context_from_analysis(self, analysis_state: Dict[str, Any]) -> SearchContext:
        """Create search context from unified analysis results"""
        from src.services.intelligent_namespace_router import SearchContext
        
        return SearchContext(
            user_message=analysis_state.get("user_message", ""),
            detected_language=analysis_state.get("detected_language", "en"),
            primary_intent=analysis_state.get("detected_intent", "unknown"),
            intent_confidence=analysis_state.get("intent_confidence", 0.0),
            secondary_intents=analysis_state.get("secondary_intents", []),
            cultural_context=analysis_state.get("cultural_context", {}),
            entity_extraction=analysis_state.get("entity_extraction", {}),
            conversation_history=analysis_state.get("conversation_history", []),
            previous_namespaces=self._extract_previous_namespaces(analysis_state),
            user_preferences=analysis_state.get("user_preferences", {})
        )
    
    def _extract_previous_namespaces(self, state: Dict[str, Any]) -> List[str]:
        """Extract previously used namespaces from conversation history"""
        previous_namespaces = []
        conversation_history = state.get("conversation_history", [])
        
        for message in conversation_history[-10:]:  # Last 10 messages
            if message.get("role") == "assistant":
                metadata = message.get("metadata", {})
                if "target_namespace" in metadata:
                    previous_namespaces.append(metadata["target_namespace"])
        
        return list(set(previous_namespaces))  # Remove duplicates
    
    async def _synthesize_rag_response(self, search_results: MultiNamespaceSearchResult, 
                                     namespace_route: NamespaceRoute, 
                                     analysis_state: Dict[str, Any],
                                     start_time: float) -> RAGResponse:
        """Synthesize comprehensive RAG response with quality assessment"""
        
        # Calculate processing time
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # Extract response guidance from analysis
        response_guidance = analysis_state.get("response_guidance", {})
        
        # Calculate quality score
        quality_score = self._calculate_overall_quality_score(
            search_results, namespace_route, analysis_state
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            search_results, namespace_route, analysis_state
        )
        
        # Prepare search metrics
        search_metrics = {
            "overall_relevance": search_results.overall_relevance_score,
            "search_strategy": search_results.search_strategy,
            "namespace_coverage": search_results.namespace_coverage,
            "quality_metrics": search_results.quality_metrics,
            "routing_quality": namespace_route.quality_score,
            "cross_domain_detected": namespace_route.cross_domain_detected
        }
        
        return RAGResponse(
            primary_results=search_results.primary_results,
            fallback_results=search_results.fallback_results,
            cross_domain_results=search_results.cross_domain_results,
            namespace_route=namespace_route,
            search_metrics=search_metrics,
            response_guidance=response_guidance,
            processing_time=processing_time,
            quality_score=quality_score,
            recommendations=recommendations
        )
    
    def _calculate_overall_quality_score(self, search_results: MultiNamespaceSearchResult,
                                       namespace_route: NamespaceRoute,
                                       analysis_state: Dict[str, Any]) -> float:
        """Calculate overall quality score for the RAG response"""
        
        # Base quality from search results
        base_quality = search_results.overall_relevance_score * 0.4
        
        # Routing quality contribution
        routing_quality = namespace_route.quality_score * 0.3
        
        # Analysis confidence contribution
        analysis_confidence = analysis_state.get("analysis_confidence", 0.5) * 0.2
        
        # Cultural alignment contribution
        cultural_confidence = analysis_state.get("cultural_context", {}).get("cultural_confidence", 0.5) * 0.1
        
        # Calculate weighted average
        overall_quality = base_quality + routing_quality + analysis_confidence + cultural_confidence
        
        # Apply quality adjustments
        if namespace_route.cross_domain_detected:
            overall_quality = min(1.0, overall_quality + 0.05)  # Small boost for cross-domain
        
        if len(search_results.primary_results) == 0:
            overall_quality *= 0.8  # Penalty for no primary results
        
        return round(overall_quality, 3)
    
    def _generate_recommendations(self, search_results: MultiNamespaceSearchResult,
                                namespace_route: NamespaceRoute,
                                analysis_state: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving RAG performance"""
        recommendations = []
        
        # Quality-based recommendations
        if search_results.overall_relevance_score < 0.6:
            recommendations.append("Consider expanding search context or refining query")
        
        if len(search_results.primary_results) < 2:
            recommendations.append("Primary namespace returned insufficient results")
        
        if namespace_route.quality_score < 0.7:
            recommendations.append("Namespace routing confidence is low")
        
        # Cross-domain recommendations
        if namespace_route.cross_domain_detected:
            recommendations.append("Cross-domain query detected - consider multi-namespace search")
        
        # Cultural recommendations
        cultural_context = analysis_state.get("cultural_context", {})
        if cultural_context.get("cultural_confidence", 1.0) < 0.6:
            recommendations.append("Cultural context analysis confidence is low")
        
        # Performance recommendations
        if self.avg_processing_time > 2.0:
            recommendations.append("Consider optimizing search performance")
        
        return recommendations
    
    def _update_performance_metrics(self, processing_time: float):
        """Update performance tracking metrics"""
        self.request_count += 1
        
        # Update average processing time
        if self.request_count == 1:
            self.avg_processing_time = processing_time
        else:
            self.avg_processing_time = (
                (self.avg_processing_time * (self.request_count - 1) + processing_time) 
                / self.request_count
            )
    
    async def _create_fallback_response(self, rag_request: RAGRequest, start_time: float) -> RAGResponse:
        """Create fallback response when RAG processing fails"""
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # Create minimal fallback route
        from src.services.intelligent_namespace_router import NamespaceRoute
        fallback_route = NamespaceRoute(
            primary_namespace="faq",
            primary_confidence=0.3,
            fallback_namespaces=[],
            cross_domain_detected=False,
            routing_reasoning="Fallback due to processing error",
            search_strategy="single",
            quality_score=0.3
        )
        
        # Create empty search results
        from src.services.enhanced_vector_search_service import SearchResult
        fallback_results = [
            SearchResult(
                content="I apologize, but I'm having trouble processing your request. Please try rephrasing your question.",
                metadata={"source": "fallback"},
                namespace="faq",
                relevance_score=0.5,
                confidence_score=0.3,
                source_type="faq",
                cultural_relevance=0.5,
                language_match=0.8,
                context_alignment=0.5
            )
        ]
        
        return RAGResponse(
            primary_results=fallback_results,
            fallback_results=[],
            cross_domain_results=[],
            namespace_route=fallback_route,
            search_metrics={
                "overall_relevance": 0.5,
                "search_strategy": "fallback",
                "namespace_coverage": {"faq": 1},
                "quality_metrics": {"avg_relevance": 0.5},
                "routing_quality": 0.3,
                "cross_domain_detected": False
            },
            response_guidance={
                "tone": "apologetic",
                "language": "en",
                "include_greeting": False,
                "include_farewell": True
            },
            processing_time=processing_time,
            quality_score=0.3,
            recommendations=["System encountered an error - fallback response provided"]
        )
    
    async def get_rag_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics and performance metrics"""
        return {
            "total_requests": self.request_count,
            "avg_processing_time": round(self.avg_processing_time, 3),
            "system_status": "operational",
            "services": {
                "namespace_router": "active",
                "vector_search_service": "active",
                "unified_prompt_controller": "active"
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of RAG system"""
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {}
        }
        
        try:
            # Check namespace router
            router = get_intelligent_namespace_router()
            health_status["services"]["namespace_router"] = "healthy"
        except Exception as e:
            health_status["services"]["namespace_router"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        try:
            # Check vector search service
            search_service = get_enhanced_vector_search_service()
            health_status["services"]["vector_search_service"] = "healthy"
        except Exception as e:
            health_status["services"]["vector_search_service"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        try:
            # Check unified prompt controller
            prompt_controller = get_unified_prompt_controller()
            health_status["services"]["unified_prompt_controller"] = "healthy"
        except Exception as e:
            health_status["services"]["unified_prompt_controller"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status


# Global unified RAG controller instance
_unified_rag_controller: Optional[UnifiedRAGController] = None


def get_unified_rag_controller() -> UnifiedRAGController:
    """Get or create unified RAG controller instance"""
    global _unified_rag_controller
    if _unified_rag_controller is None:
        _unified_rag_controller = UnifiedRAGController()
    return _unified_rag_controller
