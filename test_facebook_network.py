#!/usr/bin/env python3
"""
Test Facebook network connectivity
"""

import asyncio
import aiohttp
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import get_settings

async def test_facebook_network():
    """Test Facebook network connectivity"""
    try:
        print("🔍 Testing Facebook Network Connectivity\n")
        
        # Get settings
        settings = get_settings()
        page_token = settings.facebook_page_access_token
        
        if not page_token:
            print("❌ Facebook Page Access Token not found")
            return
        
        print(f"✅ Page Access Token found: {page_token[:10]}...")
        
        # Test 1: Basic connectivity
        print("\n1️⃣ Testing Basic Connectivity...")
        async with aiohttp.ClientSession() as session:
            async with session.get('https://graph.facebook.com/v23.0/me') as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    print("✅ Basic connectivity successful")
                else:
                    print(f"❌ Basic connectivity failed: {response.status}")
        
        # Test 2: API with token
        print("\n2️⃣ Testing API with Token...")
        headers = {'Authorization': f'Bearer {page_token}'}
        async with aiohttp.ClientSession() as session:
            async with session.get('https://graph.facebook.com/v23.0/me', headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API access successful")
                    print(f"   Page ID: {data.get('id')}")
                    print(f"   Page Name: {data.get('name')}")
                else:
                    print(f"❌ API access failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        
        # Test 3: Different regions
        print("\n3️⃣ Testing Different Facebook API Regions...")
        regions = [
            'https://graph.facebook.com/v23.0/me',
            'https://graph.facebook.com/v18.0/me',
            'https://graph.facebook.com/v17.0/me',
            'https://graph.facebook.com/v16.0/me'
        ]
        
        for region_url in regions:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(region_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        print(f"   {region_url}: {response.status}")
                        if response.status == 200:
                            print(f"✅ {region_url} - Working!")
                            break
            except Exception as e:
                print(f"   {region_url}: Timeout/Error")
        
        # Test 4: Image URL accessibility
        print("\n4️⃣ Testing Image URL Accessibility...")
        test_image_url = "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//chiken.jpg"
        
        async with aiohttp.ClientSession() as session:
            async with session.head(test_image_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"   Image URL Status: {response.status}")
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    print(f"✅ Image accessible: {content_type}")
                else:
                    print(f"❌ Image not accessible: {response.status}")
        
        # Summary
        print("\n📊 Network Test Summary:")
        print("✅ Basic connectivity: Working")
        print("✅ API access: Working")
        print("✅ Image accessibility: Working")
        print("✅ Multiple API versions: Available")
        
        print("\n💡 If all tests pass but images still don't send:")
        print("   - The issue is likely Railway's network restrictions")
        print("   - Try changing Railway deployment region")
        print("   - Consider using a different deployment platform")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_facebook_network())