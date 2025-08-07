"""
Decision Router Node for LangGraph
Uses Smart Analysis results to decide whether to search or respond directly
Maintains HITL integration and escalation detection
"""

from typing import Dict, Any, List, Optional
from src.utils.logger import get_logger

logger = get_logger("decision_router_node")


class DecisionRouterNode:
    """
    Decision router node that determines the next action based on analysis results
    Routes between search, direct response, and human escalation
    """
    
    def __init__(self):
        """Initialize decision router node"""
        logger.info("decision_router_node_initialized")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make routing decision based on analysis results
        
        Args:
            state: Current conversation state with analysis results
            
        Returns:
            Updated state with routing decision
        """
        user_message = state.get("user_message", "")
        analysis_result = state.get("analysis_result", {})
        detected_language = state.get("detected_language", "en")
        primary_intent = state.get("primary_intent", "unknown")
        intent_confidence = state.get("intent_confidence", 0.0)
        requires_search = state.get("requires_search", False)
        
        if not user_message:
            logger.warning("empty_user_message_in_decision_router")
            return self._set_default_decision(state)
        
        try:
            # Make routing decision
            routing_decision = self._make_routing_decision(
                analysis_result, 
                detected_language, 
                primary_intent, 
                intent_confidence, 
                requires_search
            )
            
            # Update state with routing decision
            updated_state = state.copy()
            updated_state.update({
                "routing_decision": routing_decision,
                "action_type": routing_decision["action_type"],
                "rag_enabled": routing_decision["rag_enabled"],
                "human_handling": routing_decision["human_handling"],
                "escalation_reason": routing_decision["escalation_reason"],
                "decision_confidence": routing_decision["confidence"],
                "decision_reasoning": routing_decision["reasoning"]
            })
            
            # Log routing decision
            logger.info("routing_decision_made",
                       user_message=user_message[:100],
                       action_type=routing_decision["action_type"],
                       rag_enabled=routing_decision["rag_enabled"],
                       human_handling=routing_decision["human_handling"],
                       confidence=routing_decision["confidence"],
                       reasoning=routing_decision["reasoning"])
            
            return updated_state
            
        except Exception as e:
            logger.error("routing_decision_failed",
                        error=str(e),
                        user_message=user_message[:100])
            
            # Fallback to default decision
            return self._set_default_decision(state)

    def _make_routing_decision(self, analysis_result: Dict[str, Any], detected_language: str, 
                              primary_intent: str, intent_confidence: float, requires_search: bool) -> Dict[str, Any]:
        """
        Make routing decision based on analysis results
        
        Args:
            analysis_result: Analysis results from SmartAnalysisNode
            detected_language: Detected language
            primary_intent: Primary intent
            intent_confidence: Intent confidence score
            requires_search: Whether search is required
            
        Returns:
            Routing decision dictionary
        """
        # Check for human assistance requests first
        if primary_intent == "human_assistance":
            return {
                "action_type": "escalate_to_human",
                "rag_enabled": False,
                "human_handling": True,
                "escalation_reason": "User requested human assistance",
                "confidence": 0.95,
                "reasoning": "User explicitly requested human assistance"
            }
        
        # Check for escalation requests
        if self._is_escalation_request(analysis_result, primary_intent):
            return {
                "action_type": "escalate_to_human",
                "rag_enabled": False,
                "human_handling": True,
                "escalation_reason": "User requested human assistance",
                "confidence": 0.95,
                "reasoning": "User explicitly requested human assistance"
            }
        
        # Check for low confidence that requires human intervention
        if intent_confidence < 0.3:
            return {
                "action_type": "escalate_to_human",
                "rag_enabled": False,
                "human_handling": True,
                "escalation_reason": "Low confidence in intent classification",
                "confidence": 0.8,
                "reasoning": f"Intent confidence ({intent_confidence}) is too low for automated response"
            }
        
        # Check for ambiguous queries that need clarification
        if self._is_ambiguous_query(analysis_result, primary_intent):
            return {
                "action_type": "escalate_to_human",
                "rag_enabled": False,
                "human_handling": True,
                "escalation_reason": "Ambiguous query requiring clarification",
                "confidence": 0.7,
                "reasoning": "Query is ambiguous and requires human clarification"
            }
        
        # Handle greetings and goodbyes (direct response, no search)
        if primary_intent in ["greeting", "goodbye"]:
            return {
                "action_type": "direct_response",
                "rag_enabled": False,
                "human_handling": False,
                "escalation_reason": None,
                "confidence": 0.9,
                "reasoning": f"Direct response for {primary_intent} intent"
            }
        
        # Handle queries that require search
        if requires_search:
            return {
                "action_type": "perform_search",
                "rag_enabled": True,
                "human_handling": False,
                "escalation_reason": None,
                "confidence": 0.85,
                "reasoning": f"Search required for {primary_intent} intent"
            }
        
        # Handle FAQ and other queries that can be answered directly
        if primary_intent in ["faq", "events", "complaint"]:
            return {
                "action_type": "perform_search",
                "rag_enabled": True,
                "human_handling": False,
                "escalation_reason": None,
                "confidence": 0.8,
                "reasoning": f"FAQ search for {primary_intent} intent"
            }
        
        # Handle job application queries
        if primary_intent == "job_application":
            return {
                "action_type": "perform_search",
                "rag_enabled": True,
                "human_handling": False,
                "escalation_reason": None,
                "confidence": 0.8,
                "reasoning": "Job application queries require database search"
            }
        
        # Handle order placement (might need human assistance)
        if primary_intent == "order_place":
            return {
                "action_type": "escalate_to_human",
                "rag_enabled": False,
                "human_handling": True,
                "escalation_reason": "Order placement requires human assistance",
                "confidence": 0.9,
                "reasoning": "Order placement is complex and requires human handling"
            }
        
        # Handle reservation requests (might need human assistance)
        if primary_intent == "reservation":
            return {
                "action_type": "escalate_to_human",
                "rag_enabled": False,
                "human_handling": True,
                "escalation_reason": "Reservation requests require human assistance",
                "confidence": 0.9,
                "reasoning": "Reservation requests are complex and require human handling"
            }
        
        # Default fallback for unknown intents
        return {
            "action_type": "perform_search",
            "rag_enabled": True,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.5,
            "reasoning": f"Unknown intent '{primary_intent}', defaulting to search"
        }

    def _is_escalation_request(self, analysis_result: Dict[str, Any], primary_intent: str) -> bool:
        """
        Check if user is requesting human assistance based on LLM analysis only
        
        Args:
            analysis_result: Analysis results from LLM
            primary_intent: Primary intent from LLM
            
        Returns:
            True if escalation is requested (based on LLM analysis only)
        """
        # Only rely on LLM analysis - no pattern matching
        conversation_context = analysis_result.get("conversation_context", {})
        
        # Check if LLM explicitly marked this as needing clarification
        if conversation_context.get("clarification_needed", False):
            return True
        
        # Check if LLM classified as complaint intent (which might need human handling)
        if primary_intent == "complaint":
            return True
        
        # Check if LLM classified as human_assistance intent
        if primary_intent == "human_assistance":
            return True
        
        # Otherwise, trust the LLM's analysis
        return False

    def _is_ambiguous_query(self, analysis_result: Dict[str, Any], primary_intent: str) -> bool:
        """
        Check if query is ambiguous based on LLM analysis only
        
        Args:
            analysis_result: Analysis results from LLM
            primary_intent: Primary intent from LLM
            
        Returns:
            True if query is ambiguous (based on LLM analysis only)
        """
        # Only rely on LLM analysis - no pattern matching
        conversation_context = analysis_result.get("conversation_context", {})
        
        # Check if LLM explicitly marked this as needing clarification
        if conversation_context.get("clarification_needed", False):
            return True
        
        # Check if LLM classified as unknown with very low confidence
        intent_confidence = analysis_result.get("intent_confidence", 0.0)
        if primary_intent == "unknown" and intent_confidence < 0.1:
            return True
        
        # Otherwise, trust the LLM's analysis
        return False

    def _set_default_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default routing decision when processing fails
        
        Args:
            state: Current state
            
        Returns:
            State with default routing decision
        """
        default_decision = {
            "action_type": "perform_search",
            "rag_enabled": True,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.5,
            "reasoning": "Default fallback decision"
        }
        
        updated_state = state.copy()
        updated_state.update({
            "routing_decision": default_decision,
            "action_type": default_decision["action_type"],
            "rag_enabled": default_decision["rag_enabled"],
            "human_handling": default_decision["human_handling"],
            "escalation_reason": default_decision["escalation_reason"],
            "decision_confidence": default_decision["confidence"],
            "decision_reasoning": default_decision["reasoning"]
        })
        
        return updated_state
