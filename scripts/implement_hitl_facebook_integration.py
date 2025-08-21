#!/usr/bin/env python3
"""
HITL Facebook Integration Implementation Script
Helps admin panel team quickly implement Facebook messaging functionality

Usage: python scripts/implement_hitl_facebook_integration.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.services.facebook_messenger import FacebookMessengerService
from src.config.settings import get_settings

def print_header():
    """Print script header"""
    print("=" * 80)
    print("🚀 HITL Facebook Integration Implementation Script")
    print("=" * 80)
    print()

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        "FACEBOOK_PAGE_ACCESS_TOKEN",
        "FACEBOOK_VERIFY_TOKEN",
        "ADMIN_API_KEY", 
        "ADMIN_USER_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 10}{os.getenv(var)[-4:] if len(os.getenv(var)) > 4 else '****'}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these variables in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return False
    
    print("\n✅ All required environment variables are set!")
    return True

async def test_facebook_connectivity():
    """Test Facebook API connectivity"""
    print("\n🌐 Testing Facebook API connectivity...")
    
    try:
        facebook_service = FacebookMessengerService()
        result = await facebook_service.test_api_connectivity()
        
        if result["status"] == "success":
            print(f"✅ Facebook API connection successful!")
            print(f"   Page ID: {result['page_info'].get('id', 'N/A')}")
            print(f"   Page Name: {result['page_info'].get('name', 'N/A')}")
            print(f"   API Version: {result['api_version']}")
            return True
        else:
            print(f"❌ Facebook API connection failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Facebook connectivity: {str(e)}")
        return False

def generate_admin_endpoint_code():
    """Generate the admin send message endpoint code"""
    print("\n📝 Generating admin endpoint code...")
    
    code = '''# Add this to src/api/admin_routes.py

from src.services.facebook_messenger import FacebookMessengerService

class AdminMessageRequest(BaseModel):
    conversation_id: UUID
    recipient_id: str  # Facebook user ID
    message_text: str
    admin_id: UUID

@admin_router.post("/send-message", response_model=WebhookResponse, dependencies=[Depends(verify_admin_token)])
async def send_admin_message(
    request: AdminMessageRequest,
    background_tasks: BackgroundTasks
):
    """Send message from admin to Facebook user via HITL system"""
    try:
        # Initialize Facebook service
        facebook_service = FacebookMessengerService()
        
        # Send message to Facebook
        success = await facebook_service.send_message(
            recipient_id=request.recipient_id,
            message_text=request.message_text
        )
        
        if success:
            # Log the admin action
            background_tasks.add_task(
                log_admin_action,
                conversation_id=str(request.conversation_id),
                action="send_message",
                admin_id=str(request.admin_id),
                details={"message": request.message_text, "recipient": request.recipient_id}
            )
            
            return WebhookResponse(
                success=True,
                message="Message sent successfully",
                data={"recipient_id": request.recipient_id, "message": request.message_text}
            )
        else:
            return WebhookResponse(
                success=False,
                message="Failed to send message",
                data={"recipient_id": request.recipient_id, "error": "Facebook API call failed"}
            )
            
    except Exception as e:
        logger.error(f"Admin message send failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
'''
    
    print("✅ Admin endpoint code generated!")
    print("\n📋 Copy this code to your src/api/admin_routes.py file:")
    print("-" * 60)
    print(code)
    print("-" * 60)

def generate_frontend_code():
    """Generate frontend integration code"""
    print("\n📝 Generating frontend integration code...")
    
    code = '''// Add this to your HITL frontend

async function sendMessageToFacebook(recipientId, messageText, conversationId, adminId) {
    try {
        const response = await fetch('/admin/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminApiKey}`,
                'X-Admin-User-ID': adminId
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                recipient_id: recipientId,
                message_text: messageText,
                admin_id: adminId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Message sent successfully');
            return true;
        } else {
            console.error('Failed to send message:', result.message);
            return false;
        }
    } catch (error) {
        console.error('Error sending message:', error);
        return false;
    }
}

// Usage example:
// sendMessageToFacebook('facebook_user_id', 'Hello from HITL!', 'conversation_uuid', 'admin_uuid')
'''
    
    print("✅ Frontend integration code generated!")
    print("\n📋 Copy this code to your HITL frontend:")
    print("-" * 60)
    print(code)
    print("-" * 60)

def generate_test_commands():
    """Generate test commands"""
    print("\n🧪 Generating test commands...")
    
    commands = '''# Test your implementation with these commands:

# 1. Test Facebook connectivity
curl -X GET "http://localhost:8000/status"

# 2. Test admin endpoint (replace with your actual values)
curl -X POST "http://localhost:8000/admin/send-message" \\
  -H "Authorization: Bearer your_admin_api_key" \\
  -H "X-Admin-User-ID: your_admin_user_id" \\
  -H "Content-Type: application/json" \\
  -d '{
    "conversation_id": "test-uuid",
    "recipient_id": "facebook_user_id",
    "message_text": "Test message from HITL",
    "admin_id": "admin-uuid"
  }'

# 3. Test existing Facebook endpoint
curl -X POST "http://localhost:8000/test-message?recipient_id=facebook_user_id&message=Hello%20from%20HITL"
'''
    
    print("✅ Test commands generated!")
    print("\n📋 Use these commands to test your implementation:")
    print("-" * 60)
    print(commands)
    print("-" * 60)

def print_implementation_steps():
    """Print step-by-step implementation guide"""
    print("\n📋 Implementation Steps:")
    print("=" * 40)
    print("1. ✅ Environment variables checked")
    print("2. ✅ Facebook connectivity tested")
    print("3. 📝 Add admin endpoint to src/api/admin_routes.py")
    print("4. 📝 Add frontend code to your HITL interface")
    print("5. 🧪 Test with the provided commands")
    print("6. 🚀 Deploy to production")
    print()

def main():
    """Main implementation script"""
    print_header()
    
    # Check environment
    if not check_environment():
        print("\n❌ Please fix environment variables and run again.")
        return
    
    # Test Facebook connectivity
    if not asyncio.run(test_facebook_connectivity()):
        print("\n❌ Facebook connectivity test failed. Please check your configuration.")
        return
    
    # Generate implementation code
    generate_admin_endpoint_code()
    generate_frontend_code()
    generate_test_commands()
    
    # Print implementation steps
    print_implementation_steps()
    
    print("🎉 HITL Facebook integration setup complete!")
    print("\nNext steps:")
    print("1. Copy the generated code to your files")
    print("2. Test the endpoints")
    print("3. Integrate with your HITL frontend")
    print("4. Deploy and monitor")

if __name__ == "__main__":
    main()
