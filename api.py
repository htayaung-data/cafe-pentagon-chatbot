"""
FastAPI application for Cafe Pentagon Chatbot
Handles Facebook Messenger webhooks and API endpoints

Last updated: Added admin panel webhook endpoints for conversation management
"""

import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from src.services.facebook_messenger import FacebookMessengerService
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.api.admin_routes import admin_router

# Setup logging
logger = get_logger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Cafe Pentagon Chatbot API",
    description="API for Cafe Pentagon Facebook Messenger Chatbot",
    version="1.0.0"
)

# Include admin routes
app.include_router(admin_router)

# Initialize services
settings = get_settings()
facebook_service = FacebookMessengerService()
conversation_tracking = get_conversation_tracking_service()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cafe Pentagon Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode", description="Webhook verification mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token", description="Verification token"),
    hub_challenge: str = Query(..., alias="hub.challenge", description="Challenge string")
):
    """Facebook Messenger webhook verification endpoint"""
    try:
        result = await facebook_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
        if result:
            logger.info("webhook_verification_successful")
            return PlainTextResponse(result)
        else:
            logger.error("webhook_verification_failed")
            raise HTTPException(status_code=403, detail="Verification failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("webhook_verification_exception", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Facebook Messenger webhook handler"""
    try:
        # Read request body
        body = await request.body()
        
        # Log the incoming webhook
        logger.info("webhook_received", body_length=len(body))
        
        # Verify signature for security
        if not await facebook_service.verify_signature(request, body):
            logger.error("webhook_signature_verification_failed")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse JSON body
        try:
            data = json.loads(body)
            logger.info("webhook_data_parsed", data=data)
        except json.JSONDecodeError as e:
            logger.error("webhook_json_parse_failed", error=str(e))
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Process webhook
        result = await facebook_service.process_webhook(data)
        
        logger.info("webhook_processed_successfully", result=result)
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("webhook_processing_exception", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cafe_pentagon_chatbot",
        "version": "1.0.0"
    }

@app.get("/status")
async def status_check():
    """Detailed status check"""
    try:
        # Check Facebook service status
        facebook_status = "connected" if facebook_service.page_access_token else "disconnected"
        
        return {
            "status": "operational",
            "services": {
                "facebook_messenger": facebook_status,
                "main_agent": "operational"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("status_check_failed", error=str(e))
        return {
            "status": "degraded",
            "error": str(e),
            "version": "1.0.0"
        }

@app.post("/test-message")
async def test_message(recipient_id: str, message: str = "Hello from Cafe Pentagon Bot!"):
    """Test endpoint to send a message"""
    try:
        success = await facebook_service.send_message(recipient_id, message)
        return {
            "success": success,
            "recipient_id": recipient_id,
            "message": message
        }
    except Exception as e:
        logger.error("test_message_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Chat endpoint for testing conversation creation and escalation"""
    try:
        body = await request.json()
        user_id = body.get("user_id", "test_user")
        message = body.get("message", "Hello")
        platform = body.get("platform", "messenger")
        
        # Create or get conversation
        conversation = conversation_tracking.get_or_create_conversation(user_id, platform)
        conversation_id = conversation["id"]
        
        # Save the message
        saved_message = conversation_tracking.save_message(
            conversation_id=conversation_id,
            content=message,
            sender_type="user",
            metadata={"requires_human": "I need to talk to a human" in message.lower()}
        )
        
        # Check if message requires human intervention
        requires_human = "I need to talk to a human" in message.lower() or "talk to someone" in message.lower()
        
        if requires_human:
            # Escalate conversation
            from src.services.escalation_service import EscalationService
            escalation_service = EscalationService()
            escalation_service.escalate_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                reason="User requested human assistance",
                admin_id=None
            )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message_id": saved_message["id"],
            "requires_human": requires_human,
            "response": "Message received and processed"
        }
        
    except Exception as e:
        logger.error("chat_endpoint_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

# Admin Panel API Endpoints
@app.get("/admin/conversations")
async def get_active_conversations(limit: int = 100):
    """Get all active conversations for admin panel"""
    try:
        conversations = conversation_tracking.get_active_conversations(limit)
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error("get_active_conversations_failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "conversations": []
        }

@app.get("/admin/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get specific conversation by ID"""
    try:
        conversation = conversation_tracking.get_conversation_by_id(conversation_id)
        if conversation:
            messages = conversation_tracking.get_conversation_messages(conversation_id)
            return {
                "success": True,
                "conversation": conversation,
                "messages": messages
            }
        else:
            return {
                "success": False,
                "error": "Conversation not found"
            }
    except Exception as e:
        logger.error("get_conversation_failed", conversation_id=conversation_id, error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/admin/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, limit: int = 50):
    """Get messages for a specific conversation"""
    try:
        messages = conversation_tracking.get_conversation_messages(conversation_id, limit)
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        logger.error("get_conversation_messages_failed", conversation_id=conversation_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "messages": []
        }

@app.post("/admin/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: int):
    """Close a conversation"""
    try:
        success = conversation_tracking.close_conversation(conversation_id)
        return {
            "success": success,
            "conversation_id": conversation_id
        }
    except Exception as e:
        logger.error("close_conversation_failed", conversation_id=conversation_id, error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/admin/messages/{message_id}/mark-human")
async def mark_message_requires_human(message_id: int):
    """Mark a message as requiring human intervention"""
    try:
        success = conversation_tracking.mark_message_requires_human(message_id)
        return {
            "success": success,
            "message_id": message_id
        }
    except Exception as e:
        logger.error("mark_message_human_failed", message_id=message_id, error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/admin/messages/{message_id}/mark-replied")
async def mark_message_human_replied(message_id: int):
    """Mark a message as having received human reply"""
    try:
        success = conversation_tracking.mark_message_human_replied(message_id)
        return {
            "success": success,
            "message_id": message_id
        }
    except Exception as e:
        logger.error("mark_message_replied_failed", message_id=message_id, error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/admin/stats")
async def get_conversation_stats():
    """Get conversation statistics for admin dashboard"""
    try:
        stats = conversation_tracking.get_conversation_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error("get_conversation_stats_failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "stats": {}
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 
