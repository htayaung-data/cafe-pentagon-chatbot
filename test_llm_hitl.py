"""
Test LLM-Driven HITL
Test to verify that the new LLM-driven HITL system works correctly
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_llm_hitl")


async def test_llm_hitl():
    """Test that the new LLM-driven HITL system works correctly"""
    
    print("🔧 Testing LLM-Driven HITL System")
    print("=" * 50)
    
    # Create the workflow
    workflow = create_simplified_conversation_graph()
    
    # Test various messages to see how LLM handles them
    conversation_id = str(uuid.uuid4())
    user_id = "test_llm_hitl_user"
    
    test_messages = [
        "မွေးနေ့ပွဲ ကိစ္စ ဆိုင်က တာဝန်ရှိသူနဲ့ ပြောချင်ပါတယ်",  # Birthday party - should escalate
        "ဆိုင်လိပ်စာ ကဘယ်မှာလဲ",  # Location question - should NOT escalate
        "I want to speak with a manager about a complaint",  # English complaint - should escalate
        "What's on the menu today?"  # English menu question - should NOT escalate
    ]
    
    conversation_history = []
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📋 Message {i}: '{message}'")
        
        try:
            # Create initial state
            initial_state = create_simplified_initial_state(
                user_message=message,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Add conversation history to state
            initial_state["conversation_history"] = conversation_history
            
            # Run workflow
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            response = final_state.get("response", "")
            user_language = final_state.get("user_language", "unknown")
            requires_human = final_state.get("requires_human", False)
            human_handling = final_state.get("human_handling", False)
            escalation_reason = final_state.get("escalation_reason", "")
            
            # Update conversation history for next iteration
            conversation_history.append({
                "role": "user",
                "content": message
            })
            conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Check results
            print(f"   Language: {user_language}")
            print(f"   Requires Human: {requires_human}")
            print(f"   Human Handling: {human_handling}")
            print(f"   Escalation Reason: {escalation_reason}")
            print(f"   Response: {response[:100]}...")
            
            # Validate LLM-driven decisions
            if i == 1:  # Birthday party request
                if requires_human:
                    print("   ✅ LLM correctly escalated birthday party request")
                else:
                    print("   ❌ LLM should have escalated birthday party request")
            
            elif i == 2:  # Location question
                if not requires_human:
                    print("   ✅ LLM correctly did NOT escalate location question")
                else:
                    print("   ❌ LLM should NOT have escalated location question")
            
            elif i == 3:  # English complaint
                if requires_human:
                    print("   ✅ LLM correctly escalated English complaint")
                else:
                    print("   ❌ LLM should have escalated English complaint")
            
            elif i == 4:  # English menu question
                if not requires_human:
                    print("   ✅ LLM correctly did NOT escalate menu question")
                else:
                    print("   ❌ LLM should NOT have escalated menu question")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n📊 LLM-Driven HITL Test Complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_llm_hitl())
