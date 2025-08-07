"""
Enhanced Unified Prompt Controller Tests
Tests the comprehensive structured JSON output schema with confidence scoring and multi-intent support
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from src.controllers.unified_prompt_controller import UnifiedPromptController
from src.utils.api_client import get_openai_client, get_fallback_manager


class TestEnhancedUnifiedPromptController:
    """Test enhanced unified prompt controller functionality"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API client for testing"""
        with patch('src.controllers.unified_prompt_controller.get_openai_client') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """Mock fallback manager for testing"""
        with patch('src.controllers.unified_prompt_controller.get_fallback_manager') as mock:
            manager = MagicMock()
            mock.return_value = manager
            yield manager
    
    @pytest.fixture
    def controller(self, mock_api_client, mock_fallback_manager):
        """Create enhanced unified prompt controller for testing with mocked dependencies"""
        controller = UnifiedPromptController()
        controller.api_client = mock_api_client
        controller.fallback_manager = mock_fallback_manager
        return controller
    
    def test_enhanced_prompt_structure(self):
        """Test that enhanced prompt contains all required sections"""
        controller = UnifiedPromptController()
        prompt = controller.fallback_prompt
        
        # Check for enhanced JSON structure sections
        assert "intent_analysis" in prompt
        assert "namespace_routing" in prompt
        assert "hitl_assessment" in prompt
        assert "cultural_context" in prompt
        assert "entity_extraction" in prompt
        assert "response_guidance" in prompt
        assert "overall_analysis" in prompt
        
        # Check for confidence scoring guidelines
        assert "CONFIDENCE SCORING GUIDELINES" in prompt
        assert "0.9-1.0: Very high confidence" in prompt
        assert "0.0-0.29: Very low confidence" in prompt
        
        # Check for fallback logic
        assert "FALLBACK LOGIC" in prompt
        assert "primary_confidence < 0.5" in prompt
        assert "overall_confidence < 0.3" in prompt
    
    def test_enhanced_json_schema_structure(self):
        """Test that enhanced JSON schema has correct structure"""
        controller = UnifiedPromptController()
        prompt = controller.fallback_prompt
        
        # Extract JSON schema from prompt
        json_start = prompt.find('ENHANCED OUTPUT FORMAT (JSON):')
        json_end = prompt.find('CONFIDENCE SCORING GUIDELINES:')
        
        if json_start != -1 and json_end != -1:
            json_section = prompt[json_start:json_end]
            
            # Check for all required top-level keys
            assert '"intent_analysis"' in json_section
            assert '"namespace_routing"' in json_section
            assert '"hitl_assessment"' in json_section
            assert '"cultural_context"' in json_section
            assert '"entity_extraction"' in json_section
            assert '"response_guidance"' in json_section
            assert '"overall_analysis"' in json_section
    
    @pytest.mark.asyncio
    async def test_parse_enhanced_json_response_success(self):
        """Test successful parsing of enhanced JSON response"""
        controller = UnifiedPromptController()
        # Sample enhanced JSON response
        sample_response = '''
        {
          "intent_analysis": {
            "primary_intent": "menu_browse",
            "primary_confidence": 0.85,
            "secondary_intents": [
              {
                "intent": "faq",
                "confidence": 0.45,
                "reasoning": "User also asked about availability"
              }
            ],
            "overall_confidence": 0.75,
            "intent_reasoning": "User is primarily asking about menu items"
          },
          "namespace_routing": {
            "primary_namespace": "menu",
            "primary_confidence": 0.85,
            "fallback_namespaces": [
              {
                "namespace": "faq",
                "confidence": 0.45,
                "reasoning": "Backup for general questions"
              }
            ],
            "routing_confidence": 0.80,
            "cross_domain_detected": false,
            "routing_reasoning": "Clear menu-related query"
          },
          "hitl_assessment": {
            "requires_human": false,
            "escalation_confidence": 0.15,
            "escalation_reason": null,
            "escalation_urgency": "low",
            "escalation_triggers": [],
            "hitl_reasoning": "Standard menu inquiry, no human intervention needed"
          },
          "cultural_context": {
            "formality_level": "casual",
            "uses_honorifics": false,
            "honorifics_detected": [],
            "cultural_nuances": [],
            "language_mix": "english_only",
            "cultural_confidence": 0.90,
            "cultural_reasoning": "Standard English query"
          },
          "entity_extraction": {
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
            "special_requests": [],
            "extraction_confidence": 0.85,
            "entity_reasoning": "Extracted food item 'pizza'"
          },
          "response_guidance": {
            "tone": "friendly",
            "language": "english",
            "include_greeting": false,
            "include_farewell": false,
            "response_length": "medium",
            "priority_information": ["menu items", "pizza options"],
            "guidance_confidence": 0.80,
            "guidance_reasoning": "Provide menu information in friendly tone"
          },
          "overall_analysis": {
            "analysis_confidence": 0.82,
            "quality_score": 0.85,
            "fallback_required": false,
            "fallback_reason": null,
            "processing_time_estimate": "2-3 seconds",
            "recommendations": ["Provide menu categories", "Include pricing"]
          }
        }
        '''
        
        result = controller._parse_enhanced_json_response(sample_response)
        
        # Verify all sections are present
        assert "intent_analysis" in result
        assert "namespace_routing" in result
        assert "hitl_assessment" in result
        assert "cultural_context" in result
        assert "entity_extraction" in result
        assert "response_guidance" in result
        assert "overall_analysis" in result
        
        # Verify specific values
        assert result["intent_analysis"]["primary_intent"] == "menu_browse"
        assert result["intent_analysis"]["primary_confidence"] == 0.85
        assert len(result["intent_analysis"]["secondary_intents"]) == 1
        assert result["namespace_routing"]["primary_namespace"] == "menu"
        assert result["hitl_assessment"]["requires_human"] is False
        assert result["overall_analysis"]["analysis_confidence"] == 0.82
    
    @pytest.mark.asyncio
    async def test_parse_enhanced_json_response_with_markdown(self, controller):
        """Test parsing JSON response wrapped in markdown code blocks"""
        markdown_response = '''
        ```json
        {
          "intent_analysis": {
            "primary_intent": "greeting",
            "primary_confidence": 0.95,
            "secondary_intents": [],
            "overall_confidence": 0.95,
            "intent_reasoning": "Clear greeting"
          },
          "namespace_routing": {
            "primary_namespace": "faq",
            "primary_confidence": 0.95,
            "fallback_namespaces": [],
            "routing_confidence": 0.95,
            "cross_domain_detected": false,
            "routing_reasoning": "Greeting goes to FAQ"
          },
          "hitl_assessment": {
            "requires_human": false,
            "escalation_confidence": 0.05,
            "escalation_reason": null,
            "escalation_urgency": "low",
            "escalation_triggers": [],
            "hitl_reasoning": "Standard greeting"
          },
          "cultural_context": {
            "formality_level": "casual",
            "uses_honorifics": false,
            "honorifics_detected": [],
            "cultural_nuances": [],
            "language_mix": "english_only",
            "cultural_confidence": 0.95,
            "cultural_reasoning": "Standard English greeting"
          },
          "entity_extraction": {
            "food_items": [],
            "locations": [],
            "time_references": [],
            "quantities": [],
            "special_requests": [],
            "extraction_confidence": 0.95,
            "entity_reasoning": "No entities in greeting"
          },
          "response_guidance": {
            "tone": "friendly",
            "language": "english",
            "include_greeting": true,
            "include_farewell": false,
            "response_length": "short",
            "priority_information": [],
            "guidance_confidence": 0.95,
            "guidance_reasoning": "Respond with greeting"
          },
          "overall_analysis": {
            "analysis_confidence": 0.95,
            "quality_score": 0.95,
            "fallback_required": false,
            "fallback_reason": null,
            "processing_time_estimate": "1-2 seconds",
            "recommendations": []
          }
        }
        ```
        '''
        
        result = controller._parse_enhanced_json_response(markdown_response)
        
        # Verify parsing worked correctly
        assert result["intent_analysis"]["primary_intent"] == "greeting"
        assert result["intent_analysis"]["primary_confidence"] == 0.95
        assert result["namespace_routing"]["primary_namespace"] == "faq"
    
    @pytest.mark.asyncio
    async def test_update_state_with_enhanced_analysis(self, controller):
        """Test state update with enhanced analysis results"""
        # Sample enhanced analysis
        analysis = {
            "intent_analysis": {
                "primary_intent": "menu_browse",
                "primary_confidence": 0.85,
                "secondary_intents": [
                    {"intent": "faq", "confidence": 0.45, "reasoning": "Backup"}
                ],
                "overall_confidence": 0.75,
                "intent_reasoning": "Menu inquiry"
            },
            "namespace_routing": {
                "primary_namespace": "menu",
                "primary_confidence": 0.85,
                "fallback_namespaces": [
                    {"namespace": "faq", "confidence": 0.45, "reasoning": "Backup"}
                ],
                "routing_confidence": 0.80,
                "cross_domain_detected": False,
                "routing_reasoning": "Menu query"
            },
            "hitl_assessment": {
                "requires_human": False,
                "escalation_confidence": 0.15,
                "escalation_reason": None,
                "escalation_urgency": "low",
                "escalation_triggers": [],
                "hitl_reasoning": "No escalation needed"
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "english_only",
                "cultural_confidence": 0.90,
                "cultural_reasoning": "English query"
            },
            "entity_extraction": {
                "food_items": [
                    {"item": "pizza", "confidence": 0.85, "category": "main_dish"}
                ],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": [],
                "extraction_confidence": 0.85,
                "entity_reasoning": "Extracted pizza"
            },
            "response_guidance": {
                "tone": "friendly",
                "language": "english",
                "include_greeting": False,
                "include_farewell": False,
                "response_length": "medium",
                "priority_information": ["menu", "pizza"],
                "guidance_confidence": 0.80,
                "guidance_reasoning": "Friendly menu response"
            },
            "overall_analysis": {
                "analysis_confidence": 0.82,
                "quality_score": 0.85,
                "fallback_required": False,
                "fallback_reason": None,
                "processing_time_estimate": "2-3 seconds",
                "recommendations": ["Show menu", "Include prices"]
            }
        }
        
        initial_state = {
            "user_message": "What's on the menu?",
            "detected_language": "en"
        }
        
        updated_state = controller._update_state_with_enhanced_analysis(initial_state, analysis)
        
        # Verify intent analysis
        assert updated_state["detected_intent"] == "menu_browse"
        assert updated_state["intent_confidence"] == 0.85
        assert updated_state["intent_reasoning"] == "Menu inquiry"
        assert len(updated_state["secondary_intents"]) == 1
        
        # Verify namespace routing
        assert updated_state["target_namespace"] == "menu"
        assert updated_state["namespace_confidence"] == 0.80
        assert len(updated_state["fallback_namespaces"]) == 1
        assert updated_state["cross_domain_detected"] is False
        
        # Verify HITL assessment
        assert updated_state["requires_human"] is False
        assert updated_state["escalation_confidence"] == 0.15
        assert updated_state["escalation_urgency"] == "low"
        
        # Verify cultural context
        assert updated_state["cultural_context"]["formality_level"] == "casual"
        assert updated_state["cultural_confidence"] == 0.90
        
        # Verify entity extraction
        assert len(updated_state["entity_extraction"]["food_items"]) == 1
        assert updated_state["extraction_confidence"] == 0.85
        
        # Verify response guidance
        assert updated_state["response_guidance"]["tone"] == "friendly"
        assert updated_state["guidance_confidence"] == 0.80
        
        # Verify overall analysis
        assert updated_state["analysis_confidence"] == 0.82
        assert updated_state["quality_score"] == 0.85
        assert updated_state["fallback_required"] is False
        
        # Verify RAG control
        assert updated_state["rag_enabled"] is True
        assert updated_state["human_handling"] is False
    
    @pytest.mark.asyncio
    async def test_fallback_enhanced_analysis(self, controller, mock_fallback_manager):
        """Test fallback analysis when API fails"""
        # Mock fallback manager response
        mock_fallback_manager.get_fallback_intent.return_value = {
            "intent": "faq",
            "confidence": 0.6
        }
        
        initial_state = {
            "user_message": "What are your hours?",
            "detected_language": "en"
        }
        
        updated_state = controller._fallback_enhanced_analysis(
            initial_state, "What are your hours?", "en"
        )
        
        # Verify fallback was used
        mock_fallback_manager.get_fallback_intent.assert_called_once_with(
            "What are your hours?", "en"
        )
        
        # Verify state was updated with fallback values
        assert updated_state["detected_intent"] == "faq"
        assert updated_state["intent_confidence"] == 0.6
        assert updated_state["target_namespace"] == "faq"
        assert updated_state["requires_human"] is False
        assert updated_state["rag_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_set_default_enhanced_analysis(self, controller):
        """Test default analysis when processing fails"""
        initial_state = {
            "user_message": "",
            "detected_language": "en"
        }
        
        updated_state = controller._set_default_enhanced_analysis(initial_state)
        
        # Verify default values
        assert updated_state["detected_intent"] == "unknown"
        assert updated_state["intent_confidence"] == 0.0
        assert updated_state["target_namespace"] == "faq"
        assert updated_state["requires_human"] is False
        assert updated_state["rag_enabled"] is True
        assert updated_state["analysis_confidence"] == 0.0
        assert updated_state["fallback_required"] is False
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, controller, mock_api_client, mock_fallback_manager):
        """Test successful query processing with enhanced analysis"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
          "intent_analysis": {
            "primary_intent": "reservation",
            "primary_confidence": 0.90,
            "secondary_intents": [],
            "overall_confidence": 0.90,
            "intent_reasoning": "User wants to make reservation"
          },
          "namespace_routing": {
            "primary_namespace": "faq",
            "primary_confidence": 0.90,
            "fallback_namespaces": [],
            "routing_confidence": 0.90,
            "cross_domain_detected": false,
            "routing_reasoning": "Reservation goes to FAQ"
          },
          "hitl_assessment": {
            "requires_human": true,
            "escalation_confidence": 0.85,
            "escalation_reason": "Reservation requires human assistance",
            "escalation_urgency": "medium",
            "escalation_triggers": ["reservation_request"],
            "hitl_reasoning": "Reservations need human handling"
          },
          "cultural_context": {
            "formality_level": "formal",
            "uses_honorifics": false,
            "honorifics_detected": [],
            "cultural_nuances": [],
            "language_mix": "english_only",
            "cultural_confidence": 0.95,
            "cultural_reasoning": "Formal English request"
          },
          "entity_extraction": {
            "food_items": [],
            "locations": [],
            "time_references": [],
            "quantities": [],
            "special_requests": [],
            "extraction_confidence": 0.95,
            "entity_reasoning": "No specific entities"
          },
          "response_guidance": {
            "tone": "professional",
            "language": "english",
            "include_greeting": true,
            "include_farewell": true,
            "response_length": "medium",
            "priority_information": ["escalation", "human_assistance"],
            "guidance_confidence": 0.90,
            "guidance_reasoning": "Professional escalation response"
          },
          "overall_analysis": {
            "analysis_confidence": 0.92,
            "quality_score": 0.90,
            "fallback_required": false,
            "fallback_reason": null,
            "processing_time_estimate": "3-4 seconds",
            "recommendations": ["Escalate to human", "Provide contact info"]
          }
        }
        '''
        
        mock_api_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Mock cache
        mock_fallback_manager.get_cached_response = AsyncMock(return_value=None)
        mock_fallback_manager.cache_response = AsyncMock()
        mock_fallback_manager.is_cache_valid.return_value = False
        
        initial_state = {
            "user_message": "I want to make a reservation",
            "detected_language": "en",
            "conversation_history": []
        }
        
        updated_state = await controller.process_query(initial_state)
        
        # Verify API was called
        mock_api_client.chat_completion.assert_called_once()
        
        # Verify state was updated correctly
        assert updated_state["detected_intent"] == "reservation"
        assert updated_state["intent_confidence"] == 0.90
        assert updated_state["target_namespace"] == "faq"
        assert updated_state["requires_human"] is True
        assert updated_state["escalation_reason"] == "Reservation requires human assistance"
        assert updated_state["escalation_urgency"] == "medium"
        assert updated_state["rag_enabled"] is False
        assert updated_state["human_handling"] is True
        assert updated_state["analysis_confidence"] == 0.92
    
    @pytest.mark.asyncio
    async def test_process_query_with_cache(self, controller, mock_fallback_manager):
        """Test query processing with cached results"""
        # Mock cached response
        cached_analysis = {
            "intent_analysis": {
                "primary_intent": "greeting",
                "primary_confidence": 0.95,
                "secondary_intents": [],
                "overall_confidence": 0.95,
                "intent_reasoning": "Cached greeting"
            },
            "namespace_routing": {
                "primary_namespace": "faq",
                "primary_confidence": 0.95,
                "fallback_namespaces": [],
                "routing_confidence": 0.95,
                "cross_domain_detected": False,
                "routing_reasoning": "Cached routing"
            },
            "hitl_assessment": {
                "requires_human": False,
                "escalation_confidence": 0.05,
                "escalation_reason": None,
                "escalation_urgency": "low",
                "escalation_triggers": [],
                "hitl_reasoning": "Cached HITL"
            },
            "cultural_context": {
                "formality_level": "casual",
                "uses_honorifics": False,
                "honorifics_detected": [],
                "cultural_nuances": [],
                "language_mix": "english_only",
                "cultural_confidence": 0.95,
                "cultural_reasoning": "Cached cultural"
            },
            "entity_extraction": {
                "food_items": [],
                "locations": [],
                "time_references": [],
                "quantities": [],
                "special_requests": [],
                "extraction_confidence": 0.95,
                "entity_reasoning": "Cached entities"
            },
            "response_guidance": {
                "tone": "friendly",
                "language": "english",
                "include_greeting": True,
                "include_farewell": False,
                "response_length": "short",
                "priority_information": [],
                "guidance_confidence": 0.95,
                "guidance_reasoning": "Cached guidance"
            },
            "overall_analysis": {
                "analysis_confidence": 0.95,
                "quality_score": 0.95,
                "fallback_required": False,
                "fallback_reason": None,
                "processing_time_estimate": "1-2 seconds",
                "recommendations": []
            }
        }
        
        mock_fallback_manager.get_cached_response = AsyncMock(return_value=cached_analysis)
        mock_fallback_manager.is_cache_valid.return_value = True
        
        initial_state = {
            "user_message": "Hello",
            "detected_language": "en",
            "conversation_history": []
        }
        
        updated_state = await controller.process_query(initial_state)
        
        # Verify cache was used
        mock_fallback_manager.get_cached_response.assert_called_once()
        mock_fallback_manager.is_cache_valid.assert_called_once()
        
        # Verify state was updated with cached values
        assert updated_state["detected_intent"] == "greeting"
        assert updated_state["intent_confidence"] == 0.95
        assert updated_state["requires_human"] is False
        assert updated_state["rag_enabled"] is True
    
    def test_confidence_scoring_guidelines_in_prompt(self, controller):
        """Test that confidence scoring guidelines are properly included in prompt"""
        prompt = controller.fallback_prompt
        
        # Check for all confidence levels
        assert "0.9-1.0: Very high confidence" in prompt
        assert "0.7-0.89: High confidence" in prompt
        assert "0.5-0.69: Medium confidence" in prompt
        assert "0.3-0.49: Low confidence" in prompt
        assert "0.0-0.29: Very low confidence" in prompt
    
    def test_fallback_logic_in_prompt(self, controller):
        """Test that fallback logic is properly included in prompt"""
        prompt = controller.fallback_prompt
        
        # Check for fallback conditions
        assert "primary_confidence < 0.5" in prompt
        assert "overall_confidence < 0.3" in prompt
        assert "cross_domain_detected = true" in prompt
        assert "cultural_confidence < 0.4" in prompt
    
    def test_multi_intent_support_in_schema(self, controller):
        """Test that multi-intent support is included in JSON schema"""
        prompt = controller.fallback_prompt
        
        # Check for secondary intents structure
        assert '"secondary_intents"' in prompt
        assert '"intent"' in prompt
        assert '"confidence"' in prompt
        assert '"reasoning"' in prompt
    
    def test_fallback_namespaces_in_schema(self, controller):
        """Test that fallback namespaces are included in JSON schema"""
        prompt = controller.fallback_prompt
        
        # Check for fallback namespaces structure
        assert '"fallback_namespaces"' in prompt
        assert '"namespace"' in prompt
        assert '"routing_confidence"' in prompt
        assert '"cross_domain_detected"' in prompt


if __name__ == "__main__":
    pytest.main([__file__])
