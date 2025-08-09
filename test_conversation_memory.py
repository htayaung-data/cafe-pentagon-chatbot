"""
Test Conversation Memory Integration
Focused test to verify conversation memory is working correctly
"""

import asyncio
import uuid
from src.graph.simplified_state_graph import create_simplified_conversation_graph, create_simplified_initial_state
from src.utils.logger import get_logger

logger = get_logger("test_conversation_memory")


async def test_conversation_memory():
    """Test conversation memory functionality with proper UUIDs"""
    
    print("💾 Testing Conversation Memory Integration")
    print("=" * 50)
    
    # Create the workflow
    workflow = create_simplified_conversation_graph()
    
    # Test conversation continuity with proper UUID
    conversation_id = str(uuid.uuid4())  # Use proper UUID format
    user_id = "memory_test_user"
    
    test_messages = [
        "Hello",
        "What's on your menu?",
        "How much is the coffee?",
        "Thank you"
    ]
    
    memory_working = True
    total_messages = len(test_messages)
    
    print(f"Testing conversation: {conversation_id}")
    print(f"User: {user_id}")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Message {i}/{total_messages}: '{message}'")
        
        try:
            # Create initial state with proper UUID
            initial_state = create_simplified_initial_state(
                user_message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                platform="test"
            )
            
            # Run workflow
            compiled_workflow = workflow.compile()
            final_state = await compiled_workflow.ainvoke(initial_state)
            
            # Check memory results
            memory_loaded = final_state.get("memory_loaded", False)
            memory_updated = final_state.get("memory_updated", False)
            conversation_history = final_state.get("conversation_history", [])
            response = final_state.get("response", "")
            
            print(f"  Memory Loaded: {memory_loaded}")
            print(f"  Memory Updated: {memory_updated}")
            print(f"  History Length: {len(conversation_history)}")
            print(f"  Response: {response[:50]}...")
            
            if not (memory_loaded and memory_updated):
                memory_working = False
                print(f"  ❌ Memory not working properly")
            else:
                print(f"  ✅ Memory working correctly")
                
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            memory_working = False
    
    # Print summary
    print(f"\n📊 Conversation Memory Test Summary")
    print("=" * 50)
    if memory_working:
        print("✅ Conversation memory is working correctly")
        print(f"✅ All {total_messages} messages processed successfully")
        print(f"✅ Memory loaded and updated for all messages")
    else:
        print("❌ Conversation memory has issues")
        print("❌ Some messages failed to process")
    
    return memory_working


if __name__ == "__main__":
    asyncio.run(test_conversation_memory())
