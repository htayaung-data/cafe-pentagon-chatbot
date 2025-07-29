#!/usr/bin/env python3
"""
Test script for Facebook Messenger image sending functionality
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.facebook_messenger import FacebookMessengerService
from src.config.settings import get_settings

async def test_facebook_messenger():
    """Test Facebook Messenger functionality"""
    try:
        # Initialize the service
        fb_service = FacebookMessengerService()
        
        print("🔍 Testing Facebook Messenger API connectivity...")
        
        # Test API connectivity
        connectivity_result = await fb_service.test_api_connectivity()
        print(f"📡 API Connectivity: {connectivity_result['status']}")
        
        if connectivity_result['status'] == 'success':
            print(f"✅ Page ID: {connectivity_result['page_info'].get('id')}")
            print(f"✅ Page Name: {connectivity_result['page_info'].get('name')}")
        else:
            print(f"❌ Error: {connectivity_result.get('error', 'Unknown error')}")
            return
        
        # Test image sending (you'll need to provide a test recipient ID)
        test_recipient_id = input("Enter a test recipient ID (Facebook user ID): ").strip()
        
        if test_recipient_id:
            print("🖼️ Testing image sending...")
            
            # Test with a known working image URL
            test_result = await fb_service.test_image_sending(
                test_recipient_id,
                "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop"
            )
            
            print(f"📸 Image Test Result: {test_result['status']}")
            print(f"📸 Image Sent: {test_result['image_sent']}")
            
            if test_result['status'] == 'success':
                print("✅ Image sending test completed successfully!")
            else:
                print(f"❌ Image sending failed: {test_result.get('error', 'Unknown error')}")
        else:
            print("⚠️ No recipient ID provided, skipping image test")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_facebook_messenger())