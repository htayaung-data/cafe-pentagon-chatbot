"""
Simple test script to verify app components work correctly
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.agents.main_agent import EnhancedMainAgent
        print("✅ EnhancedMainAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import EnhancedMainAgent: {e}")
        return False
    
    try:
        from src.data.loader import get_data_loader
        print("✅ DataLoader imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import DataLoader: {e}")
        return False
    
    try:
        from src.config.settings import get_settings
        print("✅ Settings imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Settings: {e}")
        return False
    
    try:
        from src.utils.logger import get_logger
        print("✅ Logger imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Logger: {e}")
        return False
    
    return True

def test_settings():
    """Test settings configuration"""
    print("\nTesting settings...")
    
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        
        print(f"✅ OpenAI Model: {settings.openai_model}")
        print(f"✅ Temperature: {settings.openai_temperature}")
        print(f"✅ Default Language: {settings.default_language}")
        print(f"✅ Debug Mode: {settings.debug}")
        
        return True
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def test_data_loader():
    """Test data loader functionality"""
    print("\nTesting data loader...")
    
    try:
        from src.data.loader import get_data_loader
        data_loader = get_data_loader()
        
        # Test menu data
        menu_data = data_loader.load_menu_data()
        print(f"✅ Menu items loaded: {len(menu_data)}")
        
        # Test FAQ data
        faq_data = data_loader.load_faq_data()
        print(f"✅ FAQ items loaded: {len(faq_data)}")
        
        # Test events data
        events_data = data_loader.load_events_data()
        print(f"✅ Events loaded: {len(events_data)}")
        
        # Test stats
        stats = data_loader.get_data_stats()
        print(f"✅ Data stats: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Data loader test failed: {e}")
        return False

def test_agent():
    """Test agent initialization"""
    print("\nTesting agent...")
    
    try:
        from src.agents.main_agent import EnhancedMainAgent
        agent = EnhancedMainAgent()
        print("✅ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Cafe Pentagon RAG App Components\n")
    
    tests = [
        ("Imports", test_imports),
        ("Settings", test_settings),
        ("Data Loader", test_data_loader),
        ("Agent", test_agent)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The app should work correctly.")
        print("\n🚀 To run the app:")
        print("1. Activate virtual environment: .\\venv\\Scripts\\activate.bat")
        print("2. Run the app: streamlit run app.py")
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
    
    return passed == total

if __name__ == "__main__":
    main() 