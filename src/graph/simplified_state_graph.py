"""
Simplified LangGraph State Graph for Cafe Pentagon Chatbot
Uses unified prompt controller for better performance and accuracy
"""

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START
from src.utils.logger import get_logger
from src.controllers.unified_prompt_controller import get_unified_prompt_controller
from .nodes.rag_retriever import RAGRetrieverNode
from .nodes.response_generator import ResponseGeneratorNode
from .nodes.conversation_memory_updater import ConversationMemoryUpdaterNode

logger = get_logger("simplified_langgraph_state")


class SimplifiedStateSchema(TypedDict):
    """Enhanced simplified state schema for unified multi-modal conversation flow"""
    # User input
    user_message: str
    user_id: str
    conversation_id: str
    
    # Language detection
    detected_language: str
    
    # Enhanced unified analysis (from enhanced unified prompt controller)
    detected_intent: str
    intent_confidence: float
    intent_reasoning: str
    
    # Multi-intent support
    secondary_intents: List[Dict[str, Any]]  # List of secondary intents with confidence
    
    # Enhanced namespace routing
    target_namespace: str
    namespace_confidence: float
    fallback_namespaces: List[Dict[str, Any]]  # List of fallback namespaces
    cross_domain_detected: bool
    routing_reasoning: str
    
    # Enhanced HITL assessment
    requires_human: bool
    escalation_confidence: float
    escalation_reason: str
    escalation_urgency: str  # low, medium, high, critical
    escalation_triggers: List[str]
    hitl_reasoning: str
    
    # Enhanced cultural context
    cultural_context: Dict[str, Any]  # formality_level, honorifics, cultural_nuances
    cultural_confidence: float
    cultural_reasoning: str
    
    # Enhanced entity extraction
    entity_extraction: Dict[str, Any]  # food_items, locations, time_references, quantities
    extraction_confidence: float
    entity_reasoning: str
    
    # Enhanced response guidance
    response_guidance: Dict[str, Any]  # tone, language, include_greeting, include_farewell
    guidance_confidence: float
    guidance_reasoning: str
    
    # Overall analysis quality
    analysis_confidence: float
    quality_score: float
    fallback_required: bool
    fallback_reason: str
    processing_time_estimate: str
    recommendations: List[str]
    
    # RAG processing
    rag_results: List[Dict[str, Any]]
    relevance_score: float
    rag_enabled: bool
    human_handling: bool
    
    # Response generation
    response: str
    response_generated: bool
    response_quality: str
    
    # Conversation management
    conversation_history: List[Dict[str, Any]]
    conversation_state: str
    memory_updated: bool
    
    # Metadata
    response_time: int
    platform: str
    metadata: Dict[str, Any]


