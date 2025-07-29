"""
Cafe Pentagon RAG Chatbot Test Application
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.main_agent import EnhancedMainAgent
from src.data.loader import get_data_loader
from src.config.settings import get_settings
from src.utils.logger import get_logger

# Configure page
st.set_page_config(
    page_title="Cafe Pentagon RAG Chatbot",
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
</style>
""", unsafe_allow_html=True)

def initialize_agent():
    """Initialize agent once and store in session state"""
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = EnhancedMainAgent()
            return True
        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            return False
    return True

def clear_conversation():
    """Clear conversation history"""
    st.session_state.messages = []
    st.success("Conversation cleared!")

def process_user_message(user_message, user_id):
    """Process user message and get response"""
    try:
        # Call the agent
        result = asyncio.run(st.session_state.agent.chat(user_message, user_id))
        
        # Extract response and image info from the result
        if isinstance(result, dict):
            response = result.get('response', '')
            image_info = result.get('image_info')
            
            # If there's image info, add it to the response for display
            if image_info and image_info.get('image_url'):
                # The response already contains the markdown image, so we can return it as is
                return response
            else:
                return response
        elif isinstance(result, str):
            return result
        else:
            return str(result)
            
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def main():
    st.title("☕ Cafe Pentagon RAG Chatbot")
    st.markdown("---")
    
    # Initialize agent once
    if not initialize_agent():
        st.error("Failed to initialize the chatbot. Please check your configuration.")
        return
    
    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # User ID input
        user_id = st.text_input(
            "User ID",
            value="test_user_001",
            help="Enter a unique user ID for this conversation"
        )
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", type="primary"):
            clear_conversation()
    
    # Main chat area
    st.header("💬 Chat")
    
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
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show processing message
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                # Get response from agent
                response = process_user_message(prompt, user_id)
                
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
                
                # Add assistant message to chat
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 