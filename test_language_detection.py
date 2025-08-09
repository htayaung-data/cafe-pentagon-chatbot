"""
Test Language Detection and Response Generation
Focused test to verify language detection and response generation is working correctly
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_language_detection")


async def test_language_detection():
    """Test language detection and response generation"""
    
    print("🌐 Testing Language Detection and Response Generation")
    print("=" * 60)
    
    # Create the workflow
    workflow = create_simplified_conversation_graph()
    
    # Test cases for different languages and scenarios
    language_tests = [
        {"message": "Hello", "expected_lang": "en", "expected_strategy": "direct_answer"},
        {"message": "ဆိုင်ဘယ်မှာလဲ", "expected_lang": "my", "expected_strategy": "search_and_answer"},
        {"message": "Thank you", "expected_lang": "en", "expected_strategy": "direct_answer"},
        {"message": "ကျေးဇူးတင်ပါတယ်", "expected_lang": "my", "expected_strategy": "direct_answer"},
        {"message": "What's the menu?", "expected_lang": "en", "expected_strategy": "search_and_answer"},
        {"message": "အစားအစာတွေဘာတွေရှိလဲ", "expected_lang": "my", "expected_strategy": "search_and_answer"}
    ]
    
    language_correct = 0
    strategy_correct = 0
    response_generated = 0
    total_tests = len(language_tests)
    
    for i, test in enumerate(language_tests, 1):
        print(f"\n📋 Test {i}/{total_tests}: '{test['message']}'")
        print(f"   Expected: {test['expected_lang']} | {test['expected_strategy']}")
        
        try:
            # Create initial state with proper UUID
            initial_state = create_simplified_initial_state(
                user_message=test["message"],
                user_id="lang_test_user",
                conversation_id=str(uuid.uuid4()),
                platform="test"
            )
            
            # Run workflow
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            detected_language = final_state.get("user_language", "unknown")
            response_strategy = final_state.get("response_strategy", "unknown")
            response = final_state.get("response", "")
            analysis_confidence = final_state.get("analysis_confidence", 0.0)
            data_found = final_state.get("data_found", False)
            search_performed = final_state.get("search_performed", False)
            
            # Check language detection
            lang_correct = detected_language == test["expected_lang"]
            if lang_correct:
                language_correct += 1
                print(f"   ✅ Language: {detected_language} (correct)")
            else:
                print(f"   ❌ Language: {detected_language} (expected: {test['expected_lang']})")
            
            # Check response strategy
            strat_correct = response_strategy == test["expected_strategy"]
            if strat_correct:
                strategy_correct += 1
                print(f"   ✅ Strategy: {response_strategy} (correct)")
            else:
                print(f"   ❌ Strategy: {response_strategy} (expected: {test['expected_strategy']})")
            
            # Check response generation
            if len(response) > 0:
                response_generated += 1
                print(f"   ✅ Response: {response[:50]}...")
            else:
                print(f"   ❌ No response generated")
            
            # Additional details
            print(f"   Confidence: {analysis_confidence:.2f}")
            print(f"   Data Found: {data_found}")
            print(f"   Search Performed: {search_performed}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    # Calculate accuracy
    language_accuracy = (language_correct / total_tests) * 100
    strategy_accuracy = (strategy_correct / total_tests) * 100
    response_accuracy = (response_generated / total_tests) * 100
    
    # Print summary
    print(f"\n📊 Language Detection Test Summary")
    print("=" * 60)
    print(f"Language Detection Accuracy: {language_accuracy:.1f}% ({language_correct}/{total_tests})")
    print(f"Strategy Accuracy: {strategy_accuracy:.1f}% ({strategy_correct}/{total_tests})")
    print(f"Response Generation: {response_accuracy:.1f}% ({response_generated}/{total_tests})")
    
    if language_accuracy >= 80 and strategy_accuracy >= 80 and response_accuracy >= 80:
        print("🎉 Language detection and response generation working correctly!")
        return True
    else:
        print("⚠️  Language detection has some issues")
        return False


if __name__ == "__main__":
    asyncio.run(test_language_detection())
