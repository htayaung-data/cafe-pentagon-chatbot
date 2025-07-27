"""
Test Facebook API Connectivity
Simple script to check if we can reach Facebook's API
"""

import asyncio
import aiohttp
import requests
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings

async def test_facebook_api_async():
    """Test Facebook API connectivity using aiohttp"""
    print("🔍 Testing Facebook API Connectivity (Async)...")
    
    try:
        settings = get_settings()
        url = f"https://graph.facebook.com/v18.0/me?access_token={settings.facebook_page_access_token}"
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Facebook API accessible (Async)")
                    print(f"   Page ID: {data.get('id', 'Unknown')}")
                    print(f"   Page Name: {data.get('name', 'Unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Facebook API error (Async): {response.status} - {error_text}")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Facebook API timeout (Async)")
        return False
    except Exception as e:
        print(f"❌ Facebook API exception (Async): {str(e)}")
        return False

def test_facebook_api_sync():
    """Test Facebook API connectivity using requests"""
    print("🔍 Testing Facebook API Connectivity (Sync)...")
    
    try:
        settings = get_settings()
        url = f"https://graph.facebook.com/v18.0/me?access_token={settings.facebook_page_access_token}"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Facebook API accessible (Sync)")
            print(f"   Page ID: {data.get('id', 'Unknown')}")
            print(f"   Page Name: {data.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Facebook API error (Sync): {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Facebook API timeout (Sync)")
        return False
    except Exception as e:
        print(f"❌ Facebook API exception (Sync): {str(e)}")
        return False

def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("🔍 Testing Basic Internet Connectivity...")
    
    try:
        # Test basic HTTPS connectivity
        response = requests.get("https://www.google.com", timeout=10)
        if response.status_code == 200:
            print("✅ Basic internet connectivity: OK")
            return True
        else:
            print(f"❌ Basic internet connectivity: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Basic internet connectivity: Failed - {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🚀 Facebook API Connectivity Test")
    print("=" * 40)
    
    # Test basic connectivity first
    basic_ok = test_basic_connectivity()
    if not basic_ok:
        print("\n❌ Basic internet connectivity failed. Check your network connection.")
        return
    
    # Test Facebook API with both methods
    sync_ok = test_facebook_api_sync()
    async_ok = await test_facebook_api_async()
    
    print("\n📋 Summary:")
    print(f"   Basic Connectivity: {'✅ OK' if basic_ok else '❌ Failed'}")
    print(f"   Facebook API (Sync): {'✅ OK' if sync_ok else '❌ Failed'}")
    print(f"   Facebook API (Async): {'✅ OK' if async_ok else '❌ Failed'}")
    
    if not sync_ok and not async_ok:
        print("\n🚨 Facebook API is not accessible!")
        print("Possible causes:")
        print("1. Network firewall blocking Facebook")
        print("2. Invalid access token")
        print("3. Network connectivity issues")
        print("4. Facebook API service issues")
        
        print("\n💡 Solutions:")
        print("1. Try from a different network (mobile hotspot)")
        print("2. Check your Facebook Page Access Token")
        print("3. Check if Facebook is accessible in your browser")
        print("4. Contact your network administrator")

if __name__ == "__main__":
    asyncio.run(main()) 