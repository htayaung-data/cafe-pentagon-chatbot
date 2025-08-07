"""
Test Decision Router Node
Tests the new DecisionRouterNode that makes routing decisions based on analysis results
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.nodes.decision_router_node import DecisionRouterNode


class TestDecisionRouterNode:
    """Test Decision Router Node functionality"""
    
    @pytest.fixture
    def decision_router(self):
        return DecisionRouterNode()
    
    @pytest.fixture
    def sample_analysis_result(self):
        return {
            "detected_language": "my",
            "primary_intent": "menu_browse",
            "intent_confidence": 0.85,
            "requires_search": True,
            "search_context": {
                "namespace": "menu",
                "keywords": ["noodles", "ခေါက်ဆွဲ"],
                "semantic_query": "What types of noodles are available?"
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "burmese_only"
            },
            "conversation_context": {
                "is_follow_up": False,
                "previous_intent": None,
                "clarification_needed": False
            },
            "user_message": "ခေါက်ဆွဲ ဘာတွေ ရှိလဲ"
        }
    
    @pytest.mark.asyncio
    async def test_menu_search_decision(self, decision_router, sample_analysis_result):
        """Test routing decision for menu search"""
        state = {
            "user_message": "ခေါက်ဆွဲ ဘာတွေ ရှိလဲ",
            "analysis_result": sample_analysis_result,
            "detected_language": "my",
            "primary_intent": "menu_browse",
            "intent_confidence": 0.85,
            "requires_search": True
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["escalation_reason"] is None
        assert result["decision_confidence"] == 0.85
        assert "Search required for menu_browse intent" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_greeting_direct_response(self, decision_router):
        """Test routing decision for greeting (direct response)"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "greeting",
            "intent_confidence": 0.95,
            "requires_search": False,
            "user_message": "မင်္ဂလာပါ ခင်ဗျာ"
        }
        
        state = {
            "user_message": "မင်္ဂလာပါ ခင်ဗျာ",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "greeting",
            "intent_confidence": 0.95,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "direct_response"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is False
        assert result["escalation_reason"] is None
        assert result["decision_confidence"] == 0.9
        assert "Direct response for greeting intent" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_escalation_request_detection(self, decision_router):
        """Test routing decision for escalation requests (LLM-based)"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "human_assistance",
            "intent_confidence": 0.5,
            "requires_search": False,
            "user_message": "လူသားနဲ့ပြောချင်ပါတယ်"
        }
        
        state = {
            "user_message": "လူသားနဲ့ပြောချင်ပါတယ်",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "human_assistance",
            "intent_confidence": 0.5,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "escalate_to_human"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is True
        assert result["escalation_reason"] == "User requested human assistance"
        assert result["decision_confidence"] == 0.95
        assert "User explicitly requested human assistance" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_low_confidence_escalation(self, decision_router):
        """Test routing decision for low confidence queries"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.2,
            "requires_search": False,
            "user_message": "ဘာ"
        }
        
        state = {
            "user_message": "ဘာ",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.2,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "escalate_to_human"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is True
        assert result["escalation_reason"] == "Low confidence in intent classification"
        assert result["decision_confidence"] == 0.8
        assert "Intent confidence (0.2) is too low for automated response" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_ambiguous_query_escalation(self, decision_router):
        """Test routing decision for ambiguous queries"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.4,
            "requires_search": False,
            "user_message": "ဘာ",
            "cultural_context": {
                "language_mix": "burmese_only"
            }
        }
        
        state = {
            "user_message": "ဘာ",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.4,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision - with confidence 0.4, it should perform search, not escalate
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["escalation_reason"] is None
        assert result["decision_confidence"] == 0.5
        assert "Unknown intent" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_order_placement_escalation(self, decision_router):
        """Test routing decision for order placement"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "order_place",
            "intent_confidence": 0.9,
            "requires_search": False,
            "user_message": "ခေါက်ဆွဲ မှာယူချင်ပါတယ်"
        }
        
        state = {
            "user_message": "ခေါက်ဆွဲ မှာယူချင်ပါတယ်",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "order_place",
            "intent_confidence": 0.9,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "escalate_to_human"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is True
        assert result["escalation_reason"] == "Order placement requires human assistance"
        assert result["decision_confidence"] == 0.9
        assert "Order placement is complex" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_reservation_escalation(self, decision_router):
        """Test routing decision for reservation requests"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "reservation",
            "intent_confidence": 0.9,
            "requires_search": False,
            "user_message": "စားပွဲ ကြိုတင်မှာယူချင်ပါတယ်"
        }
        
        state = {
            "user_message": "စားပွဲ ကြိုတင်မှာယူချင်ပါတယ်",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "reservation",
            "intent_confidence": 0.9,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "escalate_to_human"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is True
        assert result["escalation_reason"] == "Reservation requests require human assistance"
        assert result["decision_confidence"] == 0.9
        assert "Reservation requests are complex" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_faq_search_decision(self, decision_router):
        """Test routing decision for FAQ queries"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "faq",
            "intent_confidence": 0.8,
            "requires_search": True,
            "user_message": "ဘယ်အချိန်ဖွင့်လဲ"
        }
        
        state = {
            "user_message": "ဘယ်အချိန်ဖွင့်လဲ",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "faq",
            "intent_confidence": 0.8,
            "requires_search": True
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["escalation_reason"] is None
        assert result["decision_confidence"] == 0.85
        assert "Search required for faq intent" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_job_application_search(self, decision_router):
        """Test routing decision for job application queries"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "job_application",
            "intent_confidence": 0.8,
            "requires_search": True,
            "user_message": "အလုပ်ရှိလား"
        }
        
        state = {
            "user_message": "အလုပ်ရှိလား",
            "analysis_result": analysis_result,
            "detected_language": "my",
            "primary_intent": "job_application",
            "intent_confidence": 0.8,
            "requires_search": True
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["escalation_reason"] is None
        assert result["decision_confidence"] == 0.85
        assert "Search required for job_application intent" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_english_escalation_detection(self, decision_router):
        """Test routing decision for English escalation requests"""
        analysis_result = {
            "detected_language": "en",
            "primary_intent": "unknown",
            "intent_confidence": 0.5,
            "requires_search": False,
            "user_message": "I need to talk to a human"
        }
        
        state = {
            "user_message": "I need to talk to a human",
            "analysis_result": analysis_result,
            "detected_language": "en",
            "primary_intent": "unknown",
            "intent_confidence": 0.5,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify routing decision - with confidence 0.5, it should perform search, not escalate
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["escalation_reason"] is None
        assert result["decision_confidence"] == 0.5
        assert "Unknown intent" in result["decision_reasoning"]
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, decision_router):
        """Test handling of empty messages"""
        state = {
            "user_message": "",
            "analysis_result": {},
            "detected_language": "en",
            "primary_intent": "unknown",
            "intent_confidence": 0.0,
            "requires_search": False
        }
        
        result = await decision_router.process(state)
        
        # Verify default decision
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["decision_confidence"] == 0.5
        assert "Default fallback decision" in result["decision_reasoning"]
    
    # Removed test_escalation_keyword_detection - no longer using pattern matching for escalation
    
    def test_ambiguous_query_detection(self, decision_router):
        """Test ambiguous query detection"""
        # Test very short queries
        short_queries = ["ဘာ", "what", "how", "when"]
        
        for query in short_queries:
            analysis_result = {"user_message": query}
            is_ambiguous = decision_router._is_ambiguous_query(analysis_result, "unknown")
            assert is_ambiguous is True, f"Failed to detect ambiguity in: {query}"
        
        # Test unknown intent
        analysis_result = {"user_message": "some message"}
        is_ambiguous = decision_router._is_ambiguous_query(analysis_result, "unknown")
        assert is_ambiguous is True, "Failed to detect ambiguity for unknown intent"
        
        # Test mixed language short query
        analysis_result = {
            "user_message": "hello ဘာ",
            "cultural_context": {"language_mix": "mixed"}
        }
        is_ambiguous = decision_router._is_ambiguous_query(analysis_result, "unknown")
        assert is_ambiguous is True, "Failed to detect ambiguity in mixed language short query"
