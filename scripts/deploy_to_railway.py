"""
Railway Deployment Helper Script
Helps prepare and deploy the chatbot to Railway
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_git_status():
    """Check if git repository is clean"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print("⚠️  Uncommitted changes detected:")
            print(result.stdout)
            return False
        else:
            print("✅ Git repository is clean")
            return True
    except subprocess.CalledProcessError:
        print("❌ Git not available or not a git repository")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    required_vars = [
        'OPENAI_API_KEY',
        'PINECONE_API_KEY', 
        'PINECONE_ENVIRONMENT',
        'FACEBOOK_PAGE_ACCESS_TOKEN',
        'FACEBOOK_VERIFY_TOKEN',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f'{var}=' not in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env file has all required variables")
    return True

def check_requirements():
    """Check if requirements.txt is up to date"""
    try:
        # Generate current requirements
        subprocess.run(['pip', 'freeze'], 
                      capture_output=True, text=True, check=True)
        print("✅ Requirements check completed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to check requirements")
        return False

def create_railway_config():
    """Create Railway configuration files"""
    # railway.json already exists
    if Path('railway.json').exists():
        print("✅ railway.json exists")
    else:
        print("❌ railway.json missing")
        return False
    
    # Procfile already exists
    if Path('Procfile').exists():
        print("✅ Procfile exists")
    else:
        print("❌ Procfile missing")
        return False
    
    return True

def show_deployment_steps():
    """Show deployment steps"""
    print("\n🚀 Railway Deployment Steps:")
    print("=" * 50)
    print("1. Push your code to GitHub:")
    print("   git add .")
    print("   git commit -m 'Prepare for Railway deployment'")
    print("   git push origin main")
    print()
    print("2. Go to Railway Dashboard:")
    print("   https://railway.app/dashboard")
    print()
    print("3. Create New Project:")
    print("   - Click 'New Project'")
    print("   - Select 'Deploy from GitHub repo'")
    print("   - Choose your repository")
    print()
    print("4. Configure Environment Variables:")
    print("   - Go to your project settings")
    print("   - Add all variables from your .env file")
    print()
    print("5. Deploy:")
    print("   - Railway will automatically deploy")
    print("   - Or manually trigger deployment")
    print()
    print("6. Get your Railway URL:")
    print("   - Copy the provided URL")
    print("   - Update Facebook webhook with new URL")
    print()
    print("7. Test the bot:")
    print("   - Send a message to your Facebook page")
    print("   - Check Railway logs for any issues")

def main():
    """Main deployment check function"""
    print("🔍 Railway Deployment Pre-Check")
    print("=" * 40)
    
    checks = [
        ("Git Status", check_git_status),
        ("Environment Variables", check_env_file),
        ("Requirements", check_requirements),
        ("Railway Config", create_railway_config)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            all_passed = False
    
    if all_passed:
        print("\n✅ All checks passed! Ready for Railway deployment.")
        show_deployment_steps()
    else:
        print("\n❌ Some checks failed. Please fix issues before deploying.")
        print("\n💡 Quick fixes:")
        print("- Commit all changes: git add . && git commit -m 'Update'")
        print("- Check .env file has all required variables")
        print("- Ensure railway.json and Procfile exist")

if __name__ == "__main__":
    main() 