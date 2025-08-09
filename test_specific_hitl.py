"""
Test Specific HITL Messages
Test to verify that the HITL system works for the user's specific messages
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_specific_hitl")


async def test_specific_hitl():
    """Test that the HITL system works for the user's specific messages"""
    
    print("🔧 Testing Specific HITL Messages")
    print("=" * 50)
    
    # Create the workflow
    workflow = create_simplified_conversation_graph()
    
    # Test the exact messages from the user
    conversation_id = str(uuid.uuid4())
    user_id = "test_specific_hitl_user"
    
    test_messages = [
        "မွေးနေ့ပွဲလုပ်လို့ ရလား",  # Should NOT escalate - general question
        "အဲဒီကိစ္စအတွက် တာဝန်ခံ တစ်ယောက်ယောက်နဲ့ ပြောလို့ရလား",  # Should escalate - human request
        "တာဝန်ရှိသူ နဲံ ပြောလို့ မရဘူးလား"  # Should escalate - human request
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
            
            # Validate decisions
            if i == 1:  # Birthday party question
                if not requires_human:
                    print("   ✅ LLM correctly did NOT escalate birthday party question")
                else:
                    print("   ❌ LLM should NOT have escalated birthday party question")
            
            elif i == 2:  # Human assistance request
                if requires_human:
                    print("   ✅ LLM correctly escalated human assistance request")
                else:
                    print("   ❌ LLM should have escalated human assistance request")
            
            elif i == 3:  # Human assistance request
                if requires_human:
                    print("   ✅ LLM correctly escalated human assistance request")
                else:
                    print("   ❌ LLM should have escalated human assistance request")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n📊 Specific HITL Test Complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_specific_hitl())
