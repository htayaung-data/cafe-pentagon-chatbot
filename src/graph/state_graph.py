"""
State Graph for LangGraph
Defines the conversation flow and state schema
Uses the new simplified 3-node workflow
"""

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START
from src.utils.logger import get_logger
from .simplified_state_graph import (
    create_simplified_conversation_graph,
    create_simplified_initial_state,
    validate_simplified_state,
    log_simplified_state_transition,
    SimpleStateSchema
)

logger = get_logger("state_graph")


# Re-export the simplified workflow functions
def create_conversation_graph() -> StateGraph:
    """
    Create the simplified LangGraph conversation flow
    
    Flow:
    START → simple_analysis → direct_search → contextual_response → END
    """
    return create_simplified_conversation_graph()


def create_initial_state(
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
    return create_simplified_initial_state(user_message, user_id, conversation_id, platform)


def validate_state(state: Dict[str, Any]) -> bool:
    """
    Validate the simplified state schema
    """
    return validate_simplified_state(state)


def log_state_transition(
    from_node: str,
    to_node: str,
    state: Dict[str, Any]
) -> None:
    """
    Log state transition in simplified workflow
    
    Args:
        from_node: Node from which transition occurred
        to_node: Node to which transition occurred
        state: Current state
    """
    log_simplified_state_transition(from_node, to_node, state)


# Legacy compatibility - re-export the schema
StateSchema = SimpleStateSchema 