#!/usr/bin/env python3
"""
Debug script to test image sending functionality
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.main_agent import EnhancedMainAgent
from src.services.facebook_messenger import FacebookMessengerService

async def test_image_generation():
    """Test image generation in the main agent"""
    try:
        print("🔍 Testing image generation in main agent...")
        
        # Initialize the agent
        agent = EnhancedMainAgent()
        
        # Test with a known menu item
        test_message = "Show me the photo of Fried Noodle with pork"
        user_id = "test_user_123"
        
        print(f"📝 Testing with message: {test_message}")
        
        # Get response from agent
        result = await agent.chat(test_message, user_id)
        
        print(f"📋 Response: {result.get('response', 'No response')}")
        print(f"🖼️ Image info: {result.get('image_info', 'No image info')}")
        print(f"🎯 Primary intent: {result.get('primary_intent', 'No intent')}")
        
        # Check if image info is present
        if result.get('image_info'):
            image_info = result['image_info']
            print(f"✅ Image URL: {image_info.get('image_url')}")
            print(f"✅ Caption: {image_info.get('caption')}")
        else:
            print("❌ No image info found in response")
            
            # Check if the response contains image markers
            response = result.get('response', '')
            if '[IMAGE_MARKER:' in response:
                print("🔍 Found IMAGE_MARKER in response text")
            elif '<img' in response:
                print("🔍 Found HTML img tag in response text")
            else:
                print("🔍 No image markers found in response text")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_facebook_image_sending():
    """Test Facebook image sending"""
    try:
        print("\n🔍 Testing Facebook image sending...")
        
        # Initialize Facebook service
        fb_service = FacebookMessengerService()
        
        # Test API connectivity first
        connectivity_result = await fb_service.test_api_connectivity()
        print(f"📡 API Connectivity: {connectivity_result['status']}")
        
        if connectivity_result['status'] != 'success':
            print(f"❌ Cannot test image sending - API connectivity failed")
            return
        
        # Test with a known working image URL
        test_image_url = "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//bread.jpg"
        
        print(f"🖼️ Testing with image URL: {test_image_url}")
        
        # Note: This would require a real recipient ID, so we'll just test the method structure
        print("⚠️ Note: This test requires a real Facebook recipient ID")
        print("✅ Facebook service initialized successfully")
        
    except Exception as e:
        print(f"❌ Facebook test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_vector_search():
    """Test vector search for image retrieval"""
    try:
        print("\n🔍 Testing vector search for image retrieval...")
        
        from src.services.vector_search_service import get_vector_search_service
        
        vector_search = get_vector_search_service()
        
        # Test with a known menu item
        test_item = "Fried Noodle with pork"
        
        print(f"🔍 Searching for: {test_item}")
        
        image_info = await vector_search.get_item_image(test_item)
        
        if image_info:
            print(f"✅ Found image info:")
            print(f"   Item name: {image_info.get('item_name')}")
            print(f"   Image URL: {image_info.get('image_url')}")
            print(f"   Price: {image_info.get('price')}")
            print(f"   Category: {image_info.get('category')}")
        else:
            print(f"❌ No image info found for: {test_item}")
        
    except Exception as e:
        print(f"❌ Vector search test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("🚀 Starting image functionality debug tests...\n")
    
    # Test 1: Image generation in main agent
    await test_image_generation()
    
    # Test 2: Vector search for image retrieval
    await test_vector_search()
    
    # Test 3: Facebook image sending (requires real recipient ID)
    await test_facebook_image_sending()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())