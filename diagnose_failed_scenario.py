"""
Diagnose Failed Scenario
Quick test to identify which scenario failed and why
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("diagnose_failed_scenario")


async def test_individual_scenarios():
    """Test each scenario individually to identify the failure"""
    
    print("🔍 Diagnosing Failed Scenario")
    print("=" * 50)
    
    workflow = create_simplified_conversation_graph()
    
    # Test each scenario individually
    scenarios = [
        {
            "name": "Complete English Customer Journey",
            "conversation": ["Hello", "What's on your menu?"],
            "expected_languages": ["en", "en"],
            "expected_strategies": ["direct_answer", "search_and_answer"]
        },
        {
            "name": "Complete Burmese Customer Journey", 
            "conversation": ["မင်္ဂလာပါ", "အစားအစာတွေဘာတွေရှိလဲ"],
            "expected_languages": ["my", "my"],
            "expected_strategies": ["direct_answer", "search_and_answer"]
        },
        {
            "name": "HITL Escalation Scenario",
            "conversation": ["Hello", "I have a complaint about the service"],
            "expected_languages": ["en", "en"],
            "expected_strategies": ["direct_answer", "search_and_answer"],
            "expect_hitl": [False, True]
        },
        {
            "name": "Mixed Language Scenario",
            "conversation": ["Hello", "အစားအစာတွေဘာတွေရှိလဲ"],
            "expected_languages": ["en", "my"],
            "expected_strategies": ["direct_answer", "search_and_answer"]
        }
    ]
    
    for scenario_idx, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Testing Scenario {scenario_idx}: {scenario['name']}")
        print("-" * 40)
        
        scenario_passed = True
        conversation_id = str(uuid.uuid4())
        user_id = f"diagnose_user_{scenario_idx}"
        
        for msg_idx, (message, expected_lang, expected_strategy) in enumerate(
            zip(scenario['conversation'], scenario['expected_languages'], scenario['expected_strategies'])
        ):
            print(f"   Message {msg_idx + 1}: '{message}'")
            
            try:
                initial_state = create_simplified_initial_state(
                    user_message=message,
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                
                compiled_workflow = workflow.compile()
                final_state = await compiled_workflow.ainvoke(initial_state)
                
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
                print(f"      Language: {user_language} (expected: {expected_lang}) {'✅' if lang_correct else '❌'}")
                print(f"      Strategy: {response_strategy} (expected: {expected_strategy}) {'✅' if strategy_correct else '❌'}")
                print(f"      HITL: {requires_human}")
                print(f"      Memory: Loaded={memory_loaded}, Updated={memory_updated}")
                print(f"      Response: {response[:50]}...")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                scenario_passed = False
        
        if scenario_passed:
            print(f"   🎉 SCENARIO {scenario_idx} PASSED")
        else:
            print(f"   ❌ SCENARIO {scenario_idx} FAILED")
    
    print(f"\n📊 Diagnosis Complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_individual_scenarios())
