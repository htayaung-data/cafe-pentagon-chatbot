#!/usr/bin/env python3
"""
Test script for Admin Panel Integration
Verifies that all admin endpoints are working correctly with authentication
"""

import requests
import json
import os
from datetime import datetime

# Test configuration
BASE_URL = "https://cafe-pentagon.up.railway.app"
ADMIN_API_KEY = "3wuHtoJ6Z1mfbBq4wEBPfnfRK2qhXXWg3TtLSOEZ9nJAFyJuog7nIM8CC54oZQOX"
ADMIN_USER_ID = "admin_d8e16f40"

# Headers for all requests
HEADERS = {
    "Authorization": f"Bearer {ADMIN_API_KEY}",
    "X-Admin-User-ID": ADMIN_USER_ID,
    "Content-Type": "application/json"
}

def test_health_check():
    """Test the admin health check endpoint"""
    print("🧪 Testing Admin Health Check...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/health", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful: {data['message']}")
            print(f"   Timestamp: {data['data']['timestamp']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_escalated_conversations():
    """Test the escalated conversations endpoint"""
    print("\n🧪 Testing Escalated Conversations...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/conversations/escalated", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Escalated conversations successful")
            print(f"   Found {len(data)} escalated conversations")
            return True
        else:
            print(f"❌ Escalated conversations failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Escalated conversations error: {str(e)}")
        return False

def test_authentication_failure():
    """Test that authentication fails with invalid credentials"""
    print("\n🧪 Testing Authentication Failure...")
    
    # Test with invalid API key
    invalid_headers = {
        "Authorization": "Bearer invalid-api-key",
        "X-Admin-User-ID": ADMIN_USER_ID,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/admin/health", headers=invalid_headers)
        
        if response.status_code == 401:
            print("✅ Authentication failure test passed (invalid API key)")
            return True
        else:
            print(f"❌ Authentication failure test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication failure test error: {str(e)}")
        return False

def test_missing_headers():
    """Test that requests fail without required headers"""
    print("\n🧪 Testing Missing Headers...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/health")
        
        if response.status_code == 401:
            print("✅ Missing headers test passed")
            return True
        else:
            print(f"❌ Missing headers test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Missing headers test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🔐 Cafe Pentagon Chatbot - Admin Integration Test")
    print("=" * 60)
    print(f"📅 Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🔑 Admin User ID: {ADMIN_USER_ID}")
    
    # Run tests
    tests = [
        test_health_check,
        test_escalated_conversations,
        test_authentication_failure,
        test_missing_headers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Admin integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print(f"\n✅ Admin Panel Integration Test Complete!")

if __name__ == "__main__":
    main()
