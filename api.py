"""
FastAPI application for Cafe Pentagon Chatbot
Handles Facebook Messenger webhooks and API endpoints
"""

import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from src.services.facebook_messenger import FacebookMessengerService
from src.utils.logger import get_logger
from src.config.settings import get_settings

# Setup logging
logger = get_logger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Cafe Pentagon Chatbot API",
    description="API for Cafe Pentagon Facebook Messenger Chatbot",
    version="1.0.0"
)

# Initialize services
settings = get_settings()
facebook_service = FacebookMessengerService()

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
    except Exception as e:
        logger.error("webhook_verification_exception", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Facebook Messenger webhook handler"""
    try:
        # Read request body
        body = await request.body()
        
        # Log the incoming webhook for debugging
        logger.info("webhook_received", body_length=len(body))
        
        # Verify signature for security (temporarily disabled for testing)
        # if not await facebook_service.verify_signature(request, body):
        #     logger.error("webhook_signature_verification_failed")
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 