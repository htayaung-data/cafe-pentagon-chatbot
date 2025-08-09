"""
Integration Test for Simplified System
Tests both Streamlit and Facebook Messenger integrations
"""

import asyncio
import json
from datetime import datetime
from src.graph.state_graph import create_conversation_graph, create_initial_state
from src.utils.logger import get_logger

logger = get_logger("integration_test")


async def test_streamlit_integration():
    """Test Streamlit integration with simplified system"""
    print("🧪 Testing Streamlit Integration")
    print("=" * 50)
    
    try:
        # Create workflow
        workflow = create_conversation_graph()
        compiled_workflow = workflow.compile()
        
        # Test cases
        test_cases = [
            {
                "name": "English Greeting",
                "message": "Hello",
                "expected_language": "en",
                "expected_strategy": "direct_answer"
            },
            {
                "name": "Burmese Menu Query",
                "message": "ဘာတွေစားလို့ရလဲ",
                "expected_language": "my",
                "expected_strategy": "search_and_answer"
            },
            {
                "name": "English Location Query",
                "message": "Where are you located?",
                "expected_language": "en",
                "expected_strategy": "search_and_answer"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            print(f"   Message: {test_case['message']}")
            
            # Create initial state
            initial_state = create_initial_state(
                user_message=test_case["message"],
                user_id=f"test_user_{i}",
                conversation_id=f"test_conv_{i}",
                platform="streamlit"
            )
            
            # Execute workflow
            start_time = datetime.now()
            final_state = await compiled_workflow.ainvoke(initial_state)
            end_time = datetime.now()
            
            # Extract results
            response = final_state.get("response", "")
            user_language = final_state.get("user_language", "unknown")
            response_strategy = final_state.get("response_strategy", "unknown")
            data_found = final_state.get("data_found", False)
            response_quality = final_state.get("response_quality", "unknown")
            response_time = (end_time - start_time).total_seconds()
            
            # Validate results
            success = True
            validation_notes = []
            
            if user_language != test_case["expected_language"]:
                success = False
                validation_notes.append(f"Language mismatch: expected {test_case['expected_language']}, got {user_language}")
            
            if response_strategy != test_case["expected_strategy"]:
                success = False
                validation_notes.append(f"Strategy mismatch: expected {test_case['expected_strategy']}, got {response_strategy}")
            
            if not response:
                success = False
                validation_notes.append("No response generated")
            
            # Print results
            if success:
                print(f"   ✅ PASSED")
                print(f"   Language: {user_language}")
                print(f"   Strategy: {response_strategy}")
                print(f"   Data Found: {data_found}")
                print(f"   Quality: {response_quality}")
                print(f"   Response Time: {response_time:.2f}s")
                print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            else:
                print(f"   ❌ FAILED")
                for note in validation_notes:
                    print(f"   - {note}")
                print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        print(f"\n✅ Streamlit Integration Test Completed")
        
    except Exception as e:
        print(f"❌ Streamlit Integration Test Failed: {str(e)}")


async def test_facebook_integration():
    """Test Facebook Messenger integration with simplified system"""
    print("\n🧪 Testing Facebook Messenger Integration")
    print("=" * 50)
    
    try:
        # Create workflow
        workflow = create_conversation_graph()
        compiled_workflow = workflow.compile()
        
        # Test cases
        test_cases = [
            {
                "name": "Burmese Greeting",
                "message": "မင်္ဂလာ",
                "expected_language": "my",
                "expected_strategy": "direct_answer"
            },
            {
                "name": "English Menu Query",
                "message": "What's on the menu?",
                "expected_language": "en",
                "expected_strategy": "search_and_answer"
            },
            {
                "name": "Burmese Location Query",
                "message": "ဆိုင်ဘယ်မှာလဲ",
                "expected_language": "my",
                "expected_strategy": "search_and_answer"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            print(f"   Message: {test_case['message']}")
            
            # Create initial state
            initial_state = create_initial_state(
                user_message=test_case["message"],
                user_id=f"fb_test_user_{i}",
                conversation_id=f"fb_test_conv_{i}",
                platform="facebook"
            )
            
            # Add Facebook-specific metadata
            initial_state["metadata"] = {
                "message_type": "text",
                "platform": "facebook",
                "facebook_profile": {"id": f"fb_test_user_{i}"}
            }
            
            # Execute workflow
            start_time = datetime.now()
            final_state = await compiled_workflow.ainvoke(initial_state)
            end_time = datetime.now()
            
            # Extract results
            response = final_state.get("response", "")
            user_language = final_state.get("user_language", "unknown")
            response_strategy = final_state.get("response_strategy", "unknown")
            data_found = final_state.get("data_found", False)
            response_quality = final_state.get("response_quality", "unknown")
            response_time = (end_time - start_time).total_seconds()
            
            # Validate results
            success = True
            validation_notes = []
            
            if user_language != test_case["expected_language"]:
                success = False
                validation_notes.append(f"Language mismatch: expected {test_case['expected_language']}, got {user_language}")
            
            if response_strategy != test_case["expected_strategy"]:
                success = False
                validation_notes.append(f"Strategy mismatch: expected {test_case['expected_strategy']}, got {response_strategy}")
            
            if not response:
                success = False
                validation_notes.append("No response generated")
            
            # Print results
            if success:
                print(f"   ✅ PASSED")
                print(f"   Language: {user_language}")
                print(f"   Strategy: {response_strategy}")
                print(f"   Data Found: {data_found}")
                print(f"   Quality: {response_quality}")
                print(f"   Response Time: {response_time:.2f}s")
                print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            else:
                print(f"   ❌ FAILED")
                for note in validation_notes:
                    print(f"   - {note}")
                print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        print(f"\n✅ Facebook Messenger Integration Test Completed")
        
    except Exception as e:
        print(f"❌ Facebook Messenger Integration Test Failed: {str(e)}")


async def test_consistency():
    """Test consistency between platforms"""
    print("\n🧪 Testing Platform Consistency")
    print("=" * 50)
    
    try:
        workflow = create_conversation_graph()
        compiled_workflow = workflow.compile()
        
        # Test the same message on both platforms
        test_message = "What's on the menu?"
        
        print(f"Testing message: '{test_message}'")
        
        # Streamlit test
        streamlit_state = create_initial_state(
            user_message=test_message,
            user_id="consistency_test_user",
            conversation_id="consistency_test_conv_streamlit",
            platform="streamlit"
        )
        
        streamlit_final = await compiled_workflow.ainvoke(streamlit_state)
        
        # Facebook test
        facebook_state = create_initial_state(
            user_message=test_message,
            user_id="consistency_test_user",
            conversation_id="consistency_test_conv_facebook",
            platform="facebook"
        )
        
        facebook_final = await compiled_workflow.ainvoke(facebook_state)
        
        # Compare results
        streamlit_language = streamlit_final.get("user_language")
        facebook_language = facebook_final.get("user_language")
        streamlit_strategy = streamlit_final.get("response_strategy")
        facebook_strategy = facebook_final.get("response_strategy")
        streamlit_data_found = streamlit_final.get("data_found")
        facebook_data_found = facebook_final.get("data_found")
        
        print(f"   Streamlit - Language: {streamlit_language}, Strategy: {streamlit_strategy}, Data Found: {streamlit_data_found}")
        print(f"   Facebook  - Language: {facebook_language}, Strategy: {facebook_strategy}, Data Found: {facebook_data_found}")
        
        # Check consistency
        language_consistent = streamlit_language == facebook_language
        strategy_consistent = streamlit_strategy == facebook_strategy
        data_consistent = streamlit_data_found == facebook_data_found
        
        if language_consistent and strategy_consistent and data_consistent:
            print(f"   ✅ Platform Consistency: PASSED")
        else:
            print(f"   ❌ Platform Consistency: FAILED")
            if not language_consistent:
                print(f"   - Language inconsistency: {streamlit_language} vs {facebook_language}")
            if not strategy_consistent:
                print(f"   - Strategy inconsistency: {streamlit_strategy} vs {facebook_strategy}")
            if not data_consistent:
                print(f"   - Data found inconsistency: {streamlit_data_found} vs {facebook_data_found}")
        
    except Exception as e:
        print(f"❌ Consistency Test Failed: {str(e)}")


async def main():
    """Run all integration tests"""
    print("🚀 Simplified System Integration Tests")
    print("Testing both Streamlit and Facebook Messenger integrations")
    print("=" * 60)
    
    # Run tests
    await test_streamlit_integration()
    await test_facebook_integration()
    await test_consistency()
    
    print("\n🎉 All Integration Tests Completed!")
    print("The simplified system is ready for production use.")


if __name__ == "__main__":
    asyncio.run(main())
