"""
Cloudflare Tunnel Setup Script for Facebook Messenger Webhook Testing
Alternative to ngrok for creating secure tunnels
"""

import subprocess
import time
import requests
import json
import sys
import os
import re
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings


def check_cloudflared_installed() -> bool:
    """Check if cloudflared is installed and accessible"""
    try:
        result = subprocess.run(['cloudflared', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Cloudflared found: {result.stdout.strip()}")
            return True
        else:
            # Try local cloudflared.exe
            result = subprocess.run(['./cloudflared.exe', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Local cloudflared found: {result.stdout.strip()}")
                return True
            else:
                print("❌ Cloudflared not found or not accessible")
                return False
    except FileNotFoundError:
        print("❌ Cloudflared not found. Please install cloudflared first.")
        return False


def check_cloudflared_auth() -> bool:
    """Check if cloudflared is authenticated"""
    try:
        result = subprocess.run(['cloudflared', 'tunnel', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Cloudflared is authenticated")
            return True
        else:
            # Try local cloudflared.exe
            result = subprocess.run(['./cloudflared.exe', 'tunnel', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Cloudflared is authenticated")
                return True
            else:
                print("❌ Cloudflared not authenticated. Please run: cloudflared tunnel login")
                return False
    except Exception as e:
        print(f"❌ Error checking authentication: {str(e)}")
        return False


def create_tunnel(tunnel_name: str = "cafe-pentagon-bot") -> Optional[str]:
    """Create a new Cloudflare tunnel"""
    try:
        print(f"🚀 Creating tunnel: {tunnel_name}")
        
        # Create tunnel
        result = subprocess.run(
            ['cloudflared', 'tunnel', 'create', tunnel_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Try local cloudflared.exe
            result = subprocess.run(
                ['./cloudflared.exe', 'tunnel', 'create', tunnel_name],
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            print(f"✅ Tunnel created: {tunnel_name}")
            return tunnel_name
        else:
            print(f"❌ Failed to create tunnel: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating tunnel: {str(e)}")
        return None


def get_tunnel_url(tunnel_name: str) -> Optional[str]:
    """Get the public URL for a tunnel"""
    try:
        # Get tunnel info
        result = subprocess.run(
            ['cloudflared', 'tunnel', 'info', tunnel_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Try local cloudflared.exe
            result = subprocess.run(
                ['./cloudflared.exe', 'tunnel', 'info', tunnel_name],
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            # Parse the output to find the URL
            output = result.stdout
            # Look for the tunnel URL pattern
            url_match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', output)
            if url_match:
                return url_match.group(0)
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting tunnel URL: {str(e)}")
        return None


def start_tunnel(tunnel_name: str, port: int = 8000) -> Optional[str]:
    """Start a Cloudflare tunnel"""
    try:
        print(f"🚀 Starting tunnel {tunnel_name} for port {port}...")
        
        # Start tunnel in background
        process = subprocess.Popen(
            ['cloudflared', 'tunnel', 'run', tunnel_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for tunnel to start
        time.sleep(5)
        
        # Get tunnel URL
        tunnel_url = get_tunnel_url(tunnel_name)
        
        if tunnel_url:
            print(f"✅ Tunnel started: {tunnel_url}")
            return tunnel_url
        else:
            print("❌ Failed to get tunnel URL")
            return None
            
    except Exception as e:
        print(f"❌ Error starting tunnel: {str(e)}")
        return None


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
        
        response = requests.get(webhook_url, params=test_params, timeout=10)
        
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
    print("☁️ Cloudflare Tunnel Setup for Facebook Messenger Webhook")
    print("="*60)
    
    # Check if cloudflared is installed
    if not check_cloudflared_installed():
        print("\n📥 Please install cloudflared first:")
        print("1. Download from: https://github.com/cloudflare/cloudflared/releases")
        print("2. Or run: winget install Cloudflare.cloudflared")
        print("3. Or use the local cloudflared.exe in this directory")
        return
    
    # Check if cloudflared is authenticated
    if not check_cloudflared_auth():
        print("\n🔐 Please authenticate cloudflared:")
        print("Run: cloudflared tunnel login")
        print("Or: ./cloudflared.exe tunnel login")
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
    
    # Create tunnel
    tunnel_name = "cafe-pentagon-bot"
    tunnel = create_tunnel(tunnel_name)
    
    if not tunnel:
        print("❌ Failed to create tunnel")
        return
    
    # Start tunnel
    webhook_url = start_tunnel(tunnel, 8000)
    
    if not webhook_url:
        print("❌ Failed to start tunnel")
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
            print("\n🛑 Stopping tunnel...")
            print("👋 Goodbye!")
    else:
        print("❌ Webhook endpoint test failed")


if __name__ == "__main__":
    main() 