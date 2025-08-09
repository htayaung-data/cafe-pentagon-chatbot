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
        # Entry guard: if admin has locked the conversation, skip processing and show notice
        from src.services.conversation_tracking_service import get_conversation_tracking_service
        tracking = get_conversation_tracking_service()
        try:
            status = tracking.get_conversation_status(conversation_id)
            if status and (status.get("human_handling") or not status.get("rag_enabled") or status.get("status") == "escalated"):
                # Indicate to UI to suppress assistant message entirely
                return {
                    "response": None,
                    "language": "en",
                    "strategy": "hitl_locked",
                    "confidence": 0.0,
                    "data_found": False,
                    "search_performed": False,
                    "search_namespace": "",
                    "search_terms": [],
                    "response_quality": "blocked"
                }
        except Exception:
            pass

        # Create initial state
        initial_state = create_initial_state(
            user_message=user_message,
            user_id=user_id,
            conversation_id=conversation_id,
            platform="streamlit"
        )
        
        # Execute LangGraph workflow (compile once and reuse)
        if 'compiled_langgraph' not in st.session_state:
            st.session_state.compiled_langgraph = st.session_state.langgraph_workflow.compile()
        final_state = await st.session_state.compiled_langgraph.ainvoke(initial_state)
        
        # Extract response and metadata from simplified system
        response = final_state.get("response", "")
        user_language = final_state.get("user_language", "en")
        response_strategy = final_state.get("response_strategy", "polite_fallback")
        analysis_confidence = final_state.get("analysis_confidence", 0.0)
        data_found = final_state.get("data_found", False)
        search_performed = final_state.get("search_performed", False)
        search_namespace = final_state.get("search_namespace_used", "")
        search_terms = final_state.get("search_terms_used", [])
        response_quality = final_state.get("response_quality", "fallback")
        
        # Log the processing results
        logger = get_logger("langgraph_app")
        logger.info("simplified_processing_completed",
                   user_id=user_id,
                   conversation_id=conversation_id,
                   user_language=user_language,
                   response_strategy=response_strategy,
                   analysis_confidence=analysis_confidence,
                   data_found=data_found,
                   search_performed=search_performed,
                   search_namespace=search_namespace,
                   response_quality=response_quality)
        
        # Note: Conversation tracking is handled by LangGraph workflow
        # No need to duplicate the conversation tracking here
        # LangGraph already saves messages and updates conversation status
        
        # Before returning to UI, re-check lock to avoid showing a message if admin just locked
        try:
            status_after = tracking.get_conversation_status(conversation_id)
            if status_after and (status_after.get("human_handling") or not status_after.get("rag_enabled") or status_after.get("status") == "escalated"):
                # Indicate to UI to suppress assistant message entirely
                return {
                    "response": None,
                    "language": user_language,
                    "strategy": response_strategy,
                    "confidence": analysis_confidence,
                    "data_found": data_found,
                    "search_performed": search_performed,
                    "search_namespace": search_namespace,
                    "search_terms": search_terms,
                    "response_quality": "blocked"
                }
        except Exception:
            pass

        return {
            "response": response,
            "language": user_language,
            "strategy": response_strategy,
            "confidence": analysis_confidence,
            "data_found": data_found,
            "search_performed": search_performed,
            "search_namespace": search_namespace,
            "search_terms": search_terms,
            "response_quality": response_quality
        }
        
    except Exception as e:
        logger = get_logger("langgraph_app")
        logger.error("langgraph_processing_failed", error=str(e))
        return {
            "response": "တောင်းပန်ပါတယ်၊ ပြဿနာတစ်ခု ဖြစ်နေပါတယ်။ ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ပြန်လည်မေးမြန်းပေးပါ။",
            "language": "my",
            "strategy": "polite_fallback",
            "confidence": 0.0,
            "data_found": False,
            "search_performed": False,
            "search_namespace": "",
            "search_terms": [],
            "response_quality": "fallback"
        }

def main():
    st.title("☕ Cafe Pentagon RAG Chatbot (Simplified)")
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
        
        # Simplified System Status
        st.header("📊 Simplified System Status")
        st.success("✅ 3-Node Workflow Active")
        st.info("🔄 Ultra-Simple Processing")
        st.info("🧠 Pure LLM-Driven Analysis")
        st.info("🔍 Direct Vector Search")
        st.info("📚 Real Data Responses")
    
    # Main chat area
    st.header("💬 Chat (Simplified)")
    
    # Initialize messages in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check if the message contains HTML images or markdown images
            content = message["content"]
            if isinstance(content, str) and ("<img" in content or "![(" in content):
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
                        if isinstance(part, str) and part.strip():
                            st.markdown(part)
            else:
                # Regular message without images
                if isinstance(content, str) and content.strip():
                    st.markdown(content)
            
            # Show metadata if available
            if "metadata" in message:
                metadata = message["metadata"]
                with st.expander("🔍 Simplified System Metadata"):
                    st.json(metadata)
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show processing message
        with st.chat_message("assistant"):
            with st.spinner("Processing with Simplified System..."):
                # Get response from LangGraph workflow
                result = asyncio.run(process_user_message_langgraph(
                    prompt, 
                    user_id, 
                    st.session_state.conversation_id
                ))
                
                response = result["response"]
                
                # Display response with proper image handling
                if isinstance(response, str) and ("<img" in response or "![(" in response):
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
                            if isinstance(part, str) and part.strip():
                                st.markdown(part)
                else:
                    # Regular response without images; suppress if blocked/None
                    if response is not None and response.strip():
                        st.markdown(response)
                
                # Add assistant message only if there is actual content
                if response is not None and isinstance(response, str) and response.strip():
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "metadata": {
                            "language": result["language"],
                            "strategy": result["strategy"],
                            "confidence": result["confidence"],
                            "data_found": result["data_found"],
                            "search_performed": result["search_performed"],
                            "search_namespace": result["search_namespace"],
                            "search_terms": result["search_terms"],
                            "response_quality": result["response_quality"]
                        }
                    })
                
                # Show processing summary only when we actually produced a response
                if response is not None and isinstance(response, str) and response.strip():
                    with st.expander("📊 Simplified System Processing Summary"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Language", result["language"])
                            st.metric("Strategy", result["strategy"])
                            st.metric("Confidence", f"{result['confidence']:.2f}")
                        with col2:
                            st.metric("Data Found", "✅" if result["data_found"] else "❌")
                            st.metric("Search Performed", "✅" if result["search_performed"] else "❌")
                            st.metric("Quality", result["response_quality"])

if __name__ == "__main__":
    main() 