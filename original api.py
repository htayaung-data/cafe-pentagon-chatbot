"""
FastAPI application for Cafe Pentagon Chatbot
Handles Facebook Messenger webhooks and API endpoints

CHANGES MADE FOR HITL FILE SENDING:
1. Added /send-image endpoint - sends images to Facebook with proper previews
2. Added /send-file endpoint - sends files as formatted text with clickable links
3. Added CORS middleware - fixes cross-origin request blocking
4. Uses existing FacebookMessengerService.send_image() method for images
5. Simplified file handling - no complex attachments, just formatted text links

Last updated: Simplified file handling approach - files sent as formatted text with clickable links
"""

import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from src.services.facebook_messenger import FacebookMessengerService
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.api.admin_routes import admin_router
from datetime import datetime

# Setup logging
logger = get_logger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Cafe Pentagon Chatbot API",
    description="API for Cafe Pentagon Facebook Messenger Chatbot",
    version="1.0.0"
)

# CORS middleware - allows frontend to call backend from different origins
# CRITICAL: This fixes the CORS policy error blocking HITL image sending
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Development frontend
        "http://localhost:3001",      # Alternative dev port
        "https://your-production-domain.com",  # Production frontend (update this)
        "*"                           # Allow all origins (for development - remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/send-image")
