#!/usr/bin/env python3
"""
Test script to verify the improvements to the Cafe Pentagon Chatbot
Tests both Burmese and English queries to ensure consistent responses
"""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.graph.state_graph import create_conversation_graph, create_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_improvements")

async def test_query(user_message: str, user_id: str = "test_user", platform: str = "test"):
    """Test a single query through the LangGraph workflow"""
    try:
        # Create conversation graph
        conversation_graph = create_conversation_graph()
        
        # Create initial state
        conversation_id = f"test_{user_id}_{int(asyncio.get_event_loop().time())}"
        initial_state = create_initial_state(
            user_message=user_message,
            user_id=user_id,
            conversation_id=conversation_id,
            platform=platform
        )
        
        # Execute workflow
        compiled_workflow = conversation_graph.compile()
        final_state = await compiled_workflow.ainvoke(initial_state)
        
        # Extract results
        response = final_state.get("response", "")
        detected_language = final_state.get("detected_language", "")
        primary_intent = final_state.get("primary_intent", "")
        intent_confidence = final_state.get("intent_confidence", 0.0)
        action_type = final_state.get("action_type", "")
        rag_enabled = final_state.get("rag_enabled", True)
        rag_results_count = len(final_state.get("rag_results", []))
        relevance_score = final_state.get("relevance_score", 0.0)
        
        return {
            "user_message": user_message,
            "response": response,
            "detected_language": detected_language,
            "primary_intent": primary_intent,
            "intent_confidence": intent_confidence,
            "action_type": action_type,
            "rag_enabled": rag_enabled,
            "rag_results_count": rag_results_count,
            "relevance_score": relevance_score
        }
        
    except Exception as e:
        logger.error("test_query_failed", error=str(e), user_message=user_message)
        return {
            "user_message": user_message,
            "response": f"Error: {str(e)}",
            "detected_language": "error",
            "primary_intent": "error",
            "intent_confidence": 0.0,
            "action_type": "error",
            "rag_enabled": False,
            "rag_results_count": 0,
            "relevance_score": 0.0
        }

async def run_tests():
    """Run comprehensive tests"""
    print("🧪 Testing Cafe Pentagon Chatbot Improvements")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        # Burmese queries that should work better now
        "ဆိုင်လိပ်စာ ဘယ်မှာ ရှိလဲ",
        "ဆိုင်ဘယ်အချိန် ပိတ်လဲ", 
        "ဘာ အစားအသောက်တွေ ရလဲ",
        "မင်္ဂလာပါ",
        "ဖုန်းနံပါတ် ဘယ်လိုလဲ",
        
        # English queries for comparison
        "What is the location of the cafe?",
        "What are the opening hours?",
        "What food do you have?",
        "Hello",
        "What is the phone number?",
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        result = await test_query(query)
        results.append(result)
        
        print(f"Response: {result['response'][:200]}...")
        print(f"Language: {result['detected_language']}")
        print(f"Intent: {result['primary_intent']} (confidence: {result['intent_confidence']:.2f})")
        print(f"Action: {result['action_type']}")
        print(f"RAG Results: {result['rag_results_count']}")
        print(f"Relevance Score: {result['relevance_score']:.2f}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    burmese_tests = results[:5]
    english_tests = results[5:]
    
    print(f"Burmese Tests: {len(burmese_tests)}")
    print(f"English Tests: {len(english_tests)}")
    
    # Check for improvements
    burmese_with_rag = sum(1 for r in burmese_tests if r['rag_results_count'] > 0)
    english_with_rag = sum(1 for r in english_tests if r['rag_results_count'] > 0)
    
    print(f"Burmese queries with RAG results: {burmese_with_rag}/{len(burmese_tests)}")
    print(f"English queries with RAG results: {english_with_rag}/{len(english_tests)}")
    
    # Check response quality
    burmese_responses = [r['response'] for r in burmese_tests if 'error' not in r['response'].lower()]
    english_responses = [r['response'] for r in english_tests if 'error' not in r['response'].lower()]
    
    print(f"Successful Burmese responses: {len(burmese_responses)}/{len(burmese_tests)}")
    print(f"Successful English responses: {len(english_responses)}/{len(english_tests)}")
    
    # Check for location and hours queries specifically
    location_queries = [r for r in results if 'လိပ်စာ' in r['user_message'] or 'location' in r['user_message'].lower()]
    hours_queries = [r for r in results if 'အချိန်' in r['user_message'] or 'hours' in r['user_message'].lower()]
    
    print(f"\n📍 Location queries with RAG results: {sum(1 for r in location_queries if r['rag_results_count'] > 0)}/{len(location_queries)}")
    print(f"🕐 Hours queries with RAG results: {sum(1 for r in hours_queries if r['rag_results_count'] > 0)}/{len(hours_queries)}")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_tests())
