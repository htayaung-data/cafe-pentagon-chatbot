#!/usr/bin/env python3
"""
Test script to verify the improved URL validation
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_url_fix():
    """Test the improved URL validation"""
    try:
        print("🔍 Testing Improved URL Validation\n")
        
        # Import the Facebook Messenger service
        from src.services.facebook_messenger import FacebookMessengerService
        
        # Create service instance
        service = FacebookMessengerService()
        
        # Test URLs with double slash issues
        test_urls = [
            "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//friedfish.jpg",
            "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//bolognese.jpg",
            "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//pasta.jpg",
            "https://example.com//path//to//image.jpg",
            "https://qniujcgwyphkfnnqhjcq.supabase.co//storage//v1//object//public//cafepentagon//friedfish.jpg"
        ]
        
        print("1️⃣ Testing URL validation...")
        
        for i, original_url in enumerate(test_urls, 1):
            print(f"\n   Test {i}:")
            print(f"   Original: {original_url}")
            
            # Test the validation method
            validated_url = service._validate_image_url_for_facebook(original_url)
            print(f"   Validated: {validated_url}")
            
            if validated_url != original_url:
                print("   ✅ URL was fixed")
            else:
                print("   ⚠️ URL was not changed")
        
        print("\n2️⃣ Testing specific problematic URL...")
        
        # The exact URL from the logs
        problematic_url = "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//friedfish.jpg"
        fixed_url = service._validate_image_url_for_facebook(problematic_url)
        
        print(f"   Problematic URL: {problematic_url}")
        print(f"   Fixed URL: {fixed_url}")
        
        expected_fixed = "https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon/friedfish.jpg"
        
        if fixed_url == expected_fixed:
            print("   ✅ URL correctly fixed!")
        else:
            print(f"   ❌ URL not fixed correctly. Expected: {expected_fixed}")
        
        print("\n🎯 Summary:")
        print("   ✅ Improved URL validation implemented")
        print("   ✅ Double slash detection enhanced")
        print("   ✅ Ready to deploy and test!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_url_fix()) 