async def send_image_endpoint(request: Request):
    """
    NEW ENDPOINT: Send image to Facebook Messenger with proper preview
    
    PURPOSE: Fixes HITL page image sending - images now appear as previews instead of text URLs
    USES: Existing FacebookMessengerService.send_image() method (same as working chatbot)
    CALLED BY: HITL page when admin uploads and sends images
    """
    try:
        # Parse request body
        body = await request.json()
        recipient_id = body.get("recipient_id")
        image_url = body.get("image_url")
        caption = body.get("caption", "")
        
        logger.info("image_send_request_received", 
                   recipient_id=recipient_id,
                   image_url=image_url,
                   caption_length=len(caption))
        
        # Validate required parameters
        if not recipient_id or not image_url:
            logger.error("missing_required_parameters", 
                        recipient_id=recipient_id,
                        image_url=image_url)
            return {
                "success": False,
                "error": "Missing required parameters: recipient_id and image_url"
            }
        
        # Use the existing Facebook service that the chatbot uses
        try:
            success = await facebook_service.send_image(recipient_id, image_url, caption)
            
            if success:
                logger.info("image_sent_successfully", 
                           recipient_id=recipient_id,
                           image_url=image_url)
                return {
                    "success": True,
                    "recipient_id": recipient_id,
                    "image_url": image_url,
                    "caption": caption,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("image_send_failed", 
                              recipient_id=recipient_id,
                              image_url=image_url)
                return {
                    "success": False,
                    "error": "Facebook API returned false - check backend logs for details",
                    "recipient_id": recipient_id,
                    "image_url": image_url,
                    "caption": caption,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as facebook_error:
            logger.error("facebook_service_error", 
                        error=str(facebook_error),
                        recipient_id=recipient_id,
                        image_url=image_url)
            return {
                "success": False,
                "error": f"Facebook service error: {str(facebook_error)}",
                "recipient_id": recipient_id,
                "image_url": image_url,
                "caption": caption,
                "timestamp": datetime.now().isoformat()
            }
    except json.JSONDecodeError as e:
        logger.error("invalid_json_in_request", error=str(e))
        return {
            "success": False,
            "error": "Invalid JSON in request body"
        }
    except Exception as e:
        logger.error("image_send_endpoint_failed", 
                    error=str(e),
                    recipient_id=recipient_id if 'recipient_id' in locals() else None,
                    image_url=image_url if 'image_url' in locals() else None)
        return {
            "success": False,
            "error": str(e),
            "recipient_id": recipient_id if 'recipient_id' in locals() else None,
            "image_url": image_url if 'image_url' in locals() else None
        }

@app.post("/send-file")
async def send_file_endpoint(request: Request):
    """
    CLEAN ENDPOINT: Send file to Facebook Messenger as clean filename with hidden clickable URL
    
    PURPOSE: Fixes HITL page file sending - files now appear as clean filenames instead of ugly text
    APPROACH: Send as clean filename + hidden URL that Facebook automatically makes clickable
    CALLED BY: HITL page when admin uploads and sends files (PDF, Excel, Word, etc.)
    
    EXAMPLE OUTPUT: "📎 Document.pdf\n[file_url]" - Facebook shows clean filename, hides URL
    """
    try:
        # Parse request body
        body = await request.json()
        recipient_id = body.get("recipient_id")
        file_url = body.get("file_url")
        file_name = body.get("file_name", "File")
        file_type = body.get("file_type", "application/octet-stream")
        
        logger.info("file_send_request_received", 
                   recipient_id=recipient_id,
                   file_url=file_url,
                   file_name=file_name,
                   file_type=file_type)
        
        # Validate required parameters
        if not recipient_id or not file_url:
            logger.error("missing_required_parameters", 
                        recipient_id=recipient_id,
                        file_url=file_url)
            return {
                "success": False,
                "error": "Missing required parameters: recipient_id and file_url"
            }
        
        # CLEAN APPROACH: Format file as clean filename with hidden clickable URL
        # Facebook automatically makes URLs clickable, so we show clean filename + hidden URL
        try:
            # Create a clean message with just filename and hidden URL
            # Use appropriate emoji based on file type
            file_emoji = get_file_emoji(file_type)
            
            # Format: Show filename with emoji, then URL on next line (Facebook will make it clickable)
            # Facebook automatically makes URLs clickable, so the filename appears clean
            message_text = f"{file_emoji} {file_name}\n{file_url}"
            
            # Send using the existing Facebook service
            success = await facebook_service.send_message(recipient_id, message_text)
            
            if success:
                logger.info("file_sent_successfully", 
                           recipient_id=recipient_id,
                           file_name=file_name,
                           file_type=file_type)
                return {
                    "success": True,
                    "recipient_id": recipient_id,
                    "file_url": file_url,
                    "file_name": file_name,
                    "file_type": file_type,
                    "message_sent": message_text,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("file_send_failed", 
                              recipient_id=recipient_id,
                              file_name=file_name)
                return {
                    "success": False,
                    "error": "Facebook API returned false - check backend logs for details",
                    "recipient_id": recipient_id,
                    "file_url": file_url,
                    "file_name": file_name,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as facebook_error:
            logger.error("facebook_service_error", 
                        error=str(facebook_error),
                        recipient_id=recipient_id,
                        file_url=file_url)
            return {
                "success": False,
                "error": f"Facebook service error: {str(facebook_error)}",
                "recipient_id": recipient_id,
                "file_url": file_url,
                "file_name": file_name,
                "timestamp": datetime.now().isoformat()
            }
    except json.JSONDecodeError as e:
        logger.error("invalid_json_in_request", error=str(e))
        return {
            "success": False,
            "error": "Invalid JSON in request body"
        }
    except Exception as e:
        logger.error("file_send_endpoint_failed", 
                    error=str(e),
                    recipient_id=recipient_id if 'recipient_id' in locals() else None,
                    file_url=file_url if 'file_url' in locals() else None)
        return {
            "success": False,
            "error": str(e),
            "recipient_id": recipient_id if 'recipient_id' in locals() else None,
            "file_url": file_url if 'file_url' in locals() else None
        }

@app.post("/send-multiple-files")
async def send_multiple_files_endpoint(request: Request):
    """
    CLEAN ENDPOINT: Send multiple files to Facebook Messenger as clean filenames with hidden clickable URLs
    
    PURPOSE: Efficiently send multiple files from HITL page in a single request
    APPROACH: Combine all files into one clean message with filenames and hidden URLs
    CALLED BY: HITL page when admin uploads and sends multiple files
    
    EXAMPLE OUTPUT: "📎 Files attached:\n\n📄 Document1.pdf\n[url1]\n\n📝 Document2.docx\n[url2]" - Facebook shows clean filenames
    """
    try:
        # Parse request body
        body = await request.json()
        recipient_id = body.get("recipient_id")
        files = body.get("files", [])  # Array of {file_url, file_name, file_type}
        
        logger.info("multiple_files_send_request_received", 
                   recipient_id=recipient_id,
                   files_count=len(files))
        
        # Validate required parameters
        if not recipient_id or not files or len(files) == 0:
            logger.error("missing_required_parameters", 
                        recipient_id=recipient_id,
                        files_count=len(files) if files else 0)
            return {
                "success": False,
                "error": "Missing required parameters: recipient_id and files array"
            }
        
        # SIMPLIFIED APPROACH: Format all files into one message with clickable links
        try:
            # Build the combined message
            if len(files) == 1:
                # Single file - use the same clean format as /send-file
                file = files[0]
                file_emoji = get_file_emoji(file.get("file_type", "application/octet-stream"))
                message_text = f"{file_emoji} {file.get('file_name', 'File')}\n{file.get('file_url')}"
            else:
                # Multiple files - create a clean list format
                message_text = f"📎 {len(files)} files attached:\n\n"
                for i, file in enumerate(files):
                    file_emoji = get_file_emoji(file.get("file_type", "application/octet-stream"))
                    file_name = file.get("file_name", f"File {i+1}")
                    file_url = file.get("file_url")
                    message_text += f"{file_emoji} {file_name}\n{file_url}\n\n"
                message_text = message_text.strip()  # Remove trailing newlines
            
            # Send using the existing Facebook service
            success = await facebook_service.send_message(recipient_id, message_text)
            
            if success:
                logger.info("multiple_files_sent_successfully", 
                           recipient_id=recipient_id,
                           files_count=len(files))
                return {
                    "success": True,
                    "recipient_id": recipient_id,
                    "files_count": len(files),
                    "message_sent": message_text,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("multiple_files_send_failed", 
                              recipient_id=recipient_id,
                              files_count=len(files))
                return {
                    "success": False,
                    "error": "Facebook API returned false - check backend logs for details",
                    "recipient_id": recipient_id,
                    "files_count": len(files),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as facebook_error:
            logger.error("facebook_service_error", 
                        error=str(facebook_error),
                        recipient_id=recipient_id,
                        files_count=len(files))
            return {
                "success": False,
                "error": f"Facebook service error: {str(facebook_error)}",
                "recipient_id": recipient_id,
                "files_count": len(files),
                "timestamp": datetime.now().isoformat()
            }
    except json.JSONDecodeError as e:
        logger.error("invalid_json_in_request", error=str(e))
        return {
            "success": False,
            "error": "Invalid JSON in request body"
        }
    except Exception as e:
        logger.error("multiple_files_send_endpoint_failed", 
                    error=str(e),
                    recipient_id=recipient_id if 'recipient_id' in locals() else None,
                    files_count=len(files) if 'files' in locals() else 0)
        return {
            "success": False,
            "error": str(e),
            "recipient_id": recipient_id if 'recipient_id' in locals() else None,
            "files_count": len(files) if 'files' in locals() else 0
        }

# Helper function to get appropriate emoji for file type
def get_file_emoji(file_type: str) -> str:
    """Get appropriate emoji based on file type"""
    if file_type.startswith("image/"):
        return "🖼️"
    elif "pdf" in file_type:
        return "📄"
    elif "word" in file_type or "document" in file_type:
        return "📝"
    elif "excel" in file_type or "spreadsheet" in file_type:
        return "📊"
    elif "powerpoint" in file_type or "presentation" in file_type:
        return "📊"
    elif "zip" in file_type or "rar" in file_type:
        return "📦"
    else:
        return "📎"  # Default paperclip

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
        
        # Save the message - no pattern matching, let LLM handle escalation
        saved_message = conversation_tracking.save_message(
            conversation_id=conversation_id,
            content=message,
            sender_type="user",
            metadata={}
        )
        
        # No pattern matching - let the LangGraph workflow handle escalation decisions
        requires_human = False
        
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

# Admin Panel API Endpoints - REMOVED: These are now handled by secured admin routes
# All admin endpoints are now secured and available through /admin/* routes
# See src/api/admin_routes.py for the secured implementation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 
