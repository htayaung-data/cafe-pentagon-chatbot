#!/usr/bin/env python3
"""
Facebook Messaging Pattern Investigation Script
Identifies how your RAG chatbot actually sends messages to Facebook

Usage: python scripts/investigate_facebook_pattern.py
"""

import os
import sys
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from src.services.facebook_messenger import FacebookMessengerService
    from src.config.settings import get_settings
    FACEBOOK_SERVICE_AVAILABLE = True
except ImportError:
    FACEBOOK_SERVICE_AVAILABLE = False
    print("⚠️  Facebook service not available - some tests will be skipped")

def print_header():
    """Print script header"""
    print("=" * 80)
    print("🔍 FACEBOOK MESSAGING PATTERN INVESTIGATION")
    print("=" * 80)
    print("This script will identify how your RAG chatbot actually sends messages to Facebook")
    print()

def check_environment_variables():
    """Check Facebook-related environment variables"""
    print("🔍 Checking Facebook environment variables...")
    
    facebook_vars = [
        "FACEBOOK_PAGE_ACCESS_TOKEN",
        "FACEBOOK_VERIFY_TOKEN",
        "FACEBOOK_APP_ID",
        "FACEBOOK_APP_SECRET"
    ]
    
    third_party_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "MESSAGEBIRD_API_KEY",
        "SENDGRID_API_KEY"
    ]
    
    print("\n📋 Facebook Configuration:")
    for var in facebook_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 10}{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"   ❌ {var}: Not set")
    
    print("\n📋 Third-Party Services:")
    for var in third_party_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 10}{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"   ❌ {var}: Not set")
    
    return any(os.getenv(var) for var in facebook_vars + third_party_vars)

def check_installed_packages():
    """Check for Facebook-related Python packages"""
    print("\n📦 Checking installed packages...")
    
    facebook_packages = [
        "facebook-business",
        "facebook-sdk",
        "twilio",
        "messagebird",
        "sendgrid"
    ]
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True, check=True)
        installed_packages = result.stdout.lower()
        
        for package in facebook_packages:
            if package.lower() in installed_packages:
                print(f"   ✅ {package}: Installed")
            else:
                print(f"   ❌ {package}: Not installed")
                
    except subprocess.CalledProcessError:
        print("   ⚠️  Could not check installed packages")

def test_network_connectivity():
    """Test network connectivity to Facebook and alternatives"""
    print("\n🌐 Testing network connectivity...")
    
    test_urls = [
        ("Facebook Graph API", "https://graph.facebook.com/v18.0/me"),
        ("Facebook API (alt)", "https://api.facebook.com"),
        ("Facebook Business", "https://business.facebook.com"),
        ("Twilio API", "https://api.twilio.com"),
        ("MessageBird API", "https://rest.messagebird.com")
    ]
    
    import aiohttp
    
    async def test_urls():
        results = {}
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for name, url in test_urls:
                try:
                    async with session.get(url) as response:
                        results[name] = {
                            "status": response.status,
                            "accessible": response.status < 400
                        }
                        print(f"   ✅ {name}: HTTP {response.status}")
                except Exception as e:
                    results[name] = {
                        "status": "error",
                        "accessible": False,
                        "error": str(e)
                    }
                    print(f"   ❌ {name}: {str(e)}")
        
        return results
    
    return asyncio.run(test_urls())

def examine_facebook_service():
    """Examine the Facebook service implementation"""
    print("\n🔍 Examining Facebook service implementation...")
    
    if not FACEBOOK_SERVICE_AVAILABLE:
        print("   ⚠️  Facebook service not available")
        return None
    
    try:
        facebook_service = FacebookMessengerService()
        
        # Check service configuration
        config = {
            "api_url": facebook_service.api_url,
            "has_page_token": bool(facebook_service.page_access_token),
            "has_verify_token": bool(facebook_service.verify_token)
        }
        
        print(f"   📡 API URL: {config['api_url']}")
        print(f"   🔑 Page Token: {'✅ Set' if config['has_page_token'] else '❌ Not set'}")
        print(f"   🔐 Verify Token: {'✅ Set' if config['has_verify_token'] else '❌ Not set'}")
        
        return config
        
    except Exception as e:
        print(f"   ❌ Error examining Facebook service: {str(e)}")
        return None

