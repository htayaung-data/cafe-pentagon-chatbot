"""
Services package for Cafe Pentagon Chatbot
"""

from .embedding_service import get_embedding_service, EmbeddingService

__all__ = ["get_embedding_service", "EmbeddingService"] 