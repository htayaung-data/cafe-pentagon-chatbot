"""
LangGraph State Graph for Cafe Pentagon Chatbot
Enhanced stateful conversation management with two-LLM-call architecture
"""

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START
from src.utils.logger import get_logger
from .nodes.conversation_status_checker import ConversationStatusCheckerNode
from .nodes.smart_analysis_node import SmartAnalysisNode
from .nodes.decision_router_node import DecisionRouterNode
from .nodes.rag_retriever import RAGRetrieverNode
from .nodes.response_generator import ResponseGeneratorNode
from .nodes.conversation_memory_updater import ConversationMemoryUpdaterNode

logger = get_logger("langgraph_state")


class StateSchema(TypedDict):
    """Enhanced state schema for LangGraph conversation flow with two-LLM-call architecture"""
    # User input
    user_message: str
    user_id: str
    conversation_id: str
    
    # Conversation Status Check (Before LLM Processing)
    conversation_escalated: bool
    escalation_blocked: bool
    
    # Smart Analysis (First LLM Call)
    analysis_result: Dict[str, Any]
    detected_language: str
    primary_intent: str
    intent_confidence: float
    requires_search: bool
    search_context: Dict[str, Any]
    cultural_context: Dict[str, Any]
    conversation_context: Dict[str, Any]
    
    # Decision Router
    routing_decision: Dict[str, Any]
    action_type: str
    decision_confidence: float
    decision_reasoning: str
    
    # RAG processing
    rag_results: List[Dict[str, Any]]
    relevance_score: float
    rag_enabled: bool
    human_handling: bool
    
    # Response generation (Second LLM Call)
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
    Create the LangGraph conversation flow with two-LLM-call architecture
    
    Flow:
    START → conversation_status_checker → 
    [if escalated: skip LLM processing → conversation_memory_updater] → 
    [if not escalated: smart_analysis → decision_router → 
    [if action_type == "perform_search": rag_retriever → response_generator] → 
    [if action_type == "direct_response": response_generator] → 
    [if action_type == "escalate_to_human": response_generator]] → 
    conversation_memory_updater → END
    """
    
    # Initialize nodes
    conversation_status_checker = ConversationStatusCheckerNode()
    smart_analysis = SmartAnalysisNode()
    decision_router = DecisionRouterNode()
    rag_retriever = RAGRetrieverNode()
    response_generator = ResponseGeneratorNode()
    conversation_memory_updater = ConversationMemoryUpdaterNode()
    
    # Create state graph
    workflow = StateGraph(StateSchema)
    
    # Add nodes
    workflow.add_node("conversation_status_checker", conversation_status_checker.process)
    workflow.add_node("smart_analysis", smart_analysis.process)
    workflow.add_node("decision_router", decision_router.process)
    workflow.add_node("rag_retriever", rag_retriever.process)
    workflow.add_node("response_generator", response_generator.process)
    workflow.add_node("conversation_memory_updater", conversation_memory_updater.process)
    
    # Define edges
    workflow.add_edge(START, "conversation_status_checker")
    
    # Conditional routing based on escalation status
    workflow.add_conditional_edges(
        "conversation_status_checker",
        lambda state: "escalated_conversation" if state.get("conversation_escalated", False) else "continue_processing",
        {
            "escalated_conversation": "conversation_memory_updater",
            "continue_processing": "smart_analysis"
        }
    )
    
    workflow.add_edge("smart_analysis", "decision_router")
    
    # Conditional routing based on action_type
    workflow.add_conditional_edges(
        "decision_router",
        lambda state: state.get("action_type", "perform_search"),
        {
            "perform_search": "rag_retriever",
            "direct_response": "response_generator",
            "escalate_to_human": "response_generator"
        }
    )
    
    workflow.add_edge("rag_retriever", "response_generator")
    workflow.add_edge("response_generator", "conversation_memory_updater")
    workflow.add_edge("conversation_memory_updater", END)
    
    # Set entry point
    workflow.set_entry_point("conversation_status_checker")
    
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
        
        # Conversation Status Check (Before LLM Processing)
        conversation_escalated=False,
        escalation_blocked=False,
        
        # Smart Analysis (will be set by smart_analysis)
        analysis_result={},
        detected_language="",
        primary_intent="",
        intent_confidence=0.0,
        requires_search=False,
        search_context={},
        cultural_context={},
        conversation_context={},
        
        # Decision Router (will be set by decision_router)
        routing_decision={},
        action_type="",
        decision_confidence=0.0,
        decision_reasoning="",
        
        # RAG processing (will be set by rag_retriever)
        rag_results=[],
        relevance_score=0.0,
        rag_enabled=True,  # Default to enabled
        human_handling=False,
        
        # Response generation (will be set by response_generator)
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
    Validate state structure and required fields for two-LLM-call architecture
    
    Args:
        state: State dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "user_message", "user_id", "conversation_id", 
        "detected_language", "primary_intent", "action_type",
        "rag_enabled", "human_handling"
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
    Log state transition for debugging with two-LLM-call architecture
    
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
        primary_intent=state.get("primary_intent"),
        action_type=state.get("action_type"),
        intent_confidence=state.get("intent_confidence"),
        decision_confidence=state.get("decision_confidence"),
        rag_enabled=state.get("rag_enabled"),
        human_handling=state.get("human_handling")
    ) 