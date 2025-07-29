#!/usr/bin/env python3
"""
Debug script to test Supabase image URL accessibility
"""

import asyncio
import aiohttp
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_supabase_image():
    """Test the specific Supabase image URL"""
    
    # The URL from the user's message
    image_url = "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//friedfish.jpg"
    
    print(f"🔍 Testing Supabase Image URL: {image_url}")
    print()
    
    # Test 1: Basic accessibility
    print("1️⃣ Testing basic accessibility...")
    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(image_url) as response:
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                print(f"   Content-Length: {response.headers.get('content-length', 'N/A')}")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if content_type.startswith('image/'):
                        print("   ✅ Image is accessible and has correct content type")
                    else:
                        print(f"   ❌ URL accessible but not an image: {content_type}")
                else:
                    print(f"   ❌ URL not accessible: {response.status}")
    except Exception as e:
        print(f"   ❌ Error testing accessibility: {str(e)}")
    
    print()
    
    # Test 2: Try to download a small part of the image
    print("2️⃣ Testing image download...")
    try:
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(image_url, headers={'Range': 'bytes=0-1023'}) as response:
                print(f"   Status: {response.status}")
                if response.status in [200, 206]:
                    data = await response.read()
                    print(f"   Downloaded {len(data)} bytes")
                    if len(data) > 0:
                        print("   ✅ Image download successful")
                    else:
                        print("   ❌ Image download returned empty data")
                else:
                    print(f"   ❌ Image download failed: {response.status}")
    except Exception as e:
        print(f"   ❌ Error downloading image: {str(e)}")
    
    print()
    
    # Test 3: Test with Facebook-like headers
    print("3️⃣ Testing with Facebook-like headers...")
    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        headers = {
            'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
            'Accept': 'image/*'
        }
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(image_url, headers=headers) as response:
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                if response.status == 200:
                    print("   ✅ Image accessible with Facebook-like headers")
                else:
                    print(f"   ❌ Image not accessible with Facebook-like headers: {response.status}")
    except Exception as e:
        print(f"   ❌ Error with Facebook-like headers: {str(e)}")
    
    print()
    
    # Test 4: Check if URL needs fixing
    print("4️⃣ Checking URL format...")
    
    # Fix double slash issue
    fixed_url = image_url.replace('//friedfish.jpg', '/friedfish.jpg')
    print(f"   Original URL: {image_url}")
    print(f"   Fixed URL: {fixed_url}")
    
    if fixed_url != image_url:
        print("   🔧 URL has double slash issue - trying fixed URL...")
        try:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(fixed_url) as response:
                    print(f"   Fixed URL Status: {response.status}")
                    if response.status == 200:
                        print("   ✅ Fixed URL works!")
                    else:
                        print(f"   ❌ Fixed URL still doesn't work: {response.status}")
        except Exception as e:
            print(f"   ❌ Error testing fixed URL: {str(e)}")
    
    print()
    print("🎯 Summary:")
    print("   - If the image is accessible but Facebook still can't send it,")
    print("     the issue might be with Facebook's image validation or")
    print("     Supabase storage permissions.")
    print("   - We may need to use the ImageStorageService to re-upload")
    print("     to a Facebook-compatible service like Imgur or Cloudinary.")

if __name__ == "__main__":
    asyncio.run(test_supabase_image()) 