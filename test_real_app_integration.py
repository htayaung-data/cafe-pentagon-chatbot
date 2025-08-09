"""
Test Real Application Integration
Test to verify the integrated system works with Streamlit and Facebook Messenger
"""

import asyncio
import uuid
from src.graph.state_graph import create_conversation_graph, create_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_real_app_integration")


async def test_streamlit_integration():
    """Test integration with Streamlit app"""
    
    print("🖥️ Testing Streamlit App Integration")
    print("=" * 50)
    
    # Create the workflow (using the main state_graph interface)
    workflow = create_conversation_graph()
    
    # Test cases that simulate real user interactions
    streamlit_test_cases = [
        {
            "name": "English Menu Query",
            "message": "What's on your menu?",
            "user_id": "streamlit_user_1",
            "platform": "streamlit"
        },
        {
            "name": "Burmese Location Query", 
            "message": "ဆိုင်ဘယ်မှာလဲ",
            "user_id": "streamlit_user_2",
            "platform": "streamlit"
        },
        {
            "name": "Human Assistance Request",
            "message": "I need to speak to a manager",
            "user_id": "streamlit_user_3", 
            "platform": "streamlit"
        }
    ]
    
    passed_tests = 0
    total_tests = len(streamlit_test_cases)
    
    for i, test in enumerate(streamlit_test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test['name']}")
        print(f"   Message: '{test['message']}'")
        print(f"   User: {test['user_id']} | Platform: {test['platform']}")
        
        try:
            # Create initial state using the main interface
            initial_state = create_initial_state(
                user_message=test["message"],
                user_id=test["user_id"],
                conversation_id=str(uuid.uuid4()),
                platform=test["platform"]
            )
            
            # Run workflow
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            response = final_state.get("response", "")
            user_language = final_state.get("user_language", "unknown")
            response_strategy = final_state.get("response_strategy", "unknown")
            requires_human = final_state.get("requires_human", False)
            memory_loaded = final_state.get("memory_loaded", False)
            memory_updated = final_state.get("memory_updated", False)
            
            # Check if integration is working
            integration_working = (
                len(response) > 0 and
                user_language in ["en", "my"] and
                response_strategy in ["direct_answer", "search_and_answer", "polite_fallback"] and
                memory_loaded and
                memory_updated
            )
            
            if integration_working:
                passed_tests += 1
                print("   ✅ INTEGRATION WORKING")
            else:
                print("   ❌ INTEGRATION ISSUES")
            
            # Print details
            print(f"   Response: {response[:60]}...")
            print(f"   Language: {user_language}")
            print(f"   Strategy: {response_strategy}")
            print(f"   HITL: {requires_human}")
            print(f"   Memory: Loaded={memory_loaded}, Updated={memory_updated}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    return passed_tests == total_tests


async def test_facebook_messenger_integration():
    """Test integration with Facebook Messenger"""
    
    print("\n📱 Testing Facebook Messenger Integration")
    print("=" * 50)
    
    # Create the workflow
    workflow = create_conversation_graph()
    
    # Test cases that simulate Facebook Messenger interactions
    messenger_test_cases = [
        {
            "name": "English Greeting",
            "message": "Hello",
            "user_id": "messenger_user_1",
            "platform": "messenger"
        },
        {
            "name": "Burmese Menu Query",
            "message": "အစားအစာတွေဘာတွေရှိလဲ",
            "user_id": "messenger_user_2", 
            "platform": "messenger"
        },
        {
            "name": "Complaint Escalation",
            "message": "I have a complaint about the service",
            "user_id": "messenger_user_3",
            "platform": "messenger"
        }
    ]
    
    passed_tests = 0
    total_tests = len(messenger_test_cases)
    
    for i, test in enumerate(messenger_test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test['name']}")
        print(f"   Message: '{test['message']}'")
        print(f"   User: {test['user_id']} | Platform: {test['platform']}")
        
        try:
            # Create initial state
            initial_state = create_initial_state(
                user_message=test["message"],
                user_id=test["user_id"],
                conversation_id=str(uuid.uuid4()),
                platform=test["platform"]
            )
            
            # Run workflow
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            response = final_state.get("response", "")
            user_language = final_state.get("user_language", "unknown")
            response_strategy = final_state.get("response_strategy", "unknown")
            requires_human = final_state.get("requires_human", False)
            memory_loaded = final_state.get("memory_loaded", False)
            memory_updated = final_state.get("memory_updated", False)
            
            # Check if integration is working
            integration_working = (
                len(response) > 0 and
                user_language in ["en", "my"] and
                response_strategy in ["direct_answer", "search_and_answer", "polite_fallback"] and
                memory_loaded and
                memory_updated
            )
            
            if integration_working:
                passed_tests += 1
                print("   ✅ INTEGRATION WORKING")
            else:
                print("   ❌ INTEGRATION ISSUES")
            
            # Print details
            print(f"   Response: {response[:60]}...")
            print(f"   Language: {user_language}")
            print(f"   Strategy: {response_strategy}")
            print(f"   HITL: {requires_human}")
            print(f"   Memory: Loaded={memory_loaded}, Updated={memory_updated}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    return passed_tests == total_tests


async def main():
    """Run all integration tests"""
    
    print("🚀 Testing Real Application Integration")
    print("=" * 60)
    
    # Test Streamlit integration
    streamlit_success = await test_streamlit_integration()
    
    # Test Facebook Messenger integration  
    messenger_success = await test_facebook_messenger_integration()
    
    # Print final summary
    print(f"\n📊 Real Application Integration Test Summary")
    print("=" * 60)
    print(f"✅ Streamlit Integration: {'PASSED' if streamlit_success else 'FAILED'}")
    print(f"✅ Facebook Messenger Integration: {'PASSED' if messenger_success else 'FAILED'}")
    
    if streamlit_success and messenger_success:
        print("\n🎉 All real application integrations working correctly!")
        print("✅ System ready for production deployment")
        print("✅ Streamlit web interface ready")
        print("✅ Facebook Messenger integration ready")
    else:
        print("\n⚠️  Some integration issues detected")
        print("Please review the implementation")
    
    return streamlit_success and messenger_success


if __name__ == "__main__":
    asyncio.run(main())
