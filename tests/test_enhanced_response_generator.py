"""
Test Enhanced Response Generator Node
Tests the enhanced ResponseGeneratorNode that works with the new two-LLM-call architecture
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.nodes.response_generator import ResponseGeneratorNode


class TestEnhancedResponseGeneratorNode:
    """Test Enhanced Response Generator Node functionality"""
    
    @pytest.fixture
    def response_generator(self):
        return ResponseGeneratorNode()
    
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
            }
        }
    
    @pytest.fixture
    def sample_routing_decision(self):
        return {
            "action_type": "perform_search",
            "rag_enabled": True,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.85,
            "reasoning": "Search required for menu_browse intent"
        }
    
    @pytest.mark.asyncio
    async def test_menu_search_response(self, response_generator, sample_analysis_result, sample_routing_decision):
        """Test response generation for menu search with RAG results"""
        state = {
            "user_message": "ခေါက်ဆွဲ ဘာတွေ ရှိလဲ",
            "analysis_result": sample_analysis_result,
            "routing_decision": sample_routing_decision,
            "rag_results": [
                {
                    "content": "Pad Thai - Traditional Thai noodles with shrimp and vegetables",
                    "metadata": {
                        "name": "Pad Thai",
                        "myanmar_name": "ပါဒ်ထိုင်း",
                        "price": 12000,
                        "currency": "MMK",
                        "description": "Traditional Thai noodles with shrimp and vegetables"
                    },
                    "score": 0.85,
                    "source": "menu"
                }
            ]
        }
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "ကျနော်တို့ရဲ့ ခေါက်ဆွဲမီနူးမှာ ပါဒ်ထိုင်း ရှိပါတယ်။ ဈေးနှုန်းက ၁၂,၀၀၀ ကျပ်ဖြစ်ပါတယ်။"
        
        # Create a mock LLM and replace the original
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        response_generator.llm = mock_llm
        
        result = await response_generator.process(state)
        
        # Verify response generation
        assert result["response_generated"] is True
        assert "ပါဒ်ထိုင်း" in result["response"]
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
        assert result["response_quality"] in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_greeting_direct_response(self, response_generator):
        """Test direct response for greeting"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "greeting",
            "intent_confidence": 0.95,
            "cultural_context": {
                "formality_level": "formal",
                "uses_honorifics": True,
                "language_mix": "burmese_only"
            }
        }
        
        routing_decision = {
            "action_type": "direct_response",
            "rag_enabled": False,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.9
        }
        
        state = {
            "user_message": "မင်္ဂလာပါ ခင်ဗျာ",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": []
        }
        
        result = await response_generator.process(state)
        
        # Verify greeting response
        assert result["response_generated"] is True
        assert "မင်္ဂလာပါ" in result["response"]
        assert "ခင်ဗျာ" in result["response"]
        assert result["action_type"] == "direct_response"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is False
    
    @pytest.mark.asyncio
    async def test_escalation_response(self, response_generator):
        """Test escalation response generation"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.2,
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "burmese_only"
            }
        }
        
        routing_decision = {
            "action_type": "escalate_to_human",
            "rag_enabled": False,
            "human_handling": True,
            "escalation_reason": "Low confidence in intent classification",
            "confidence": 0.8
        }
        
        state = {
            "user_message": "ဘာ",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": []
        }
        
        result = await response_generator.process(state)
        
        # Verify escalation response
        assert result["response_generated"] is True
        assert "ခဏစောင့်ပေးပါ" in result["response"]
        assert "ဝန်ထမ်း" in result["response"]
        assert result["action_type"] == "escalate_to_human"
        assert result["rag_enabled"] is False
        assert result["human_handling"] is True
        assert result["escalation_reason"] == "Low confidence in intent classification"
    
    @pytest.mark.asyncio
    async def test_english_menu_response(self, response_generator):
        """Test English menu response generation"""
        analysis_result = {
            "detected_language": "en",
            "primary_intent": "menu_browse",
            "intent_confidence": 0.9,
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "english_only"
            }
        }
        
        routing_decision = {
            "action_type": "perform_search",
            "rag_enabled": True,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.9
        }
        
        state = {
            "user_message": "What noodles do you have?",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": [
                {
                    "content": "Pad Thai - Traditional Thai noodles with shrimp and vegetables",
                    "metadata": {
                        "name": "Pad Thai",
                        "price": 12000,
                        "currency": "MMK",
                        "description": "Traditional Thai noodles with shrimp and vegetables"
                    },
                    "score": 0.9,
                    "source": "menu"
                }
            ]
        }
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "We have Pad Thai, which is traditional Thai noodles with shrimp and vegetables for 12,000 MMK."
        
        # Create a mock LLM and replace the original
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        response_generator.llm = mock_llm
        
        result = await response_generator.process(state)
        
        # Verify English response
        assert result["response_generated"] is True
        assert "Pad Thai" in result["response"]
        assert result["action_type"] == "perform_search"
        assert result["rag_enabled"] is True
        assert result["human_handling"] is False
    
    @pytest.mark.asyncio
    async def test_fallback_response(self, response_generator):
        """Test fallback response when no RAG results"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.3,
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "burmese_only"
            }
        }
        
        routing_decision = {
            "action_type": "perform_search",
            "rag_enabled": True,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.5
        }
        
        state = {
            "user_message": "ဘာတွေလဲ",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": []
        }
        
        result = await response_generator.process(state)
        
        # Verify fallback response
        assert result["response_generated"] is True
        assert "တောင်းပန်ပါတယ်" in result["response"]
        assert "+959979732781" in result["response"]
        assert result["response_quality"] == "low"
    
    @pytest.mark.asyncio
    async def test_cultural_context_formal_burmese(self, response_generator):
        """Test response generation with formal Burmese cultural context"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "greeting",
            "intent_confidence": 0.95,
            "cultural_context": {
                "formality_level": "very_formal",
                "uses_honorifics": True,
                "language_mix": "burmese_only"
            }
        }
        
        routing_decision = {
            "action_type": "direct_response",
            "rag_enabled": False,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.9
        }
        
        state = {
            "user_message": "မင်္ဂလာပါ ခင်ဗျာ",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": []
        }
        
        result = await response_generator.process(state)
        
        # Verify formal response
        assert result["response_generated"] is True
        assert "မင်္ဂလာပါ ခင်ဗျာ" in result["response"]
        assert "ခင်ဗျာ" in result["response"]  # Should include honorifics
    
    @pytest.mark.asyncio
    async def test_cultural_context_casual_burmese(self, response_generator):
        """Test response generation with casual Burmese cultural context"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "greeting",
            "intent_confidence": 0.95,
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "burmese_only"
            }
        }
        
        routing_decision = {
            "action_type": "direct_response",
            "rag_enabled": False,
            "human_handling": False,
            "escalation_reason": None,
            "confidence": 0.9
        }
        
        state = {
            "user_message": "မင်္ဂလာ",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": []
        }
        
        result = await response_generator.process(state)
        
        # Verify casual response
        assert result["response_generated"] is True
        assert "မင်္ဂလာ" in result["response"]
        # Should not include honorifics for casual context
    
    @pytest.mark.asyncio
    async def test_human_assistance_detection(self, response_generator):
        """Test human assistance request detection"""
        analysis_result = {
            "detected_language": "my",
            "primary_intent": "unknown",
            "intent_confidence": 0.5,
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "language_mix": "burmese_only"
            }
        }
        
        routing_decision = {
            "action_type": "escalate_to_human",
            "rag_enabled": False,
            "human_handling": True,
            "escalation_reason": "User requested human assistance",
            "confidence": 0.8
        }
        
        state = {
            "user_message": "လူသားနဲ့ပြောချင်ပါတယ်",
            "analysis_result": analysis_result,
            "routing_decision": routing_decision,
            "rag_results": []
        }
        
        result = await response_generator.process(state)
        
        # Verify human assistance detection
        assert result["requires_human"] is True
        assert result["human_handling"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling(self, response_generator, sample_analysis_result, sample_routing_decision):
        """Test error handling in response generation"""
        state = {
            "user_message": "ခေါက်ဆွဲ ဘာတွေ ရှိလဲ",
            "analysis_result": sample_analysis_result,
            "routing_decision": sample_routing_decision,
            "rag_results": [
                {
                    "content": "Pad Thai - Traditional Thai noodles",
                    "metadata": {"name": "Pad Thai"},
                    "score": 0.85,
                    "source": "menu"
                }
            ]
        }
        
        # Mock LLM to raise exception
        # Create a mock LLM that raises exception
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API Error")
        response_generator.llm = mock_llm
        
        result = await response_generator.process(state)
        
        # Verify fallback response on error
        assert result["response_generated"] is True
        assert result["response_quality"] == "fallback"
        assert "တောင်းပန်ပါတယ်" in result["response"]
    
    def test_response_quality_assessment(self, response_generator):
        """Test response quality assessment based on confidence scores"""
        # Test high quality
        quality = response_generator._assess_response_quality("test response", 0.9, 0.8)
        assert quality == "high"
        
        # Test medium quality
        quality = response_generator._assess_response_quality("test response", 0.6, 0.5)
        assert quality == "medium"
        
        # Test low quality
        quality = response_generator._assess_response_quality("test response", 0.2, 0.3)
        assert quality == "low"
    

