"""
Simplified State Graph for LangGraph
Ultra-simple 3-node workflow: Analysis → Search → Response
Replaces complex 6-node system with linear flow
"""

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START
from src.utils.logger import get_logger
from .nodes.simple_analysis_node import SimpleAnalysisNode
from .nodes.direct_search_node import DirectSearchNode
from .nodes.contextual_response_node import ContextualResponseNode

logger = get_logger("simplified_state_graph")


class SimpleStateSchema(TypedDict):
    """Simplified state schema for ultra-simple conversation flow with HITL and memory integration"""
    # User input
    user_message: str
    user_id: str
    conversation_id: str
    
    # Analysis results (Step 1)
    analysis_result: Dict[str, Any]
    user_language: str
    search_terms: List[str]
    search_namespace: Optional[str]
    response_strategy: str
    analysis_confidence: float
    
    # Search results (Step 2)
    search_results: List[Any]
    data_found: bool
    search_performed: bool
    search_namespace_used: Optional[str]
    search_terms_used: List[str]
    
    # Response (Step 3)
    response: str
    response_language: str
    response_generated: bool
    response_quality: str
    
    # HITL (Human-in-the-Loop) integration
    requires_human: bool
    human_handling: bool
    escalation_reason: Optional[str]
    escalation_blocked: bool
    
    # Conversation memory integration
    conversation_history: List[Dict[str, Any]]
    conversation_state: str
    memory_loaded: bool
    memory_updated: bool
    
    # Metadata
    response_time: int
    platform: str
    metadata: Dict[str, Any]


def create_simplified_conversation_graph() -> StateGraph:
    """
    Create the simplified LangGraph conversation flow with HITL and memory integration
    
    Flow:
    START → load_memory → simple_analysis → hitl_check → direct_search → contextual_response → update_memory → END
    
    This extends the simple 3-node system to 5 nodes with HITL and memory integration.
    """
    
    # Initialize nodes
    from .nodes.conversation_memory_node import ConversationMemoryNode
    from .nodes.hitl_node import HITLNode
    from .nodes.simple_analysis_node import SimpleAnalysisNode
    from .nodes.direct_search_node import DirectSearchNode
    from .nodes.contextual_response_node import ContextualResponseNode
    
    load_memory = ConversationMemoryNode()
    simple_analysis = SimpleAnalysisNode()
    hitl_check = HITLNode()
    direct_search = DirectSearchNode()
    contextual_response = ContextualResponseNode()
    
    # Create state graph
    workflow = StateGraph(SimpleStateSchema)
    
    # Add nodes
    workflow.add_node("load_memory", load_memory.process)
    workflow.add_node("simple_analysis", simple_analysis.process)
    workflow.add_node("hitl_check", hitl_check.check_escalation)
    workflow.add_node("direct_search", direct_search.process)
    workflow.add_node("contextual_response", contextual_response.process)
    workflow.add_node("update_memory", load_memory.update_memory)
    
    # Define flow with conditional routing
    workflow.set_entry_point("load_memory")
    workflow.add_edge("load_memory", "simple_analysis")
    workflow.add_edge("simple_analysis", "hitl_check")
    
    # Conditional routing based on HITL decision
    def should_escalate(state: Dict[str, Any]) -> str:
        """Determine next step based on HITL decision"""
        if state.get("requires_human", False):
            return "contextual_response"  # Go to contextual response for escalated conversations
        return "direct_search"  # Continue with normal flow
    
    workflow.add_conditional_edges("hitl_check", should_escalate, {
        "direct_search": "direct_search",
        "contextual_response": "contextual_response"
    })
    
    workflow.add_edge("direct_search", "contextual_response")
    workflow.add_edge("contextual_response", "update_memory")
    workflow.set_finish_point("update_memory")
    
    logger.info("simplified_conversation_graph_with_hitl_created")
    
    return workflow


