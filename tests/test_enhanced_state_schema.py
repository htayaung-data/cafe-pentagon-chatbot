"""
Enhanced State Schema Tests
Tests the enhanced simplified state schema with comprehensive unified analysis support
"""

import pytest
from typing import Dict, Any
from src.graph.simplified_state_graph import (
    SimplifiedStateSchema,
    create_simplified_initial_state,
    validate_simplified_state,
    log_simplified_state_transition
)


class TestEnhancedStateSchema:
    """Test enhanced state schema functionality"""
    
    def test_enhanced_state_schema_structure(self):
        """Test that enhanced state schema has all required fields"""
        # Create a sample enhanced state
        sample_state = SimplifiedStateSchema(
            # User input
            user_message="What's on the menu?",
            user_id="user123",
            conversation_id="conv456",
            
            # Language detection
            detected_language="en",
            
            # Enhanced unified analysis
            detected_intent="menu_browse",
            intent_confidence=0.85,
            intent_reasoning="User is asking about menu items",
            
            # Multi-intent support
            secondary_intents=[
                {
                    "intent": "faq",
                    "confidence": 0.45,
                    "reasoning": "User also asked about availability"
                }
            ],
            
            # Enhanced namespace routing
            target_namespace="menu",
            namespace_confidence=0.85,
            fallback_namespaces=[
                {
                    "namespace": "faq",
                    "confidence": 0.45,
                    "reasoning": "Backup for general questions"
                }
            ],
            cross_domain_detected=False,
            routing_reasoning="Clear menu-related query",
            
            # Enhanced HITL assessment
            requires_human=False,
            escalation_confidence=0.15,
            escalation_reason="",
            escalation_urgency="low",
            escalation_triggers=[],
            hitl_reasoning="Standard menu inquiry",
            
            # Enhanced cultural context
            cultural_context={
                "formality_level": "casual",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "english_only"
            },
            cultural_confidence=0.90,
            cultural_reasoning="Standard English query",
            
            # Enhanced entity extraction
            entity_extraction={
                "food_items": [
                    {
                        "item": "pizza",
                        "confidence": 0.85,
                        "category": "main_dish"
                    }
                ],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": []
            },
            extraction_confidence=0.85,
            entity_reasoning="Extracted food item 'pizza'",
            
            # Enhanced response guidance
            response_guidance={
                "tone": "friendly",
                "language": "english",
                "include_greeting": False,
                "include_farewell": False,
                "response_length": "medium",
                "priority_information": ["menu items", "pizza options"]
            },
            guidance_confidence=0.80,
            guidance_reasoning="Provide menu information in friendly tone",
            
            # Overall analysis quality
            analysis_confidence=0.82,
            quality_score=0.85,
            fallback_required=False,
            fallback_reason="",
            processing_time_estimate="2-3 seconds",
            recommendations=["Provide menu categories", "Include pricing"],
            
            # RAG processing
            rag_results=[],
            relevance_score=0.0,
            rag_enabled=True,
            human_handling=False,
            
            # Response generation
            response="",
            response_generated=False,
            response_quality="",
            
            # Conversation management
            conversation_history=[],
            conversation_state="active",
            memory_updated=False,
            
            # Metadata
            response_time=0,
            platform="messenger",
            metadata={}
        )
        
        # Verify all enhanced fields are present
        assert sample_state["detected_intent"] == "menu_browse"
        assert sample_state["intent_confidence"] == 0.85
        assert len(sample_state["secondary_intents"]) == 1
        assert sample_state["target_namespace"] == "menu"
        assert sample_state["namespace_confidence"] == 0.85
        assert len(sample_state["fallback_namespaces"]) == 1
        assert sample_state["cross_domain_detected"] is False
        assert sample_state["escalation_urgency"] == "low"
        assert sample_state["cultural_confidence"] == 0.90
        assert sample_state["extraction_confidence"] == 0.85
        assert sample_state["guidance_confidence"] == 0.80
        assert sample_state["analysis_confidence"] == 0.82
        assert sample_state["quality_score"] == 0.85
    
    def test_create_simplified_initial_state(self):
        """Test creation of initial state with enhanced schema"""
        initial_state = create_simplified_initial_state(
            user_message="Hello",
            user_id="user123",
            conversation_id="conv456",
            platform="messenger"
        )
        
        # Verify basic fields
        assert initial_state["user_message"] == "Hello"
        assert initial_state["user_id"] == "user123"
        assert initial_state["conversation_id"] == "conv456"
        assert initial_state["platform"] == "messenger"
        
        # Verify enhanced fields are initialized with defaults
        assert initial_state["detected_intent"] == ""
        assert initial_state["intent_confidence"] == 0.0
        assert initial_state["secondary_intents"] == []
        assert initial_state["target_namespace"] == ""
        assert initial_state["namespace_confidence"] == 0.0
        assert initial_state["fallback_namespaces"] == []
        assert initial_state["cross_domain_detected"] is False
        assert initial_state["requires_human"] is False
        assert initial_state["escalation_confidence"] == 0.0
        assert initial_state["escalation_urgency"] == ""
        assert initial_state["escalation_triggers"] == []
        assert initial_state["cultural_context"] == {}
        assert initial_state["cultural_confidence"] == 0.0
        assert initial_state["entity_extraction"] == {}
        assert initial_state["extraction_confidence"] == 0.0
        assert initial_state["response_guidance"] == {}
        assert initial_state["guidance_confidence"] == 0.0
        assert initial_state["analysis_confidence"] == 0.0
        assert initial_state["quality_score"] == 0.0
        assert initial_state["fallback_required"] is False
        assert initial_state["recommendations"] == []
        
        # Verify RAG and response fields
        assert initial_state["rag_enabled"] is True
        assert initial_state["human_handling"] is False
        assert initial_state["response"] == ""
        assert initial_state["response_generated"] is False
    
    def test_validate_simplified_state_success(self):
        """Test successful state validation"""
        valid_state = {
            "user_message": "Test message",
            "user_id": "user123",
            "conversation_id": "conv456",
            "detected_language": "en",
            "rag_enabled": True,
            "human_handling": False,
            # Enhanced fields
            "detected_intent": "faq",
            "intent_confidence": 0.8,
            "secondary_intents": [],
            "target_namespace": "faq",
            "namespace_confidence": 0.8,
            "fallback_namespaces": [],
            "cross_domain_detected": False,
            "requires_human": False,
            "escalation_confidence": 0.1,
            "escalation_urgency": "low",
            "escalation_triggers": [],
            "cultural_confidence": 0.9,
            "extraction_confidence": 0.8,
            "guidance_confidence": 0.8,
            "analysis_confidence": 0.8,
            "quality_score": 0.8,
            "fallback_required": False
        }
        
        assert validate_simplified_state(valid_state) is True
    
    def test_validate_simplified_state_missing_fields(self):
        """Test state validation with missing required fields"""
        invalid_state = {
            "user_message": "Test message",
            # Missing user_id, conversation_id, etc.
        }
        
        assert validate_simplified_state(invalid_state) is False
    
    def test_enhanced_state_with_multi_intent(self):
        """Test state with multiple intents"""
        multi_intent_state = SimplifiedStateSchema(
            user_message="I want to order pizza and check your hours",
            user_id="user123",
            conversation_id="conv456",
            detected_language="en",
            detected_intent="order",
            intent_confidence=0.75,
            intent_reasoning="Primary intent is ordering",
            secondary_intents=[
                {
                    "intent": "faq",
                    "confidence": 0.65,
                    "reasoning": "User also asked about hours"
                },
                {
                    "intent": "menu_browse",
                    "confidence": 0.45,
                    "reasoning": "User mentioned pizza"
                }
            ],
            target_namespace="menu",
            namespace_confidence=0.75,
            fallback_namespaces=[
                {
                    "namespace": "faq",
                    "confidence": 0.65,
                    "reasoning": "Hours question"
                }
            ],
            cross_domain_detected=True,
            routing_reasoning="Cross-domain query: order + hours",
            requires_human=False,
            escalation_confidence=0.25,
            escalation_reason="",
            escalation_urgency="low",
            escalation_triggers=[],
            hitl_reasoning="Standard multi-intent query",
            cultural_context={
                "formality_level": "casual",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "english_only"
            },
            cultural_confidence=0.85,
            cultural_reasoning="Casual English query",
            entity_extraction={
                "food_items": [
                    {
                        "item": "pizza",
                        "confidence": 0.9,
                        "category": "main_dish"
                    }
                ],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": []
            },
            extraction_confidence=0.9,
            entity_reasoning="Extracted pizza order",
            response_guidance={
                "tone": "friendly",
                "language": "english",
                "include_greeting": False,
                "include_farewell": False,
                "response_length": "medium",
                "priority_information": ["order process", "hours"]
            },
            guidance_confidence=0.8,
            guidance_reasoning="Handle order and provide hours",
            analysis_confidence=0.78,
            quality_score=0.8,
            fallback_required=False,
            fallback_reason="",
            processing_time_estimate="3-4 seconds",
            recommendations=["Process order", "Provide hours"],
            rag_results=[],
            relevance_score=0.0,
            rag_enabled=True,
            human_handling=False,
            response="",
            response_generated=False,
            response_quality="",
            conversation_history=[],
            conversation_state="active",
            memory_updated=False,
            response_time=0,
            platform="messenger",
            metadata={}
        )
        
        # Verify multi-intent handling
        assert multi_intent_state["detected_intent"] == "order"
        assert len(multi_intent_state["secondary_intents"]) == 2
        assert multi_intent_state["secondary_intents"][0]["intent"] == "faq"
        assert multi_intent_state["secondary_intents"][1]["intent"] == "menu_browse"
        assert multi_intent_state["cross_domain_detected"] is True
        assert "order process" in multi_intent_state["response_guidance"]["priority_information"]
        assert "hours" in multi_intent_state["response_guidance"]["priority_information"]
    
    def test_enhanced_state_with_escalation(self):
        """Test state with human escalation"""
        escalation_state = SimplifiedStateSchema(
            user_message="I need to cancel my reservation and get a refund",
            user_id="user123",
            conversation_id="conv456",
            detected_language="en",
            detected_intent="reservation_cancel",
            intent_confidence=0.9,
            intent_reasoning="User wants to cancel reservation",
            secondary_intents=[],
            target_namespace="faq",
            namespace_confidence=0.9,
            fallback_namespaces=[],
            cross_domain_detected=False,
            routing_reasoning="Cancellation goes to FAQ",
            requires_human=True,
            escalation_confidence=0.95,
            escalation_reason="Refund requests require human assistance",
            escalation_urgency="high",
            escalation_triggers=["refund_request", "cancellation"],
            hitl_reasoning="Financial transactions need human oversight",
            cultural_context={
                "formality_level": "formal",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "english_only"
            },
            cultural_confidence=0.9,
            cultural_reasoning="Formal request",
            entity_extraction={
                "food_items": [],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": ["refund", "cancellation"]
            },
            extraction_confidence=0.9,
            entity_reasoning="Extracted refund and cancellation requests",
            response_guidance={
                "tone": "professional",
                "language": "english",
                "include_greeting": True,
                "include_farewell": True,
                "response_length": "medium",
                "priority_information": ["escalation", "contact_info"]
            },
            guidance_confidence=0.9,
            guidance_reasoning="Professional escalation response",
            analysis_confidence=0.92,
            quality_score=0.9,
            fallback_required=False,
            fallback_reason="",
            processing_time_estimate="2-3 seconds",
            recommendations=["Escalate to human", "Provide contact info"],
            rag_results=[],
            relevance_score=0.0,
            rag_enabled=False,
            human_handling=True,
            response="",
            response_generated=False,
            response_quality="",
            conversation_history=[],
            conversation_state="active",
            memory_updated=False,
            response_time=0,
            platform="messenger",
            metadata={}
        )
        
        # Verify escalation handling
        assert escalation_state["requires_human"] is True
        assert escalation_state["escalation_confidence"] == 0.95
        assert escalation_state["escalation_urgency"] == "high"
        assert len(escalation_state["escalation_triggers"]) == 2
        assert "refund_request" in escalation_state["escalation_triggers"]
        assert escalation_state["rag_enabled"] is False
        assert escalation_state["human_handling"] is True
        assert escalation_state["response_guidance"]["tone"] == "professional"
        assert "escalation" in escalation_state["response_guidance"]["priority_information"]
    
    def test_log_simplified_state_transition(self):
        """Test state transition logging"""
        test_state = {
            "user_id": "user123",
            "conversation_id": "conv456",
            "detected_language": "en",
            "detected_intent": "faq",
            "rag_enabled": True,
            "human_handling": False
        }
        
        # This should not raise any exceptions
        log_simplified_state_transition("unified_analysis", "rag_retriever", test_state)


if __name__ == "__main__":
    pytest.main([__file__])
