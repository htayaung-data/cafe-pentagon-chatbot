"""
Comprehensive Testing Suite for Cafe Pentagon Chatbot
Covers all LangGraph nodes, services, and integration points
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test configuration
TEST_CONFIG = {
    "mock_services": True,
    "use_real_apis": False,
    "test_database": "test_supabase",
    "test_pinecone": "test_index",
    "test_openai": "test_key"
} 