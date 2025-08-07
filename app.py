"""
Cafe Pentagon RAG Chatbot - LangGraph Main Application
Replaces the old EnhancedMainAgent with LangGraph workflow
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
import os
from uuid import uuid4

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.graph.state_graph import create_conversation_graph, create_initial_state
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.logger import get_logger

# Configure page
st.set_page_config(
    page_title="Cafe Pentagon RAG Chatbot (LangGraph)",
    page_icon="☕",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .stButton > button {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
    }
    .stButton > button:hover {
        background-color: #ff3333;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .escalation-message {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    .rag-disabled {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

def initialize_langgraph():
    """Initialize LangGraph workflow once and store in session state"""
    if 'langgraph_workflow' not in st.session_state:
        try:
            st.session_state.langgraph_workflow = create_conversation_graph()
            st.session_state.conversation_tracking = get_conversation_tracking_service()
            return True
        except Exception as e:
            st.error(f"Failed to initialize LangGraph: {str(e)}")
            return False
    return True

def clear_conversation():
    """Clear conversation history"""
    st.session_state.messages = []
    st.session_state.conversation_id = str(uuid4())
    st.success("Conversation cleared!")

async def process_user_message_langgraph(user_message, user_id, conversation_id):
    """Process user message using LangGraph workflow"""
    try:
        # Create initial state
        initial_state = create_initial_state(
            user_message=user_message,
            user_id=user_id,
            conversation_id=conversation_id,
            platform="streamlit"
        )
        
        # Execute LangGraph workflow
        compiled_workflow = st.session_state.langgraph_workflow.compile()
        final_state = await compiled_workflow.ainvoke(initial_state)
        
        # Extract response and metadata
        response = final_state.get("response", "")
        detected_intent = final_state.get("detected_intent", "")
        intent_confidence = final_state.get("intent_confidence", 0.0)
        detected_language = final_state.get("detected_language", "")
        rag_enabled = final_state.get("rag_enabled", True)
        human_handling = final_state.get("human_handling", False)
        requires_human = final_state.get("requires_human", False)
        rag_results_count = len(final_state.get("rag_results", []))
        relevance_score = final_state.get("relevance_score", 0.0)
        
        # Log the processing results
        logger = get_logger("langgraph_app")
        logger.info("langgraph_processing_completed",
                   user_id=user_id,
                   conversation_id=conversation_id,
                   detected_intent=detected_intent,
                   intent_confidence=intent_confidence,
                   detected_language=detected_language,
                   rag_enabled=rag_enabled,
                   human_handling=human_handling,
                   requires_human=requires_human,
                   rag_results_count=rag_results_count,
                   relevance_score=relevance_score)
        
        # Note: Conversation tracking is handled by LangGraph workflow
        # No need to duplicate the conversation tracking here
        # LangGraph already saves messages and updates conversation status
        
        return {
            "response": response,
            "intent": detected_intent,
            "confidence": intent_confidence,
            "language": detected_language,
            "rag_enabled": rag_enabled,
            "human_handling": human_handling,
            "requires_human": requires_human,
            "rag_results_count": rag_results_count,
            "relevance_score": relevance_score
        }
        
    except Exception as e:
        logger = get_logger("langgraph_app")
        logger.error("langgraph_processing_failed", error=str(e))
        return {
            "response": "တောင်းပန်ပါတယ်၊ ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။ ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ပြန်လည်မေးမြန်းပေးပါ။",
            "intent": "error",
            "confidence": 0.0,
            "language": "my",
            "rag_enabled": False,
            "human_handling": False,
            "requires_human": False,
            "rag_results_count": 0,
            "relevance_score": 0.0
        }

def main():
    st.title("☕ Cafe Pentagon RAG Chatbot (LangGraph)")
    st.markdown("---")
    
    # Initialize LangGraph once
    if not initialize_langgraph():
        st.error("Failed to initialize the LangGraph chatbot. Please check your configuration.")
        return
    
    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ LangGraph Controls")
        
        # User ID input
        user_id = st.text_input(
            "User ID",
            value="test_user_001",
            help="Enter a unique user ID for this conversation"
        )
        
        # Conversation ID
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = str(uuid4())
        
        st.info(f"Conversation ID: {st.session_state.conversation_id[:8]}...")
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", type="primary"):
            clear_conversation()
        
        # LangGraph Status
        st.header("📊 LangGraph Status")
        st.success("✅ LangGraph Workflow Active")
        st.info("🔄 Stateful Conversation Management")
        st.info("🧠 Enhanced Burmese Processing")
        st.info("🔍 Intelligent Intent Classification")
        st.info("📚 RAG-Enabled Responses")
    
    # Main chat area
    st.header("💬 Chat (LangGraph)")
    
    # Initialize messages in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check if the message contains HTML images or markdown images
            content = message["content"]
            if "<img" in content or "![(" in content:
                # Split content to separate text and images
                import re
                # Split by HTML img tags
                parts = re.split(r'(<img[^>]+>)', content)
                
                for part in parts:
                    if part.startswith('<img'):
                        # This is an HTML image, render it with unsafe_allow_html
                        st.markdown(part, unsafe_allow_html=True)
                    elif part.startswith('![') and part.endswith(')'):
                        # This is a markdown image, render it
                        st.markdown(part, unsafe_allow_html=True)
                    else:
                        # This is regular text
                        if part.strip():
                            st.markdown(part)
            else:
                # Regular message without images
                st.markdown(content)
            
            # Show metadata if available
            if "metadata" in message:
                metadata = message["metadata"]
                with st.expander("🔍 LangGraph Metadata"):
                    st.json(metadata)
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show processing message
        with st.chat_message("assistant"):
            with st.spinner("Processing with LangGraph..."):
                # Get response from LangGraph workflow
                result = asyncio.run(process_user_message_langgraph(
                    prompt, 
                    user_id, 
                    st.session_state.conversation_id
                ))
                
                response = result["response"]
                
                # Display response with proper image handling
                if "<img" in response or "![(" in response:
                    # Split content to separate text and images
                    import re
                    # Split by HTML img tags
                    parts = re.split(r'(<img[^>]+>)', response)
                    
                    for part in parts:
                        if part.startswith('<img'):
                            # This is an HTML image, render it with unsafe_allow_html
                            st.markdown(part, unsafe_allow_html=True)
                        elif part.startswith('![') and part.endswith(')'):
                            # This is a markdown image, render it
                            st.markdown(part, unsafe_allow_html=True)
                        else:
                            # This is regular text
                            if part.strip():
                                st.markdown(part)
                else:
                    # Regular response without images
                    st.markdown(response)
                
                # Add assistant message to chat with metadata
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "metadata": {
                        "intent": result["intent"],
                        "confidence": result["confidence"],
                        "language": result["language"],
                        "rag_enabled": result["rag_enabled"],
                        "human_handling": result["human_handling"],
                        "requires_human": result["requires_human"],
                        "rag_results_count": result["rag_results_count"],
                        "relevance_score": result["relevance_score"]
                    }
                })
                
                # Show processing summary
                with st.expander("📊 LangGraph Processing Summary"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Intent", result["intent"])
                        st.metric("Confidence", f"{result['confidence']:.2f}")
                        st.metric("Language", result["language"])
                    with col2:
                        st.metric("RAG Enabled", "✅" if result["rag_enabled"] else "❌")
                        st.metric("RAG Results", result["rag_results_count"])
                        st.metric("Relevance Score", f"{result['relevance_score']:.2f}")

if __name__ == "__main__":
    main() 