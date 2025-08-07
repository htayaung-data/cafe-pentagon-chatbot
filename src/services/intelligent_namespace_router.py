"""
Intelligent Namespace Router for Cafe Pentagon Chatbot
Handles dynamic namespace selection based on enhanced unified analysis
Provides cross-domain query handling and confidence-based fallback strategies
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.config.constants import PINECONE_NAMESPACES

logger = get_logger("intelligent_namespace_router")


@dataclass
class NamespaceRoute:
    """Represents a namespace routing decision"""
    primary_namespace: str
    primary_confidence: float
    fallback_namespaces: List[Dict[str, Any]]
    cross_domain_detected: bool
    routing_reasoning: str
    search_strategy: str  # single, multi, hybrid
    quality_score: float


@dataclass
class SearchContext:
    """Context for namespace routing decisions"""
    user_message: str
    detected_language: str
    primary_intent: str
    intent_confidence: float
    secondary_intents: List[Dict[str, Any]]
    cultural_context: Dict[str, Any]
    entity_extraction: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    previous_namespaces: List[str]
    user_preferences: Dict[str, Any]


class IntelligentNamespaceRouter:
    """
    Intelligent namespace router that handles dynamic namespace selection
    based on enhanced unified analysis with cross-domain capabilities
    """
    
    def __init__(self):
        """Initialize intelligent namespace router"""
        self.settings = get_settings()
        self.available_namespaces = PINECONE_NAMESPACES
        self.namespace_weights = self._initialize_namespace_weights()
        self.cross_domain_patterns = self._initialize_cross_domain_patterns()
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "minimum": 0.3
        }
        logger.info("intelligent_namespace_router_initialized")
    
    def _initialize_namespace_weights(self) -> Dict[str, float]:
        """Initialize namespace weights based on typical usage patterns"""
        return {
            "faq": 0.35,      # Most common queries
            "menu": 0.30,     # Food-related queries
            "jobs": 0.15,     # Employment queries
            "events": 0.20    # Events and promotions
        }
    
    def _initialize_cross_domain_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that indicate cross-domain queries"""
        return {
            "menu_faq": [
                "menu", "food", "price", "cost", "hours", "location",
                "အစားအသောက်", "စျေးနှုန်း", "ဈေးနှုန်း", "အချိန်", "နေရာ"
            ],
            "events_menu": [
                "event", "promotion", "special", "menu", "food", "discount",
                "ပွဲ", "ပရိုမိုရှင်း", "အထူး", "အစားအသောက်", "လျှော့စျေး"
            ],
            "jobs_faq": [
                "job", "career", "employment", "apply", "work", "hours", "location",
                "အလုပ်", "အလုပ်အကိုင်င်", "လျှောက်ထား", "အချိန်", "နေရာ"
            ]
        }
    
    async def route_namespaces(self, search_context: SearchContext) -> NamespaceRoute:
        """
        Route to appropriate namespaces based on enhanced analysis
        
        Args:
            search_context: Context containing unified analysis results
            
        Returns:
            NamespaceRoute with routing decisions
        """
        try:
            # Primary namespace selection
            primary_namespace = self._select_primary_namespace(search_context)
            primary_confidence = self._calculate_primary_confidence(search_context)
            
            # Cross-domain detection
            cross_domain_detected = self._detect_cross_domain_query(search_context)
            
            # Fallback namespace selection
            fallback_namespaces = self._select_fallback_namespaces(
                search_context, primary_namespace, cross_domain_detected
            )
            
            # Search strategy determination
            search_strategy = self._determine_search_strategy(
                primary_confidence, cross_domain_detected, fallback_namespaces
            )
            
            # Quality assessment
            quality_score = self._assess_routing_quality(
                primary_confidence, cross_domain_detected, fallback_namespaces
            )
            
            # Generate reasoning
            routing_reasoning = self._generate_routing_reasoning(
                search_context, primary_namespace, primary_confidence, 
                cross_domain_detected, fallback_namespaces
            )
            
            route = NamespaceRoute(
                primary_namespace=primary_namespace,
                primary_confidence=primary_confidence,
                fallback_namespaces=fallback_namespaces,
                cross_domain_detected=cross_domain_detected,
                routing_reasoning=routing_reasoning,
                search_strategy=search_strategy,
                quality_score=quality_score
            )
            
            logger.info("namespace_routing_completed",
                       primary_namespace=primary_namespace,
                       primary_confidence=primary_confidence,
                       cross_domain_detected=cross_domain_detected,
                       search_strategy=search_strategy,
                       quality_score=quality_score)
            
            return route
            
        except Exception as e:
            logger.error("namespace_routing_failed", error=str(e))
            return self._get_fallback_route(search_context)
    
    def _select_primary_namespace(self, context: SearchContext) -> str:
        """Select primary namespace based on intent and entities"""
        # Intent-based selection
        intent_namespace = self._map_intent_to_namespace(context.primary_intent)
        
        # Entity-based refinement
        entity_namespace = self._get_entity_based_namespace(context.entity_extraction)
        
        # Cultural context consideration
        cultural_namespace = self._get_cultural_based_namespace(context.cultural_context)
        
        # Weighted decision
        namespace_scores = {
            intent_namespace: 0.5,
            entity_namespace: 0.3,
            cultural_namespace: 0.2
        }
        
        # Add namespace weights
        for namespace, score in namespace_scores.items():
            if namespace in self.namespace_weights:
                namespace_scores[namespace] += self.namespace_weights[namespace] * 0.1
        
        # Select highest scoring namespace
        primary_namespace = max(namespace_scores.items(), key=lambda x: x[1])[0]
        
        return primary_namespace
    
    def _map_intent_to_namespace(self, intent: str) -> str:
        """Map intent to primary namespace"""
        mapping = {
            "greeting": "faq",
            "menu_browse": "menu",
            "order_place": "menu",
            "reservation": "faq",
            "faq": "faq",
            "events": "events",
            "complaint": "faq",
            "job_application": "jobs",
            "goodbye": "faq",
            "unknown": "faq"
        }
        return mapping.get(intent, "faq")
    
    def _get_entity_based_namespace(self, entity_extraction: Dict[str, Any]) -> str:
        """Determine namespace based on extracted entities"""
        food_items = entity_extraction.get("food_items", [])
        locations = entity_extraction.get("locations", [])
        time_references = entity_extraction.get("time_references", [])
        
        if food_items:
            return "menu"
        # No pattern matching - use intent-based routing only
        return "faq"
        
        return "faq"
    
    def _get_cultural_based_namespace(self, cultural_context: Dict[str, Any]) -> str:
        """Consider cultural context for namespace selection"""
        formality_level = cultural_context.get("formality_level", "casual")
        language_mix = cultural_context.get("language_mix", "english_only")
        
        # More formal queries might be FAQ-related
        if formality_level in ["formal", "very_formal"]:
            return "faq"
        
        # Burmese language queries might be more menu-focused
        if language_mix in ["burmese_only", "mixed"]:
            return "menu"
        
        return "faq"
    
    def _calculate_primary_confidence(self, context: SearchContext) -> float:
        """Calculate confidence in primary namespace selection"""
        base_confidence = context.intent_confidence
        
        # Adjust based on entity extraction confidence
        entity_confidence = context.entity_extraction.get("extraction_confidence", 0.5)
        base_confidence = (base_confidence + entity_confidence) / 2
        
        # Adjust based on cultural confidence
        cultural_confidence = context.cultural_context.get("cultural_confidence", 0.5)
        base_confidence = (base_confidence + cultural_confidence) / 2
        
        # Boost confidence if entities strongly support the namespace
        if self._entities_support_namespace(context.entity_extraction, context.primary_intent):
            base_confidence = min(1.0, base_confidence + 0.2)
        
        return round(base_confidence, 3)
    
    def _entities_support_namespace(self, entity_extraction: Dict[str, Any], intent: str) -> bool:
        """Check if extracted entities support the namespace"""
        food_items = entity_extraction.get("food_items", [])
        
        if intent in ["menu_browse", "order_place"] and food_items:
            return True
        
        return False
    
    def _detect_cross_domain_query(self, context: SearchContext) -> bool:
        """Detect if query spans multiple domains based on intent analysis"""
        # Check secondary intents for domain diversity
        secondary_intents = [si.get("intent", "") for si in context.secondary_intents]
        primary_domain = self._map_intent_to_namespace(context.primary_intent)
        secondary_domains = [self._map_intent_to_namespace(si) for si in secondary_intents]
        
        # If we have multiple different domains from intent analysis, it's cross-domain
        if len(set([primary_domain] + secondary_domains)) > 1:
            return True
        
        # Check entity extraction for domain diversity
        food_items = context.entity_extraction.get("food_items", [])
        faq_entities = context.entity_extraction.get("faq_entities", [])
        job_entities = context.entity_extraction.get("job_entities", [])
        
        # If we have entities from multiple domains, it's cross-domain
        domain_entity_counts = {
            "menu": len(food_items),
            "faq": len(faq_entities),
            "jobs": len(job_entities)
        }
        
        active_domains = [domain for domain, count in domain_entity_counts.items() if count > 0]
        if len(active_domains) > 1:
            return True
        
        return False
    
    def _select_fallback_namespaces(self, context: SearchContext, primary_namespace: str, cross_domain: bool) -> List[Dict[str, Any]]:
        """Select fallback namespaces based on context"""
        fallback_namespaces = []
        
        if cross_domain:
            # For cross-domain queries, include relevant secondary namespaces
            secondary_intents = [si.get("intent", "") for si in context.secondary_intents]
            for intent in secondary_intents:
                namespace = self._map_intent_to_namespace(intent)
                if namespace != primary_namespace:
                    confidence = next((si.get("confidence", 0.5) for si in context.secondary_intents if si.get("intent") == intent), 0.5)
                    fallback_namespaces.append({
                        "namespace": namespace,
                        "confidence": confidence,
                        "reasoning": f"Secondary intent '{intent}' suggests {namespace} namespace"
                    })
        
        # Always include FAQ as a fallback for low confidence scenarios
        if context.intent_confidence < self.confidence_thresholds["medium"]:
            fallback_namespaces.append({
                "namespace": "faq",
                "confidence": 0.4,
                "reasoning": "Low confidence in primary intent, FAQ as safe fallback"
            })
        
        # Add menu fallback for food-related entities
        food_items = context.entity_extraction.get("food_items", [])
        if food_items and primary_namespace != "menu":
            fallback_namespaces.append({
                "namespace": "menu",
                "confidence": 0.6,
                "reasoning": f"Food entities detected: {[item.get('item', '') for item in food_items[:3]]}"
            })
        
        return fallback_namespaces
    
    def _determine_search_strategy(self, primary_confidence: float, cross_domain: bool, fallback_namespaces: List[Dict[str, Any]]) -> str:
        """Determine the search strategy to use"""
        if cross_domain:
            return "multi"
        elif primary_confidence < self.confidence_thresholds["medium"] and fallback_namespaces:
            return "hybrid"
        else:
            return "single"
    
    def _assess_routing_quality(self, primary_confidence: float, cross_domain: bool, fallback_namespaces: List[Dict[str, Any]]) -> float:
        """Assess the quality of the routing decision"""
        quality_score = primary_confidence
        
        # Boost for cross-domain detection
        if cross_domain:
            quality_score = min(1.0, quality_score + 0.1)
        
        # Boost for appropriate fallback selection
        if fallback_namespaces:
            avg_fallback_confidence = sum(fb.get("confidence", 0) for fb in fallback_namespaces) / len(fallback_namespaces)
            quality_score = min(1.0, quality_score + avg_fallback_confidence * 0.1)
        
        return round(quality_score, 3)
    
    def _generate_routing_reasoning(self, context: SearchContext, primary_namespace: str, primary_confidence: float, 
                                  cross_domain: bool, fallback_namespaces: List[Dict[str, Any]]) -> str:
        """Generate detailed reasoning for the routing decision"""
        reasoning_parts = []
        
        # Primary namespace reasoning
        reasoning_parts.append(f"Primary namespace '{primary_namespace}' selected based on intent '{context.primary_intent}' (confidence: {primary_confidence})")
        
        # Entity-based reasoning
        food_items = context.entity_extraction.get("food_items", [])
        if food_items:
            reasoning_parts.append(f"Food entities detected: {[item.get('item', '') for item in food_items[:3]]}")
        
        # Cross-domain reasoning
        if cross_domain:
            reasoning_parts.append("Cross-domain query detected based on multiple domain keywords and secondary intents")
        
        # Fallback reasoning
        if fallback_namespaces:
            fallback_reasons = [fb.get("reasoning", "") for fb in fallback_namespaces]
            reasoning_parts.append(f"Fallback namespaces: {', '.join(fallback_reasons)}")
        
        return "; ".join(reasoning_parts)
    
    def _get_fallback_route(self, context: SearchContext) -> NamespaceRoute:
        """Get fallback route when routing fails"""
        return NamespaceRoute(
            primary_namespace="faq",
            primary_confidence=0.3,
            fallback_namespaces=[{
                "namespace": "menu",
                "confidence": 0.3,
                "reasoning": "Fallback due to routing failure"
            }],
            cross_domain_detected=False,
            routing_reasoning="Fallback routing due to processing error",
            search_strategy="single",
            quality_score=0.3
        )


# Global namespace router instance
_namespace_router: Optional[IntelligentNamespaceRouter] = None


def get_intelligent_namespace_router() -> IntelligentNamespaceRouter:
    """Get or create intelligent namespace router instance"""
    global _namespace_router
    if _namespace_router is None:
        _namespace_router = IntelligentNamespaceRouter()
    return _namespace_router