def create_simplified_initial_state(
    user_message: str,
    user_id: str,
    conversation_id: str,
    platform: str = "messenger"
) -> SimpleStateSchema:
    """
    Create initial state for simplified conversation flow
    
    Args:
        user_message: User's input message
        user_id: User identifier
        conversation_id: Conversation identifier
        platform: Platform (streamlit, messenger)
        
    Returns:
        Initial state for simplified workflow
    """
    from datetime import datetime
    
    initial_state = {
        # User input
        "user_message": user_message,
        "user_id": user_id,
        "conversation_id": conversation_id,
        
        # Analysis results (will be populated by simple_analysis)
        "analysis_result": {},
        "user_language": "en",
        "search_terms": [],
        "search_namespace": None,
        "response_strategy": "polite_fallback",
        "analysis_confidence": 0.0,
        
        # Search results (will be populated by direct_search)
        "search_results": [],
        "data_found": False,
        "search_performed": False,
        "search_namespace_used": None,
        "search_terms_used": [],
        
        # Response (will be populated by contextual_response)
        "response": "",
        "response_language": "en",
        "response_generated": False,
        "response_quality": "pending",
        
        # HITL (Human-in-the-Loop) integration
        "requires_human": False,
        "human_handling": False,
        "escalation_reason": None,
        "escalation_blocked": False,
        
        # Conversation memory integration
        "conversation_history": [],
        "conversation_state": "active",
        "memory_loaded": False,
        "memory_updated": False,
        
        # Metadata
        "response_time": 0,
        "platform": platform,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "workflow_version": "simplified_v2_with_hitl",
            "node_count": 5
        }
    }
    
    logger.info("simplified_initial_state_created",
               user_id=user_id,
               conversation_id=conversation_id,
               platform=platform,
               message_length=len(user_message))
    
    return initial_state


def validate_simplified_state(state: Dict[str, Any]) -> bool:
    """
    Validate simplified state structure
    
    Args:
        state: State dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "user_message", "user_id", "conversation_id",
        "analysis_result", "user_language", "search_terms", "search_namespace", "response_strategy",
        "search_results", "data_found", "search_performed",
        "response", "response_language", "response_generated",
        "requires_human", "human_handling", "escalation_reason", "escalation_blocked",
        "conversation_history", "conversation_state", "memory_loaded", "memory_updated",
        "response_time", "platform", "metadata"
    ]
    
    for field in required_fields:
        if field not in state:
            logger.error("missing_required_field_in_simplified_state", field=field)
            return False
    
    # Validate data types
    if not isinstance(state.get("user_message"), str):
        logger.error("invalid_user_message_type")
        return False
    
    if not isinstance(state.get("search_terms"), list):
        logger.error("invalid_search_terms_type")
        return False
    
    if not isinstance(state.get("search_results"), list):
        logger.error("invalid_search_results_type")
        return False
    
    return True


def log_simplified_state_transition(
    from_node: str, 
    to_node: str, 
    state: Dict[str, Any]
) -> None:
    """
    Log state transition in simplified workflow
    
    Args:
        from_node: Source node name
        to_node: Target node name
        state: Current state
    """
    user_message = state.get("user_message", "")[:50]
    user_language = state.get("user_language", "unknown")
    response_strategy = state.get("response_strategy", "unknown")
    data_found = state.get("data_found", False)
    
    logger.info("simplified_state_transition",
               from_node=from_node,
               to_node=to_node,
               user_message=user_message,
               user_language=user_language,
               response_strategy=response_strategy,
               data_found=data_found)


def get_simplified_workflow_stats() -> Dict[str, Any]:
    """
    Get statistics about the simplified workflow
    
    Returns:
        Workflow statistics
    """
    return {
        "workflow_type": "simplified_with_hitl",
        "node_count": 5,
        "nodes": ["load_memory", "simple_analysis", "hitl_check", "direct_search", "contextual_response", "update_memory"],
        "flow_type": "conditional_linear",
        "complexity": "simplified_with_integration",
        "version": "2.0.0",
        "description": "Simplified 5-node workflow with HITL and conversation memory integration"
    }
