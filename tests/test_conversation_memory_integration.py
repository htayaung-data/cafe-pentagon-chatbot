"""
Integration Test for Conversation Memory System
Tests the complete conversation memory integration with LangGraph workflow
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.graph.state_graph import create_conversation_graph, create_initial_state
from src.services.conversation_memory_service import get_conversation_memory_service


class TestConversationMemoryIntegration:
    """Test conversation memory integration with LangGraph workflow"""
    
    @pytest.fixture
    def conversation_graph(self):
        return create_conversation_graph()
    
    @pytest.fixture
    def memory_service(self):
        return get_conversation_memory_service()
    
    @pytest.mark.asyncio
    async def test_conversation_memory_in_workflow(self, conversation_graph, memory_service):
        """Test that conversation memory is properly integrated in the workflow"""
        
        # Mock the conversation memory service
        with patch('src.services.conversation_memory_service.get_conversation_memory_service', return_value=memory_service):
            with patch.object(memory_service, 'load_conversation_history', return_value=[]):
                with patch.object(memory_service, 'add_message_to_history', return_value=True):
                    with patch.object(memory_service, 'update_conversation_context', return_value=True):
                    
                        # Create initial state with conversation memory  
                        initial_state = create_initial_state(
                            user_message="Hello",
                            user_id="test_user",
                            conversation_id="550e8400-e29b-41d4-a716-446655440000",
                            platform="test"
                        )
                    
                    # Verify conversation history is loaded
                    assert "conversation_history" in initial_state
                    assert isinstance(initial_state["conversation_history"], list)
                    
                    # Mock the workflow nodes to avoid actual processing
                    with patch('src.graph.nodes.pattern_matcher.PatternMatcherNode.process') as mock_pattern:
                        with patch('src.graph.nodes.intent_classifier.IntentClassifierNode.process') as mock_intent:
                            with patch('src.graph.nodes.rag_controller.RAGControllerNode.process') as mock_rag_control:
                                with patch('src.graph.nodes.rag_retriever.RAGRetrieverNode.process') as mock_rag_retrieve:
                                    with patch('src.graph.nodes.response_generator.ResponseGeneratorNode.process') as mock_response:
                                        with patch('src.graph.nodes.conversation_memory_updater.ConversationMemoryUpdaterNode.process') as mock_memory:
                                            
                                            # Mock each node to return appropriate state
                                            mock_pattern.return_value = {
                                                **initial_state,
                                                "detected_language": "en",
                                                "is_greeting": True
                                            }
                                            
                                            mock_intent.return_value = {
                                                **initial_state,
                                                "detected_language": "en",
                                                "is_greeting": True,
                                                "detected_intent": "greeting",
                                                "intent_confidence": 0.9
                                            }
                                            
                                            mock_rag_control.return_value = {
                                                **initial_state,
                                                "detected_language": "en",
                                                "is_greeting": True,
                                                "detected_intent": "greeting",
                                                "intent_confidence": 0.9,
                                                "rag_enabled": True
                                            }
                                            
                                            mock_rag_retrieve.return_value = {
                                                **initial_state,
                                                "detected_language": "en",
                                                "is_greeting": True,
                                                "detected_intent": "greeting",
                                                "intent_confidence": 0.9,
                                                "rag_enabled": True,
                                                "rag_results": []
                                            }
                                            
                                            mock_response.return_value = {
                                                **initial_state,
                                                "detected_language": "en",
                                                "is_greeting": True,
                                                "detected_intent": "greeting",
                                                "intent_confidence": 0.9,
                                                "rag_enabled": True,
                                                "rag_results": [],
                                                "response": "Hello! How can I help you?",
                                                "response_generated": True
                                            }
                                            
                                            mock_memory.return_value = {
                                                **initial_state,
                                                "detected_language": "en",
                                                "is_greeting": True,
                                                "detected_intent": "greeting",
                                                "intent_confidence": 0.9,
                                                "rag_enabled": True,
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
                                            memory_service.add_message_to_history.assert_called()
                                            memory_service.update_conversation_context.assert_called_once()
    
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
        
        with patch('src.services.conversation_memory_service.get_conversation_memory_service', return_value=memory_service):
            with patch.object(memory_service, 'load_conversation_history', return_value=initial_history):
                with patch.object(memory_service, 'add_message_to_history', return_value=True):
                    with patch.object(memory_service, 'update_conversation_context', return_value=True):
                    
                    # Create initial state for second message
                    initial_state = create_initial_state(
                        user_message="What's on the menu?",
                        user_id=user_id,
                        conversation_id=conversation_id,
                        platform="test"
                    )
                    
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
        
        with patch('src.services.conversation_memory_service.get_conversation_memory_service', return_value=memory_service):
            with patch.object(memory_service, 'load_conversation_history', return_value=burmese_history):
                with patch.object(memory_service, 'add_message_to_history', return_value=True):
                    with patch.object(memory_service, 'update_conversation_context', return_value=True):
                    
                    # Create initial state for Burmese message
                    initial_state = create_initial_state(
                        user_message="မီနူးထဲ ဘာတွေ ရှိလဲ?",
                        user_id=user_id,
                        conversation_id=conversation_id,
                        platform="test"
                    )
                    
                    # Verify Burmese conversation history is loaded
                    assert len(initial_state["conversation_history"]) == 2
                    assert initial_state["conversation_history"][0]["content"] == "မင်္ဂလာပါ"
                    assert initial_state["conversation_history"][0]["language"] == "my"
                    assert initial_state["conversation_history"][1]["language"] == "my" 