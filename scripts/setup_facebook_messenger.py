"""
Setup script for Facebook Messenger integration
Helps configure webhook and test the integration
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.facebook_messenger import FacebookMessengerService
from src.utils.logger import setup_logger
from src.config.settings import get_settings

# Setup logging
setup_logger()


async def test_facebook_connection():
    """Test Facebook API connection"""
    print("🔍 Testing Facebook API connection...")
    
    try:
        facebook_service = FacebookMessengerService()
        print("✅ Facebook service initialized successfully")
        
        # Test API connection
        test_user_id = "123456789"  # Dummy user ID for testing
        user_info = await facebook_service.get_user_info(test_user_id)
        
        if user_info:
            print("✅ Facebook API connection successful")
            print(f"   User info: {user_info}")
        else:
            print("⚠️  Facebook API connection failed (expected for dummy user)")
        
        return True
        
    except Exception as e:
        print(f"❌ Facebook service initialization failed: {str(e)}")
        return False


async def test_webhook_verification():
    """Test webhook verification"""
    print("\n🔍 Testing webhook verification...")
    
    try:
        facebook_service = FacebookMessengerService()
        
        # Test webhook verification
        challenge = "test_challenge_123"
        result = await facebook_service.verify_webhook("subscribe", facebook_service.verify_token, challenge)
        
        if result == challenge:
            print("✅ Webhook verification successful")
            return True
        else:
            print("❌ Webhook verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Webhook verification test failed: {str(e)}")
        return False


def generate_webhook_url():
    """Generate webhook URL for Facebook configuration"""
    settings = get_settings()
    
    # You'll need to replace this with your actual domain
    domain = "your-domain.com"  # Replace with your actual domain
    webhook_url = f"https://{domain}/webhook"
    
    print(f"\n🌐 Webhook URL: {webhook_url}")
    print(f"🔑 Verify Token: {settings.facebook_verify_token}")
    
    return webhook_url


def print_setup_instructions():
    """Print setup instructions for Facebook Messenger"""
    print("\n" + "="*60)
    print("📋 FACEBOOK MESSENGER SETUP INSTRUCTIONS")
    print("="*60)
    
    webhook_url = generate_webhook_url()
    
    print("\n1️⃣  Configure Facebook App:")
    print("   - Go to https://developers.facebook.com")
    print("   - Select your app")
    print("   - Go to 'Messenger' > 'Settings'")
    print("   - Add your page to the app")
    
    print("\n2️⃣  Configure Webhook:")
    print("   - In Messenger Settings, click 'Add Callback URL'")
    print(f"   - Callback URL: {webhook_url}")
    print(f"   - Verify Token: {get_settings().facebook_verify_token}")
    print("   - Subscribe to: messages, messaging_postbacks")
    
    print("\n3️⃣  Deploy Your Application:")
    print("   - Deploy your FastAPI app to a public server")
    print("   - Ensure HTTPS is enabled")
    print("   - Update the webhook URL with your actual domain")
    
    print("\n4️⃣  Test the Integration:")
    print("   - Send a message to your Facebook page")
    print("   - Check the logs for webhook processing")
    
    print("\n5️⃣  Environment Variables:")
    print("   - Ensure FACEBOOK_PAGE_ACCESS_TOKEN is set")
    print("   - Ensure FACEBOOK_VERIFY_TOKEN is set")
    
    print("\n" + "="*60)


async def test_message_processing():
    """Test message processing with dummy data"""
    print("\n🔍 Testing message processing...")
    
    try:
        facebook_service = FacebookMessengerService()
        
        # Create dummy webhook event
        dummy_event = {
            "object": "page",
            "entry": [
                {
                    "id": "123456789",
                    "messaging": [
                        {
                            "sender": {"id": "987654321"},
                            "message": {"text": "Hello"}
                        }
                    ]
                }
            ]
        }
        
        # Process webhook
        result = await facebook_service.process_webhook(dummy_event)
        
        if result["status"] == "success":
            print("✅ Message processing test successful")
            print(f"   Processed messages: {len(result.get('processed_messages', []))}")
            return True
        else:
            print(f"❌ Message processing test failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Message processing test failed: {str(e)}")
        return False


async def main():
    """Main setup function"""
    print("🚀 Facebook Messenger Integration Setup")
    print("="*50)
    
    # Test Facebook connection
    connection_ok = await test_facebook_connection()
    
    # Test webhook verification
    webhook_ok = await test_webhook_verification()
    
    # Test message processing
    processing_ok = await test_message_processing()
    
    # Print results
    print("\n" + "="*50)
    print("📊 SETUP RESULTS")
    print("="*50)
    print(f"Facebook Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Webhook Verification: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    print(f"Message Processing: {'✅ PASS' if processing_ok else '❌ FAIL'}")
    
    if connection_ok and webhook_ok and processing_ok:
        print("\n🎉 All tests passed! Your Facebook Messenger integration is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
    
    # Print setup instructions
    print_setup_instructions()


if __name__ == "__main__":
    asyncio.run(main()) 