class UnifiedAnalysisNode:
    """
    LangGraph node that uses unified prompt controller
    Replaces multiple separate nodes with single comprehensive analysis
    """
    
    def __init__(self):
        """Initialize unified analysis node"""
        self.unified_controller = get_unified_prompt_controller()
        logger.info("unified_analysis_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state using unified prompt controller
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with comprehensive analysis
        """
        try:
            # Use unified prompt controller for comprehensive analysis
            updated_state = await self.unified_controller.process_query(state)
            
            logger.info("unified_analysis_completed",
                       intent=updated_state.get("detected_intent"),
                       confidence=updated_state.get("intent_confidence"),
                       namespace=updated_state.get("target_namespace"),
                       requires_human=updated_state.get("requires_human"))
            
            return updated_state
            
        except Exception as e:
            logger.error("unified_analysis_failed", error=str(e))
            # Return state with default values
            state.update({
                "detected_intent": "unknown",
                "intent_confidence": 0.0,
                "target_namespace": "faq",
                "requires_human": False,
                "rag_enabled": True,
                "human_handling": False
            })
            return state


def create_simplified_conversation_graph() -> StateGraph:
    """
    Create simplified LangGraph conversation flow
    
    Flow:
    START → unified_analysis → [if rag_enabled: rag_retriever → response_generator] → 
    [if not rag_enabled: human_response_handler] → conversation_memory_updater → END
    """
    
    # Initialize nodes
    unified_analysis = UnifiedAnalysisNode()
    rag_retriever = RAGRetrieverNode()
    response_generator = ResponseGeneratorNode()
    conversation_memory_updater = ConversationMemoryUpdaterNode()
    
    # Create state graph
    workflow = StateGraph(SimplifiedStateSchema)
    
    # Add nodes
    workflow.add_node("unified_analysis", unified_analysis.process)
    workflow.add_node("rag_retriever", rag_retriever.process)
    workflow.add_node("response_generator", response_generator.process)
    workflow.add_node("conversation_memory_updater", conversation_memory_updater.process)
    
    # Define edges
    workflow.add_edge(START, "unified_analysis")
    workflow.add_edge("unified_analysis", "rag_retriever")
    workflow.add_edge("rag_retriever", "response_generator")
    workflow.add_edge("response_generator", "conversation_memory_updater")
    workflow.add_edge("conversation_memory_updater", END)
    
    # Set entry point
    workflow.set_entry_point("unified_analysis")
    
    logger.info("simplified_langgraph_conversation_flow_created")
    
    return workflow


def create_simplified_initial_state(
    user_message: str,
    user_id: str,
    conversation_id: str,
    platform: str = "messenger"
) -> SimplifiedStateSchema:
    """
    Create initial state for simplified conversation flow
    
    Args:
        user_message: User's input message
        user_id: User identifier
        conversation_id: Conversation identifier
        platform: Platform (messenger, streamlit, etc.)
        
    Returns:
        Initial state dictionary with loaded conversation history
    """
    # Load conversation history
    conversation_history = []
    try:
        from src.services.conversation_memory_service import get_conversation_memory_service
        memory_service = get_conversation_memory_service()
        conversation_history = memory_service.load_conversation_history(conversation_id, user_id, limit=10)
        
        logger.info("conversation_history_loaded_for_simplified_state", 
                   conversation_id=conversation_id,
                   history_length=len(conversation_history))
    except Exception as e:
        logger.error("failed_to_load_conversation_history_for_simplified_state", 
                    conversation_id=conversation_id,
                    error=str(e))
    
    return SimplifiedStateSchema(
        # User input
        user_message=user_message,
        user_id=user_id,
        conversation_id=conversation_id,
        
        # Language detection (will be set by unified analysis)
        detected_language="",
        
        # Unified analysis (will be set by unified analysis node)
        detected_intent="",
        intent_confidence=0.0,
        intent_reasoning="",
        secondary_intents=[],
        target_namespace="",
        namespace_confidence=0.0,
        fallback_namespaces=[],
        cross_domain_detected=False,
        routing_reasoning="",
        requires_human=False,
        escalation_confidence=0.0,
        escalation_reason="",
        escalation_urgency="",
        escalation_triggers=[],
        hitl_reasoning="",
        cultural_context={},
        cultural_confidence=0.0,
        cultural_reasoning="",
        entity_extraction={},
        extraction_confidence=0.0,
        entity_reasoning="",
        response_guidance={},
        guidance_confidence=0.0,
        guidance_reasoning="",
        analysis_confidence=0.0,
        quality_score=0.0,
        fallback_required=False,
        fallback_reason="",
        processing_time_estimate="",
        recommendations=[],
        
        # RAG processing (will be set by RAG retriever)
        rag_results=[],
        relevance_score=0.0,
        rag_enabled=True,
        human_handling=False,
        
        # Response generation (will be set by response generator)
        response="",
        response_generated=False,
        response_quality="",
        
        # Conversation management
        conversation_history=conversation_history,
        conversation_state="active",
        memory_updated=False,
        
        # Metadata
        response_time=0,
        platform=platform,
        metadata={}
    )


def validate_simplified_state(state: Dict[str, Any]) -> bool:
    """
    Validate simplified state structure and required fields
    
    Args:
        state: State dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "user_message", "user_id", "conversation_id", 
        "detected_language", "rag_enabled", "human_handling"
    ]
    
    for field in required_fields:
        if field not in state:
            logger.error("missing_required_field_in_simplified_state", field=field)
            return False
    
    return True


def log_simplified_state_transition(
    from_node: str, 
    to_node: str, 
    state: Dict[str, Any]
) -> None:
    """
    Log simplified state transition for debugging
    
    Args:
        from_node: Source node name
        to_node: Target node name
        state: Current state
    """
    logger.info(
        "simplified_state_transition",
        from_node=from_node,
        to_node=to_node,
        user_id=state.get("user_id"),
        conversation_id=state.get("conversation_id"),
        detected_language=state.get("detected_language"),
        detected_intent=state.get("detected_intent"),
        rag_enabled=state.get("rag_enabled"),
        human_handling=state.get("human_handling")
    )