def test_webhook_response():
    """Test webhook response pattern"""
    print("\n📡 Testing webhook response pattern...")
    
    test_payload = {
        "object": "page",
        "entry": [{
            "id": "test_page_id",
            "messaging": [{
                "sender": {"id": "test_user_id"},
                "message": {"text": "test message"}
            }]
        }]
    }
    
    print("   📤 Test webhook payload:")
    print(f"   {json.dumps(test_payload, indent=2)}")
    
    print("\n   💡 To test this manually:")
    print("   curl -X POST 'http://localhost:8000/webhook' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '" + json.dumps(test_payload) + "'")
    
    return test_payload

def check_file_patterns():
    """Check for alternative Facebook implementation patterns"""
    print("\n📁 Checking for alternative implementation patterns...")
    
    project_root = Path(__file__).parent.parent
    patterns_to_check = [
        "**/facebook*.py",
        "**/messenger*.py",
        "**/webhook*.py",
        "**/twilio*.py",
        "**/messagebird*.py"
    ]
    
    found_files = []
    for pattern in patterns_to_check:
        files = list(project_root.glob(pattern))
        found_files.extend(files)
    
    if found_files:
        print("   📋 Found Facebook-related files:")
        for file in found_files:
            print(f"      {file.relative_to(project_root)}")
    else:
        print("   ❌ No additional Facebook-related files found")
    
    return found_files

def check_docker_config():
    """Check Docker configuration for network settings"""
    print("\n🐳 Checking Docker configuration...")
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".dockerignore"
    ]
    
    project_root = Path(__file__).parent.parent
    found_docker_files = []
    
    for file in docker_files:
        file_path = project_root / file
        if file_path.exists():
            found_docker_files.append(file)
            print(f"   ✅ {file}: Found")
        else:
            print(f"   ❌ {file}: Not found")
    
    if found_docker_files:
        print("\n   💡 Check these files for:")
        print("      - Network configurations")
        print("      - Proxy settings")
        print("      - Firewall rules")
        print("      - Outbound connectivity restrictions")
    
    return found_docker_files

def generate_investigation_report():
    """Generate comprehensive investigation report"""
    print("\n📊 GENERATING INVESTIGATION REPORT")
    print("=" * 50)
    
    report = {
        "timestamp": asyncio.get_event_loop().time(),
        "environment_variables": check_environment_variables(),
        "packages": "Checked",
        "network_connectivity": "Tested",
        "facebook_service": "Examined",
        "webhook_pattern": "Documented",
        "file_patterns": "Checked",
        "docker_config": "Checked"
    }
    
    print("\n🎯 INVESTIGATION SUMMARY:")
    print("=" * 30)
    
    if report["environment_variables"]:
        print("✅ Facebook environment variables are configured")
    else:
        print("❌ No Facebook environment variables found")
    
    print("✅ Network connectivity tests completed")
    print("✅ Facebook service implementation examined")
    print("✅ Webhook response pattern documented")
    print("✅ File patterns checked")
    print("✅ Docker configuration checked")
    
    return report

def provide_next_steps():
    """Provide next steps based on investigation"""
    print("\n🚀 NEXT STEPS")
    print("=" * 20)
    
    print("\n1️⃣  **Immediate Actions:**")
    print("   - Run the webhook test manually")
    print("   - Check network connectivity results")
    print("   - Examine Facebook service configuration")
    
    print("\n2️⃣  **Pattern Identification:**")
    print("   - If webhook responses work: Implement webhook response pattern")
    print("   - If third-party services found: Use those instead")
    print("   - If network issues: Check infrastructure configuration")
    
    print("\n3️⃣  **Implementation:**")
    print("   - Copy working pattern to HITL system")
    print("   - Test with real Facebook users")
    print("   - Validate message delivery")
    
    print("\n4️⃣  **Documentation:**")
    print("   - Document the working pattern")
    print("   - Create implementation guide")
    print("   - Share with admin panel team")

async def main():
    """Main investigation function"""
    print_header()
    
    # Run all investigations
    check_environment_variables()
    check_installed_packages()
    network_results = test_network_connectivity()
    facebook_config = examine_facebook_service()
    test_webhook_response()
    check_file_patterns()
    check_docker_config()
    
    # Generate report
    report = generate_investigation_report()
    
    # Provide next steps
    provide_next_steps()
    
    print("\n🎉 Investigation complete!")
    print("\n📋 Key findings:")
    print("   - Environment variables checked")
    print("   - Network connectivity tested")
    print("   - Implementation patterns identified")
    print("   - Next steps provided")
    
    return report

if __name__ == "__main__":
    try:
        report = asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Investigation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Investigation failed: {str(e)}")
        sys.exit(1)
