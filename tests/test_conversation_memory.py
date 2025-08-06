"""
Test Conversation Memory System
Tests the conversation memory loading, updating, and context management
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.conversation_memory_service import ConversationMemoryService
from src.graph.nodes.conversation_memory_updater import ConversationMemoryUpdaterNode


class TestConversationMemoryService:
    """Test conversation memory service functionality"""
    
    @pytest.fixture
    def memory_service(self):
        return ConversationMemoryService()
    
    @pytest.fixture
    def sample_conversation_history(self):
        return [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2024-01-01T10:00:00Z",
                "intent": "greeting",
                "language": "en",
                "conversation_state": "active"
            },
            {
                "role": "assistant", 
                "content": "Hi there! How can I help you today?",
                "timestamp": "2024-01-01T10:00:01Z",
                "intent": "greeting",
                "language": "en",
                "conversation_state": "active"
            }
        ]
    
    def test_load_conversation_history_from_cache(self, memory_service, sample_conversation_history):
        """Test loading conversation history from cache"""
        # Mock cache to return history
        with patch.object(memory_service.cache, 'get', return_value=sample_conversation_history):
            history = memory_service.load_conversation_history("test_conv_id", "test_user", limit=5)
            
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"
    
    def test_load_conversation_history_from_database(self, memory_service, sample_conversation_history):
        """Test loading conversation history from database"""
        # Mock cache to return None (cache miss)
        with patch.object(memory_service.cache, 'get', return_value=None):
            # Mock database to return messages
            db_messages = [
                {
                    "id": "msg1",
                    "sender_type": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "metadata": {"intent": "greeting", "user_language": "en", "conversation_state": "active"}
                },
                {
                    "id": "msg2", 
                    "sender_type": "bot",
                    "content": "Hi there!",
                    "timestamp": "2024-01-01T10:00:01Z",
                    "metadata": {"intent": "greeting", "user_language": "en", "conversation_state": "active"}
                }
            ]
            
            with patch.object(memory_service.conversation_tracking, 'get_conversation_messages', return_value=db_messages):
                with patch.object(memory_service.cache, 'set') as mock_set:
                    history = memory_service.load_conversation_history("test_conv_id", "test_user", limit=5)
                    
                    assert len(history) == 2
                    assert history[0]["role"] == "user"
                    assert history[1]["role"] == "assistant"
                    
                    # Verify cache was updated
                    mock_set.assert_called_once()
    
    def test_add_message_to_history(self, memory_service):
        """Test adding message to conversation history"""
        with patch.object(memory_service.cache, 'get', return_value=[]):
            with patch.object(memory_service.cache, 'set') as mock_set:
                success = memory_service.add_message_to_history(
                    conversation_id="test_conv_id",
                    role="user",
                    content="Test message",
                    metadata={"intent": "test", "language": "en"}
                )
                
                assert success is True
                mock_set.assert_called_once()
    
    def test_get_conversation_summary(self, memory_service, sample_conversation_history):
        """Test getting conversation summary"""
        with patch.object(memory_service, 'load_conversation_history', return_value=sample_conversation_history):
            summary = memory_service.get_conversation_summary("test_conv_id")
            
            assert summary is not None
            assert summary["total_messages"] == 2
            assert summary["primary_language"] == "en"
            assert summary["last_user_message"] == "Hello"
            assert summary["last_bot_message"] == "Hi there! How can I help you today?"


class TestConversationMemoryUpdaterNode:
    """Test conversation memory updater node"""
    
    @pytest.fixture
    def memory_updater(self):
        return ConversationMemoryUpdaterNode()
    
    @pytest.fixture
    def sample_state(self):
        return {
            "user_message": "Hello",
            "response": "Hi there!",
            "conversation_id": "test_conv_id",
            "user_id": "test_user",
            "detected_language": "en",
            "detected_intent": "greeting",
            "intent_confidence": 0.9,
            "response_generated": True,
            "response_quality": "high",
            "conversation_history": []
        }
    
    @pytest.mark.asyncio
    async def test_process_with_valid_state(self, memory_updater, sample_state):
        """Test processing with valid state"""
        with patch.object(memory_updater.memory_service, 'add_message_to_history', return_value=True):
            with patch.object(memory_updater.memory_service, 'update_conversation_context', return_value=True):
                with patch.object(memory_updater.memory_service, 'load_conversation_history', return_value=[]):
                    result = await memory_updater.process(sample_state)
                    
                    assert result["memory_updated"] is True
                    assert "conversation_history" in result
    
    @pytest.mark.asyncio
    async def test_process_without_conversation_id(self, memory_updater, sample_state):
        """Test processing without conversation ID"""
        sample_state["conversation_id"] = ""
        
        result = await memory_updater.process(sample_state)
        
        # Should return state unchanged
        assert result == sample_state
        assert "memory_updated" not in result
    
    @pytest.mark.asyncio
    async def test_process_without_response(self, memory_updater, sample_state):
        """Test processing without generated response"""
        sample_state["response_generated"] = False
        sample_state["response"] = ""
        
        with patch.object(memory_updater.memory_service, 'add_message_to_history', return_value=True):
            with patch.object(memory_updater.memory_service, 'update_conversation_context', return_value=True):
                with patch.object(memory_updater.memory_service, 'load_conversation_history', return_value=[]):
                    result = await memory_updater.process(sample_state)
                    
                    assert result["memory_updated"] is True
                    # Should still add user message but not bot message 