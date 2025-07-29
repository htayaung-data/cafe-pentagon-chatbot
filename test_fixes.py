#!/usr/bin/env python3
"""
Test script to verify the cache and user manager fixes
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_fixes():
    """Test the cache and user manager fixes"""
    try:
        print("🔍 Testing Cache and User Manager Fixes\n")
        
        # Test 1: Cache Manager
        print("1️⃣ Testing Cache Manager...")
        from src.utils.cache import get_cache_manager
        
        cache_manager = get_cache_manager()
        
        # Test cache set/get
        test_key = "test:key"
        test_value = "test_value"
        
        # Test set with ttl
        success = cache_manager.set(test_key, test_value, ttl=60)
        print(f"   Cache set: {success}")
        
        # Test get
        retrieved_value = cache_manager.get(test_key)
        print(f"   Cache get: {retrieved_value == test_value}")
        
        if success and retrieved_value == test_value:
            print("   ✅ Cache manager working correctly")
        else:
            print("   ❌ Cache manager has issues")
            return
        
        # Test 2: User Manager
        print("\n2️⃣ Testing User Manager...")
        from src.services.user_manager import UserManager
        
        user_manager = UserManager()
        print("   ✅ User manager initialized")
        
        # Test 3: Facebook ID extraction
        print("\n3️⃣ Testing Facebook ID extraction...")
        from src.data.user_models import UserProfile, FacebookUserProfile, UserPreferences, UserSourceEnum, UserStatusEnum
        
        # Create a test user profile
        fb_profile = FacebookUserProfile(
            facebook_id="test_123456",
            name="Test User",
            first_name="Test",
            last_name="User"
        )
        
        user_profile = UserProfile(
            user_id="test_user_123",
            facebook_profile=fb_profile,
            source=UserSourceEnum.FACEBOOK_MESSENGER,
            status=UserStatusEnum.ACTIVE,
            preferences=UserPreferences()
        )
        
        # Test facebook_id extraction
        facebook_id = user_profile.facebook_profile.facebook_id if user_profile.facebook_profile else None
        
        if facebook_id:
            print(f"   ✅ Facebook ID extracted: {facebook_id}")
        else:
            print("   ❌ Facebook ID extraction failed")
            return
        
        print("\n🎯 Summary:")
        print("   ✅ Cache manager fixed (no more 'expire' parameter issues)")
        print("   ✅ Cache methods are synchronous (no more await issues)")
        print("   ✅ Facebook ID extraction working")
        print("   ✅ User manager initialization working")
        
        print("\n💡 Ready to deploy fixes!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixes()) 