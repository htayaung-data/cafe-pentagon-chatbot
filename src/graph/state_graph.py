"""
LangGraph State Graph for Cafe Pentagon Chatbot
Stateful conversation management with intent-based routing and RAG control
"""

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START
from src.utils.logger import get_logger
from .nodes.pattern_matcher import PatternMatcherNode
from .nodes.rag_controller import RAGControllerNode
from .nodes.intent_classifier import IntentClassifierNode
from .nodes.rag_retriever import RAGRetrieverNode
from .nodes.response_generator import ResponseGeneratorNode
from .nodes.conversation_memory_updater import ConversationMemoryUpdaterNode

logger = get_logger("langgraph_state")


class StateSchema(TypedDict):
    """Enhanced state schema for LangGraph conversation flow"""
    # User input
    user_message: str
    user_id: str
    conversation_id: str
    
    # Language detection
    detected_language: str
    
    # Pattern matching
    is_greeting: bool
    is_goodbye: bool
    is_escalation_request: bool
    
    # Intent classification
    detected_intent: str
    intent_confidence: float
    all_intents: List[Dict[str, Any]]
    target_namespace: str
    intent_reasoning: str
    intent_entities: Dict[str, Any]
    
    # RAG processing
    rag_results: List[Dict[str, Any]]
    relevance_score: float
    rag_enabled: bool
    human_handling: bool
    
    # Response generation
    response: str
    response_generated: bool
    response_quality: str
    requires_human: bool
    escalation_reason: str
    
    # Conversation management
    conversation_history: List[Dict[str, Any]]
    conversation_state: str
    memory_updated: bool
    
    # Metadata
    response_time: int
    platform: str
    metadata: Dict[str, Any]


def create_conversation_graph() -> StateGraph:
    """
    Create the LangGraph conversation flow
    
    Flow:
    START → pattern_matcher → intent_classifier → rag_controller → 
    [if rag_enabled: namespace_router → rag_retriever → response_generator] → 
    [if not rag_enabled: human_response_handler] → escalation_detector → END
    """
    
    # Initialize nodes
    pattern_matcher = PatternMatcherNode()
    intent_classifier = IntentClassifierNode()
    rag_controller = RAGControllerNode()
    rag_retriever = RAGRetrieverNode()
    response_generator = ResponseGeneratorNode()
    conversation_memory_updater = ConversationMemoryUpdaterNode()
    
    # Create state graph
    workflow = StateGraph(StateSchema)
    
    # Add nodes
    workflow.add_node("pattern_matcher", pattern_matcher.process)
    workflow.add_node("intent_classifier", intent_classifier.process)
    workflow.add_node("rag_controller", rag_controller.process)
    workflow.add_node("rag_retriever", rag_retriever.process)
    workflow.add_node("response_generator", response_generator.process)
    workflow.add_node("conversation_memory_updater", conversation_memory_updater.process)
    
    # Define edges
    workflow.add_edge(START, "pattern_matcher")
    workflow.add_edge("pattern_matcher", "intent_classifier")
    workflow.add_edge("intent_classifier", "rag_controller")
    workflow.add_edge("rag_controller", "rag_retriever")
    workflow.add_edge("rag_retriever", "response_generator")
    workflow.add_edge("response_generator", "conversation_memory_updater")
    workflow.add_edge("conversation_memory_updater", END)
    
    # Set entry point
    workflow.set_entry_point("pattern_matcher")
    
    logger.info("langgraph_conversation_flow_created")
    
    return workflow


def create_initial_state(
    user_message: str,
    user_id: str,
    conversation_id: str,
    platform: str = "messenger"
) -> StateSchema:
    """
    Create initial state for conversation with conversation memory
    
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
        
        logger.info("conversation_history_loaded_for_initial_state", 
                   conversation_id=conversation_id,
                   history_length=len(conversation_history))
    except Exception as e:
        logger.error("failed_to_load_conversation_history_for_initial_state", 
                    conversation_id=conversation_id,
                    error=str(e))
    
    return StateSchema(
        # User input
        user_message=user_message,
        user_id=user_id,
        conversation_id=conversation_id,
        
        # Language detection (will be set by pattern matcher)
        detected_language="",
        
        # Pattern matching (will be set by pattern matcher)
        is_greeting=False,
        is_goodbye=False,
        is_escalation_request=False,
        
        # Intent classification (will be set by intent classifier)
        detected_intent="",
        intent_confidence=0.0,
        all_intents=[],
        target_namespace="",
        intent_reasoning="",
        intent_entities={},
        
        # RAG processing (will be set by RAG controller)
        rag_results=[],
        relevance_score=0.0,
        rag_enabled=True,  # Default to enabled
        human_handling=False,
        
        # Response generation (will be set by response generator)
        response="",
        response_generated=False,
        response_quality="",
        requires_human=False,
        escalation_reason="",
        
        # Conversation management
        conversation_history=conversation_history,
        conversation_state="greeting",
        memory_updated=False,
        
        # Metadata
        response_time=0,
        platform=platform,
        metadata={}
    )


def validate_state(state: Dict[str, Any]) -> bool:
    """
    Validate state structure and required fields
    
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
            logger.error("missing_required_field", field=field)
            return False
    
    return True


def log_state_transition(
    from_node: str, 
    to_node: str, 
    state: Dict[str, Any]
) -> None:
    """
    Log state transition for debugging
    
    Args:
        from_node: Source node name
        to_node: Target node name
        state: Current state
    """
    logger.info(
        "state_transition",
        from_node=from_node,
        to_node=to_node,
        user_id=state.get("user_id"),
        conversation_id=state.get("conversation_id"),
        detected_language=state.get("detected_language"),
        is_greeting=state.get("is_greeting"),
        is_goodbye=state.get("is_goodbye"),
        rag_enabled=state.get("rag_enabled"),
        human_handling=state.get("human_handling")
    ) 