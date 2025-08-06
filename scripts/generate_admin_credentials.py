#!/usr/bin/env python3
"""
Generate secure admin credentials for the Cafe Pentagon Chatbot
This script generates a secure API key and admin user ID for admin panel authentication
"""

import secrets
import string
import uuid
from datetime import datetime

def generate_secure_api_key(length: int = 64) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_admin_user_id() -> str:
    """Generate a unique admin user ID"""
    return f"admin_{uuid.uuid4().hex[:8]}"

def main():
    """Generate and display admin credentials"""
    print("🔐 Cafe Pentagon Chatbot - Admin Credentials Generator")
    print("=" * 60)
    
    # Generate credentials
    api_key = generate_secure_api_key(64)
    admin_user_id = generate_admin_user_id()
    
    print(f"\n📅 Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n🔑 Generated Credentials:")
    print(f"   ADMIN_API_KEY={api_key}")
    print(f"   ADMIN_USER_ID={admin_user_id}")
    
    print(f"\n📋 Environment Variables for Railway:")
    print(f"   ADMIN_API_KEY={api_key}")
    print(f"   ADMIN_USER_ID={admin_user_id}")
    
    print(f"\n🔧 For Local Development (.env file):")
    print(f"   ADMIN_API_KEY={api_key}")
    print(f"   ADMIN_USER_ID={admin_user_id}")
    
    print(f"\n⚠️  IMPORTANT SECURITY NOTES:")
    print(f"   • Keep these credentials secure and confidential")
    print(f"   • Do not commit them to version control")
    print(f"   • Use different credentials for development and production")
    print(f"   • Rotate credentials regularly for security")
    
    print(f"\n🧪 Test the credentials with:")
    print(f"   curl -H 'Authorization: Bearer {api_key}' \\")
    print(f"        -H 'X-Admin-User-ID: {admin_user_id}' \\")
    print(f"        https://your-railway-app.up.railway.app/admin/health")
    
    print(f"\n✅ Credentials generated successfully!")
    print(f"   Please add these to your Railway environment variables.")

if __name__ == "__main__":
    main()
