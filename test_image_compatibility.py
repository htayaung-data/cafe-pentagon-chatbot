#!/usr/bin/env python3
"""
Test script to check image URL compatibility with Facebook Messenger
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.facebook_messenger import FacebookMessengerService
from src.agents.main_agent import EnhancedMainAgent

async def test_image_compatibility():
    """Test image URL compatibility with Facebook Messenger"""
    try:
        print("🔍 Testing Image URL Compatibility with Facebook Messenger\n")
        
        # Test 1: Get image info from main agent
        print("1️⃣ Getting Image Info from Main Agent...")
        agent = EnhancedMainAgent()
        
        test_message = "Show me the photo of Fried Noodle with pork"
        user_id = "test_user_123"
        
        result = await agent.chat(test_message, user_id)
        
        if result.get('image_info'):
            print("✅ Image info generated successfully")
            image_url = result['image_info']['image_url']
            caption = result['image_info']['caption']
            print(f"   Image URL: {image_url}")
            print(f"   Caption: {caption}")
        else:
            print("❌ No image info generated")
            return
        
        # Test 2: Initialize Facebook service
        print("\n2️⃣ Initializing Facebook Service...")
        fb_service = FacebookMessengerService()
        print("✅ Facebook service initialized")
        
        # Test 3: Validate image URL
        print("\n3️⃣ Validating Image URL...")
        validated_url = fb_service._validate_image_url_for_facebook(image_url)
        print(f"   Original URL: {image_url}")
        print(f"   Validated URL: {validated_url}")
        print(f"   Validation: {'✅ Passed' if validated_url else '❌ Failed'}")
        
        if not validated_url:
            print("❌ Image URL validation failed")
            return
        
        # Test 4: Test image accessibility
        print("\n4️⃣ Testing Image Accessibility...")
        is_accessible = await fb_service._test_image_url_accessibility(validated_url)
        print(f"   Accessibility: {'✅ Accessible' if is_accessible else '❌ Not Accessible'}")
        
        if not is_accessible:
            print("❌ Image URL is not accessible")
            print("   This might be why Facebook can't display the image")
            return
        
        # Test 5: Test Facebook API connectivity
        print("\n5️⃣ Testing Facebook API Connectivity...")
        connectivity_result = await fb_service.test_api_connectivity()
        print(f"   Status: {connectivity_result['status']}")
        
        if connectivity_result['status'] == 'success':
            print("✅ Facebook API connectivity successful")
        elif connectivity_result['status'] == 'timeout':
            print("⏰ Facebook API timeout - this is the main issue")
        else:
            print(f"❌ Facebook API issue: {connectivity_result.get('error', 'Unknown')}")
        
        # Test 6: Try sending image (if API is accessible)
        if connectivity_result['status'] == 'success':
            print("\n6️⃣ Testing Image Sending...")
            success = await fb_service.send_image(
                "test_recipient", 
                validated_url, 
                caption
            )
            print(f"   Image sending: {'✅ Success' if success else '❌ Failed'}")
        else:
            print("\n6️⃣ Skipping Image Sending (API not accessible)")
        
        # Summary
        print("\n📊 Compatibility Test Summary:")
        print(f"✅ Image generation: Working")
        print(f"✅ URL validation: {'Working' if validated_url else 'Failed'}")
        print(f"✅ URL accessibility: {'Working' if is_accessible else 'Failed'}")
        print(f"📡 Facebook API: {connectivity_result['status']}")
        
        if validated_url and is_accessible and connectivity_result['status'] == 'success':
            print("\n🎉 All tests passed! Images should work with Facebook Messenger.")
        elif validated_url and is_accessible and connectivity_result['status'] == 'timeout':
            print("\n⚠️ Image URLs are valid and accessible, but Facebook API is timing out.")
            print("   This suggests a network connectivity issue to Facebook's servers.")
            print("   The fallback mechanism will provide image URLs to users.")
        else:
            print("\n❌ Some compatibility issues detected.")
            print("   The fallback mechanism will ensure users still get image information.")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_compatibility())