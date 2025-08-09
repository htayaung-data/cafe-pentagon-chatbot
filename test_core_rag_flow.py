"""
Test Core RAG Flow
Focused test to verify the simplified 3-step RAG system is working correctly
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_core_rag_flow")


async def test_core_rag_flow():
    """Test the core RAG flow (Analysis → Search → Response)"""
    
    print("🔍 Testing Core RAG Flow (Simplified 3-Step System)")
    print("=" * 60)
    
    # Create the workflow
    workflow = create_simplified_conversation_graph()
    
    # Test cases for different RAG scenarios
    rag_test_cases = [
        {
            "name": "Menu Query (English)",
            "message": "What's on your menu?",
            "expected_strategy": "search_and_answer",
            "expected_namespace": "menu",
            "should_find_data": True
        },
        {
            "name": "Menu Query (Burmese)",
            "message": "အစားအစာတွေဘာတွေရှိလဲ",
            "expected_strategy": "search_and_answer", 
            "expected_namespace": "menu",
            "should_find_data": True
        },
        {
            "name": "Location Query (English)",
            "message": "Where is your restaurant located?",
            "expected_strategy": "search_and_answer",
            "expected_namespace": "faq",
            "should_find_data": True
        },
        {
            "name": "Location Query (Burmese)",
            "message": "ဆိုင်ဘယ်မှာလဲ",
            "expected_strategy": "search_and_answer",
            "expected_namespace": "faq", 
            "should_find_data": True
        },
        {
            "name": "Simple Greeting (English)",
            "message": "Hello",
            "expected_strategy": "direct_answer",
            "expected_namespace": None,
            "should_find_data": False
        },
        {
            "name": "Simple Greeting (Burmese)",
            "message": "မင်္ဂလာပါ",
            "expected_strategy": "direct_answer",
            "expected_namespace": None,
            "should_find_data": False
        }
    ]
    
    passed_tests = 0
    total_tests = len(rag_test_cases)
    
    for i, test in enumerate(rag_test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test['name']}")
        print(f"   Message: '{test['message']}'")
        print(f"   Expected: {test['expected_strategy']} | {test['expected_namespace']}")
        
        try:
            # Create initial state with proper UUID
            initial_state = create_simplified_initial_state(
                user_message=test["message"],
                user_id="rag_test_user",
                conversation_id=str(uuid.uuid4()),
                platform="test"
            )
            
            # Run workflow
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            response_strategy = final_state.get("response_strategy", "unknown")
            search_namespace = final_state.get("search_namespace_used", "unknown")
            data_found = final_state.get("data_found", False)
            search_performed = final_state.get("search_performed", False)
            response = final_state.get("response", "")
            analysis_confidence = final_state.get("analysis_confidence", 0.0)
            user_language = final_state.get("user_language", "unknown")
            
            # Check strategy
            strategy_correct = response_strategy == test["expected_strategy"]
            
            # Check namespace (only for search queries)
            namespace_correct = True
            if test["expected_namespace"]:
                namespace_correct = search_namespace == test["expected_namespace"]
            
            # Check data found
            data_correct = data_found == test["should_find_data"]
            
            # Check response generation
            response_valid = len(response) > 0
            
            # Determine if test passed
            test_passed = strategy_correct and namespace_correct and data_correct and response_valid
            
            if test_passed:
                passed_tests += 1
                print("   ✅ PASSED")
            else:
                print("   ❌ FAILED")
            
            # Print details
            print(f"   Strategy: {response_strategy} (expected: {test['expected_strategy']})")
            print(f"   Namespace: {search_namespace} (expected: {test['expected_namespace']})")
            print(f"   Data Found: {data_found} (expected: {test['should_find_data']})")
            print(f"   Search Performed: {search_performed}")
            print(f"   Language: {user_language}")
            print(f"   Confidence: {analysis_confidence:.2f}")
            print(f"   Response: {response[:80]}...")
            
            if not test_passed:
                print("   Issues:")
                if not strategy_correct:
                    print("     - Strategy mismatch")
                if not namespace_correct:
                    print("     - Namespace mismatch")
                if not data_correct:
                    print("     - Data found mismatch")
                if not response_valid:
                    print("     - No response generated")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    # Print summary
    print(f"\n📊 Core RAG Flow Test Summary")
    print("=" * 60)
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 Core RAG flow is working correctly!")
        print("✅ Analysis → Search → Response pipeline functioning")
        print("✅ Multi-language support working")
        print("✅ Data retrieval and response generation working")
    else:
        print("⚠️  Core RAG flow has some issues")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    asyncio.run(test_core_rag_flow())
