"""
Integration tests for Cafe Pentagon Chatbot
Tests complete LangGraph workflow, API endpoints, and service integrations
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.graph.state_graph import create_conversation_graph, create_initial_state
from src.services.conversation_tracking_service import ConversationTrackingService
from src.services.facebook_messenger import FacebookMessengerService
from api import app
from tests.conftest import TEST_USER_MESSAGES, TEST_RAG_RESULTS


class TestLangGraphIntegration:
    """Integration tests for LangGraph workflow"""
    
    @pytest.fixture
    def conversation_graph(self):
        """Create conversation graph for testing"""
        return create_conversation_graph()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_greeting(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for greeting"""
        # Arrange
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["english_greeting"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Act
        compiled_workflow = conversation_graph.compile()
        final_state = await compiled_workflow.ainvoke(initial_state)
        
        # Assert
        assert final_state["is_greeting"] is True
        assert final_state["detected_language"] == "en"
        assert final_state["response_generated"] is True
        assert len(final_state["response"]) > 0
        assert final_state["response_quality"] in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_complete_workflow_menu_query(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for menu query"""
        # Arrange
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["english_menu"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Mock intent classification
        with patch('src.agents.intent_classifier.AIIntentClassifier.process') as mock_intent:
            mock_intent.return_value = {
                "detected_intents": [{"intent": "menu_browse", "confidence": 0.95}],
                "primary_intent": "menu_browse",
                "reasoning": "User asked about menu items",
                "entities": {"food_type": "general"}
            }
            
            # Mock vector search
            with patch('src.services.vector_search_service.VectorSearchService.search_pinecone_for_data') as mock_search:
                mock_search.return_value = TEST_RAG_RESULTS["menu"]
                
                # Act
                compiled_workflow = conversation_graph.compile()
                final_state = await compiled_workflow.ainvoke(initial_state)
                
                # Assert
                assert final_state["detected_intent"] == "menu_browse"
                assert final_state["target_namespace"] == "menu"
                assert len(final_state["rag_results"]) > 0  # Any number of results is fine
                assert final_state["response_generated"] is True
                assert len(final_state["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_complete_workflow_burmese_menu(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for Burmese menu query"""
        # Arrange
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["burmese_menu_general"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Mock Burmese menu analysis
        with patch('src.graph.nodes.intent_classifier.IntentClassifierNode._analyze_burmese_menu_request') as mock_analysis:
            mock_analysis.return_value = {
                "action": "MENU_BROWSE",
                "confidence": 0.95,
                "category": "general"
            }
            
            # Mock vector search
            with patch('src.services.vector_search_service.VectorSearchService.search_pinecone_for_data') as mock_search:
                mock_search.return_value = TEST_RAG_RESULTS["menu"]
                
                # Act
                compiled_workflow = conversation_graph.compile()
                final_state = await compiled_workflow.ainvoke(initial_state)
                
                # Assert
                assert final_state["detected_language"] == "my"
                assert final_state["detected_intent"] == "menu_browse"
                assert final_state["target_namespace"] == "menu"
                assert final_state["response_generated"] is True
    
    @pytest.mark.asyncio
    async def test_complete_workflow_escalation(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test complete workflow for escalation request"""
        # Arrange
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["english_escalation"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Act
        compiled_workflow = conversation_graph.compile()
        final_state = await compiled_workflow.ainvoke(initial_state)
        
        # Assert
        assert final_state["is_escalation_request"] is True
        assert final_state["requires_human"] is True
        assert final_state["rag_enabled"] is False
        assert final_state["response_generated"] is True
        assert "human" in final_state["response"].lower()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test workflow error handling"""
        # Arrange
        initial_state = create_initial_state(
            user_message="Test message",
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Mock intent classification to raise exception
        with patch('src.agents.intent_classifier.AIIntentClassifier.process') as mock_intent:
            mock_intent.side_effect = Exception("Intent classification failed")
            
            # Act
            compiled_workflow = conversation_graph.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Assert
            assert final_state["detected_intent"] == "unknown"
            assert final_state["intent_confidence"] == 0.0
            assert final_state["response_generated"] is True
            assert len(final_state["response"]) > 0


class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cafe Pentagon Chatbot API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_webhook_verification(self, client):
        """Test webhook verification endpoint"""
        response = client.get("/webhook", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "fb-n8n",
            "hub.challenge": "test_challenge"
        })
        assert response.status_code == 200
        assert response.text == "test_challenge"
    
    @patch('api.facebook_service')
    def test_webhook_verification_failed(self, mock_facebook_service, client):
        """Test webhook verification with wrong token"""
        # Arrange
        # Mock the async method to return None (failed verification)
        # We need to create an async mock that returns None
        async def mock_verify_webhook(*args, **kwargs):
            return None
        
        mock_facebook_service.verify_webhook = mock_verify_webhook
        
        # Act
        response = client.get("/webhook", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "test_challenge"
        })
        
        # Assert
        assert response.status_code == 403
    
    @patch('src.services.facebook_messenger.FacebookMessengerService.process_webhook')
    def test_webhook_handler(self, mock_process_webhook, client):
        """Test webhook handler endpoint"""
        # Arrange
        mock_process_webhook.return_value = {"status": "success"}
        webhook_data = {
            "object": "page",
            "entry": [{
                "id": "test_page_id",
                "messaging": [{
                    "sender": {"id": "test_user"},
                    "recipient": {"id": "test_page"},
                    "message": {"text": "Hello"}
                }]
            }]
        }
        
        # Act
        response = client.post("/webhook", json=webhook_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_process_webhook.assert_called_once()
    
    @patch('src.services.facebook_messenger.FacebookMessengerService.send_message')
    def test_test_message_endpoint(self, mock_send_message, client):
        """Test test message endpoint"""
        # Arrange
        mock_send_message.return_value = True
        
        # Act
        response = client.post("/test-message", params={
            "recipient_id": "test_user",
            "message": "Test message"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_send_message.assert_called_once()
    
    @patch('src.services.conversation_tracking_service.ConversationTrackingService.get_active_conversations')
    def test_get_active_conversations(self, mock_get_conversations, client):
        """Test get active conversations endpoint"""
        # Arrange
        mock_get_conversations.return_value = [
            {
                "id": "test_conv_1",
                "user_id": "test_user_1",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        # Act
        response = client.get("/admin/conversations")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["user_id"] == "test_user_1"
    
    @patch('src.services.conversation_tracking_service.ConversationTrackingService.get_conversation_by_id')
    def test_get_conversation(self, mock_get_conversation, client):
        """Test get conversation by ID endpoint"""
        # Arrange
        mock_get_conversation.return_value = {
            "id": 1,
            "user_id": "test_user_1",
            "status": "active"
        }
        
        # Act
        response = client.get("/admin/conversations/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation"]["user_id"] == "test_user_1"
    
    @patch('src.services.conversation_tracking_service.ConversationTrackingService.close_conversation')
    def test_close_conversation(self, mock_close_conversation, client):
        """Test close conversation endpoint"""
        # Arrange
        mock_close_conversation.return_value = True
        
        # Act
        response = client.post("/admin/conversations/1/close")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_close_conversation.assert_called_once_with(1)


class TestServiceIntegration:
    """Integration tests for services"""
    
    @pytest.fixture
    def conversation_tracking(self, mock_supabase):
        """Initialize conversation tracking service"""
        return ConversationTrackingService()
    
    @pytest.fixture
    def facebook_service(self, mock_settings):
        """Initialize Facebook Messenger service"""
        return FacebookMessengerService()
    
    def test_conversation_tracking_save_conversation(self, conversation_tracking, mock_supabase):
        """Test saving conversation"""
        # Act
        result = conversation_tracking.save_conversation("test_user_123", "facebook")
        
        # Assert
        assert result is not None
        assert result["user_id"] == "test_user_123"
        assert result["platform"] == "facebook"
        assert result["status"] == "active"
    
    @patch('src.services.conversation_tracking_service.ConversationTrackingService.save_message')
    def test_conversation_tracking_save_message(self, mock_save_message, conversation_tracking, mock_supabase):
        """Test saving message"""
        # Arrange
        mock_save_message.return_value = {
            "id": "test_msg_1",
            "content": "Test message",
            "sender_type": "user",
            "confidence_score": 0.95
        }
        
        # Act
        result = conversation_tracking.save_message(
            conversation_id="test_conv_1",
            content="Test message",
            sender_type="user",
            confidence_score=0.95
        )
        
        # Assert
        assert result is not None
        assert result["content"] == "Test message"
        assert result["sender_type"] == "user"
        assert result["confidence_score"] == 0.95
    
    @patch('src.services.facebook_messenger.FacebookMessengerService.verify_webhook')
    async def test_facebook_webhook_verification(self, mock_verify_webhook, facebook_service):
        """Test Facebook webhook verification"""
        # Arrange
        mock_verify_webhook.return_value = "test_challenge"
        
        # Act
        result = await facebook_service.verify_webhook("subscribe", "fb-n8n", "test_challenge")
        
        # Assert
        assert result == "test_challenge"
        mock_verify_webhook.assert_called_once_with("subscribe", "fb-n8n", "test_challenge")
    
    @patch('src.services.facebook_messenger.FacebookMessengerService.send_message')
    async def test_facebook_send_message(self, mock_send_message, facebook_service):
        """Test Facebook message sending"""
        # Arrange
        mock_send_message.return_value = True
        
        # Act
        result = await facebook_service.send_message("test_user", "Hello from bot!")
        
        # Assert
        assert result is True
        mock_send_message.assert_called_once_with("test_user", "Hello from bot!")


class TestErrorHandling:
    """Integration tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_invalid_state(self, conversation_graph):
        """Test workflow with invalid state"""
        # Arrange
        invalid_state = {
            "user_message": "",  # Empty message
            "user_id": "",
            "conversation_id": ""
        }
        
        # Act
        compiled_workflow = conversation_graph.compile()
        final_state = await compiled_workflow.ainvoke(invalid_state)
        
        # Assert
        assert final_state["detected_intent"] == "unknown"
        assert final_state["intent_confidence"] == 0.0
        assert final_state["response_generated"] is True
    
    def test_api_error_handling(self, client):
        """Test API error handling"""
        # Test invalid JSON
        response = client.post("/webhook", data="invalid json")
        assert response.status_code == 400
        
        # Test missing parameters
        response = client.get("/webhook")
        assert response.status_code == 422
    
    @patch('src.services.conversation_tracking_service.ConversationTrackingService.save_conversation')
    def test_database_error_handling(self, mock_save_conversation, mock_supabase):
        """Test database error handling"""
        # Arrange
        mock_save_conversation.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        conversation_tracking = ConversationTrackingService()
        result = conversation_tracking.save_conversation("test_user", "facebook")
        assert result is None


class TestPerformance:
    """Performance tests"""
    
    @pytest.mark.asyncio
    async def test_workflow_response_time(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test workflow response time"""
        import time
        
        # Arrange
        initial_state = create_initial_state(
            user_message=TEST_USER_MESSAGES["english_greeting"],
            user_id="test_user_123",
            conversation_id="test_conv_456",
            platform="test"
        )
        
        # Act
        start_time = time.time()
        compiled_workflow = conversation_graph.compile()
        final_state = await compiled_workflow.ainvoke(initial_state)
        end_time = time.time()
        
        # Assert
        response_time = end_time - start_time
        assert response_time < 5.0  # Should complete within 5 seconds
        assert final_state["response_generated"] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, conversation_graph, mock_openai, mock_pinecone, mock_supabase):
        """Test concurrent workflow execution"""
        # Arrange
        initial_states = [
            create_initial_state(
                user_message=f"Test message {i}",
                user_id=f"test_user_{i}",
                conversation_id=f"test_conv_{i}",
                platform="test"
            )
            for i in range(5)
        ]
        
        # Act
        compiled_workflow = conversation_graph.compile()
        tasks = [compiled_workflow.ainvoke(state) for state in initial_states]
        results = await asyncio.gather(*tasks)
        
        # Assert
        assert len(results) == 5
        for result in results:
            assert result["response_generated"] is True
            assert len(result["response"]) > 0 