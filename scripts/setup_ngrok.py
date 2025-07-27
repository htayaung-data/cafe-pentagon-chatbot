"""
Ngrok Setup Script for Facebook Messenger Webhook Testing
Helps configure ngrok for local development
"""

import subprocess
import time
import requests
import json
import sys
import os
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings


def check_ngrok_installed() -> bool:
    """Check if ngrok is installed and accessible"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ngrok found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ngrok not found or not accessible")
            return False
    except FileNotFoundError:
        print("❌ Ngrok not found. Please install ngrok first.")
        return False


def get_ngrok_tunnels() -> Optional[Dict[str, Any]]:
    """Get current ngrok tunnels"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def start_ngrok_tunnel(port: int = 8000) -> Optional[str]:
    """Start ngrok tunnel for the specified port"""
    try:
        print(f"🚀 Starting ngrok tunnel for port {port}...")
        
        # Start ngrok in background
        process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Check if ngrok started successfully
        tunnels = get_ngrok_tunnels()
        if tunnels and tunnels.get('tunnels'):
            https_url = None
            for tunnel in tunnels['tunnels']:
                if tunnel['proto'] == 'https':
                    https_url = tunnel['public_url']
                    break
            
            if https_url:
                print(f"✅ Ngrok tunnel started: {https_url}")
                return https_url
            else:
                print("❌ No HTTPS tunnel found")
                return None
        else:
            print("❌ Failed to start ngrok tunnel")
            return None
            
    except Exception as e:
        print(f"❌ Error starting ngrok: {str(e)}")
        return None


def stop_ngrok_tunnel():
    """Stop ngrok tunnel"""
    try:
        # Kill ngrok process
        subprocess.run(['pkill', 'ngrok'], capture_output=True)
        print("🛑 Ngrok tunnel stopped")
    except Exception as e:
        print(f"⚠️  Error stopping ngrok: {str(e)}")


def test_webhook_endpoint(base_url: str) -> bool:
    """Test webhook endpoint"""
    try:
        webhook_url = f"{base_url}/webhook"
        
        # Test webhook verification
        test_params = {
            'mode': 'subscribe',
            'token': get_settings().facebook_verify_token,
            'challenge': 'test_challenge_123'
        }
        
        response = requests.get(webhook_url, params=test_params)
        
        if response.status_code == 200:
            print(f"✅ Webhook verification test passed: {response.text}")
            return True
        else:
            print(f"❌ Webhook verification test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook test error: {str(e)}")
        return False


def print_facebook_setup_instructions(webhook_url: str):
    """Print Facebook setup instructions"""
    print("\n" + "="*60)
    print("📋 FACEBOOK MESSENGER WEBHOOK SETUP")
    print("="*60)
    
    print(f"\n🌐 Your webhook URL: {webhook_url}")
    print(f"🔑 Verify Token: {get_settings().facebook_verify_token}")
    
    print("\n1️⃣  Go to Facebook Developers Console:")
    print("   https://developers.facebook.com")
    
    print("\n2️⃣  Select your app and go to Messenger > Settings")
    
    print("\n3️⃣  Add your page to the app if not already added")
    
    print("\n4️⃣  Click 'Add Callback URL' and enter:")
    print(f"   Callback URL: {webhook_url}")
    print(f"   Verify Token: {get_settings().facebook_verify_token}")
    
    print("\n5️⃣  Subscribe to these events:")
    print("   ✅ messages")
    print("   ✅ messaging_postbacks")
    
    print("\n6️⃣  Click 'Verify and Save'")
    
    print("\n7️⃣  Test by sending a message to your Facebook page")
    
    print("\n" + "="*60)


def main():
    """Main setup function"""
    print("🌐 Ngrok Setup for Facebook Messenger Webhook")
    print("="*50)
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        print("\n📥 Please install ngrok first:")
        print("1. Go to https://ngrok.com")
        print("2. Sign up for a free account")
        print("3. Download and install ngrok")
        print("4. Run: ngrok config add-authtoken YOUR_TOKEN")
        return
    
    # Check if FastAPI app is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ FastAPI app not running on port 8000")
            print("Please start your app first: python api.py")
            return
    except requests.exceptions.RequestException:
        print("❌ FastAPI app not running on port 8000")
        print("Please start your app first: python api.py")
        return
    
    print("✅ FastAPI app is running on port 8000")
    
    # Start ngrok tunnel
    webhook_url = start_ngrok_tunnel(8000)
    
    if not webhook_url:
        print("❌ Failed to start ngrok tunnel")
        return
    
    # Test webhook endpoint
    if test_webhook_endpoint(webhook_url):
        print("✅ Webhook endpoint is working correctly")
        
        # Print setup instructions
        print_facebook_setup_instructions(webhook_url)
        
        print("\n🔄 Keep this terminal open to maintain the tunnel")
        print("Press Ctrl+C to stop the tunnel")
        
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping ngrok tunnel...")
            stop_ngrok_tunnel()
            print("👋 Goodbye!")
    else:
        print("❌ Webhook endpoint test failed")
        stop_ngrok_tunnel()


if __name__ == "__main__":
    main() 