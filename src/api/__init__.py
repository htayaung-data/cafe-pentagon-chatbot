"""
API module for Cafe Pentagon Chatbot
Contains FastAPI routes and endpoints
"""

from .admin_routes import admin_router

__all__ = ["admin_router"] 