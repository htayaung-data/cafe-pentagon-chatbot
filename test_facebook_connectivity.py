#!/usr/bin/env python3
"""
Simple test script to check Facebook API connectivity
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.facebook_messenger import FacebookMessengerService
from src.config.settings import get_settings

async def test_facebook_connectivity():
    """Test Facebook API connectivity"""
    try:
        print("🔍 Testing Facebook API connectivity...")
        
        # Check if Facebook credentials are configured
        settings = get_settings()
        if not settings.facebook_page_access_token:
            print("❌ Facebook Page Access Token not configured")
            print("Please set FACEBOOK_PAGE_ACCESS_TOKEN in your environment variables")
            return
        
        print("✅ Facebook Page Access Token is configured")
        
        # Initialize Facebook service
        fb_service = FacebookMessengerService()
        
        # Test API connectivity
        print("📡 Testing API connectivity...")
        connectivity_result = await fb_service.test_api_connectivity()
        
        print(f"📊 Connectivity Result: {connectivity_result['status']}")
        
        if connectivity_result['status'] == 'success':
            print("✅ Facebook API connectivity successful!")
            page_info = connectivity_result['page_info']
            print(f"   Page ID: {page_info.get('id')}")
            print(f"   Page Name: {page_info.get('name')}")
        elif connectivity_result['status'] == 'timeout':
            print("⏰ Connection timeout - this might be due to:")
            print("   - Network connectivity issues")
            print("   - Facebook API being temporarily unavailable")
            print("   - Firewall blocking the connection")
        elif connectivity_result['status'] == 'failed':
            print(f"❌ API call failed: {connectivity_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Exception occurred: {connectivity_result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_facebook_connectivity())