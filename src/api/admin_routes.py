"""
Admin Panel Webhook API Routes
Handles communication between Admin Panel and Chatbot for conversation management
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from uuid import UUID

from src.services.conversation_tracking_service import ConversationTrackingService
from src.services.escalation_service import EscalationService
from supabase import create_client, Client
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Admin Authentication Middleware
async def verify_admin_token(request: Request):
    """
    Verify admin authentication token
    Checks for Bearer token in Authorization header and admin user ID in X-Admin-User-ID header
    """
    settings = get_settings()
    
    # Check if admin authentication is configured
    if not settings.admin_api_key or not settings.admin_user_id:
        logger.error("Admin authentication not configured - rejecting all requests")
        raise HTTPException(status_code=401, detail="Admin authentication not configured")
    
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication - Bearer token required")
    
    # Extract and verify API key
    token = auth_header.split(" ")[1]
    if token != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Verify admin user ID
    admin_user_id = request.headers.get("X-Admin-User-ID")
    if admin_user_id != settings.admin_user_id:
        raise HTTPException(status_code=401, detail="Invalid admin user ID")
    
    logger.info(f"Admin authentication successful for user: {admin_user_id}")

# Pydantic models for request/response
class ConversationControlRequest(BaseModel):
    conversation_id: UUID
    action: str = Field(..., description="Action to perform: 'disable_rag', 'enable_rag', 'assign_human', 'release_human', 'close_conversation'")
    admin_id: Optional[UUID] = Field(None, description="Admin ID for assignment actions")
    reason: Optional[str] = Field(None, description="Reason for the action")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1-5)")

class ConversationStatusResponse(BaseModel):
    conversation_id: UUID
    status: str
    rag_enabled: bool
    human_handling: bool
    assigned_admin_id: Optional[UUID]
    priority: int
    escalation_reason: Optional[str]
    escalation_timestamp: Optional[datetime]
    last_message_at: datetime
    message_count: int

class EscalatedConversationResponse(BaseModel):
    conversation_id: UUID
    user_id: str
    platform: str
    status: str
    priority: int
    assigned_admin_id: Optional[UUID]
    escalation_reason: Optional[str]
    escalation_timestamp: Optional[datetime]
    last_message_at: datetime
    message_count: int
    requires_human_count: int

class WebhookResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Dependency injection
def get_conversation_service():
    return ConversationTrackingService()

def get_escalation_service():
    return EscalationService()

def get_supabase_client():
    """Get Supabase client for direct database operations"""
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

@admin_router.post("/conversation/control", response_model=WebhookResponse, dependencies=[Depends(verify_admin_token)])
async def control_conversation(
    request: ConversationControlRequest,
    background_tasks: BackgroundTasks,
    conversation_service: ConversationTrackingService = Depends(get_conversation_service),
    escalation_service: EscalationService = Depends(get_escalation_service)
):
    """
    Control conversation behavior (RAG enable/disable, human assignment, etc.)
    Called by Admin Panel when staff takes action
    """
    try:
        logger.info(f"Admin control request: {request.action} for conversation {request.conversation_id}")
        
        if request.action == "disable_rag":
            # Disable RAG for this conversation
            # Get user_id from conversation
            conversation = conversation_service.get_conversation_by_id(str(request.conversation_id))
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            escalation_service.escalate_conversation(
                conversation_id=str(request.conversation_id),
                user_id=conversation["user_id"],
                reason=request.reason or "admin_disabled_rag",
                admin_id=str(request.admin_id) if request.admin_id else None
            )
            message = "RAG disabled for conversation"
            
        elif request.action == "enable_rag":
            # Re-enable RAG for this conversation
            escalation_service.deescalate_conversation(
                conversation_id=str(request.conversation_id),
                admin_id=str(request.admin_id) if request.admin_id else "system"
            )
            message = "RAG re-enabled for conversation"
            
        elif request.action == "assign_human":
            # Assign conversation to human admin
            if not request.admin_id:
                raise HTTPException(status_code=400, detail="admin_id required for assignment")
            
            escalation_service.assign_conversation(
                conversation_id=str(request.conversation_id),
                admin_id=str(request.admin_id)
            )
            message = f"Conversation assigned to admin {request.admin_id}"
            
        elif request.action == "release_human":
            # Release conversation from human admin (use deescalate)
            escalation_service.deescalate_conversation(
                conversation_id=str(request.conversation_id),
                admin_id=str(request.admin_id) if request.admin_id else "system"
            )
            message = "Conversation released from human admin"
            
        elif request.action == "close_conversation":
            # Close the conversation
            conversation_service.close_conversation(str(request.conversation_id))
            message = "Conversation closed"
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
        
        # Add background task to log the action
        background_tasks.add_task(
            log_admin_action,
            conversation_id=str(request.conversation_id),
            action=request.action,
            admin_id=str(request.admin_id) if request.admin_id else None,
            reason=request.reason
        )
        
        return WebhookResponse(
            success=True,
            message=message,
            data={"conversation_id": str(request.conversation_id), "action": request.action}
        )
        
    except Exception as e:
        logger.error(f"Error in conversation control: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@admin_router.get("/conversation/{conversation_id}/status", response_model=ConversationStatusResponse, dependencies=[Depends(verify_admin_token)])
async def get_conversation_status(
    conversation_id: UUID,
    conversation_service: ConversationTrackingService = Depends(get_conversation_service),
    escalation_service: EscalationService = Depends(get_escalation_service)
):
    """
    Get current status of a conversation
    Called by Admin Panel to display conversation details
    """
    try:
        # Get conversation details
        conversation = conversation_service.get_conversation_by_id(str(conversation_id))
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get escalation status
        escalation_status = escalation_service.get_conversation_escalation_status(str(conversation_id))
        
        # Get message count
        supabase = get_supabase_client()
        messages_response = supabase.table("messages").select("id").eq("conversation_id", str(conversation_id)).execute()
        message_count = len(messages_response.data) if messages_response.data else 0
        
        return ConversationStatusResponse(
            conversation_id=conversation_id,
            status=conversation.get("status", "unknown"),
            rag_enabled=escalation_status.get("rag_enabled", True),
            human_handling=escalation_status.get("human_handling", False),
            assigned_admin_id=escalation_status.get("assigned_admin_id"),
            priority=escalation_status.get("priority", 1),
            escalation_reason=escalation_status.get("escalation_reason"),
            escalation_timestamp=escalation_status.get("escalation_timestamp"),
            last_message_at=conversation.get("last_message_at"),
            message_count=message_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@admin_router.get("/conversations/escalated", response_model=List[EscalatedConversationResponse], dependencies=[Depends(verify_admin_token)])
async def get_escalated_conversations(
    escalation_service: EscalationService = Depends(get_escalation_service)
):
    """
    Get all conversations that require human attention
    Called by Admin Panel to show escalation queue
    """
    try:
        escalated_conversations = escalation_service.get_escalated_conversations()
        
        # Enhance with message counts
        supabase = get_supabase_client()
        enhanced_conversations = []
        
        for conv in escalated_conversations:
            # Get total message count
            messages_response = supabase.table("messages").select("id").eq("conversation_id", conv["id"]).execute()
            message_count = len(messages_response.data) if messages_response.data else 0
            
            # Get messages requiring human attention
            human_messages_response = supabase.table("messages").select("id").eq("conversation_id", conv["id"]).eq("requires_human", True).execute()
            requires_human_count = len(human_messages_response.data) if human_messages_response.data else 0
            
            enhanced_conversations.append(EscalatedConversationResponse(
                conversation_id=UUID(conv["id"]),
                user_id=conv["user_id"],
                platform=conv["platform"],
                status=conv["status"],
                priority=conv["priority"],
                assigned_admin_id=UUID(conv["assigned_admin_id"]) if conv["assigned_admin_id"] else None,
                escalation_reason=conv["escalation_reason"],
                escalation_timestamp=conv["escalation_timestamp"],
                last_message_at=conv["last_message_at"],
                message_count=message_count,
                requires_human_count=requires_human_count
            ))
        
        return enhanced_conversations
        
    except Exception as e:
        logger.error(f"Error getting escalated conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@admin_router.post("/message/{message_id}/mark-human-replied", response_model=WebhookResponse, dependencies=[Depends(verify_admin_token)])
async def mark_message_human_replied(
    message_id: UUID,
    escalation_service: EscalationService = Depends(get_escalation_service)
):
    """
    Mark a message as replied to by human
    Called by Admin Panel when staff responds to a message
    """
    try:
        escalation_service.mark_human_replied(str(message_id), "system")
        
        return WebhookResponse(
            success=True,
            message=f"Message {message_id} marked as human replied",
            data={"message_id": str(message_id)}
        )
        
    except Exception as e:
        logger.error(f"Error marking message as human replied: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@admin_router.get("/health", response_model=WebhookResponse, dependencies=[Depends(verify_admin_token)])
async def admin_health_check():
    """
    Health check endpoint for admin panel
    """
    return WebhookResponse(
        success=True,
        message="Admin API is healthy",
        data={"timestamp": datetime.now().isoformat()}
    )

# Background task function
async def log_admin_action(
    conversation_id: str,
    action: str,
    admin_id: Optional[str],
    reason: Optional[str]
):
    """
    Log admin actions for audit trail
    """
    try:
        supabase = get_supabase_client()
        
        # Log to a separate admin_actions table (if it exists) or to conversation metadata
        action_log = {
            "conversation_id": conversation_id,
            "action": action,
            "admin_id": admin_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        # For now, we'll log to console. In production, you might want a dedicated table
        logger.info(f"Admin action logged: {action_log}")
        
    except Exception as e:
        logger.error(f"Error logging admin action: {str(e)}") 