"""
Comprehensive Test for Integrated System with HITL and Conversation Memory
Tests the simplified system with integrated HITL and conversation memory features
"""

import asyncio
import json
import uuid
from datetime import datetime
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_integrated_system")


async def test_integrated_workflow():
    """Test the integrated workflow with HITL and conversation memory"""
    
    print("🧪 Testing Integrated System with HITL and Conversation Memory")
    print("=" * 70)
    
    # Create the integrated workflow
    workflow = create_simplified_conversation_graph()
    
    # Test cases covering different scenarios
    test_cases = [
        {
            "name": "Normal English Greeting",
            "message": "Hello",
            "user_id": "test_user_1",
            "conversation_id": "test_conv_1",
            "expected_strategy": "direct_answer",
            "expected_hitl": False,
            "expected_memory": True
        },
        {
            "name": "Burmese Location Query",
            "message": "ဆိုင်ဘယ်မှာလဲ",
            "user_id": "test_user_2", 
            "conversation_id": "test_conv_2",
            "expected_strategy": "search_and_answer",
            "expected_hitl": False,
            "expected_memory": True
        },
        {
            "name": "Human Assistance Request",
            "message": "I want to speak to a human",
            "user_id": "test_user_3",
            "conversation_id": "test_conv_3", 
            "expected_strategy": "polite_fallback",
            "expected_hitl": True,
            "expected_memory": True
        },
        {
            "name": "Complex Complaint",
            "message": "I have a complaint about the service",
            "user_id": "test_user_4",
            "conversation_id": "test_conv_4",
            "expected_strategy": "polite_fallback", 
            "expected_hitl": True,
            "expected_memory": True
        },
        {
            "name": "Low Confidence Query",
            "message": "xyz123",
            "user_id": "test_user_5",
            "conversation_id": "test_conv_5",
            "expected_strategy": "polite_fallback",
            "expected_hitl": True,
            "expected_memory": True
        },
        {
            "name": "Menu Item Query",
            "message": "What's on your menu?",
            "user_id": "test_user_6",
            "conversation_id": "test_conv_6",
            "expected_strategy": "search_and_answer",
            "expected_hitl": False,
            "expected_memory": True
        },
        {
            "name": "Burmese Menu Query",
            "message": "အစားအစာတွေဘာတွေရှိလဲ",
            "user_id": "test_user_7",
            "conversation_id": "test_conv_7",
            "expected_strategy": "search_and_answer",
            "expected_hitl": False,
            "expected_memory": True
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
        print(f"   Message: {test_case['message']}")
        
        try:
            # Create initial state
            initial_state = create_simplified_initial_state(
                user_message=test_case['message'],
                user_id=test_case['user_id'],
                conversation_id=test_case['conversation_id'],
                platform="test"
            )
            
            # Run workflow
            start_time = datetime.now()
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            end_time = datetime.now()
            
            # Extract results
            response_strategy = final_state.get("response_strategy", "unknown")
            requires_human = final_state.get("requires_human", False)
            human_handling = final_state.get("human_handling", False)
            response = final_state.get("response", "")
            memory_loaded = final_state.get("memory_loaded", False)
            memory_updated = final_state.get("memory_updated", False)
            response_generated = final_state.get("response_generated", False)
            user_language = final_state.get("user_language", "unknown")
            analysis_confidence = final_state.get("analysis_confidence", 0.0)
            data_found = final_state.get("data_found", False)
            search_performed = final_state.get("search_performed", False)
            escalation_reason = final_state.get("escalation_reason", "")
            
            # Calculate response time
            response_time = (end_time - start_time).total_seconds()
            
            # Validate results
            strategy_correct = response_strategy == test_case['expected_strategy']
            hitl_correct = requires_human == test_case['expected_hitl']
            response_valid = len(response) > 0
            memory_valid = memory_loaded and memory_updated
            
            # Determine test result
            test_passed = strategy_correct and hitl_correct and response_valid and memory_valid
            
            if test_passed:
                passed_tests += 1
                print("   ✅ PASSED")
            else:
                print("   ❌ FAILED")
            
            # Print detailed results
            print(f"   Strategy: {response_strategy} (expected: {test_case['expected_strategy']})")
            print(f"   Language: {user_language}")
            print(f"   Confidence: {analysis_confidence:.2f}")
            print(f"   HITL: {requires_human} (expected: {test_case['expected_hitl']})")
            print(f"   Human Handling: {human_handling}")
            print(f"   Data Found: {data_found}")
            print(f"   Search Performed: {search_performed}")
            print(f"   Response Generated: {response_generated}")
            print(f"   Memory: Loaded={memory_loaded}, Updated={memory_updated}")
            print(f"   Response Time: {response_time:.2f}s")
            print(f"   Response: {response[:100]}...")
            
            if escalation_reason:
                print(f"   Escalation Reason: {escalation_reason}")
            
            if not test_passed:
                print(f"   Issues:")
                if not strategy_correct:
                    print(f"     - Strategy mismatch")
                if not hitl_correct:
                    print(f"     - HITL decision mismatch")
                if not response_valid:
                    print(f"     - No response generated")
                if not memory_valid:
                    print(f"     - Memory not properly loaded/updated")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            logger.error("test_case_failed", 
                        test_case=test_case['name'],
                        error=str(e))
    
    # Print summary
    print(f"\n📊 Test Summary")
    print("=" * 70)
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Integrated system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed_tests == total_tests


async def test_hitl_escalation():
    """Test HITL escalation scenarios specifically"""
    
    print("\n🔍 Testing HITL Escalation Scenarios")
    print("=" * 50)
    
    workflow = create_simplified_conversation_graph()
    
    escalation_triggers = [
        "I need to speak to a manager",
        "This is a complaint about your service",
        "I want a refund",
        "I have a food allergy",
        "Can I make a reservation for a party?",
        "I need help with my bill",
        "Your service is terrible",
        "I want to cancel my order",
        "There's a problem with my food",
        "I need to speak to someone in charge"
    ]
    
    escalation_count = 0
    total_triggers = len(escalation_triggers)
    
    for trigger in escalation_triggers:
        try:
            initial_state = create_simplified_initial_state(
                user_message=trigger,
                user_id="hitl_test_user",
                conversation_id=f"hitl_test_{uuid.uuid4()}",
                platform="test"
            )
            
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            requires_human = final_state.get("requires_human", False)
            escalation_reason = final_state.get("escalation_reason", "")
            
            if requires_human:
                escalation_count += 1
                print(f"✅ '{trigger}' -> ESCALATED ({escalation_reason})")
            else:
                print(f"❌ '{trigger}' -> NOT ESCALATED")
                
        except Exception as e:
            print(f"❌ '{trigger}' -> ERROR: {str(e)}")
    
    escalation_rate = (escalation_count / total_triggers) * 100
    print(f"\nEscalation Rate: {escalation_rate:.1f}% ({escalation_count}/{total_triggers})")
    
    return escalation_rate >= 80  # Expect at least 80% escalation rate


async def test_conversation_memory():
    """Test conversation memory functionality"""
    
    print("\n💾 Testing Conversation Memory Integration")
    print("=" * 50)
    
    workflow = create_simplified_conversation_graph()
    
    # Test conversation continuity
    conversation_id = f"memory_test_{uuid.uuid4()}"
    user_id = "memory_test_user"
    
    test_messages = [
        "Hello",
        "What's on your menu?",
        "How much is the coffee?",
        "Thank you"
    ]
    
    memory_working = True
    
    for i, message in enumerate(test_messages, 1):
        try:
            initial_state = create_simplified_initial_state(
                user_message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                platform="test"
            )
            
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            memory_loaded = final_state.get("memory_loaded", False)
            memory_updated = final_state.get("memory_updated", False)
            conversation_history = final_state.get("conversation_history", [])
            
            print(f"Message {i}: '{message}'")
            print(f"  Memory Loaded: {memory_loaded}")
            print(f"  Memory Updated: {memory_updated}")
            print(f"  History Length: {len(conversation_history)}")
            
            if not (memory_loaded and memory_updated):
                memory_working = False
                print(f"  ❌ Memory not working properly")
            else:
                print(f"  ✅ Memory working correctly")
                
        except Exception as e:
            print(f"Message {i}: '{message}' -> ERROR: {str(e)}")
            memory_working = False
    
    if memory_working:
        print(f"\n✅ Conversation memory is working correctly")
    else:
        print(f"\n❌ Conversation memory has issues")
    
    return memory_working


async def test_language_detection():
    """Test language detection and response generation"""
    
    print("\n🌐 Testing Language Detection and Response")
    print("=" * 50)
    
    workflow = create_simplified_conversation_graph()
    
    language_tests = [
        {"message": "Hello", "expected": "en"},
        {"message": "ဆိုင်ဘယ်မှာလဲ", "expected": "my"},
        {"message": "Thank you", "expected": "en"},
        {"message": "ကျေးဇူးတင်ပါတယ်", "expected": "my"},
        {"message": "What's the menu?", "expected": "en"},
        {"message": "အစားအစာတွေဘာတွေရှိလဲ", "expected": "my"}
    ]
    
    language_correct = 0
    total_language_tests = len(language_tests)
    
    for test in language_tests:
        try:
            initial_state = create_simplified_initial_state(
                user_message=test["message"],
                user_id="lang_test_user",
                conversation_id=f"lang_test_{uuid.uuid4()}",
                platform="test"
            )
            
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            detected_language = final_state.get("user_language", "unknown")
            response = final_state.get("response", "")
            
            if detected_language == test["expected"]:
                language_correct += 1
                print(f"✅ '{test['message']}' -> {detected_language} (expected: {test['expected']})")
            else:
                print(f"❌ '{test['message']}' -> {detected_language} (expected: {test['expected']})")
            
            print(f"  Response: {response[:50]}...")
            
        except Exception as e:
            print(f"❌ '{test['message']}' -> ERROR: {str(e)}")
    
    language_accuracy = (language_correct / total_language_tests) * 100
    print(f"\nLanguage Detection Accuracy: {language_accuracy:.1f}% ({language_correct}/{total_language_tests})")
    
    return language_accuracy >= 80  # Expect at least 80% accuracy


if __name__ == "__main__":
    async def main():
        print("🚀 Starting Comprehensive Integration Tests")
        print("=" * 70)
        
        # Test integrated workflow
        print("\n1️⃣ Testing Integrated Workflow")
        workflow_success = await test_integrated_workflow()
        
        # Test HITL escalation
        print("\n2️⃣ Testing HITL Escalation")
        hitl_success = await test_hitl_escalation()
        
        # Test conversation memory
        print("\n3️⃣ Testing Conversation Memory")
        memory_success = await test_conversation_memory()
        
        # Test language detection
        print("\n4️⃣ Testing Language Detection")
        language_success = await test_language_detection()
        
        # Overall result
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        print(f"✅ Integrated Workflow: {'PASSED' if workflow_success else 'FAILED'}")
        print(f"✅ HITL Escalation: {'PASSED' if hitl_success else 'FAILED'}")
        print(f"✅ Conversation Memory: {'PASSED' if memory_success else 'FAILED'}")
        print(f"✅ Language Detection: {'PASSED' if language_success else 'FAILED'}")
        
        all_passed = workflow_success and hitl_success and memory_success and language_success
        
        if all_passed:
            print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
            print("✅ HITL and Conversation Memory successfully integrated")
            print("✅ Simplified RAG system working correctly")
            print("✅ Language detection and response generation working")
            print("✅ Conversation memory persistence working")
        else:
            print("\n⚠️  Some comprehensive tests failed")
            print("Please review the implementation")
        
        return all_passed
    
    asyncio.run(main())
