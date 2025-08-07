"""
Integration tests for conversation memory functionality
Tests memory loading, updating, and persistence in the conversation workflow
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.state_graph import create_conversation_graph
from src.services.conversation_memory_service import ConversationMemoryService


class TestConversationMemoryIntegration:
    """Test conversation memory integration with the workflow"""
    
    @pytest.fixture
    def conversation_graph(self):
        """Create conversation graph for testing"""
        return create_conversation_graph()
    
    @pytest.fixture
    def memory_service(self):
        """Create memory service for testing"""
        return ConversationMemoryService()
    
    @pytest.mark.asyncio
    async def test_conversation_memory_in_workflow(self, conversation_graph, memory_service):
        """Test that conversation memory is properly integrated in the workflow"""
        
        # Mock the memory service
        with patch('src.services.conversation_memory_service.ConversationMemoryService') as mock_memory_service_class:
            mock_memory_service = MagicMock()
            mock_memory_service_class.return_value = mock_memory_service
            
            # Mock conversation history loading
            mock_memory_service.load_conversation_history.return_value = [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "intent": "greeting",
                    "language": "en"
                }
            ]
            
            # Create initial state
            initial_state = {
                "user_message": "Hello",
                "user_id": "test_user_123",
                "session_id": "test_session_456",
                "conversation_history": []
            }
            
            # Verify conversation history is loaded
            assert "conversation_history" in initial_state
            assert isinstance(initial_state["conversation_history"], list)
            
            # Mock the workflow nodes to avoid actual processing
            with patch('src.graph.nodes.smart_analysis_node.SmartAnalysisNode.process') as mock_smart_analysis:
                with patch('src.graph.nodes.decision_router_node.DecisionRouterNode.process') as mock_decision_router:
                    with patch('src.graph.nodes.rag_retriever.RAGRetrieverNode.process') as mock_rag_retrieve:
                        with patch('src.graph.nodes.response_generator.ResponseGeneratorNode.process') as mock_response:
                            with patch('src.graph.nodes.conversation_memory_updater.ConversationMemoryUpdaterNode.process') as mock_memory:
                                
                                # Mock each node to return appropriate state
                                mock_smart_analysis.return_value = {
                                    **initial_state,
                                    "analysis_result": {
                                        "detected_language": "en",
                                        "primary_intent": "greeting",
                                        "intent_confidence": 0.9,
                                        "requires_search": False,
                                        "search_context": {
                                            "namespace": None,
                                            "keywords": [],
                                            "semantic_query": ""
                                        },
                                        "cultural_context": {
                                            "formality_level": "casual",
                                            "uses_honorifics": False,
                                            "language_mix": "english_only"
                                        },
                                        "conversation_context": {
                                            "is_follow_up": True,
                                            "previous_intent": "greeting",
                                            "clarification_needed": False
                                        }
                                    }
                                }
                                
                                mock_decision_router.return_value = {
                                    **initial_state,
                                    "analysis_result": {
                                        "detected_language": "en",
                                        "primary_intent": "greeting",
                                        "intent_confidence": 0.9,
                                        "requires_search": False,
                                        "search_context": {
                                            "namespace": None,
                                            "keywords": [],
                                            "semantic_query": ""
                                        },
                                        "cultural_context": {
                                            "formality_level": "casual",
                                            "uses_honorifics": False,
                                            "language_mix": "english_only"
                                        },
                                        "conversation_context": {
                                            "is_follow_up": True,
                                            "previous_intent": "greeting",
                                            "clarification_needed": False
                                        }
                                    },
                                    "routing_decision": {
                                        "action_type": "direct_response",
                                        "rag_enabled": False,
                                        "human_handling": False,
                                        "escalation_reason": None,
                                        "confidence": 0.9
                                    }
                                }
                                
                                mock_rag_retrieve.return_value = {
                                    **initial_state,
                                    "analysis_result": {
                                        "detected_language": "en",
                                        "primary_intent": "greeting",
                                        "intent_confidence": 0.9,
                                        "requires_search": False,
                                        "search_context": {
                                            "namespace": None,
                                            "keywords": [],
                                            "semantic_query": ""
                                        },
                                        "cultural_context": {
                                            "formality_level": "casual",
                                            "uses_honorifics": False,
                                            "language_mix": "english_only"
                                        },
                                        "conversation_context": {
                                            "is_follow_up": True,
                                            "previous_intent": "greeting",
                                            "clarification_needed": False
                                        }
                                    },
                                    "routing_decision": {
                                        "action_type": "direct_response",
                                        "rag_enabled": False,
                                        "human_handling": False,
                                        "escalation_reason": None,
                                        "confidence": 0.9
                                    },
                                    "rag_results": []
                                }
                                
                                mock_response.return_value = {
                                    **initial_state,
                                    "analysis_result": {
                                        "detected_language": "en",
                                        "primary_intent": "greeting",
                                        "intent_confidence": 0.9,
                                        "requires_search": False,
                                        "search_context": {
                                            "namespace": None,
                                            "keywords": [],
                                            "semantic_query": ""
                                        },
                                        "cultural_context": {
                                            "formality_level": "casual",
                                            "uses_honorifics": False,
                                            "language_mix": "english_only"
                                        },
                                        "conversation_context": {
                                            "is_follow_up": True,
                                            "previous_intent": "greeting",
                                            "clarification_needed": False
                                        }
                                    },
                                    "routing_decision": {
                                        "action_type": "direct_response",
                                        "rag_enabled": False,
                                        "human_handling": False,
                                        "escalation_reason": None,
                                        "confidence": 0.9
                                    },
                                    "rag_results": [],
                                    "response": "Hello! How can I help you?",
                                    "response_generated": True
                                }
                                
                                mock_memory.return_value = {
                                    **initial_state,
                                    "analysis_result": {
                                        "detected_language": "en",
                                        "primary_intent": "greeting",
                                        "intent_confidence": 0.9,
                                        "requires_search": False,
                                        "search_context": {
                                            "namespace": None,
                                            "keywords": [],
                                            "semantic_query": ""
                                        },
                                        "cultural_context": {
                                            "formality_level": "casual",
                                            "uses_honorifics": False,
                                            "language_mix": "english_only"
                                        },
                                        "conversation_context": {
                                            "is_follow_up": True,
                                            "previous_intent": "greeting",
                                            "clarification_needed": False
                                        }
                                    },
                                    "routing_decision": {
                                        "action_type": "direct_response",
                                        "rag_enabled": False,
                                        "human_handling": False,
                                        "escalation_reason": None,
                                        "confidence": 0.9
                                    },
                                    "rag_results": [],
                                    "response": "Hello! How can I help you?",
                                    "response_generated": True,
                                    "memory_updated": True,
                                    "conversation_history": [
                                        {
                                            "role": "user",
                                            "content": "Hello",
                                            "timestamp": "2024-01-01T10:00:00Z",
                                            "intent": "greeting",
                                            "language": "en"
                                        },
                                        {
                                            "role": "assistant",
                                            "content": "Hello! How can I help you?",
                                            "timestamp": "2024-01-01T10:00:01Z",
                                            "intent": "greeting",
                                            "language": "en"
                                        }
                                    ]
                                }
                                
                                # Run the workflow
                                compiled_workflow = conversation_graph.compile()
                                final_state = await compiled_workflow.ainvoke(initial_state)
                                
                                # Verify the workflow completed
                                assert final_state is not None
                                assert final_state.get("memory_updated") is True
                                assert "conversation_history" in final_state
                                assert len(final_state["conversation_history"]) == 2
                                
                                # Verify memory service was called
                                memory_service.load_conversation_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_conversation_memory_persistence(self, memory_service):
        """Test that conversation memory persists across multiple messages"""
        
        conversation_id = "550e8400-e29b-41d4-a716-446655440000"
        user_id = "test_user"
        
        # Mock conversation history loading
        initial_history = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2024-01-01T10:00:00Z",
                "intent": "greeting",
                "language": "en"
            },
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": "2024-01-01T10:00:01Z",
                "intent": "greeting",
                "language": "en"
            }
        ]
        
        with patch('src.services.conversation_memory_service.ConversationMemoryService') as mock_memory_service_class:
            mock_memory_service = MagicMock()
            mock_memory_service_class.return_value = mock_memory_service
            
            with patch.object(mock_memory_service, 'load_conversation_history', return_value=initial_history):
                with patch.object(mock_memory_service, 'add_message_to_history', return_value=True):
                    with patch.object(mock_memory_service, 'update_conversation_context', return_value=True):
                        
                        # Create initial state for second message
                        initial_state = {
                            "user_message": "What's on the menu?",
                            "user_id": user_id,
                            "session_id": "test_session_456",
                            "conversation_history": []
                        }
                    
                    # Verify previous conversation history is loaded
                    assert len(initial_state["conversation_history"]) == 2
                    assert initial_state["conversation_history"][0]["content"] == "Hello"
                    assert initial_state["conversation_history"][1]["content"] == "Hi there!"
                    
                    # Verify memory service was called to load history
                    memory_service.load_conversation_history.assert_called_once_with(
                        conversation_id, user_id, limit=10
                    )
    
    @pytest.mark.asyncio
    async def test_conversation_memory_with_burmese(self, memory_service):
        """Test conversation memory with Burmese language"""
        
        conversation_id = "550e8400-e29b-41d4-a716-446655440000"
        user_id = "test_user"
        
        # Mock Burmese conversation history
        burmese_history = [
            {
                "role": "user",
                "content": "မင်္ဂလာပါ",
                "timestamp": "2024-01-01T10:00:00Z",
                "intent": "greeting",
                "language": "my"
            },
            {
                "role": "assistant",
                "content": "မင်္ဂလာပါ! ဘယ်လိုကူညီပေးရမလဲ?",
                "timestamp": "2024-01-01T10:00:01Z",
                "intent": "greeting",
                "language": "my"
            }
        ]
        
        with patch('src.services.conversation_memory_service.ConversationMemoryService') as mock_memory_service_class:
            mock_memory_service = MagicMock()
            mock_memory_service_class.return_value = mock_memory_service
            
            with patch.object(mock_memory_service, 'load_conversation_history', return_value=burmese_history):
                with patch.object(mock_memory_service, 'add_message_to_history', return_value=True):
                    with patch.object(mock_memory_service, 'update_conversation_context', return_value=True):
                        
                        # Create initial state for Burmese message
                        initial_state = {
                            "user_message": "မီနူးထဲ ဘာတွေ ရှိလဲ?",
                            "user_id": user_id,
                            "session_id": "test_session_456",
                            "conversation_history": []
                        }
                    
                    # Verify Burmese conversation history is loaded
                    assert len(initial_state["conversation_history"]) == 2
                    assert initial_state["conversation_history"][0]["content"] == "မင်္ဂလာပါ"
                    assert initial_state["conversation_history"][0]["language"] == "my"
                    assert initial_state["conversation_history"][1]["language"] == "my" 