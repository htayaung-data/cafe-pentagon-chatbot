"""
Facebook Webhook Debugging Script
Helps identify issues with Facebook Messenger integration
"""

import asyncio
import json
import requests
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings
from src.services.facebook_messenger import FacebookMessengerService
from src.utils.logger import get_logger

logger = get_logger("debug_facebook_webhook")


async def test_facebook_service():
    """Test Facebook service initialization and configuration"""
    print("🔍 Testing Facebook Service Configuration...")
    
    try:
        settings = get_settings()
        
        # Check settings
        print(f"✅ Page Access Token: {'Configured' if settings.facebook_page_access_token else '❌ Missing'}")
        print(f"✅ Verify Token: {'Configured' if settings.facebook_verify_token else '❌ Missing'}")
        
        if not settings.facebook_page_access_token:
            print("❌ Facebook Page Access Token is not configured!")
            return False
            
        # Test service initialization
        facebook_service = FacebookMessengerService()
        print("✅ Facebook service initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Facebook service initialization failed: {str(e)}")
        return False


async def test_webhook_verification():
    """Test webhook verification endpoint"""
    print("\n🔍 Testing Webhook Verification...")
    
    try:
        # Test webhook verification
        test_url = "https://cafe-pentagon-chatbot.loca.lt/webhook"
        test_params = {
            'hub.mode': 'subscribe',
            'hub.verify_token': get_settings().facebook_verify_token,
            'hub.challenge': 'test_challenge_123'
        }
        
        response = requests.get(test_url, params=test_params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Webhook verification successful: {response.text}")
            return True
        else:
            print(f"❌ Webhook verification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook verification test failed: {str(e)}")
        return False


async def test_message_sending():
    """Test sending a message via Facebook API"""
    print("\n🔍 Testing Message Sending...")
    
    try:
        facebook_service = FacebookMessengerService()
        
        # You'll need to replace this with a real Facebook user ID
        # You can get this from the webhook logs when you send a message
        test_user_id = "YOUR_FACEBOOK_USER_ID"  # Replace this
        
        if test_user_id == "YOUR_FACEBOOK_USER_ID":
            print("⚠️  Skipping message sending test - need real user ID")
            print("   Send a message to your Facebook page and check the logs for your user ID")
            return True
        
        success = await facebook_service.send_message(test_user_id, "Test message from debug script")
        
        if success:
            print("✅ Message sent successfully")
            return True
        else:
            print("❌ Message sending failed")
            return False
            
    except Exception as e:
        print(f"❌ Message sending test failed: {str(e)}")
        return False


async def test_main_agent():
    """Test main agent functionality"""
    print("\n🔍 Testing Main Agent...")
    
    try:
        from src.agents.main_agent import EnhancedMainAgent
        
        agent = EnhancedMainAgent()
        response = await agent.chat("Hello", "test_user", "en")
        
        print(f"✅ Main agent test successful")
        print(f"   Response: {response.get('response', 'No response')}")
        print(f"   Intent: {response.get('primary_intent', 'No intent')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main agent test failed: {str(e)}")
        return False


async def test_webhook_processing():
    """Test webhook processing with sample data"""
    print("\n🔍 Testing Webhook Processing...")
    
    try:
        facebook_service = FacebookMessengerService()
        
        # Sample webhook data
        sample_webhook = {
            "object": "page",
            "entry": [
                {
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [
                        {
                            "sender": {
                                "id": "USER_ID_HERE"
                            },
                            "recipient": {
                                "id": "123456789"
                            },
                            "timestamp": 1234567890,
                            "message": {
                                "mid": "m_123456789",
                                "text": "Hello"
                            }
                        }
                    ]
                }
            ]
        }
        
        result = await facebook_service.process_webhook(sample_webhook)
        
        print(f"✅ Webhook processing test successful")
        print(f"   Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook processing test failed: {str(e)}")
        return False


async def check_environment():
    """Check environment configuration"""
    print("🔍 Checking Environment Configuration...")
    
    try:
        settings = get_settings()
        
        # Check required environment variables
        required_vars = [
            'OPENAI_API_KEY',
            'PINECONE_API_KEY',
            'PINECONE_ENVIRONMENT',
            'FACEBOOK_PAGE_ACCESS_TOKEN',
            'FACEBOOK_VERIFY_TOKEN',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var.lower(), None):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        else:
            print("✅ All required environment variables are configured")
            return True
            
    except Exception as e:
        print(f"❌ Environment check failed: {str(e)}")
        return False


async def main():
    """Main debugging function"""
    print("🚀 Facebook Webhook Debugging Script")
    print("=" * 50)
    
    # Check environment
    env_ok = await check_environment()
    if not env_ok:
        print("\n❌ Environment configuration issues found. Please fix them first.")
        return
    
    # Test Facebook service
    service_ok = await test_facebook_service()
    if not service_ok:
        print("\n❌ Facebook service issues found.")
        return
    
    # Test webhook verification
    webhook_ok = await test_webhook_verification()
    if not webhook_ok:
        print("\n❌ Webhook verification issues found.")
        return
    
    # Test main agent
    agent_ok = await test_main_agent()
    if not agent_ok:
        print("\n❌ Main agent issues found.")
        return
    
    # Test webhook processing
    processing_ok = await test_webhook_processing()
    if not processing_ok:
        print("\n❌ Webhook processing issues found.")
        return
    
    # Test message sending (optional)
    await test_message_sending()
    
    print("\n✅ All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Send a message to your Facebook page")
    print("2. Check the FastAPI logs for webhook processing")
    print("3. Look for any error messages in the logs")
    print("4. If webhooks are received but no response, check the main agent logs")


if __name__ == "__main__":
    asyncio.run(main()) 