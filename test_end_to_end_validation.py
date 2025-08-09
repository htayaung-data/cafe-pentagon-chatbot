"""
End-to-End System Validation
Comprehensive test to validate the entire integrated system works correctly
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_end_to_end_validation")


async def test_end_to_end_scenarios():
    """Test complete end-to-end scenarios"""
    
    print("🚀 End-to-End System Validation")
    print("=" * 60)
    
    # Create the workflow
    workflow = create_simplified_conversation_graph()
    
    # Comprehensive test scenarios
    e2e_scenarios = [
        {
            "name": "Complete English Customer Journey",
            "conversation": [
                "Hello",
                "What's on your menu?",
                "Do you have vegetarian options?",
                "What are your opening hours?",
                "Thank you, goodbye"
            ],
            "expected_languages": ["en", "en", "en", "en", "en"],
            "expected_strategies": ["direct_answer", "search_and_answer", "search_and_answer", "search_and_answer", "direct_answer"]
        },
        {
            "name": "Complete Burmese Customer Journey", 
            "conversation": [
                "မင်္ဂလာပါ",
                "အစားအစာတွေဘာတွေရှိလဲ",
                "ဆိုင်ဘယ်မှာလဲ",
                "အချိန်ဘယ်လောက်ဖွင့်လဲ",
                "ကျေးဇူးတင်ပါတယ်"
            ],
            "expected_languages": ["my", "my", "my", "my", "my"],
            "expected_strategies": ["direct_answer", "search_and_answer", "search_and_answer", "search_and_answer", "direct_answer"]
        },
        {
            "name": "HITL Escalation Scenario",
            "conversation": [
                "Hello",
                "I have a complaint about the service",
                "I need to speak to a manager immediately"
            ],
            "expected_languages": ["en", "en", "en"],
            "expected_strategies": ["direct_answer", "search_and_answer", "polite_fallback"],
            "expect_hitl": [False, True, True]
        },
        {
            "name": "Mixed Language Scenario",
            "conversation": [
                "Hello",
                "အစားအစာတွေဘာတွေရှိလဲ",
                "What are your prices?",
                "ကျေးဇူးတင်ပါတယ်"
            ],
            "expected_languages": ["en", "my", "en", "my"],
            "expected_strategies": ["direct_answer", "search_and_answer", "search_and_answer", "direct_answer"]
        }
    ]
    
    total_scenarios = len(e2e_scenarios)
    passed_scenarios = 0
    
    for scenario_idx, scenario in enumerate(e2e_scenarios, 1):
        print(f"\n📋 Scenario {scenario_idx}/{total_scenarios}: {scenario['name']}")
        print("-" * 50)
        
        conversation_id = str(uuid.uuid4())
        user_id = f"e2e_user_{scenario_idx}"
        
        scenario_passed = True
        conversation_history = []
        
        for msg_idx, (message, expected_lang, expected_strategy) in enumerate(
            zip(scenario['conversation'], scenario['expected_languages'], scenario['expected_strategies'])
        ):
            print(f"   Message {msg_idx + 1}: '{message}'")
            
            try:
                # Create initial state
                initial_state = create_simplified_initial_state(
                    user_message=message,
                    user_id=user_id,
                    conversation_id=conversation_id
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
                
                # Validate results
                lang_correct = user_language == expected_lang
                strategy_correct = response_strategy == expected_strategy
                response_valid = len(response) > 0
                memory_working = memory_loaded and memory_updated
                
                # Check HITL if expected
                hitl_correct = True
                if "expect_hitl" in scenario:
                    expected_hitl = scenario["expect_hitl"][msg_idx]
                    hitl_correct = requires_human == expected_hitl
                
                # Update conversation history
                conversation_history.append({
                    "role": "user",
                    "content": message
                })
                conversation_history.append({
                    "role": "assistant", 
                    "content": response
                })
                
                # Check if this message passed
                message_passed = (
                    lang_correct and 
                    strategy_correct and 
                    response_valid and 
                    memory_working and
                    hitl_correct
                )
                
                if message_passed:
                    print(f"   ✅ PASSED")
                else:
                    print(f"   ❌ FAILED")
                    scenario_passed = False
                
                # Print details
                print(f"      Language: {user_language} (expected: {expected_lang})")
                print(f"      Strategy: {response_strategy} (expected: {expected_strategy})")
                print(f"      HITL: {requires_human}")
                print(f"      Memory: Loaded={memory_loaded}, Updated={memory_updated}")
                print(f"      Response: {response[:50]}...")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                scenario_passed = False
        
        if scenario_passed:
            passed_scenarios += 1
            print(f"   🎉 SCENARIO PASSED")
        else:
            print(f"   ❌ SCENARIO FAILED")
    
    return passed_scenarios, total_scenarios


async def test_system_performance():
    """Test system performance and reliability"""
    
    print("\n⚡ Testing System Performance")
    print("=" * 50)
    
    workflow = create_simplified_conversation_graph()
    
    # Performance test cases
    performance_tests = [
        "Hello",
        "What's on your menu?",
        "ဆိုင်ဘယ်မှာလဲ",
        "I need help",
        "Thank you"
    ]
    
    total_tests = len(performance_tests)
    successful_tests = 0
    total_response_time = 0
    
    for i, message in enumerate(performance_tests, 1):
        print(f"   Test {i}/{total_tests}: '{message}'")
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            initial_state = create_simplified_initial_state(
                user_message=message,
                user_id=f"perf_user_{i}",
                conversation_id=str(uuid.uuid4())
            )
            
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            total_response_time += response_time
            
            response = final_state.get("response", "")
            if len(response) > 0:
                successful_tests += 1
                print(f"   ✅ Success ({response_time:.2f}s)")
            else:
                print(f"   ❌ No response ({response_time:.2f}s)")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    avg_response_time = total_response_time / total_tests if total_tests > 0 else 0
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n   📊 Performance Results:")
    print(f"      Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    print(f"      Average Response Time: {avg_response_time:.2f}s")
    
    return success_rate >= 80 and avg_response_time <= 10.0


async def main():
    """Run complete end-to-end validation"""
    
    print("🎯 Complete End-to-End System Validation")
    print("=" * 70)
    
    # Test end-to-end scenarios
    passed_scenarios, total_scenarios = await test_end_to_end_scenarios()
    
    # Test system performance
    performance_passed = await test_system_performance()
    
    # Print final summary
    print(f"\n📊 End-to-End Validation Summary")
    print("=" * 70)
    print(f"✅ End-to-End Scenarios: {passed_scenarios}/{total_scenarios} passed")
    print(f"✅ System Performance: {'PASSED' if performance_passed else 'FAILED'}")
    
    overall_success = (passed_scenarios == total_scenarios) and performance_passed
    
    if overall_success:
        print("\n🎉 COMPLETE SYSTEM VALIDATION PASSED!")
        print("✅ All components working correctly")
        print("✅ HITL integration functional")
        print("✅ Conversation memory operational")
        print("✅ Language detection accurate")
        print("✅ RAG system performing well")
        print("✅ System ready for production")
    else:
        print("\n⚠️  Some validation issues detected")
        print("Please review the implementation")
    
    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
