"""
Enhanced Vector Search Service for Cafe Pentagon Chatbot
Provides multi-namespace retrieval with relevance scoring and context-aware search
Integrates with intelligent namespace router for dynamic namespace selection
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from src.config.settings import get_settings
from src.config.constants import PINECONE_NAMESPACES
from src.utils.logger import get_logger
from src.utils.api_client import get_openai_client, get_fallback_manager
from src.services.intelligent_namespace_router import get_intelligent_namespace_router, SearchContext, NamespaceRoute

logger = get_logger("enhanced_vector_search_service")


@dataclass
class SearchResult:
    """Represents a search result with enhanced metadata"""
    content: str
    metadata: Dict[str, Any]
    namespace: str
    relevance_score: float
    confidence_score: float
    source_type: str  # faq, menu_item, job_posting, event
    cultural_relevance: float
    language_match: float
    context_alignment: float


@dataclass
class MultiNamespaceSearchResult:
    """Represents results from multiple namespace search"""
    primary_results: List[SearchResult]
    fallback_results: List[SearchResult]
    cross_domain_results: List[SearchResult]
    overall_relevance_score: float
    search_strategy: str
    namespace_coverage: Dict[str, int]
    quality_metrics: Dict[str, float]


class EnhancedVectorSearchService:
    """
    Enhanced vector search service with multi-namespace capabilities
    Provides context-aware search with cultural and language optimizations
    """
    
    def __init__(self):
        """Initialize enhanced vector search service"""
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=self.settings.openai_api_key
        )
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=self.settings.openai_api_key
        )
        
        # Initialize services
        self.api_client = get_openai_client()
        self.fallback_manager = get_fallback_manager()
        self.namespace_router = get_intelligent_namespace_router()
        
        # Initialize Pinecone
        from pinecone import Pinecone
        pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.pinecone_index = pc.Index(self.settings.pinecone_index_name)
        
        # Search configuration
        self.search_config = {
            "max_results_per_namespace": 5,
            "min_relevance_threshold": 0.6,
            "context_window_size": 3,
            "cultural_boost_factor": 1.2,
            "language_boost_factor": 1.1,
            "cross_domain_penalty": 0.9
        }
        
        logger.info("enhanced_vector_search_service_initialized")
    
    async def search_with_intelligent_routing(self, state: Dict[str, Any]) -> MultiNamespaceSearchResult:
        """
        Perform intelligent multi-namespace search based on unified analysis
        
        Args:
            state: Conversation state with unified analysis results
            
        Returns:
            MultiNamespaceSearchResult with comprehensive search results
        """
        try:
            # Create search context from state
            search_context = self._create_search_context(state)
            
            # Get namespace routing decision
            namespace_route = await self.namespace_router.route_namespaces(search_context)
            
            # Perform search based on routing strategy
            if namespace_route.search_strategy == "multi":
                return await self._perform_multi_namespace_search(search_context, namespace_route)
            elif namespace_route.search_strategy == "hybrid":
                return await self._perform_hybrid_search(search_context, namespace_route)
            else:
                return await self._perform_single_namespace_search(search_context, namespace_route)
                
        except Exception as e:
            logger.error("enhanced_search_failed", error=str(e))
            return await self._get_fallback_search_result(state)
    
    def _create_search_context(self, state: Dict[str, Any]) -> SearchContext:
        """Create search context from conversation state"""
        return SearchContext(
            user_message=state.get("user_message", ""),
            detected_language=state.get("detected_language", "en"),
            primary_intent=state.get("detected_intent", "unknown"),
            intent_confidence=state.get("intent_confidence", 0.0),
            secondary_intents=state.get("secondary_intents", []),
            cultural_context=state.get("cultural_context", {}),
            entity_extraction=state.get("entity_extraction", {}),
            conversation_history=state.get("conversation_history", []),
            previous_namespaces=self._extract_previous_namespaces(state),
            user_preferences=state.get("user_preferences", {})
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
    
    async def _perform_multi_namespace_search(self, search_context: SearchContext, 
                                            namespace_route: NamespaceRoute) -> MultiNamespaceSearchResult:
        """Perform search across multiple namespaces"""
        all_namespaces = [namespace_route.primary_namespace] + [
            fb["namespace"] for fb in namespace_route.fallback_namespaces
        ]
        
        # Search all namespaces concurrently
        search_tasks = []
        for namespace in all_namespaces:
            task = self._search_namespace(search_context, namespace, is_primary=(namespace == namespace_route.primary_namespace))
            search_tasks.append(task)
        
        namespace_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process and categorize results
        primary_results = []
        fallback_results = []
        cross_domain_results = []
        
        for i, result in enumerate(namespace_results):
            if isinstance(result, Exception):
                logger.error("namespace_search_failed", namespace=all_namespaces[i], error=str(result))
                continue
            
            namespace = all_namespaces[i]
            if namespace == namespace_route.primary_namespace:
                primary_results.extend(result)
            else:
                fallback_results.extend(result)
        
        # Identify cross-domain results
        cross_domain_results = self._identify_cross_domain_results(primary_results, fallback_results, search_context)
        
        # Calculate overall metrics
        overall_relevance = self._calculate_overall_relevance(primary_results, fallback_results, cross_domain_results)
        namespace_coverage = self._calculate_namespace_coverage(primary_results, fallback_results)
        quality_metrics = self._calculate_quality_metrics(primary_results, fallback_results, cross_domain_results)
        
        return MultiNamespaceSearchResult(
            primary_results=primary_results,
            fallback_results=fallback_results,
            cross_domain_results=cross_domain_results,
            overall_relevance_score=overall_relevance,
            search_strategy="multi",
            namespace_coverage=namespace_coverage,
            quality_metrics=quality_metrics
        )
    
    async def _perform_hybrid_search(self, search_context: SearchContext, 
                                   namespace_route: NamespaceRoute) -> MultiNamespaceSearchResult:
        """Perform hybrid search with primary focus and fallback support"""
        # Search primary namespace first
        primary_results = await self._search_namespace(search_context, namespace_route.primary_namespace, is_primary=True)
        
        # If primary results are insufficient, search fallback namespaces
        fallback_results = []
        if len(primary_results) < 3 or max(r.relevance_score for r in primary_results) < 0.7:
            for fallback in namespace_route.fallback_namespaces:
                fallback_ns_results = await self._search_namespace(
                    search_context, fallback["namespace"], is_primary=False
                )
                fallback_results.extend(fallback_ns_results)
        
        # Identify cross-domain results
        cross_domain_results = self._identify_cross_domain_results(primary_results, fallback_results, search_context)
        
        # Calculate metrics
        overall_relevance = self._calculate_overall_relevance(primary_results, fallback_results, cross_domain_results)
        namespace_coverage = self._calculate_namespace_coverage(primary_results, fallback_results)
        quality_metrics = self._calculate_quality_metrics(primary_results, fallback_results, cross_domain_results)
        
        return MultiNamespaceSearchResult(
            primary_results=primary_results,
            fallback_results=fallback_results,
            cross_domain_results=cross_domain_results,
            overall_relevance_score=overall_relevance,
            search_strategy="hybrid",
            namespace_coverage=namespace_coverage,
            quality_metrics=quality_metrics
        )
    
    async def _perform_single_namespace_search(self, search_context: SearchContext, 
                                             namespace_route: NamespaceRoute) -> MultiNamespaceSearchResult:
        """Perform search in single namespace with high confidence"""
        primary_results = await self._search_namespace(search_context, namespace_route.primary_namespace, is_primary=True)
        
        # No fallback results for single namespace search
        fallback_results = []
        cross_domain_results = []
        
        # Calculate metrics
        overall_relevance = self._calculate_overall_relevance(primary_results, fallback_results, cross_domain_results)
        namespace_coverage = self._calculate_namespace_coverage(primary_results, fallback_results)
        quality_metrics = self._calculate_quality_metrics(primary_results, fallback_results, cross_domain_results)
        
        return MultiNamespaceSearchResult(
            primary_results=primary_results,
            fallback_results=fallback_results,
            cross_domain_results=cross_domain_results,
            overall_relevance_score=overall_relevance,
            search_strategy="single",
            namespace_coverage=namespace_coverage,
            quality_metrics=quality_metrics
        )
    
    async def _search_namespace(self, search_context: SearchContext, namespace: str, is_primary: bool = False) -> List[SearchResult]:
        """Search a specific namespace with enhanced relevance scoring"""
        try:
            # Generate search query with context
            search_query = await self._generate_contextual_search_query(search_context, namespace)
            
            # Get embeddings for search query
            query_embedding = await self.embeddings.aembed_query(search_query)
            
            # Search Pinecone
            search_response = self.pinecone_index.query(
                vector=query_embedding,
                namespace=namespace,
                top_k=self.search_config["max_results_per_namespace"],
                include_metadata=True
            )
            
            # Process and enhance results
            results = []
            for match in search_response.matches:
                if match.score >= self.search_config["min_relevance_threshold"]:
                    search_result = self._create_search_result(match, namespace, search_context, is_primary)
                    results.append(search_result)
            
            # Sort by enhanced relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info("namespace_search_completed",
                       namespace=namespace,
                       results_count=len(results),
                       top_relevance_score=results[0].relevance_score if results else 0.0)
            
            return results
            
        except Exception as e:
            logger.error("namespace_search_failed", namespace=namespace, error=str(e))
            return []
    
    async def _generate_contextual_search_query(self, search_context: SearchContext, namespace: str) -> str:
        """Generate context-aware search query"""
        base_query = search_context.user_message
        
        # Add entity context
        entity_context = self._extract_entity_context(search_context.entity_extraction)
        if entity_context:
            base_query += f" {entity_context}"
        
        # Add cultural context for language-specific optimization
        cultural_context = self._extract_cultural_context(search_context.cultural_context, namespace)
        if cultural_context:
            base_query += f" {cultural_context}"
        
        # Add conversation context for continuity
        conversation_context = self._extract_conversation_context(search_context.conversation_history)
        if conversation_context:
            base_query += f" context: {conversation_context}"
        
        return base_query
    
    def _extract_entity_context(self, entity_extraction: Dict[str, Any]) -> str:
        """Extract relevant entity context for search"""
        context_parts = []
        
        food_items = entity_extraction.get("food_items", [])
        if food_items:
            food_names = [item.get("item", "") for item in food_items[:3]]
            context_parts.append(f"food items: {', '.join(food_names)}")
        
        locations = entity_extraction.get("locations", [])
        if locations:
            location_names = [loc.get("location", "") for loc in locations[:2]]
            context_parts.append(f"locations: {', '.join(location_names)}")
        
        time_references = entity_extraction.get("time_references", [])
        if time_references:
            time_refs = [time.get("time", "") for time in time_references[:2]]
            context_parts.append(f"time: {', '.join(time_refs)}")
        
        return " ".join(context_parts)
    
    def _extract_cultural_context(self, cultural_context: Dict[str, Any], namespace: str) -> str:
        """Extract cultural context for search optimization"""
        context_parts = []
        
        language_mix = cultural_context.get("language_mix", "english_only")
        if language_mix in ["burmese_only", "mixed"]:
            context_parts.append("burmese language")
        
        formality_level = cultural_context.get("formality_level", "casual")
        if formality_level in ["formal", "very_formal"]:
            context_parts.append("formal tone")
        
        honorifics = cultural_context.get("honorifics_detected", [])
        if honorifics:
            context_parts.append(f"honorifics: {', '.join(honorifics)}")
        
        return " ".join(context_parts)
    
    def _extract_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Extract relevant context from conversation history"""
        if not conversation_history:
            return ""
        
        # Get last few user messages for context
        recent_messages = []
        for message in conversation_history[-self.search_config["context_window_size"]:]:
            if message.get("role") == "user":
                content = message.get("content", "")[:50]  # Truncate for context
                recent_messages.append(content)
        
        return " ".join(recent_messages)
    
    def _create_search_result(self, match: Any, namespace: str, search_context: SearchContext, is_primary: bool) -> SearchResult:
        """Create enhanced search result with comprehensive scoring"""
        # Base relevance score
        base_relevance = match.score
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(match, search_context)
        
        # Calculate cultural relevance
        cultural_relevance = self._calculate_cultural_relevance(match, search_context)
        
        # Calculate language match
        language_match = self._calculate_language_match(match, search_context)
        
        # Calculate context alignment
        context_alignment = self._calculate_context_alignment(match, search_context)
        
        # Enhanced relevance score
        relevance_score = self._calculate_enhanced_relevance(
            base_relevance, confidence_score, cultural_relevance, 
            language_match, context_alignment, is_primary
        )
        
        # Determine source type
        source_type = self._determine_source_type(match, namespace)
        
        return SearchResult(
            content=match.metadata.get("content", ""),
            metadata=match.metadata,
            namespace=namespace,
            relevance_score=relevance_score,
            confidence_score=confidence_score,
            source_type=source_type,
            cultural_relevance=cultural_relevance,
            language_match=language_match,
            context_alignment=context_alignment
        )
    
    def _calculate_confidence_score(self, match: Any, search_context: SearchContext) -> float:
        """Calculate confidence score based on match quality and context"""
        base_confidence = match.score
        
        # Boost for exact entity matches
        entity_boost = self._calculate_entity_match_boost(match, search_context)
        
        # Boost for intent alignment
        intent_boost = self._calculate_intent_alignment_boost(match, search_context)
        
        return min(1.0, base_confidence + entity_boost + intent_boost)
    
    def _calculate_entity_match_boost(self, match: Any, search_context: SearchContext) -> float:
        """Calculate boost for entity matches"""
        boost = 0.0
        content = match.metadata.get("content", "").lower()
        
        # Check for food item matches
        food_items = search_context.entity_extraction.get("food_items", [])
        for item in food_items:
            item_name = item.get("item", "").lower()
            if item_name in content:
                boost += 0.1
        
        # Check for location matches
        locations = search_context.entity_extraction.get("locations", [])
        for location in locations:
            loc_name = location.get("location", "").lower()
            if loc_name in content:
                boost += 0.05
        
        return min(0.3, boost)  # Cap at 0.3
    
    def _calculate_intent_alignment_boost(self, match: Any, search_context: SearchContext) -> float:
        """Calculate boost for intent alignment"""
        intent = search_context.primary_intent
        content = match.metadata.get("content", "").lower()
        
        intent_keywords = {
            "menu_browse": ["menu", "food", "dish", "item", "အစားအသောက်"],
            "order_place": ["order", "buy", "purchase", "လျှောက်ထား"],
            "reservation": ["reservation", "book", "table", "ကြိုတင်စာရင်း"],
            "faq": ["question", "answer", "information", "သိတာ"],
            "events": ["event", "promotion", "special", "ပွဲ"],
            "job_application": ["job", "career", "employment", "အလုပ်"]
        }
        
        keywords = intent_keywords.get(intent, [])
        matches = sum(1 for keyword in keywords if keyword in content)
        
        return min(0.2, matches * 0.05)  # 0.05 per keyword match, cap at 0.2
    
    def _calculate_cultural_relevance(self, match: Any, search_context: SearchContext) -> float:
        """Calculate cultural relevance score"""
        cultural_context = search_context.cultural_context
        content = match.metadata.get("content", "")
        
        relevance = 0.5  # Base relevance
        
        # Language match
        language_mix = cultural_context.get("language_mix", "english_only")
        if language_mix in ["burmese_only", "mixed"]:
            # Check for Burmese characters in content
            burmese_chars = sum(1 for char in content if '\u1000' <= char <= '\u109F')
            if burmese_chars > 0:
                relevance += 0.3
        
        # Formality match
        formality_level = cultural_context.get("formality_level", "casual")
        if formality_level in ["formal", "very_formal"]:
            formal_indicators = ["please", "kindly", "would you", "could you", "ကျေးဇူးပြု"]
            if any(indicator in content.lower() for indicator in formal_indicators):
                relevance += 0.2
        
        return min(1.0, relevance)
    
    def _calculate_language_match(self, match: Any, search_context: SearchContext) -> float:
        """Calculate language match score"""
        detected_language = search_context.detected_language
        content = match.metadata.get("content", "")
        
        if detected_language == "my":
            # Check for Burmese characters
            burmese_chars = sum(1 for char in content if '\u1000' <= char <= '\u109F')
            total_chars = len(content)
            if total_chars > 0:
                return min(1.0, burmese_chars / total_chars * 2)  # Boost for Burmese content
        
        return 0.8  # Default high score for English content
    
    def _calculate_context_alignment(self, match: Any, search_context: SearchContext) -> float:
        """Calculate context alignment score"""
        content = match.metadata.get("content", "").lower()
        conversation_history = search_context.conversation_history
        
        if not conversation_history:
            return 0.7  # Default score
        
        # Check alignment with recent conversation
        recent_context = " ".join([
            msg.get("content", "").lower() 
            for msg in conversation_history[-3:] 
            if msg.get("role") == "user"
        ])
        
        # Simple keyword overlap
        content_words = set(content.split())
        context_words = set(recent_context.split())
        
        if context_words:
            overlap = len(content_words.intersection(context_words))
            return min(1.0, overlap / len(context_words))
        
        return 0.7
    
    def _calculate_enhanced_relevance(self, base_relevance: float, confidence: float, 
                                    cultural_relevance: float, language_match: float, 
                                    context_alignment: float, is_primary: bool) -> float:
        """Calculate enhanced relevance score"""
        # Weighted combination
        enhanced_score = (
            base_relevance * 0.4 +
            confidence * 0.2 +
            cultural_relevance * 0.15 +
            language_match * 0.15 +
            context_alignment * 0.1
        )
        
        # Boost for primary namespace results
        if is_primary:
            enhanced_score *= self.search_config["cultural_boost_factor"]
        
        return min(1.0, enhanced_score)
    
    def _determine_source_type(self, match: Any, namespace: str) -> str:
        """Determine the source type of the result"""
        metadata = match.metadata
        
        if namespace == "menu":
            return "menu_item"
        elif namespace == "jobs":
            return "job_posting"
        elif namespace == "events":
            return "event"
        else:
            return "faq"
    
    def _identify_cross_domain_results(self, primary_results: List[SearchResult], 
                                     fallback_results: List[SearchResult], 
                                     search_context: SearchContext) -> List[SearchResult]:
        """Identify results that span multiple domains"""
        cross_domain_results = []
        
        # Check for results that contain keywords from multiple domains
        all_results = primary_results + fallback_results
        
        for result in all_results:
            content = result.content.lower()
            
            # Check for cross-domain keywords
            domain_keywords = {
                "menu": ["food", "menu", "dish", "price", "အစားအသောက်"],
                "events": ["event", "promotion", "special", "ပွဲ"],
                "jobs": ["job", "career", "employment", "အလုပ်"],
                "faq": ["question", "answer", "information", "သိတာ"]
            }
            
            domain_matches = {}
            for domain, keywords in domain_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in content)
                if matches > 0:
                    domain_matches[domain] = matches
            
            # If content matches multiple domains, it's cross-domain
            if len(domain_matches) > 1:
                cross_domain_results.append(result)
        
        return cross_domain_results
    
    def _calculate_overall_relevance(self, primary_results: List[SearchResult], 
                                   fallback_results: List[SearchResult], 
                                   cross_domain_results: List[SearchResult]) -> float:
        """Calculate overall relevance score"""
        all_results = primary_results + fallback_results
        
        if not all_results:
            return 0.0
        
        # Weight primary results more heavily
        primary_scores = [r.relevance_score for r in primary_results]
        fallback_scores = [r.relevance_score for r in fallback_results]
        
        if primary_scores:
            avg_primary = sum(primary_scores) / len(primary_scores)
        else:
            avg_primary = 0.0
        
        if fallback_scores:
            avg_fallback = sum(fallback_scores) / len(fallback_scores)
        else:
            avg_fallback = 0.0
        
        # Weighted average (70% primary, 30% fallback)
        overall_relevance = avg_primary * 0.7 + avg_fallback * 0.3
        
        # Boost for cross-domain results
        if cross_domain_results:
            cross_domain_boost = min(0.1, len(cross_domain_results) * 0.02)
            overall_relevance = min(1.0, overall_relevance + cross_domain_boost)
        
        return round(overall_relevance, 3)
    
    def _calculate_namespace_coverage(self, primary_results: List[SearchResult], 
                                    fallback_results: List[SearchResult]) -> Dict[str, int]:
        """Calculate coverage across namespaces"""
        coverage = {}
        
        for result in primary_results + fallback_results:
            namespace = result.namespace
            coverage[namespace] = coverage.get(namespace, 0) + 1
        
        return coverage
    
    def _calculate_quality_metrics(self, primary_results: List[SearchResult], 
                                 fallback_results: List[SearchResult], 
                                 cross_domain_results: List[SearchResult]) -> Dict[str, float]:
        """Calculate quality metrics for the search results"""
        all_results = primary_results + fallback_results
        
        if not all_results:
            return {
                "avg_relevance": 0.0,
                "avg_confidence": 0.0,
                "cultural_alignment": 0.0,
                "language_alignment": 0.0,
                "context_alignment": 0.0,
                "diversity_score": 0.0
            }
        
        # Calculate averages
        avg_relevance = sum(r.relevance_score for r in all_results) / len(all_results)
        avg_confidence = sum(r.confidence_score for r in all_results) / len(all_results)
        avg_cultural = sum(r.cultural_relevance for r in all_results) / len(all_results)
        avg_language = sum(r.language_match for r in all_results) / len(all_results)
        avg_context = sum(r.context_alignment for r in all_results) / len(all_results)
        
        # Calculate diversity score
        unique_namespaces = len(set(r.namespace for r in all_results))
        diversity_score = min(1.0, unique_namespaces / len(self.settings.pinecone_namespaces))
        
        return {
            "avg_relevance": round(avg_relevance, 3),
            "avg_confidence": round(avg_confidence, 3),
            "cultural_alignment": round(avg_cultural, 3),
            "language_alignment": round(avg_language, 3),
            "context_alignment": round(avg_context, 3),
            "diversity_score": round(diversity_score, 3)
        }
    
    async def _get_fallback_search_result(self, state: Dict[str, Any]) -> MultiNamespaceSearchResult:
        """Get fallback search result when enhanced search fails"""
        # Simple fallback to FAQ namespace
        try:
            fallback_results = await self._search_namespace(
                self._create_search_context(state), "faq", is_primary=True
            )
        except Exception:
            fallback_results = []
        
        return MultiNamespaceSearchResult(
            primary_results=fallback_results,
            fallback_results=[],
            cross_domain_results=[],
            overall_relevance_score=0.5,
            search_strategy="fallback",
            namespace_coverage={"faq": len(fallback_results)},
            quality_metrics={
                "avg_relevance": 0.5,
                "avg_confidence": 0.5,
                "cultural_alignment": 0.5,
                "language_alignment": 0.5,
                "context_alignment": 0.5,
                "diversity_score": 0.0
            }
        )


# Global enhanced vector search service instance
_enhanced_vector_search_service: Optional[EnhancedVectorSearchService] = None


def get_enhanced_vector_search_service() -> EnhancedVectorSearchService:
    """Get or create enhanced vector search service instance"""
    global _enhanced_vector_search_service
    if _enhanced_vector_search_service is None:
        _enhanced_vector_search_service = EnhancedVectorSearchService()
    return _enhanced_vector_search_service
